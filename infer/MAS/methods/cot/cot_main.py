from ..mas_base import MAS
import re

class CoT(MAS):
    def __init__(self, general_config):
        super().__init__(general_config)
    
    def inference(self, query,file_code):
        
        prompt =f"""
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
"""


        prompt = prompt + "\n\nLet's think step by step."
        
        response = self.call_llm(prompt=prompt)
        response = self.extract_and_format_final_answer(response)
        print(f"[DEBUG] CoT response: {response}")
        return response
    
    def extract_and_format_final_answer(self,final_answer):
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