import os
from tqdm import tqdm
import json
import re
import subprocess
from typing import Dict, List, Any
import base64
import concurrent.futures
import sys
import shutil
import argparse
import traceback

JSON_REPORT_FILENAME = "pytest_report.json"

def parse_pytest_output_dict_format(output: str) -> Dict[str, Any]:
    """
    Parses pytest output, retaining original summary keys and adding a
    dictionary mapping detailed test case nodeids to their outcomes.
    Uses raw_decode to handle trailing non-JSON text.

    Args:
        output: Raw pytest output text, potentially containing an embedded JSON report.

    Returns:
        Dictionary containing:
        - passed, failed, warnings, errors: Original summary counts.
        - total_tests: Original total_tests calculation (p+f+e+w).
        - errors_info, failures_info: Text blocks from summary.
        - output: Raw output text (can be large).
        --- Added/Modified Keys ---
        - has_detailed_results: Boolean indicating if JSON report was parsed AND contained test info.
        - detailed_dict: Dictionary mapping test case nodeid (str) to outcome string ('passed', 'failed', etc.).
        - detailed_parse_error: Error message if JSON parsing failed (or None).
    """
    results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0,
        'errors': 0,
        'total_tests': 0,
        'errors_info': None,
        'failures_info': None,
        'output': output,
        # --- New structure for detailed results ---
        'has_detailed_results': False,
        'detailed_dict': {}, # Initialize as empty dict
        'detailed_parse_error': None
    }

    # --- 1. Parse Original Summary Info ---
    results['passed'] = int(re.search(r'(\d+) passed', output).group(1)) if re.search(r'(\d+) passed', output) else 0
    results['failed'] = int(re.search(r'(\d+) failed', output).group(1)) if re.search(r'(\d+) failed', output) else 0
    results['warnings'] = int(re.search(r'(\d+) warnings?', output).group(1)) if re.search(r'(\d+) warnings?', output) else 0
    results['errors'] = int(re.search(r'(\d+) errors?', output).group(1)) if re.search(r'(\d+) errors?', output) else 0
    results['total_tests'] = results['passed'] + results['failed'] + results['errors'] + results['warnings']

    errors_match = re.search(r'=+ ERRORS =+(.*?)(?=\n=+ \w+ =+|\Z)', output, re.DOTALL)
    if errors_match:
        results['errors_info'] = errors_match.group(1).strip()

    failures_match = re.search(r'=+ FAILURES =+(.*?)(?=\n=+ \w+ =+|\Z)', output, re.DOTALL)
    if failures_match:
        results['failures_info'] = failures_match.group(1).strip()

    # --- 2. Parse Detailed JSON Report and build detailed_dict ---
    json_start_index = -1
    try:
        # Heuristic to find the start of the JSON report block
        json_start_index = output.rfind('{"created":') # Based on sample output
        if json_start_index != -1:
            decoder = json.JSONDecoder()
            json_data, end_index = decoder.raw_decode(output, json_start_index)
            # JSON decoding itself succeeded

            if 'tests' in json_data and isinstance(json_data['tests'], list):
                temp_detailed_dict = {}
                found_valid_tests = False
                for test in json_data['tests']:
                    nodeid = test.get('nodeid')
                    outcome = str(test.get('outcome', 'unknown')).lower()
                    if nodeid: # Check if nodeid is present and not None/empty
                        temp_detailed_dict[nodeid] = outcome
                        found_valid_tests = True # Mark that we found at least one usable test entry
                    else:
                        # This case should be rare with standard pytest runs
                        print(f"Warning: Found test entry with missing nodeid in JSON report. Skipping entry: {test}")

                if found_valid_tests:
                    results['detailed_dict'] = temp_detailed_dict
                    results['has_detailed_results'] = True # Set flag only if we got usable data
                else:
                    # JSON parsed and 'tests' list found, but contained no valid test entries (e.g., all missing nodeid)
                    results['detailed_parse_error'] = "JSON 'tests' list found, but contained no entries with valid nodeids."
                    results['has_detailed_results'] = False
                    results['detailed_dict'] = {}

            else:
                # JSON was parsed correctly, but didn't contain the expected 'tests' list structure
                results['detailed_parse_error'] = "JSON parsed, but 'tests' key missing or not a list."
                results['has_detailed_results'] = False
                results['detailed_dict'] = {}
        # else: JSON start marker not found, results remain default (has_detailed_results=False)

    except json.JSONDecodeError as e:
        results['detailed_parse_error'] = f"JSONDecodeError: {e}. Attempted start index: {json_start_index}."
        results['has_detailed_results'] = False
        results['detailed_dict'] = {} # Ensure dict is empty on error
    except Exception as e:
        results['detailed_parse_error'] = f"Unexpected error processing JSON: {e}"
        results['has_detailed_results'] = False
        results['detailed_dict'] = {} # Ensure dict is empty on error

    return results

