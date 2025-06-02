INPUT_KB_EXEMPLARS = """Given a problem, provide relevant problems then identify the algorithm behind it and also explain the tutorial of the algorithm.
# Problem:
{query}
# Previous code:
{file_code}
# Exemplars:
Recall {k} relevant and distinct problems (different from problem mentioned above). For each problem,
1. describe it
2. generate {language} code step by step to solve that problem
3. finally generate a planning to solve that problem

# Algorithm:

----------------
Important!!!:
Your response must follow the following xml format-

<root>
<problem>
# Recall {k} relevant and distinct problems (different from problem mentioned above). Write each problem in the following format.
<description>
# Describe the problem.
</description>
<code>
# Let's think step by step to solve this problem in {language} programming language.
</code>
<planning>
# Planning to solve this problem.
</planning>
</problem>
----------------
Important!!!:
Your response must follow the following xml format-
<root>
<problem>
# Recall {k} relevant and distinct problems (different from problem mentioned above). Write each problem in the following format.
<description>
# Describe the problem.
</description>
<code>
# Let's think step by step to solve this problem in {language} programming language.
</code>
<planning>
# Planning to solve this problem.
</planning>
</problem>
----------------
Important!!!:
Your response must follow the following xml format-
<root>
<problem>
# Recall {k} relevant and distinct problems (different from problem mentioned above). Write each problem in the following format.
<description>
# Describe the problem.
</description>
<code>
# Let's think step by step to solve this problem in {language} programming language.
</code>
<planning>
# Planning to solve this problem.
</planning>
</problem>
----------------

# similarly add more problems here...

<algorithm>
# Identify the algorithm (Brute-force, Dynamic Programming, Divide-and-conquer, Greedy, Backtracking, Recursive, Binary search, and so on) that needs to be used to solve the original problem.
# Write a useful tutorial about the above mentioned algorithms. Provide a high level generic tutorial for solving this types of problem. Do not generate code.
</algorithm>
</root>
"""

ALGORITHM_PROMPT = "## Relevant Algorithm to solve the next problem:\n{algorithm}"

SAMPLE_IO_PROMPT = "## Sample Test cases: \n{sample_io}\n"

PLANNING = """Given a competitive programming problem generate a concrete planning to solve the problem.
# Problem:
{example_problem}
# Previous code:
{file_code}
# Planning:
{example_planning}
{algorithm_prompt}
## Problem to be solved:
{prompt}
{sample_io_prompt}
## Planning:

----------------
Important: You should give only the planning to solve the problem. Do not add extra explanation or words."""

PLANNING_FOR_VERIFICATION = """Given a competitive programming problem and a plan to solve the problem in {language}, tell whether the plan is correct to solve this problem.

# Problem:
{query}
# Planning:
{planning}
# Previous code:
{file_code}
----------------
Important!!!: Your response must follow the following xml format-
<root>
<explanation> Discuss whether the given competitive programming problem is solvable by using the above mentioned planning.</explanation>
<confidence> Confidence score regarding the solvability of the problem. Must be an integer between 0 and 100. </confidence>
</root>
----------------
Important!!!: Your response must follow the following xml format-
<root>
<explanation> Discuss whether the given competitive programming problem is solvable by using the above mentioned planning.</explanation>
<confidence> Confidence score regarding the solvability of the problem. Must be an integer between 0 and 100. </confidence>
</root>
----------------
Important!!!: Your response must follow the following xml format-
<root>
<explanation> Discuss whether the given competitive programming problem is solvable by using the above mentioned planning.</explanation>
<confidence> Confidence score regarding the solvability of the problem. Must be an integer between 0 and 100. </confidence>
</root>
"""

FINAL_CODE_GENARATION = """Given a programming problem and existing code structure, generate {language} code to solve the problem by ONLY modifying the specified empty functions/methods. Preserve ALL EXISTING CODE exactly as provided - including imports, classes, functions, and comments.
## Your Task:
When implementing the functions:
1. Carefully identify which functions from the Problem Requirements need implementation.Implement them based on the docstrings and specifications in the Problem Requirements
2. Do not add any new "import" statements unless absolutely necessary
3. Do not modify ANY existing code structure, only implement the empty functions

For each file mentioned in the Problem Requirements, you MUST output the COMPLETE file code with your implementations inserted. Your output format must follow this exact pattern:
## Output Format:

@ [filename]
```python
[COMPLETE file code including ALL original code plus your implementations]
```

## Important Rules:
1.DO NOT add new imports or modify existing class/function structures
2.DO NOT alter any existing code outside the specified empty functions
3.Ensure implemented functions match the exact signatures and docstrings provided
4.Output must include THE ENTIRE ORIGINAL CODE with only the required additions

Make sure your output includes EVERY function, class, import statement, and comment from the original code context. The only difference should be that the empty functions specified in the PRD are now implemented.
## Problem Requirements:
{prompt}
## Code Context (COMPLETE existing code):
{code}
## Implementation Plan:
{planning}
Let's think step by step:
{sample_io_prompt}
## Your response must contain the complete code with the modified code clearly identified within the Python code block.
{std_input_prompt}
"""

IMPROVING_CODE = """Given a competitive programming problem, you have generated {language} code to solve the problem. However, the generated code cannot pass the sample test cases. Improve your code based on the previous implementation.
{algorithm_prompt}
## Problem to be solved:
{prompt}
{response}
## Test Report:
{test_log}
## Modified Planning:
## Let's think step by step to improve the {language} code for solving this problem.

----------------
Important:
{std_input_prompt}
## Your response must contain the modified code combined with the previous code, clearly identifying any changes or additions within the Python code block."""