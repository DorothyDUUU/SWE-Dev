# Standard library imports (no comments per requirement)
import os
import shutil
import glob
import subprocess
import json
import concurrent.futures
import argparse
import threading
from tqdm import tqdm
import traceback
import re
import sys
from methods import method2class, get_method_class  # Custom module for method handling

class SuppressPrints:
    """Context manager for conditionally suppressing print outputs.
    
    Attributes:
        suppress (bool): Flag to determine if output should be suppressed
        original_stdout (file): Reference to the original stdout stream
    """
    def __init__(self, suppress):
        self.suppress = suppress
        self.original_stdout = None
        
    def __enter__(self):
        """Redirects stdout to devnull when suppression is enabled."""
        if self.suppress:
            self.original_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')  # Discard output
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restores original stdout stream after context exit."""
        if self.suppress:
            sys.stdout.close()
            sys.stdout = self.original_stdout  # Restore original output

# Command-line argument configuration
parser = argparse.ArgumentParser(description="Distributed inference pipeline for code generation models")
parser.add_argument("--method", type=str, required=True, 
                   choices=method2class.keys(), 
                   help="Algorithmic approach for code generation")
parser.add_argument("--metadata_folder", type=str, required=True,
                   help="Directory containing JSON metadata files with prompts and context")
parser.add_argument("--max_workers", type=int, default=50,
                   help="Maximum parallel threads for metadata processing")
parser.add_argument("--method_config_name", type=str, default=None,
                   help="Configuration preset for the selected method")
parser.add_argument("--model_name", type=str, default="gpt-4o-mini",
                   help="Target LLM for code generation")
parser.add_argument("--model_api_config", type=str, default="model_api_configs/model_api_config.json",
                   help="Path to API configuration file for model access")
parser.add_argument("--model_temperature", type=float, default=0.5,
                   help="Creativity control parameter for LLM generation (0-1)")
parser.add_argument("--model_max_tokens", type=int, default=8192,
                   help="Token limit for LLM responses")
parser.add_argument("--model_timeout", type=int, default=600,
                   help="Maximum execution time (seconds) per inference call")
parser.add_argument("--require_val", action="store_true",
                   help="Enable validation step in processing pipeline")
parser.add_argument("--show_method_prints", action="store_true",
                   help="Display intermediate outputs from method classes")
args = parser.parse_args()

# Initialize result directory for current method
tmp_result_dir = os.path.join("result", args.method)
os.makedirs(tmp_result_dir, exist_ok=True)  # Ensure directory exists

def load_model_api_config(model_api_config, model_name):
    """Loads and processes API configuration for target model.
    
    Args:
        model_api_config (str): Path to configuration file
        model_name (str): Identifier for target LLM
        
    Returns:
        dict: Processed configuration with max_workers calculation
    """
    with open(model_api_config, "r") as f:
        model_api_config = json.load(f)
    for model_name in model_api_config:
        # Calculate total concurrent workers across all instances
        actural_max_workers = model_api_config[model_name]["max_workers_per_model"] * len(model_api_config[model_name]["model_list"])
        model_api_config[model_name]["max_workers"] = actural_max_workers
    return model_api_config

def write_to_jsonl(lock, file_name, data):
    """Thread-safe JSONL writing with file locking.
    
    Args:
        lock (threading.Lock): Synchronization primitive
        file_name (str): Target output file path
        data (dict): Record to append
    """
    with lock:  # Acquire exclusive file access
        with open(file_name, 'a') as f:
            json.dump(data, f)
            f.write('\n')  # Newline-delimited JSON format

def remove_docstrings(code: str) -> str:
    """Sanitizes code by removing docstrings for model efficiency.
    
    Args:
        code (str): Source code to process
        
    Returns:
        str: Code with docstrings removed
    """
    pattern = r"\"\"\".*?\"\"\"|'''.*?'''"  # Regex for triple-quoted strings
    cleaned_code = re.sub(pattern, "", code, flags=re.DOTALL)
    return cleaned_code.strip()

def reserve_unprocessed(output_json, test_dataset):
    """Filters dataset to exclude already processed samples.
    
    Args:
        output_json (str): Path to existing results file
        test_dataset (list): Full dataset to filter
        
    Returns:
        list: Unprocessed samples
    """
    processed_queries = set()
    if os.path.exists(output_json):
        with open(output_json, "r") as f:
            for line in f:
                infered_sample = json.loads(line)
                processed_queries.add(infered_sample["query"])
    return [sample for sample in test_dataset if sample["query"] not in processed_queries]

def load_sample_from_metadata(metadata_path):
    """Extracts inference samples from metadata file.
    
    Args:
        metadata_path (str): Path to JSON metadata file
        
    Returns:
        list: Processed samples with query and sanitized code
    """
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    # Structure data for processing pipeline
    return [{"query": metadata.get("PRD", ""), "file_code": metadata.get("file_code", "")}]

def process_sample(general_config, sample, output_file, lock):
    """Executes single inference task and saves results.
    
    Args:
        general_config (dict): Global configuration parameters
        sample (dict): Input data sample
        output_file (str): Results destination path
        lock (threading.Lock): File write synchronization
    """
    metadata_name = os.path.splitext(os.path.basename(general_config['metadata_path']))[0]
    # Dynamic method class instantiation
    MAS_METHOD = get_method_class(general_config['method_name'], metadata_name)
    
    # Initialize method class with appropriate configuration
    if general_config['method_config_name'] is not None:
        mas = MAS_METHOD(general_config, method_config_name=general_config['method_config_name'])
    else:
        mas = MAS_METHOD(general_config)
    
    save_data = sample.copy()  # Initialize result container
    query = sample["query"]
    metadata_file = sample['file_code']
    
    # Preprocess code files
    for filename, code in metadata_file.items():
        metadata_file[filename] = remove_docstrings(code)
    
    try:
        # Execute inference with output suppression control
        with SuppressPrints(suppress=not general_config['show_method_prints']):
            response = mas.inference(query=query, file_code=metadata_file)
        save_data["generated_output"] = {filename: code for filename, code in response.items()}
    except Exception as e:
        # Capture full error trace for diagnostics
        save_data["error"] = f"Inference Error: {traceback.format_exc()}"
    
    # Append token usage statistics
    save_data.update({"token_stats": mas.get_token_stats()})
    write_to_jsonl(lock, output_file, save_data)  # Persist results

def run_inference(metadata_file):
    """Orchestrates processing pipeline for a metadata file.
    
    Args:
        metadata_file (str): Path to target metadata file
    """
    # Consolidate configuration parameters
    general_config = {
        'method_name': args.method,
        'method_config_name': args.method_config_name,
        'model_name': args.model_name,
        'model_api_config': load_model_api_config(args.model_api_config, args.model_name),
        'model_temperature': args.model_temperature,
        'model_max_tokens': args.model_max_tokens,
        'model_timeout': args.model_timeout,
        'require_val': args.require_val,
        'metadata_path': metadata_file,
        'output_path': tmp_result_dir,
        'show_method_prints': args.show_method_prints
    }
    
    # Load and preprocess dataset
    test_dataset = load_sample_from_metadata(metadata_file)
    metadata_name = os.path.splitext(os.path.basename(metadata_file))[0]
    output_file = os.path.join(tmp_result_dir, f"{metadata_name}_results.jsonl")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Filter processed samples
    test_dataset = reserve_unprocessed(output_file, test_dataset)
    
    # Optional validation setup
    if args.require_val:
        MAS_METHOD = get_method_class(args.method, metadata_name)
        if args.method_config_name is not None:
            mas = MAS_METHOD(general_config, method_config_name=args.method_config_name)
        else:
            mas = MAS_METHOD(general_config)
    
    # Process remaining samples
    if test_dataset:
        # Determine optimal concurrency from API config
        max_workers = general_config['model_api_config'][args.model_name]["max_workers"]
        lock = threading.Lock()  # Resource synchronization
        
        # Parallel execution with thread pooling
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map samples to processing function
            executor.map(lambda sample: process_sample(general_config, sample, output_file, lock), test_dataset)
    
    # Organize final outputs
    folder_name = os.path.basename(args.metadata_folder)
    output_dir = f"{args.method}_result_{folder_name}"  # Structured output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy original metadata to results directory
    copied_metadata_path = os.path.join(output_dir, os.path.basename(metadata_file))
    shutil.copy(metadata_file, copied_metadata_path)
    
    # Merge generated outputs with original metadata
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            results = json.load(f)
            generated_output = results.get("generated_output", None)
        
        if generated_output is not None:
            with open(copied_metadata_path, 'r+') as f:
                metadata_content = json.load(f)
                metadata_content["generated_file_code"] = generated_output  # Augment with results
                f.seek(0)
                json.dump(metadata_content, f, indent=4)  # Overwrite file
                f.truncate()

# Main execution block
if __name__ == "__main__":
    # Discover all metadata files in target directory
    metadata_files = glob.glob(os.path.join(args.metadata_folder, "*.json"))
    
    # Progress-tracked parallel processing
    with tqdm(total=len(metadata_files), desc="Processing metadata files") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            # Dispatch metadata processing tasks
            futures = {executor.submit(run_inference, file): file for file in metadata_files}
            for future in concurrent.futures.as_completed(futures):
                pbar.update(1)  # Update progress per completed task