def run_tests_in_docker(metadata: Dict, file_code_key: str = "GT_file_code") -> Dict:
    """Run tests in Docker container using specified file code
    
    Args:
        metadata: Test configuration metadata
        file_code_key: Key in metadata containing the file code to test
        
    Returns:
        Detailed test results dictionary from parse_pytest_output
    """
    package_name = metadata["package_name"]
    
    # Build test script
    script_content = "#!/bin/sh\nset -e\n"
    
    # Write test files to container
    if file_code_key:
        for rel_path, content in metadata[file_code_key].items():
            container_path = os.path.join(metadata["dir_path"], rel_path)
            container_path_escaped = container_path.replace("'", "'\\''")
            encoded_content = base64.b64encode(content.encode()).decode()
            script_content += (
                f"mkdir -p \"$(dirname '{container_path_escaped}')\"\n"
                f"printf '%s' {encoded_content} | base64 -d > '{container_path_escaped}'\n"
            )
        
    # Run pytest
    test_file_path = os.path.join(metadata["dir_path"], metadata["test_file"])
    test_dir = os.path.dirname(test_file_path)
    test_filename_escaped = os.path.basename(test_file_path).replace("'", "'\\''")
    script_content += f"cd '{test_dir.replace("'", "'\\''")}'\n"
    script_content += f"pytest -v --json-report --json-report-file={JSON_REPORT_FILENAME} '{test_filename_escaped}' || true\n"
    script_content += f"if [ -f {JSON_REPORT_FILENAME} ]; then cat {JSON_REPORT_FILENAME}; else echo 'JSON report file not found.'; fi\n"

    try:
        result = subprocess.run(
            ['docker', 'run', '--rm', '-i', f'{package_name}-image', 'sh', '-s'],
            input=script_content,
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout + result.stderr
    except subprocess.CalledProcessError as e:
        output = e.stdout + e.stderr

    return parse_pytest_output_dict_format(output)

def evaluator(metadata_path: str, target_dir: str):
    """Main evaluation function that:
    1. Runs tests with GT_file_code to get baseline passed count
    2. Runs tests with generated_file_code
    3. Calculates pass rate using GT passed count as denominator
    4. Includes detailed error info and raw output from both runs
    
    Args:
        metadata_path: Path to metadata JSON file
    """
    with open(metadata_path) as f:
        metadata = json.load(f)

    # First run with GT_file_code to get baseline results
    gt_results = run_tests_in_docker(metadata, "")
    max_possible_passed = gt_results['passed']
    
    # 修改部分
    for key in metadata['GT_file_code'].keys():
        if key not in metadata['GPT4o_file_code'].keys():
            metadata['GPT4o_file_code'][key] = metadata['file_code'][key]
        
    # Then run with generated_file_code
    gen_results = run_tests_in_docker(metadata, "GPT4o_file_code") #根据生成代码的键进行相应修改

    for key in gen_results['detailed_dict'].keys():
        if key not in gt_results['detailed_dict'].keys():
            gt_results['detailed_dict'][key] = 'failed'

    # Calculate pass rate using GT passed count as denominator
    if max_possible_passed > 0 :
        passed_rate = gen_results['passed'] / max_possible_passed
        if passed_rate > 1.0:
            passed_rate = 1.0
    else:
        passed_rate = 0.0

    # Prepare final results with all details
    test_results = {
        'gt_results': {
            'passed': gt_results['passed'],
            'warnings': gt_results['warnings'],
            'total_tests': gt_results['total_tests'],
            'output': gt_results['output'],
            'detailed_dict': gt_results['detailed_dict']
        },
        'generated_results': {
            'passed': gen_results['passed'],
            'failed': gen_results['failed'],
            'warnings': gen_results['warnings'],
            'errors': gen_results['errors'],
            'total_tests': gen_results['total_tests'],
            'errors_info': gen_results['errors_info'],
            'failures_info': gen_results['failures_info'],
            'output': gen_results['output'],
            'detailed_dict': gen_results['detailed_dict']
        },
        'passed_rate': round(passed_rate, 4),
        'max_possible_passed': max_possible_passed
    }

    # Save results
    # Get current working directory
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    output_path = os.path.join(target_dir, f"{metadata['sample_name']}_adjusted.json")
    
    with open(output_path, 'w') as f:
        json.dump(test_results, f, indent=2)

    print(f"Adjusted test results saved to: {current_dir}/{output_path}")

# --- Pass@k Calculation Functions ---
def calculate_pass_at_k(metadata_ls, target_dir, sample_ls, k=1):
    """
    Calculate the Pass@k metric, using the average pass rate of each sample as the result.

    Args:
        metadata_ls: A list containing all evaluation folders.
        target_dir: The directory for evaluation results.
        k: The k value, representing the number of attempts.

    Returns:
        The sample-level Pass@k value and detailed sample pass information.
    """
    # Collect the test case results for all samples.
    sample_results = {}  # {sample_name: [model1_results, model2_results, ...]}
    num_samples = len(sample_ls)
    
    for eval_folder in metadata_ls:
        eval_folder_path = os.path.join(target_dir, eval_folder)
        if not os.path.exists(eval_folder_path):
            print(f"Warning: Folder {eval_folder_path} does not exist.")
            continue
            
        for sample_name in sample_ls:
            sample_fpath = os.path.join(eval_folder_path, f"{sample_name}_adjusted.json")
            if os.path.exists(sample_fpath):
                with open(sample_fpath, 'r') as f:
                    result_data = json.load(f)

                # Extract the test case pass information from the ground truth (GT) and the generated results.
                result_entry = {
                    "gt_detailed": result_data.get('gt_results', {}).get('detailed_dict', {}),
                    "gen_detailed": result_data.get('generated_results', {}).get('detailed_dict', {}),
                    "total_tests": result_data.get('gt_results', {}).get('passed', 0),
                    'total_passed': result_data.get('generated_results', {}).get('passed', 0),
                }
                if sample_name not in sample_results:
                    sample_results[sample_name] = []
                sample_results[sample_name].append(result_entry)
            else:
                result_entry = {
                    "gt_detailed": {},
                    "gen_detailed": {},
                    "total_tests": 0,
                    'total_passed': 0,
                }
                if sample_name not in sample_results:
                    sample_results[sample_name] = []
                sample_results[sample_name].append(result_entry)

    # Calculate the Pass@k for each sample.
    sample_pass_rates = []
    sample_details = {}
    exact_testcases = 0
    gt_testcases = 0
    sample_passat1_rates = []
    for sample_name, attempts in sample_results.items():
        # Truncate the number of attempts to k (if there are enough attempts).
        sample_attempts = attempts[:k] if len(attempts) >= k else attempts
        exact_testcases += max(attempt.get('total_tests', 0) for attempt in sample_attempts) if sample_attempts else 0

        # Identify all test cases that passed in the Ground Truth (GT).
        gt_passed_cases = set()
        passrate_ls = []
        for attempt in sample_attempts:
            passrate_ls.append(attempt['total_passed']/attempt['total_tests'] if attempt['total_tests'] > 0 else 0)
            for test_id, status in attempt["gt_detailed"].items():
                if status == 'passed':
                    gt_passed_cases.add(test_id)
        gt_testcases += len(gt_passed_cases)
        sample_passat1_rates.append(sum(passrate_ls)/len(passrate_ls))

        # If there are no test cases that passed in the Ground Truth (GT), skip that sample.
        if not gt_passed_cases:
            sample_pass_rates.append(0)
            continue
            
        # For that sample, calculate the number of test cases that passed within k attempts.
        sample_successful_tests = 0
        sample_test_details = {}
        
        for test_id in gt_passed_cases:
            # Initialize the test case details.
            sample_test_details[test_id] = {
                "gt_passed": True,
                "k_passed": False,
                "attempts_passed": []
            }
            
            # Check if any of the k attempts have passed.
            test_passed_in_k = False
            for i, attempt in enumerate(sample_attempts):
                gen_status = attempt["gen_detailed"].get(test_id)
                if gen_status == 'passed':
                    test_passed_in_k = True
                    sample_test_details[test_id]["attempts_passed"].append(i)
            
            if test_passed_in_k:
                sample_successful_tests += 1
                sample_test_details[test_id]["k_passed"] = True
        
        # Calculate the Pass@K for that sample.
        sample_pass_rate = sample_successful_tests / len(gt_passed_cases)
        sample_pass_rates.append(sample_pass_rate)
        
        # Store the sample details.
        sample_details[sample_name] = {
            "pass_rate": sample_pass_rate,
            "successful_tests": sample_successful_tests,
            "total_gt_passed": len(gt_passed_cases),
            "test_details": sample_test_details
        }

    # Calculate the average Pass@k for all samples.
    avg_pass_at_k = sum(sample_pass_rates) / num_samples
    avg_passat1_rate = sum(sample_passat1_rates) / num_samples
    print(f"Total GT passed tests: {exact_testcases} in {num_samples} samples")  
    print(f"Total GT tests: {gt_testcases} in {num_samples} samples")
    print(f"Avg Pass@1 rate of {k} attempts: {avg_passat1_rate}")
    print(f"Avg Pass@{k} rate of {k} attempts: {avg_pass_at_k}")
    return {
        "pass_at_k": avg_pass_at_k,
        "sample_pass_rates": sample_pass_rates,
        "num_samples": len(sample_pass_rates),
        "sample_details": sample_details
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str)
    parser.add_argument("--level", type=str, default="easy")
    parser.add_argument("--time_str", type=str, default="")
    parser.add_argument("--source_path", type=str)
    parser.add_argument("--pass_k", type=int, default=3)
    parser.add_argument("--save_name", type=str)
    parser.add_argument("--num_workers", type=int)
    args = parser.parse_args()

    metadata_dir = f"path/generation" # you should replace this with the path to the generation results
    target_dir = f'path/evaluation' # you should replace this with the path to the evaluation results

    metadata_ls = [sample for sample in os.listdir(metadata_dir) if sample.startswith(f'{args.save_name}_{args.model_name}_{args.level}')]
    for metadata_path in metadata_ls:
        target_dir_level = os.path.join(target_dir, metadata_path)
        metadata_dir_level = os.path.join(metadata_dir, metadata_path)
        sample_files = os.listdir(metadata_dir_level)
        sample_paths = [os.path.join(metadata_dir_level, sample_ls) for sample_ls in sample_files]
        if not os.path.exists(target_dir_level):
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_workers) as executor:
                futures = []
                for sample_path in tqdm(sample_paths, desc="Processing samples"):
                    future = executor.submit(evaluator, sample_path, target_dir_level)
                    futures.append(future)
                    
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing samples" ):  # 10 minutes timeout
                    try:
                        future.result()
                    except concurrent.futures.TimeoutError:
                        print(f"[ERROR] Timeout after 10 minutes for {future}")
                    except Exception as e:
                        print(f"[ERROR] Exception occurred: {e}")
                        traceback.print_exc()
    # --- Always run Pass@k Calculation Step ---
    print(f"\n--- Starting Pass@{args.pass_k} Calculation ---")
    print(f"Loading results from: {target_dir}")
    
    # Calculate Pass@k
    sample_file_ls = os.listdir(os.path.join(args.source_path, f"{args.level}"))
    sample_file_ls = [sample_file.split('-level')[0] for sample_file in sample_file_ls]
    pass_k_results = calculate_pass_at_k(metadata_ls, target_dir, sample_file_ls, args.pass_k)
    