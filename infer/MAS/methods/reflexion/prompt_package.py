# Simple generation mode prompt (add code completion instruction)
SIMPLE_CHAT_INSTRUCTION = """You are an AI programming assistant. Given incomplete code files and PRD requirements, output ONLY the completed code in markdown code blocks. Follow these steps:
1. Analyze PRD requirements
2. Identify missing parts in current code
3. Generate completions preserving existing code
4. Ensure the output follows the format below.
----------------------------------
  ## STRICT OUTPUT FORMAT:
  Answer: 
  @ {relative_path/filename_1}
  ```python
  [COMPLETE file code including ALL original code plus your implementations]
  ```
  @ {relative_path/filename_2}
  ```python
  [COMPLETE file code including ALL original code plus your implementations]
  ```
  @ {relative_path/filename_3}
  ```python
  [COMPLETE file code including ALL original code plus your implementations]
  ```

-------------------------------
## Important Rules:
- The output format must strictly follow the STRICT OUTPUT FORMAT, and must not contain any other format!!
- Even if there is only one file, you must add the path marker!!!!!
- Preserve all original code and add new implementations

"""


# Reflexion mode prompt (add code context)
REFLEXION_CHAT_INSTRUCTION = """You are an AI programming assistant. Given:
- Previous incomplete code
- PRD requirements
- Code feedback
- Past reflections
Ensure the output follows the format below.
----------------------------------
  ## STRICT OUTPUT FORMAT:
  Answer: 
  @ {relative_path/filename_1}
  ```python
  [COMPLETE file code including ALL original code plus your implementations]
  ```
  @ {relative_path/filename_2}
  ```python
  [COMPLETE file code including ALL original code plus your implementations]
  ```
  @ {relative_path/filename_3}
  ```python
  [COMPLETE file code including ALL original code plus your implementations]
  ```

-------------------------------
## Non-negotiable Rules:
- The output format must strictly follow the STRICT OUTPUT FORMAT FOR EACH FILE, and must not contain any other format!!
- Even if there is only one file, you must add the path marker
- You must output the entire content of the file
"""

# Self-reflection prompt (code specific)
SELF_REFLECTION_CHAT_INSTRUCTION = """You are a senior engineer. Analyze why previous code failed to meet PRD. Focus on:
- Code structure issues
- Missing requirements
- Logic errors
- Improvement methods"""

# Few-shot examples for evaluation
EVALUATION_FEW_SHOT = """Examples:
query:
What is the capital of France?
answer:
Florida
evaluation:
FAIL: The answer is incorrect. The capital of France is Paris, not Florida.

query:
What is the capital of France?
answer:
Paris
evaluation:
PASS: The answer is correct. The capital of France is indeed Paris."""

# Few-shot examples for self-reflection
SELF_REFLECTION_FEW_SHOT = """Example 1:
query:
What is the capital of France?
answer:
Florida
evaluation feedback:
FAIL: The answer is incorrect. The capital of France is Paris, not Florida.
self-reflection:
The answer is incorrect because I confused the capital of France with a US state. The correct capital of France is Paris, as indicated in the feedback. I should ensure to recall geographical facts accurately in the next attempt.

Example 2:
query:
Explain the theory of relativity in simple terms.
answer:
It's a theory by Einstein.
evaluation feedback:
FAIL: The answer is too vague and lacks explanation. The theory of relativity should be explained in simple terms, covering concepts like space, time, and gravity.
self-reflection:
The answer failed because it was too brief and did not provide a simple explanation of the theory of relativity. I need to elaborate on key concepts such as how space and time are interconnected and how gravity affects them, as suggested by the feedback."""

# Few-shot examples for reflexion
REFLEXION_FEW_SHOT = """Example 1:
previous answer:
Florida
evaluation feedback:
FAIL: The answer is incorrect. The capital of France is Paris, not Florida.
self-reflection:
The answer is incorrect because I confused the capital of France with a US state. The correct capital of France is Paris, as indicated in the feedback. I should ensure to recall geographical facts accurately in the next attempt.
past reflections:
improved answer:
Paris"""
