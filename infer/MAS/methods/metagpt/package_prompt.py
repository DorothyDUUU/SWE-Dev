CONTEXT_TEMPLATE = """
### Original Requirements
{requirements}

### Search Information
-
"""

TASKS_TEMPLATE = """

# context
{context}
# Existing Code
{code}
-----

## format example
[CONTENT]
{{
    "Required Python packages": [
        "package1==1.0.0",
        "package2==2.0.0"
    ],
    "Required Other language third-party packages": [
        "No third-party dependencies required"
    ],
    "Logic Analysis": [
        [
            "file1.py",
            "Contains Class1 and related functions"
        ],
        [
            "file2.py",
            "Contains Class2 and related functions"
        ]
    ],
    "Task list": [
        "file1.py",
        "file2.py"
    ],
    "Full API spec": "openapi: 3.0.0 ...",
    "Shared Knowledge": "`file1.py` contains shared utility functions.",
    "Anything UNCLEAR": "Clarification needed on ..."
}}
[/CONTENT]

## nodes: "<node>: <type>  # <instruction>"
- Required Python packages: typing.List[str]  # Provide required Python packages in requirements.txt format.
- Required Other language third-party packages: typing.List[str]  # List down the required packages for languages other than Python.
- Logic Analysis: typing.List[typing.List[str]]  # Provide a list of files with the classes/methods/functions to be implemented.
- Task list: typing.List[str]  # Break down the tasks into a list of filenames.
- Full API spec: <class 'str'>  # Describe all APIs using OpenAPI 3.0 spec.
- Shared Knowledge: <class 'str'>  # Detail any shared knowledge.
- Anything UNCLEAR: <class 'str'>  # Mention any unclear aspects in the project management context.

## constraint
Language: Please use the same language as Human INPUT.
Format: output wrapped inside [CONTENT][/CONTENT] like format example, nothing else.
Indentation: Ensure that the code is correctly indented following the standard practices of the language used
- Always append new functions to the file's end unless special instructions are provided.
- Avoid unnecessary restructuring, like forcing functions into classes unless explicitly stated.
- Do not import any new content or libraries. Use only the existing imports and code.

"""

CODE_TEMPLATE = """
NOTICE
Role: You are a professional engineer; the main goal is to write google-style, elegant, modular, easy to read and maintain code
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".
## Your Task:
- Implement only the described empty functions as per the given docstrings and specifications.
- Preserve all existing code exactly and ensure it's included in your output without alteration.
- Do not introduce new imports or modify any existing imports.
- Avoid modifying any existing code outside the specified functions.
# Context
## Problem Requirement
{design}


## Legacy Code
```Code
{code_context}
```

## Debug logs
```text
```

## Bug Feedback logs
```text
```

# Format example
## Code: {filename}
```python
## {filename}
...
```

# Instruction: Based on the context, follow "Format example", write code.

## Code: {filename}. Write code with triple quoto, based on the following attentions and context.
Only One file: do your best to implement THIS ONLY ONE FILE.
Append any new functions to the file's end unless specified otherwise.
Avoid modifying or restructuring existing classes or implementations unless justified by the requirements.
Include detailed, standalone code contributions, ensuring compatibility with existing systems.
Do not delete content but instead integrate new functions or classes seamlessly
## Important Rules that MUST be followed:
- You MUST adhere to the output format exactly as specified above.
- **CRUCIAL:** Output must include THE ENTIRE ORIGINAL CODE with necessary additions without any deviations!!!
- Indentation: Ensure that the code is correctly indented following the standard practices of the language used
- Include both the new code you write and all original code from Existing Code Context.

"""
FORMAT_EXAMPLE = """
# Format example 1
## Code Review: {filename}
1. No, we should fix the logic of class A due to ...
2. ...
3. ...
4. No, function B is not implemented, ...
5. ...
6. ...

## Actions
1. Fix the `handle_events` method to update the game state only if a move is successful.
   ```python
   def handle_events(self):
       for event in pygame.event.get():
           if event.type == pygame.QUIT:
               return False
           if event.type == pygame.KEYDOWN:
               moved = False
               if event.key == pygame.K_UP:
                   moved = self.game.move('UP')
               elif event.key == pygame.K_DOWN:
                   moved = self.game.move('DOWN')
               elif event.key == pygame.K_LEFT:
                   moved = self.game.move('LEFT')
               elif event.key == pygame.K_RIGHT:
                   moved = self.game.move('RIGHT')
               if moved:
                   # Update the game state only if a move was successful
                   self.render()
       return True
   ```
2. Implement function B

## Code Review Result
LBTM

# Format example 2
## Code Review: {filename}
1. Yes.
2. Yes.
3. Yes.
4. Yes.
5. Yes.
6. Yes.

## Actions
pass

## Code Review Result
LGTM
"""

PROMPT_TEMPLATE = """
# System
Role: You are a professional software engineer, and your main task is to review and revise the code. You need to ensure that the code conforms to the google-style standards, is elegantly designed and modularized, easy to read and maintain.
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".
ATTENTION: Append new functions at the file's end unless otherwise specified and avoid restructuring existing code unnecessarily.
# Context
{context}

## Code to be Reviewed: {filename}
```Code
{code}
```
"""
EXAMPLE_AND_INSTRUCTION = """

{format_example}


# Instruction: Based on the actual code situation, follow one of the "Format example". Return only 1 file under review.

## Code Review: Ordered List. Based on the "Code to be Reviewed", provide key, clear, concise, and specific answer. If any answer is no, explain how to fix it step by step.
1. Is the code implemented as per the requirements? If not, how to achieve it? Analyse it step by step.
2. Is the code logic completely correct? If there are errors, please indicate how to correct them.
3. Does the existing code follow the "Data structures and interfaces"?
4. Are all functions implemented? If there is no implementation, please indicate how to achieve it step by step.
6. Are methods from other files being reused correctly?

## Actions: Ordered List. Things that should be done after CR, such as implementing class A and function B

## Code Review Result: str. If the code doesn't have bugs, we don't need to rewrite it, so answer LGTM and stop. ONLY ANSWER LGTM/LBTM.
LGTM/LBTM

"""
REWRITE_CODE_TEMPLATE = """
# Instruction: rewrite code based on the Code Review and Actions
# Instruction: Only append new functions or fixes at the file's end unless explicitly instructed for changes elsewhere.
## Rewrite Code: CodeBlock. If it still has some bugs, rewrite {filename} with triple quotes. Do your utmost to optimize THIS SINGLE FILE. Return all completed codes and prohibit the return of unfinished codes.
# NOTE: All modifications must be based on the Existing Code. Do not delete any content from Existing Code or import new content.
# Indentation: Ensure that the code is correctly indented following the standard practices of the language used。
# The returned code must combine the provided code with the newly written code.
```Code
## {filename}
...
```

## Important Rules that MUST be followed:
- You MUST adhere to the output format exactly as specified above.
- **CRUCIAL:** Output must include THE ENTIRE ORIGINAL CODE with necessary additions without any deviations!!!
- Indentation: Ensure that the code is correctly indented following the standard practices of the language used
- Include both the new code you write and all original code from Existing Code Context.
"""