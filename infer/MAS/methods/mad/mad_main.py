import os
import re

from ..mas_base import MAS
from ..utils import load_config
from .mad_utils import Agent
from .prompt import *

NAME_LIST = [
    "Affirmative side",
    "Negative side",
    "Moderator",
]

class MAD(MAS):
    def __init__(self, general_config, method_config_name="config"):
        super().__init__(general_config)
        self.method_config = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", f"{method_config_name}.yaml"))
        self.config = {}
        
        self.num_players = self.method_config["num_players"]
        self.max_round = self.method_config["max_round"]

        self.player_meta_prompt = ""
        self.moderator_prompt = ""
        self.affirmative_prompt = ""
        self.judge_prompt_last2 = ""

    def init_prompt(self, debate_topic):
        """initialize the prompt"""
        self.player_meta_prompt = PLAYER_META_PROMPT.replace("##debate_topic##", debate_topic)
        self.moderator_prompt = MODERATOR_META_PROMPT.replace("##debate_topic##", debate_topic)
        self.affirmative_prompt = AFFIRMATIVE_PROMPT.replace("##debate_topic##", debate_topic)
        self.judge_prompt_last2 = JUDGE_PROMPT_LAST2.replace("##debate_topic##", debate_topic)

    def create_agents(self):
        """create players and moderator"""
        self.players = [Agent(name) for name in NAME_LIST]
        self.affirmative = self.players[0]
        self.negative = self.players[1]
        self.moderator = self.players[2]

    def init_agents(self):
        """initialize player_meta_prompt, and start the first round of debate"""
        self.affirmative.set_meta_prompt(self.player_meta_prompt)
        self.negative.set_meta_prompt(self.player_meta_prompt)
        self.moderator.set_meta_prompt(self.moderator_prompt)

        # An affirmative agent starts the debate
        self.affirmative.add_event(self.affirmative_prompt)
        # self.aff_ans = self.affirmative.ask()
        self.aff_ans = self.call_llm(messages=self.affirmative.memory_lst)
        self.affirmative.add_memory(self.aff_ans)
        self.base_answer = self.aff_ans  

        # A negative agent responds to the affirmative agent
        self.negative.add_event(NEGATIVE_PROMPT.replace('##aff_ans##', self.aff_ans))
        self.neg_ans = self.call_llm(messages=self.negative.memory_lst)
        self.negative.add_memory(self.neg_ans)

        # A moderator evaluates the answers from both sides
        self.moderator.add_event(
            MODERATOR_PROMPT.replace('##aff_ans##', self.aff_ans)
            .replace('##neg_ans##', self.neg_ans)
            .replace('##round##', 'first')
        )
        self.mod_ans = self.call_llm(messages=self.moderator.memory_lst)
        self.mod_ans = re.sub(r"```json|```", "", self.mod_ans).strip()
        self.moderator.add_memory(self.mod_ans)
        self.mod_ans = eval(self.mod_ans)

    def round_dct(self, num: int):
        dct = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth'
        }
        return dct.get(num, f"{num}th")

    def print_answer(self, debate_topic):
        print("\n\n===== Debate Done! =====")
        print("\n----- Debate Topic -----")
        print(debate_topic)
        print("\n----- Base Answer -----")
        print(self.base_answer)
        print("\n----- Debate Answer -----")
        print(self.debate_answer)
        print("\n----- Debate Reason -----")
        print(self.config.get("Reason", "No reason provided."))

    # ... 其余代码保持不变 ...

    def inference(self, query, file_code):
        """inference function for MAD"""
        debate_topic = query
        self.init_prompt(debate_topic)
        self.create_agents()
        self.init_agents()

        # Since unnecessary rounds often lead to errors, simplify to single round.
        try:
            aff_meta_prompt = f"""
AIM: You are the Affirmative agent engaging in this debate. Focus on providing precise solutions for the incomplete functions in the provided code files.

Problem Requirements: {query}

Debate Topic: {debate_topic}

Important Instructions:
- Keep your modifications aligned with the existing file_code.
- Do not delete any existing content in file_code.
- Strictly focus on suggestions related to the query description.
- All updates must strictly correspond to the requirements mentioned in the query.
- Do not import any new dependencies.

Files:
{file_code}
"""
            self.affirmative.add_event(aff_meta_prompt)
            self.aff_ans = self.call_llm(messages=self.affirmative.memory_lst)
            self.affirmative.add_memory(self.aff_ans)

            neg_meta_prompt = f"""
AIM: You are the Negative agent critically reviewing changes proposed by the Affirmative agent. Focus on suggesting improvements or correcting implementations with respect to the query's details.

Problem Requirements: {query}

Debate Topic: {debate_topic}

Affirmative's Proposed Changes: {self.aff_ans}

Important Instructions:
- Base your suggestions strictly on the existing file_code and the affirmative's changes.
- Do not delete any existing content in file_code.
- Suggest adjustments only if there are discrepancies with the query requirements.

Files:
{file_code}
"""
            self.negative.add_event(neg_meta_prompt)
            self.neg_ans = self.call_llm(messages=self.negative.memory_lst)
            self.negative.add_memory(self.neg_ans)

            mod_meta_prompt = f"""
AIM: As the Moderator, evaluate the suggestions from the Affirmative and Negative sides. Your task is to ensure function implementations align precisely with the query's requirements.

Problem Requirements: {query}

Current Round: first

Files:
{file_code}

Affirmative's Suggestions:
{self.aff_ans}

Negative's Suggestions:
{self.neg_ans}

Output Format:
{{
    "Supported Side": "Affirmative or Negative",
    "Reason": "Reason for the preference",
    "debate_answer": {{
        "[file_path_1]": "Replace this with the updated code content for file_path_1."
    }}
}}
"""
            self.moderator.add_event(mod_meta_prompt)
            self.mod_ans = self.call_llm(messages=self.moderator.memory_lst)
            self.mod_ans = eval(re.sub(r"```json|```", "", self.mod_ans).strip())
            if self.mod_ans.get("Supported Side") == "Affirmative":
                self.debate_answer = self.mod_ans["debate_answer"]
                self.config.update(self.mod_ans)
                self.config['success'] = True
                return self.debate_answer
            else:
                raise ValueError("Moderator failed to resolve debate in a single round.")

        except Exception as e:
            # Direct fallback to judge if any error occurs
            judge_prompt = f"""
AIM: Provide the final conclusive answer after evaluating Affirmative and Negative perspectives.

Affirmative's Suggestions:
{self.aff_ans}

Negative's Suggestions:
{self.neg_ans}

Output Format:
{{
    "debate_answer": {{
        "[file_path_1]": "Replace this with the updated code content for file_path_1."
    }},
    "Reason": "Reason why this answer is accurate."
}}
"""
            judge_player = Agent(name="Judge")
            judge_player.add_event(judge_prompt)
            ans = self.call_llm(messages=judge_player.memory_lst)
            ans = eval(re.sub(r"```json|```", "", ans).strip())
            
            self.debate_answer = ans["debate_answer"]
            self.config.update(ans)
            self.config['success'] = True

            return self.debate_answer