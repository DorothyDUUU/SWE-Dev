
from multiprocessing import Process, Queue

def function_with_timeout(func, args, timeout):
    def wrapper(func, args, queue):
        try:
            result = func(*args)
            queue.put((True, result))
        except Exception as e:
            queue.put((False, e)) 

    queue = Queue()
    process = Process(target=wrapper, args=(func, args, queue))
    process.start()
    process.join(timeout)  

    if process.is_alive():
        process.terminate()
        process.join()  
        raise TimeoutError(f"Function timed out after {timeout} seconds")
    else:
        success, value = queue.get()
        if success:
            return value 
        else:
            raise value  


def evaluate_functional_correctness(
    test_cases: list,
    completion: str,
    timeout: int = 60,
    stop_early: bool = False,
):
    test_log = ""
    passed = True
    for io in test_cases:
        try:
            code = ("from typing import *\n" if "from typing import *" not in completion else "") + \
                completion + "\n" + io + "\n"
            function_with_timeout(
                exec,
                (code, globals()),
                timeout
            )
            test_log += f"passed in test case: {io}\n"
        except Exception as e:
            if stop_early:
                return False, f"failed in test case: {io}\n"
            passed = False
            test_log += f"failed in test case: {io}\n"

    return passed, test_log

if __name__ == "__main__":
    import json
    import concurrent.futures
    from tqdm import tqdm
    cnt = 0
    with open('results/example_mbpp/gpt-4o-mini-2024-07-18/mapcoder_mbpp_infer.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            break
    code = """
def square_perimeter(n):
    while True:
        pass"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        tasks = [(data['test_cases'],  data['generated_output']) for i in range(29)] 
        # tasks = [(data['test_cases'],  code, 1) for i in range(30)] 
        tasks.append((data['test_cases'],  code, 1))
        for i in range(30):
            tasks.append((data['test_cases'],  data['generated_output']))
        results = list(executor.map(lambda args: evaluate_functional_correctness(*args), tasks))
        for idx, _ in enumerate(results):
            print(idx, _)
                # passed, _ = evaluate_functional_correctness(data['test_cases'], data['generated_output'])
            # if passed:
            #     cnt += 1
    
    print(cnt)