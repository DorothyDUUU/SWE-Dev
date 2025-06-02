import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import re
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor,as_completed
import traceback
import time
import argparse
from llm_caller import LLM

def extract_class_info_new(text:str):
    if text is None or text == "":
        return {}
    else:    
        pattern = r"@(.*?)\n```python\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)

        code_info = {}
        for match in matches:
            file_path = match[0].strip()
            if not file_path.endswith('.py'):
                file_path = file_path + '.py'
            code = match[1]
            code_info[file_path] = code
        return code_info

def process_sample(sample_ls, reviewer_config, des_path, file_paths):

    sample_path = os.path.join(file_paths, sample_ls)
    with open(sample_path, 'r') as file:
        metadata = json.load(file)
    llm = LLM(reviewer_config)
    GT_src_dict = metadata['GT_src_dict']
    metadata["Generate_code"] = {}
    new_metadata_path = os.path.join(des_path, sample_ls)
    try:
        PRD= metadata['PRD']
        file_code = metadata['file_code']

        code_snippet = ""

        for file_path, code in file_code.items():
            code_snippet += f"@ {file_path}\n```python\n{code}\n```\n"
        
        content = f"""# AIM: You need to assist me with a Python package feature development task. I will provide a Product Requirements Document (PRD) that details the functionality and lists the empty functions that need to be implemented across different file paths. I will also provide the complete "Code Context" of all files mentioned in the PRD.

Your task is to implement ONLY the empty functions described in the PRD while preserving ALL OTHER CODE in the provided files exactly as is. This is absolutely critical - you must keep all imports, class definitions, functions, comments, and other code that is not explicitly mentioned in the PRD for implementation.

When implementing the functions:
1. Carefully identify which functions from the PRD need implementation.Implement them based on the docstrings and specifications in the PRD
2. Do not add any new "import" statements unless absolutely necessary
3. Do not modify ANY existing code structure, only implement the empty functions

For each file mentioned in the PRD, you MUST output the COMPLETE file code with your implementations inserted. Your output format must follow this exact pattern:

# OUTPUT FORMAT FOR EACH FILE:
@ [relative path/filename]
```python
[COMPLETE file code including ALL original code plus your implementations]
```
@ [relative path/filename]
```python
[COMPLETE file code including ALL original code plus your implementations]
```

IMPORTANT: Make sure your output includes EVERY function, class, import statement, and comment from the original code context. The only difference should be that the empty functions specified in the PRD are now implemented.

# PRD:
{PRD}

# Code Context:
{code_snippet}"""
        response_content = llm.completion(content,sample_ls)
        code_info = extract_class_info_new(response_content)

        if code_info != {}:
            for file_path, code in code_info.items():
                metadata["Generate_code"][file_path] = code

        with open(new_metadata_path, 'w') as file:
            json.dump(metadata, file, indent=4)
        
        print(f"[INFO] PROCESSING {sample_ls}")
        print(f"[INFO] SAVED TO {new_metadata_path}")
    except Exception as e:
        print(f"[ERROR] {sample_ls} Exception occurred: {e}")
        traceback.print_exc() 


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str)
    parser.add_argument("--dataset_path", type=str)
    parser.add_argument("--num_workers", type=int, default=10)
    parser.add_argument("--api_base_url", type=str, help="If not provided, the default API base URL will be used")
    parser.add_argument("--api_key", type=str, help="If not provided, the default API key will be used")
    parser.add_argument("--level", type=str, default="easy")
    parser.add_argument("--pass_k", type=int, default=3)
    parser.add_argument("--time", type=str, default='', help="Resume from the time")
    parser.add_argument("--save_name", type=str)
    args = parser.parse_args()

    print(f"[INFO] LEVEL: {args.level}")
    for i in range(args.pass_k):

        model_config_dict = {
            'gpt-4o': {'model': 'gpt-4o', 'api_key': args.api_key, 'base_url': args.api_base_url, 'max_token': 8192},
            'gpt-4o-mini': {'model': 'gpt-4o-mini', 'api_key': args.api_key, 'base_url': args.api_base_url, 'max_token': 8192},
        }

        model_config = model_config_dict[args.model_name]
        if args.pass_k != 1:
            model_config['temperature'] = 0.5
        if args.time == '':
            time_str = time.strftime("%m%d_%H%M", time.localtime())
        else:
            time_str = args.time

        des_path = f"results/single_agent/{args.save_name}_{args.model_name}_{args.level}_{time_str}"
        if not os.path.exists(des_path):
            os.makedirs(des_path)
        
        if not args.dataset_path:
            dataset_path = f"SWE-Dev-dataset/data/test/{args.level}"
        else:
            dataset_path = f"{args.dataset_path}/{args.level}"
        sample_files = os.listdir(dataset_path)
        already_processed_files = os.listdir(des_path)
        sample_files = [file for file in sample_files if file not in already_processed_files]
        print(f"[INFO] Total samples: {len(sample_files)}")

        with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
            futures = [executor.submit(process_sample, sample_file, model_config, des_path, dataset_path) for sample_file in sample_files]
            for future in tqdm(as_completed(futures), total=len(sample_files), desc="Processing samples"):
                future.result()
