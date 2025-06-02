import os
from ..mas_base import MAS
from ..utils import load_config

class SelfConsistency(MAS):
    def __init__(self, general_config, method_config_name="config"):
        super().__init__(general_config)

        self.method_config = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", f"{method_config_name}.yaml"))
        self.parallel_num = self.method_config["parallel_num"]
    
    def inference(self, query):
        
        agent_results = [self.call_llm(prompt=query) for _ in range(self.parallel_num)]

        final_decision_instruction = self.get_final_decision_instruction(query, agent_results)
        response = self.call_llm(prompt=final_decision_instruction)

        return response
    
    def get_final_decision_instruction(self, query, agent_results):
        instruction = f"[Task]:\n{query}\n\n"

        for i, result in enumerate(agent_results):
            instruction += f"[Solution {i+1}]:\n{result}\n\n"

        instruction += "Given the task and all the above solutions, reason over them carefully and provide a final answer to the task."

        return instruction