# 简单生成模式的提示
SIMPLE_CHAT_INSTRUCTION = """You are an AI assistant that provides accurate and concise answers to general questions. Provide your answer directly."""

# 反思模式的提示
REFLEXION_CHAT_INSTRUCTION = """You are an AI assistant. You will be given your previous answer to a question, evaluation feedback, your self-reflection on the previous answer, and past reflections stored in memory. Provide an improved answer to the original query."""

# 自我反思的提示
SELF_REFLECTION_CHAT_INSTRUCTION = """You are an AI assistant. Given a query, your previous answer, and evaluation feedback, write a few sentences to explain why your answer might be incorrect or suboptimal as indicated by the feedback. Provide suggestions for improvement. Only provide the reflection text, not the improved answer."""

# 评估的少量示例
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

# 自我反思的少量示例
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

# 反思少量示例
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