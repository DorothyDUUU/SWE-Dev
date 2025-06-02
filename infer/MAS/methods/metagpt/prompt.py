CONTEXT_TEMPLATE = """
### Original Requirements
{requirements}

### Search Information
-
"""
PRD_TEMPLATE="""

## context
# {context}
# 
# -----
# 
# ## format example
# [CONTENT]
# {{
#     "Language": "en_us",
#     "Programming Language": "Python",
#     "Original Requirements": "Create a 2048 game",
#     "Project Name": "game_2048",
#     "Product Goals": [
#         "Create an engaging user experience",
#         "Improve accessibility, be responsive",
#         "More beautiful UI"
#     ],
#     "User Stories": [
#         "As a player, I want to be able to choose difficulty levels",
#         "As a player, I want to see my score after each game",
#         "As a player, I want to get restart button when I lose",
#         "As a player, I want to see beautiful UI that make me feel good",
#         "As a player, I want to play game via mobile phone"\n    ],
#     "Competitive Analysis": [
#         "2048 Game A: Simple interface, lacks responsive features",
#         "play2048.co: Beautiful and responsive UI with my best score shown",
#         "2048game.com: Responsive UI with my best score shown, but many ads"
#     ],
#     "Competitive Quadrant Chart": "quadrantChart\
#     title \\"Reach and engagement of campaigns\\"\
#     x-axis \\"Low Reach\\" --> \\"High Reach\\"\
#     y-axis \\"Low Engagement\\" --> \\"High Engagement\\"\
#     quadrant-1 \\"We should expand\\"\
#     quadrant-2 \\"Need to promote\\"\
#     quadrant-3 \\"Re-evaluate\\"\
#     quadrant-4 \\"May be improved\\"\
#     \\"Campaign A\\": [0.3, 0.6]\
#     \\"Campaign B\\": [0.45, 0.23]\
#     \\"Campaign C\\": [0.57, 0.69]\
#     \\"Campaign D\\": [0.78, 0.34]\
#     \\"Campaign E\\": [0.40, 0.34]\
#     \\"Campaign F\\": [0.35, 0.78]\
#     \\"Our Target Product\\": [0.5, 0.6]",
#     "Requirement Analysis": "",
#     "Requirement Pool": [
#         [
#             "P0",
#             "The main code ..."
#         ],
#         [
#             "P0",
#             "The game algorithm ..."
#         ]
#     ],
#     "UI Design draft": "Basic function description with a simple style and layout.",
#     "Anything UNCLEAR": ""
# }}
# [/CONTENT]
# 
# ## nodes: "<node>: <type>  # <instruction>"
# - Language: <class \'str\'>  # Provide the language used in the project, typically matching the user\'s requirement language.
# - Programming Language: <class \'str\'>  # Python/JavaScript or other mainstream programming language.
# - Original Requirements: <class \'str\'>  # Place the original user\'s requirements here.
# - Project Name: <class \'str\'>  # According to the content of "Original Requirements," name the project using snake case style , like \'game_2048\' or \'simple_crm.
# - Product Goals: typing.List[str]  # Provide up to three clear, orthogonal product goals.
# - User Stories: typing.List[str]  # Provide up to 3 to 5 scenario-based user stories.
# - Competitive Analysis: typing.List[str]  # Provide 5 to 7 competitive products.
# - Competitive Quadrant Chart: <class \'str\'>  # Use mermaid quadrantChart syntax. Distribute scores evenly between 0 and 1
# - Requirement Analysis: <class \'str\'>  # Provide a detailed analysis of the requirements.
# - Requirement Pool: typing.List[typing.List[str]]  # List down the top-5 requirements with their priority (P0, P1, P2).
# - UI Design draft: <class \'str\'>  # Provide a simple description of UI elements, functions, style, and layout.
# - Anything UNCLEAR: <class \'str\'>  # Mention any aspects of the project that are unclear and try to clarify them.


# ## constraint
# Language: Please use the same language as Human INPUT.
# Format: output wrapped inside [CONTENT][/CONTENT] like format example, nothing else.
# 
# ## action
# Follow instructions of nodes, generate output and make sure it follows the format example.

"""
DESIGN_TEMPLATE = """
## context
# {context}
# 
# -----
# 
# ## format example
# [CONTENT]
# {{
#     "Implementation approach": "We will ...",
#     "File list": [
#         "main.py",
#         "game.py"    ],
#     "Data structures and interfaces": "\\nclassDiagram\\n    class Main {{\\n        -SearchEngine search_engine\\n        +main() str\\n    }}\\n    class SearchEngine {{\\n        -Index index\\n        -Ranking ranking\\n        -Summary summary\\n        +search(query: str) str\\n    }}\\n    class Index {{\\n        -KnowledgeBase knowledge_base\\n        +create_index(data: dict)\\n        +query_index(query: str) list\\n    }}\\n    class Ranking {{\\n        +rank_results(results: list) list\\n    }}\\n    class Summary {{\\n        +summarize_results(results: list) str\\n    }}\\n    class KnowledgeBase {{\\n        +update(data: dict)\\n        +fetch_data(query: str) dict\\n    }}\\n    Main --> SearchEngine\\n    SearchEngine --> Index\\n    SearchEngine --> Ranking\\n    SearchEngine --> Summary\\n    Index --> KnowledgeBase\\n",
#     "Program call flow": "\\nsequenceDiagram\\n    participant M as Main\\n    participant SE as SearchEngine\\n    participant I as Index\\n    participant R as Ranking\\n    participant S as Summary\\n    participant KB as KnowledgeBase\\n    M->>SE: search(query)\\n    SE->>I: query_index(query)\\n    I->>KB: fetch_data(query)\\n    KB-->>I: return data\\n    I-->>SE: return results\\n    SE->>R: rank_results(results)\\n    R-->>SE: return ranked_results\\n    SE->>S: summarize_results(ranked_results)\\n    S-->>SE: return summary\\n    SE-->>M: return summary\\n",
#     "Anything UNCLEAR": "Clarification needed on third-party API integration, ..."
# }}
# [/CONTENT]
# 
# ## nodes: "<node>: <type>  # <instruction>"
# - Implementation approach: <class 'str'>  # Analyze the difficult points of the requirements, select the appropriate open-source framework
# - File list: typing.List[str]  # Only need relative paths. ALWAYS write a main.py or app.py here
# - Data structures and interfaces: <class 'str'>  # Use mermaid classDiagram code syntax, including classes, method(__init__ etc.) and functions with type annotations, CLEARLY MARK the RELATIONSHIPS between classes, and comply with PEP8 standards. The data structures SHOULD BE VERY DETAILED and the API should be comprehensive with a complete design.
# - Program call flow: <class 'str'>  # Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.
# - Anything UNCLEAR: <class 'str'>  # Mention unclear project aspects, then try to clarify it.
# 
# 
# ## constraint
# Language: Please use the same language as Human INPUT.
# Format: output wrapped inside [CONTENT][/CONTENT] like format example, nothing else.
# 
# ## action
# Follow instructions of nodes, generate output and make sure it follows the format example.
"""
TASKS_TEMPLATE="""

## context
# {context}
# 
# -----
# 
# ## format example
# [CONTENT]
# {{
#     "Required Python packages": [
#         "flask==1.1.2",
#         "bcrypt==3.2.0"
#     ],
#     "Required Other language third-party packages": [
#         "No third-party dependencies required"
#     ],
#     "Logic Analysis": [
#         [
#             "game.py",
#             "Contains Game class and ... functions"
#         ],
#         [
#             "main.py",
#             "Contains main function, from game import Game"
#         ]
#     ],
#     "Task list": [
#         "game.py",
#         "main.py"
#     ],
#     "Full API spec": "openapi: 3.0.0 ...",
#     "Shared Knowledge": "`game.py` contains functions shared across the project.",
#     "Anything UNCLEAR": "Clarification needed on how to start and initialize third-party libraries."
# }}
# [/CONTENT]
# 
# ## nodes: "<node>: <type>  # <instruction>"
# - Required Python packages: typing.List[str]  # Provide required Python packages in requirements.txt format.
# - Required Other language third-party packages: typing.List[str]  # List down the required packages for languages other than Python.
# - Logic Analysis: typing.List[typing.List[str]]  # Provide a list of files with the classes/methods/functions to be implemented, including dependency analysis and imports.
# - Task list: typing.List[str]  # Break down the tasks into a list of filenames, prioritized by dependency order.
# - Full API spec: <class \'str\'>  # Describe all APIs using OpenAPI 3.0 spec that may be used by both frontend and backend. If front-end and back-end communication is not required, leave it blank.
# - Shared Knowledge: <class \'str\'>  # Detail any shared knowledge, like common utility functions or configuration variables.
# - Anything UNCLEAR: <class \'str\'>  # Mention any unclear aspects in the project management context and try to clarify them.
# 
# 
# ## constraint
# Language: Please use the same language as Human INPUT.
# Format: output wrapped inside [CONTENT][/CONTENT] like format example, nothing else.\n\n## action
# Follow instructions of nodes, generate output and make sure it follows the format example.

"""
CODE_TEMPLATE= """
NOTICE
Role: You are a professional engineer; the main goal is to write google-style, elegant, modular, easy to read and maintain code
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context
## Design
{design}

## Task
{task}

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
1. Only One file: do your best to implement THIS ONLY ONE FILE.
2. COMPLETE CODE: Your code will be part of the entire project, so please implement complete, reliable, reusable code snippets.
3. Set default value: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE. AVOID circular import.
4. Follow design: YOU MUST FOLLOW "Data structures and interfaces". DONT CHANGE ANY DESIGN. Do not use public member functions that do not exist in your design.
5. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
6. Before using a external variable/module, make sure you import it first.
7. Write out EVERY CODE DETAIL, DON'T LEAVE TODO.

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
5. Have all necessary pre-dependencies been imported? If not, indicate which ones need to be imported
6. Are methods from other files being reused correctly?

## Actions: Ordered List. Things that should be done after CR, such as implementing class A and function B

## Code Review Result: str. If the code doesn't have bugs, we don't need to rewrite it, so answer LGTM and stop. ONLY ANSWER LGTM/LBTM.
LGTM/LBTM

"""
REWRITE_CODE_TEMPLATE = """
# Instruction: rewrite code based on the Code Review and Actions
## Rewrite Code: CodeBlock. If it still has some bugs, rewrite {filename} with triple quotes. Do your utmost to optimize THIS SINGLE FILE. Return all completed codes and prohibit the return of unfinished codes.
```Code
## {filename}
...
```
"""