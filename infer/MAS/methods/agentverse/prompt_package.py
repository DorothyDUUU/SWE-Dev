ROLE_ASSIGNER_PREPEND_PROMPT = """# Role Description
${aim}
You are the leader of a group of experts, now you are facing a problem:
## Problem Requirement:
${query}
and you should complete all the file in the Exisiting code according to Problem Requirement.
## Exisiting code:
${file_code}
this times,you need only focus on this file and you can gei information from query.
You can recruit ${cnt_agents} expert in different fields.

Here are some suggestion:
${advice}"""

ROLE_ASSIGNER_APPEND_PROMPT = """You can recruit ${cnt_agents} expert in different fields. What experts will you recruit to better generate an accurate solution?

# Response Format Guidance
You should respond with a list of expert description. For example:
1. an electrical engineer specified in the filed of xxx.
2. an economist who is good at xxx.
...

Only respond with the description of each role. Do not include your reason."""

SOLVER_PREPEND_PROMPT = """Solve the following problem: 
${aim}
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

SOLVER_APPEND_PROMPT = """You are ${role_description}. Using the information in the chat history and your knowledge, you should provide the correct solution to the problem. Explain your reasoning."""

CRITIC_PREPEND_PROMPT = """You are ${role_description}. You are in a discussion group, aiming to collaborative solve the following problem:
${query}

Based on your knowledge, give your correct solution to the problem step by step."""

CRITIC_APPEND_PROMPT = """Now compare your solution with the solution given in the chat history and give your response. When responding, you should follow the following rules:
1. This problem can be answered without any extra information. You should not ask for any extra information. 
2. Compare your solution with the given solution, give your critics. You should only give your critics, don't give your answer.
3. If the final answer in your solution is the same as the final answer in the above provided solution, end your response with a special token "[Agree]"."""

EVALUATOR_PREPEND_PROMPT = """Experts: ${all_role_description}
Problem: ${query}
Solution: 
```
${solution}
```"""

EVALUATOR_APPEND_PROMPT = """You are an experienced Problem Solver. As a good assistant, you carefully check the correctness of the given solution on a problem. When the solution is wrong, you should output a correctness of 0 and give your advice on how to correct the solution. When it is correct, output a correctness of 1 and why it is correct. You should also give some suggestion on on what experts should recruit in the next round.

You should respond in the following format:
Correctness: (0 or 1, 0 is wrong, and 1 is correct)
Response: (advice to correct the answer or why it is correct)"""