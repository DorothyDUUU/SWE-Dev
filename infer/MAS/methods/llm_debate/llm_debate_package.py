import os
from ..mas_base import MAS
from ..utils import load_config
import re

class LLMDebate_package(MAS):
    def __init__(self, general_config, method_config_name="config_general"):
        super().__init__(general_config)

        self.method_config = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", f"{method_config_name}.yaml"))
        self.agents_num = self.method_config["agents_num"]
        self.rounds_num = self.method_config["rounds_num"]
    
    def inference(self, query,file_code):
        agent_contexts = [[
{
"role": "user",
"content": f"""
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
            }
            ] for agent in range(self.agents_num)]

        for round in range(self.rounds_num):
            for i, agent_context in enumerate(agent_contexts):
                if round != 0:
                    agent_contexts_other = agent_contexts[:i] + agent_contexts[i+1:]
                    message = self.construct_message(agent_contexts_other, query,file_code, 2*round - 1)
                    agent_context.append(message)

                response = self.call_llm(messages=agent_context)
                agent_context.append({"role": "assistant", "content": response})
            # print(f"[DEBUG] Round {round + 1} responses finished.")
        
        answers = [agent_context[-1]['content'] for agent_context in agent_contexts]
        
        final_answer = self.aggregate(query, answers)
        # print(f"[DEBUG] Final answer: {final_answer}")
        final_answer = self.extract_and_format_final_answer(final_answer)
        # print(f"[DEBUG] Formatted final answer: {final_answer}")
        return final_answer
    
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

        
    def construct_message(self, agents, question, file_code, idx):
        if len(agents) == 0:
            return {
                "role": "user",
                "content": (
                    "No other agent feedback is available. Please review your solution for any improvements, "
                    "ensuring it comprehensively addresses all problem requirements. Summarize your final answer clearly."
                )
            }

        feedback_summary = "Feedback from other agents:\n"
        for agent in agents:
            agent_response = agent[idx]["content"]
            feedback_summary += f"\n- Agent feedback:\n```{agent_response}```"

        feedback_summary += (
"\n\nPlease consider the above feedback carefully to refine your solution. "
"Ensure the solution adheres to all specified requirements and constraints. "
"Make any improvements necessary, clearly stating your updated final solution. "
"Task instructions: {question}\n"
"Full original file content to maintain:\n{file_code}"
        )

        return {"role": "user", "content": feedback_summary}

    def aggregate(self, query, answers):
        aggregate_instruction = f"""
Task:\n{query}\n\n
Combine the provided solutions into a single comprehensive final answer. The final output must follow these format rules:

## Output Format:
- Each file must begin with its path, prefixed with "@ [relative path/filename]"
- The full code for each file must be enclosed in a code block:
```python
[COMPLETE file code including ALL original code plus your implementations]
"""
        for i, answer in enumerate(answers):
            aggregate_instruction += f"Solution {i+1}:\n{answer}\n\n"
        aggregate_instruction += "Given all the above solutions, reason over them carefully and provide a final answer to the task."
        response = self.call_llm(prompt=aggregate_instruction)
        return response