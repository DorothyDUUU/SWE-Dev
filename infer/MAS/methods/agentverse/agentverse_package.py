import os
import re
from typing import List, Dict, Any, Set, Tuple
import json
from ..mas_base import MAS
from ..utils import load_config
from .prompt_package import *

# Define the NEWMAS class which inherits from MAS and implements the inference method
class Agentverse_Package(MAS):
    def __init__(self, general_config, method_config_name = "config_main"):
        super().__init__(general_config)
        self.method_config = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", f"{method_config_name}.yaml"))
        
        self.max_turn = self.method_config['max_turn']
        self.cnt_agents = self.method_config['cnt_agents']
        self.max_criticizing_rounds = self.method_config['max_criticizing_rounds']
        
        self.dimensions: List[str] = ["Score", "Response"]
        self.advice = "No advice yet."
        self.history = []
    
    def inference(self,query,file_code):
        ret = dict()
        aim_prompt = "AIM: You need to assist me with a Python package feature development task. Given the Problem Requirements, implement only the empty functions in the specified files."
        self.advice = "No advice yet."
        for i in range(self.max_turn):
            # Assign roles to agents
            role_descriptions = self.assign_roles(query, file_code, aim_prompt)
            solution = self.group_vertical_solver_first(query, role_descriptions, file_code)
            Score, feedback = self.evaluate(query, role_descriptions, solution)
            print(f"[Debug] Solution is{solution}\nScore is {Score}.")
            if Score == 1:
                solution = self.extract_and_format_final_answer(solution)
                break
            else:
                self.advice = feedback
        return solution
    

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

    def assign_roles(self, query: str,aim_prompt:str,file_code):
        # Fetch prompts from config.yaml (assumed to be loaded earlier)
        prepend_prompt = f"""# Role Description
${aim_prompt}
You are the leader of a group of experts, now you are facing a problem:
## Problem Requirement:
${query}
and you should complete all the file in the Exisiting code according to Problem Requirement.
## Exisiting code:
${file_code}
this times,you need only focus on this file and you can gei information from query.
You can recruit ${self.cnt_agents} expert in different fields.

Here are some suggestion:
${self.advice}"""
        append_prompt = ROLE_ASSIGNER_APPEND_PROMPT.replace("${cnt_agents}", str(self.cnt_agents))
        
        # Call LLM to get the role assignments
        assigner_messages = self.construct_messages(prepend_prompt, [], append_prompt)
        role_assignment_response = self.call_llm(None, None, assigner_messages)
        # Extract role descriptions using regex
        role_descriptions = self.extract_role_descriptions(role_assignment_response)
        return role_descriptions

    def extract_role_descriptions(self, response: str):
        """
        Extracts the role descriptions from the model's response using regex.
        Assumes the response is formatted like:
        1. an electrical engineer specified in the field of xxx.
        2. an economist who is good at xxx.
        ...
        """
        role_pattern = r"\d+\.\s*([^.]+)"  # extract the content between the number and the period
        
        role_descriptions = re.findall(role_pattern, response)
        
        if len(role_descriptions) == self.cnt_agents:
            # print("role_descriptions:")
            # print(role_descriptions)
            return role_descriptions
        else:
            raise ValueError(f"wrong cnt_agent, expect {self.cnt_agents} agents while we find {len(role_descriptions)} role_descriptions.")

    def group_vertical_solver_first(self, query: str, role_descriptions: List[str],file_code):
        aim_prompt = "AIM: You need to assist me with a Python package feature development task. Given the Problem Requirements, implement only the empty functions in the specified files."
        max_history_solver = 5
        max_history_critic = 3
        previous_plan = "No solution yet."
        # Initialize history and other variables
        nonempty_reviews = []
        history_solver = []
        history_critic = []
        consensus_reached = False
        
        if not self.advice == "No advice yet.":
            self.history.append(
                {
                    "role": "assistant",
                    "content": f"[Evaluator]: {self.advice}",
                }
            )
            if len(self.history) > max_history_solver:
                history_solver = self.history[-max_history_solver:]
            else:
                history_solver = self.history
        # Step 1: Solver generates a solution
        solver_prepend_prompt = f"""
Solve the following problem: 
${aim_prompt}
## Problem Requirement:
${query} 
##  Existing Code Context:
${file_code}
---------------------
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

-----------------------
# STRICT OUTPUT FORMAT for each file:
@ [relative path/filename]
```python
[COMPLETE file code including ALL original code plus your implementations]
```
------------------
## Exemple output for a single file:
@ absl/command_name.py
```python
import os
import sys

def make_process_name_useful():
    set_kernel_process_name(os.path.basename(sys.argv[0]))

def set_kernel_process_name(name):
    if not isinstance(name, bytes):
        name = name.encode('ascii', 'replace')

    try:
        with open('/proc/self/comm', 'wb') as proc_comm:
            proc_comm.write(name[:15])
    except OSError:
        try:
            import ctypes  # pylint: disable=g-import-not-at-top
        except ImportError:
            return

        try:
            libc = ctypes.CDLL('libc.so.6')
        except OSError:
            return

        pr_set_name = ctypes.c_ulong(15)
        zero = ctypes.c_ulong(0)

        try:
            libc.prctl(pr_set_name, name, zero, zero, zero)
        except AttributeError:
            return
```
------------------
"""
        solver_append_prompt = SOLVER_APPEND_PROMPT.replace("${role_description}", role_descriptions[0])
        # print(f"history_solver: {history_solver}")
        solver_message = self.construct_messages(solver_prepend_prompt, history_solver, solver_append_prompt)
        solver_response = self.call_llm(None, None, solver_message)
        self.history.append(
            {
                "role": "assistant",
                "content": f"[{role_descriptions[0]}]: {solver_response}",
            }
        )
        if len(self.history) > max_history_critic:
            history_critic = self.history[-max_history_critic:]
        else:
            history_critic = self.history
        previous_plan = solver_response  # Set the solution as previous_plan
        
        cnt_critic_agent = self.cnt_agents - 1
        
        for i in range(self.max_criticizing_rounds):
            
            #step 2: Critics review the solution
            reviews = []
            for j in range(cnt_critic_agent):
                critic_prepend_prompt = CRITIC_PREPEND_PROMPT.replace("${query}", query).replace("${role_description}", role_descriptions[j+1])
                critic_append_prompt = CRITIC_APPEND_PROMPT
                critic_message = self.construct_messages(critic_prepend_prompt, history_critic, critic_append_prompt)
                critic_response = self.call_llm(None, None, critic_message)
                if "[Agree]" not in critic_response:
                    self.history.append(
                        {
                            "role": "assistant",
                            "content": f"[{role_descriptions[j+1]}]: {self.parse_critic(critic_response)}",
                        }
                    )
                    if len(self.history) > max_history_solver:
                        history_solver = self.history[-max_history_solver:]
                    else:
                        history_solver = self.history
                reviews.append(critic_response)
            for review in reviews:
                if "[Agree]" not in review:
                    nonempty_reviews.append(review)
            if len(nonempty_reviews) == 0:
                # print("Consensus Reached!")
                break
            solver_message = self.construct_messages(solver_prepend_prompt, history_solver, solver_append_prompt)
            solver_response = self.call_llm(None, None, solver_message)
            self.history.append(
                {
                    "role": "assistant",
                    "content": f"[{role_descriptions[0]}]: {solver_response}",
                }
            )
            if len(self.history) > max_history_critic:
                history_critic = self.history[-max_history_critic:]
            else:
                history_critic = self.history
            previous_plan = solver_response
        results = previous_plan
        return results
    
    def parse_critic(self, output) -> str:
        output = re.sub(r"\n+", "\n", output.strip())
        if "[Agree]" in output:
            return ""
        else:
            return output
            
    def evaluate(self, query: str, role_descriptions: List[str], Plan):
        evaluator_prepend_prompt = EVALUATOR_PREPEND_PROMPT.replace("${query}", query).replace("${all_role_description}", "\n".join(role_descriptions)).replace("${solution}", Plan)
        evaluator_append_prompt = EVALUATOR_APPEND_PROMPT
        evaluator_message = self.construct_messages(evaluator_prepend_prompt, [], evaluator_append_prompt)
        evaluator_response = self.call_llm(None, None, evaluator_message)
        return self.parse_evaluator(evaluator_response)
        
    def parse_evaluator(self, output) -> Tuple[List[int], str]:

        correctness_match = re.search(r"Correctness:\s*(\d)", output)
        if correctness_match:
            correctness = int(correctness_match.group(1))
        else:
            raise ValueError("Correctness not found in the output text.")

        advice_match = re.search(r"Response:\s*(.+)", output, re.DOTALL)  
        if advice_match:
            advice = advice_match.group(1).strip()  
            clean_advice = re.sub(r"\n+", "\n", advice.strip())
        else:

            raise ValueError("Advice not found in the output text.")
 
        return correctness, clean_advice

    def construct_messages(self, prepend_prompt: str, history: List[Dict], append_prompt: str):
        messages = []
        if prepend_prompt:
            messages.append({"role": "system", "content": prepend_prompt})
        if len(history) > 0:
            messages += history
        if append_prompt:
            messages.append({"role": "user", "content": append_prompt})
        return messages