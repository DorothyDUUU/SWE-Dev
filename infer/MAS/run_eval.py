import os
import argparse
from concurrent.futures import ThreadPoolExecutor


import os
import json
import re
import subprocess
from typing import Dict
import base64

def parse_pytest_output(output: str) -> dict:
    """Parse pytest output and return detailed test statistics
    
    Args:
        output: Raw pytest output text
        
    Returns:
        Dictionary containing:
        - passed: Number of passed tests
        - failed: Number of failed tests
        - warnings: Number of warnings
        - errors: Number of errors
        - total_tests: Total test indicators (tests + warnings)
        - errors_info: Error details text block
        - failures_info: Failure details text block
        - output: Raw output text
    """
    passed = int(re.search(r'(\d+) passed', output).group(1)) if re.search(r'(\d+) passed', output) else 0
    failed = int(re.search(r'(\d+) failed', output).group(1)) if re.search(r'(\d+) failed', output) else 0
    warnings = int(re.search(r'(\d+) warnings?', output).group(1)) if re.search(r'(\d+) warnings?', output) else 0
    errors = int(re.search(r'(\d+) errors?', output).group(1)) if re.search(r'(\d+) errors?', output) else 0
    
    # Extract error details
    errors_section = None
    errors_match = re.search(
        r'=+ ERRORS =+(.*?)(?=\n=+ \w+ =+|\Z)',
        output, 
        re.DOTALL
    )
    if errors_match:
        errors_section = errors_match.group(1).strip()

    # Extract failure details
    failures_section = None
    failures_match = re.search(
        r'=+ FAILURES =+(.*?)(?=\n=+ \w+ =+|\Z)',
        output, 
        re.DOTALL
    )
    if failures_match:
        failures_section = failures_match.group(1).strip()

    return {
        'passed': passed,
        'failed': failed,
        'warnings': warnings,
        'errors': errors,
        'total_tests': passed + failed + errors + warnings,
        'errors_info': errors_section,
        'failures_info': failures_section,
        'output': output
    }

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
    script_content += f"cd '{test_dir.replace("'", "'\\''")}'\n"
    script_content += f"pytest '{os.path.basename(test_file_path).replace("'", "'\\''")}'\n"

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

    return parse_pytest_output(output)

def get_next_metadata_index(target_dir: str) -> int:
    """Get the next available index for metadata files
    
    Args:
        target_dir: Directory to check for existing files
        
    Returns:
        Next available index (starting from 0 if no files exist)
    """
    existing_files = [f for f in os.listdir(target_dir) if f.startswith('metadata_') and f.endswith('_adjusted.json')]
    if not existing_files:
        return 0
    
    indices = []
    for f in existing_files:
        try:
            idx = int(f.split('_')[1])
            indices.append(idx)
        except (IndexError, ValueError):
            continue
    
    return max(indices) + 1 if indices else 0

def evaluator(metadata_path: str):
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

    # Check if generated_file_code exists and is not None
    if "generated_file_code" not in metadata or not metadata["generated_file_code"]:
        print("No generated_file_code found; skipping.")
        return

    # First run with GT_file_code to get baseline results
    gt_results = run_tests_in_docker(metadata, "GT_file_code")
    max_possible_passed = gt_results['passed']
    
    # # Then run with generated_file_code
    gen_results = run_tests_in_docker(metadata, "generated_file_code")
    
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
        },
        'generated_results': {
            'passed': gen_results['passed'],
            'failed': gen_results['failed'],
            'warnings': gen_results['warnings'],
            'errors': gen_results['errors'],
            'total_tests': gen_results['total_tests'],
            'errors_info': gen_results['errors_info'],
            'failures_info': gen_results['failures_info'],
            'output': gen_results['output']
        },
        'passed_rate': round(passed_rate, 4),
        'max_possible_passed': max_possible_passed,
        # 'passed_rate': gen_results['passed']/gen_results['total_tests']
    }

    # Save results
    target_dir = 'target_path' # you should replace this with the path to the evaluation results
    next_idx = get_next_metadata_index(target_dir)
    output_path = os.path.join(target_dir, f'metadata_{next_idx}_adjusted.json')
    
    with open(output_path, 'w') as f:
        json.dump(test_results, f, indent=2)

    print(f"Adjusted test results saved to: {output_path}")


def process_directory(directory_path, max_workers):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                file_path = os.path.join(directory_path, filename)
                executor.submit(evaluator, file_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量处理JSON文件的测试评估器")
    parser.add_argument("directory", help="包含JSON文件的目录路径")
    parser.add_argument("--workers", type=int, default=50, help="并行执行的线程数量")
    args = parser.parse_args()
    
    process_directory(args.directory, args.workers)

    