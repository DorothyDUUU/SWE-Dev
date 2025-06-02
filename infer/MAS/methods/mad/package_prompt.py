DEBATE_TOPIC=""
BASE_ANSWER= ""
DEBATE_ANSWER= ""
PLAYER_META_PROMPT = """
AIM: You are the Affirmative agent in a debate providing solutions aligned with the query's requirements.

Instructions:
- Provide complete solutions based strictly on file_code.
- Ensure solutions fully comprehend the functional requirements in the query.
- Avoid alterations that delete or add unrelated elements to the file_code.
- Do not import any new dependencies.

Debate Topic: ##debate_topic##
"""

MODERATOR_META_PROMPT = """
AIM: You are the Moderator, responsible for adjudicating based on the clarity and completeness of function implementations referenced in the query.

Instructions:
- Ensure each argument addresses the detailed requirements laid out in the query.
- Evaluate solutions strictly based on the file_code provided.
- Prohibit modifications that delete existing content in file_code.
- Avoid adding anything not explicitly mentioned in the query.
- Do not import any new content.

Debate Topic: ##debate_topic##
"""


AFFIRMATIVE_PROMPT = """
You propose implementing the detailed solutions for the debate topic: ##debate_topic##. 

Important Instructions:
- Focus on completing the code functions strictly as per the query instructions.
- Base your modifications strictly on the file_code provided.
- Do not delete any existing content in file_code.
- Avoid adding anything not explicitly mentioned in the query.
- Do not import any new content.
"""

NEGATIVE_PROMPT = """
{##aff_ans##}

AIM: Provide a rebuttal against the Affirmative proposal, focusing on achieving the exact function completion as described in the query.

Important Instructions:
- Base your rebuttal and suggestions strictly on the file_code and Affirmative's claims.
- Do not delete any existing content in file_code.
- Avoid proposing anything not explicitly mentioned in the query.
- Do not import any new content.
"""


MODERATOR_PROMPT = """
Now the ##round## round of debate for both sides has been completed.

Affirmative side arguing:
##aff_ans##

Negative side arguing:
##neg_ans##

You, as the Moderator, assess both sides based on how comprehensively they complete functions as described in the query.

Important Instructions:
- Judge solutions strictly based on the file_code provided.
- No modifications should delete existing content in file_code.
- Avoid adding anything not explicitly mentioned in the query.
- Do not import any new content.

Please output your evaluation in JSON format:
{
    "Whether there is a preference": "Yes or No",
    "Supported Side": "Affirmative or Negative",
    "Reason": "",
    "debate_answer": ""
}
"""


JUDGE_PROMPT_LAST1="Affirmative side arguing: ##aff_ans##\n\nNegative side arguing: ##neg_ans##\n\nNow, what answer candidates do we have? Present them without reasons."
JUDGE_PROMPT_LAST2 = """
AIM: Provide the final conclusive answer to the stated debate topic.

Instructions:
- Summarize the reasoning from both sides.
- Choose the final correct answer and explain your reasons.
- Base final decisions strictly on the file_code and query's requirements.
- Ensure no existing content in file_code is deleted unnecessarily.
- Avoid adding anything not explicitly mentioned in the query.
- Do not import any new content.

Output Format (Strict JSON):
{ "Reason": "...",     
"debate_answer": {
        "[file_path_1]": "Replace this with the updated code content for file_path_1.",
        "[file_path_2]": "Replace this with the updated code content for file_path_2."
    }
}
"""
DEBATE_PROMPT = "{##oppo_ans##}\n\nAIM: Respond to the opposing argument critically, explaining your reasoning."
