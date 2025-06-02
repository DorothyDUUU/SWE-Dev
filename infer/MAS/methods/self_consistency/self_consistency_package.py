import os
from ..mas_base import MAS
from ..utils import load_config
import re

class SelfConsistency_package(MAS):
    def __init__(self, general_config, method_config_name="config"):
        super().__init__(general_config)

        self.method_config = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", f"{method_config_name}.yaml"))
        self.parallel_num = self.method_config["parallel_num"]
    
    def inference(self, query,file_code):
        
        agent_results = [self.call_llm(prompt=f"""
AIM: You need to assist me with a Python package feature development task. Given the Problem Requirements, implement only the empty functions in the specified files. It's vital to maintain and output all existing code unaltered alongside your implementations.

## Your Task:
- Implement only the described empty functions as per the given docstrings and specifications.
- Preserve all existing code exactly and ensure it's included in your output without alteration.
- Do not introduce new imports or modify any existing imports.
- Avoid modifying any existing code outside the specified functions.

All your outputs MUST include the full content of each file in the file_code, fully unchanged, with your additions. The output format is extremely strict:

# STRICT OUTPUT FORMAT FOR EACH FILE:
@ [relative path/filename]
```python
[COMPLETE file code including ALL original code plus your implementations]
```

## Important Rules that MUST be followed:
- You MUST adhere to the output format exactly as specified above.
- **DO NOT MISS:** Ensure every file is prefixed with @ [relative path/filename], even if there is only one file in the file_code.
- **CRUCIAL:** Output must include THE ENTIRE ORIGINAL CODE with necessary additions without any deviations, and ensure to include @ [relative path/filename]!!!
- Make sure the output includes @ [relative path/filename] for each file.
- **No matter the case, especially if file_code contains a single file, include the filename prefix!**
- Repeat: Every output for a file must start with @ [relative path/filename].
- Include both the new code you write and all original code from Existing Code Context.

## Input Format:
The provided file_code is in the format: {{file_path1: code1, file_path2: code2, ...}},so you can get the file name for each code from the key of the dictionary.

## Problem Requirements:
{query} 
## Existing Code Context:
{file_code}
""") for _ in range(self.parallel_num)]

        final_decision_instruction = self.get_final_decision_instruction(query, agent_results)
        # print("Final Decision Instruction:")
        # print(final_decision_instruction)
        response = self.call_llm(prompt=final_decision_instruction)
        response = self.extract_and_format_final_answer(response)
        # print("Final Decision Response:")
        # print(response)
        return response
    
    def extract_and_format_final_answer(self,final_answer):
        # 改进后的正则表达式
        pattern = r'@ ([^\s]+)\s*```python\s*(.*?)\s*```'
        matches = re.findall(pattern, final_answer, re.DOTALL | re.MULTILINE)
        
        # print(f"[DEBUG] Regex matches: {matches}")
        
        if not matches:
            print("[DEBUG] No matches found. Check the input format.")
            return {}
        
        code_info = {}
        for file_path, code in matches:
            file_path = file_path.strip()
            if not file_path.endswith('.py'):
                file_path += '.py'
            code_info[file_path] = code.strip()
        
        return code_info

    
    def get_final_decision_instruction(self, query, agent_results):
        instruction = f"[Task]:\n{query}\n\n"

        for i, result in enumerate(agent_results):
            instruction += f"[Solution {i+1}]:\n{result}\n\n"

        instruction += """
Given the task and all the above solutions, reason over them carefully and provide a final answer to the task.
Your response should include the following:
1. A summary of the task.
2. A summary of each solution.
3. A final decision on which solution is the best, including a justification for your choice.
4. If you choose a solution, provide the complete code for that solution, including all code.
The code should be formatted as follows:
@ [relative path/filename]
```python
[COMPLETE file code including ALL original code plus your implementations]
```
"""

        return instruction