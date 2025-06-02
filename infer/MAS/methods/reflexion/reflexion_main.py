import yaml
import os
from typing import List, Dict, Any, Tuple

from ..mas_base import MAS
from .prompt_main import (
    SIMPLE_CHAT_INSTRUCTION,
    REFLEXION_CHAT_INSTRUCTION,
    SELF_REFLECTION_CHAT_INSTRUCTION,
    EVALUATION_FEW_SHOT,
    SELF_REFLECTION_FEW_SHOT,
    REFLEXION_FEW_SHOT
)

class ReflexionGeneral(MAS):
    def __init__(self, general_config, method_config_name=None):
        super().__init__(general_config, method_config_name)
        
        # 加载配置文件
        config_path = os.path.join(os.path.dirname(__file__), "config", "reflexion_main.yaml")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.max_iters = self.config.get("max_iters", 2)
        self.verbose = self.config.get("verbose", True)
        self.task_type = self.config.get("task_type", "general")
        
        # 提示模板常量直接定义在代码中，而不是从配置文件加载
        # 简单生成模式的提示
        self.simple_chat_instruction = SIMPLE_CHAT_INSTRUCTION
        self.reflexion_chat_instruction = REFLEXION_CHAT_INSTRUCTION
        self.self_reflection_chat_instruction = SELF_REFLECTION_CHAT_INSTRUCTION
        self.evaluation_few_shot = EVALUATION_FEW_SHOT
        self.self_reflection_few_shot = SELF_REFLECTION_FEW_SHOT
        self.reflexion_few_shot = REFLEXION_FEW_SHOT

    def inference(self, query: str,file_code: dict) -> str:
        """
        对输入的一般问题应用Reflexion方法并返回答案
        
        Args:
            query: 用户输入的问题
        
        Returns:
            str: 最终答案
        """
        # if self.verbose:
        #     print(f"接收到问题: {query[:50]}...")
            
        # 初始化
        problem = {"prompt": query}
        current_answer = self._generate_answer(problem["prompt"], "simple")
        answers = [current_answer]
        mem = []
        
        if self.verbose:
            print(f"初次回答: {current_answer[:50]}...")
            
        # 评估初次回答
        is_passing, feedback = self._evaluate_answer(current_answer, query)
        feedbacks = [feedback]
        
        if self.verbose:
            print(f"初次评估{'通过' if is_passing else '失败'}")
            
        # 如果初次回答通过，直接返回
        if is_passing:
            if self.verbose:
                print("第一次回答通过了评估")
            return current_answer
        
        # 使用自我反思迭代改进
        iteration = 1
        current_feedback = feedback
        
        while iteration < self.max_iters:
            if self.verbose:
                print(f"开始迭代 {iteration}/{self.max_iters}")
            
            # 生成自我反思
            reflection = self._generate_self_reflection(current_answer, current_feedback, query)
            mem.append(reflection)
            
            if self.verbose:
                print(f"生成自我反思: {reflection[:50]}...")
                
            # 应用自我反思进行下一次尝试
            current_answer = self._generate_answer(
                problem["prompt"],
                "reflexion",
                prev_answer=current_answer,
                feedback=current_feedback,
                reflection=reflection,
                memory=mem
            )
            answers.append(current_answer)
            
            # 评估新回答
            is_passing, current_feedback = self._evaluate_answer(current_answer, query)
            feedbacks.append(current_feedback)
            
            if self.verbose:
                print(f"迭代 {iteration} {'通过' if is_passing else '失败'}")
                
            # 如果通过，提前退出
            if is_passing:
                if self.verbose:
                    print(f"迭代 {iteration} 通过了评估")
                break
                
            iteration += 1
        
        # 返回最终答案
        return current_answer
    
    def _generate_answer(
        self, 
        query: str, 
        strategy: str, 
        prev_answer: str = None,
        feedback: str = None,
        reflection: str = None,
        memory: List[str] = None
    ) -> str:
        """生成答案"""
        if strategy == "simple":
            system_prompt = self.simple_chat_instruction
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            if self.verbose:
                print(f"Simple generation system prompt: {system_prompt[:50]}...")
                print(f"Simple generation user prompt: {query[:50]}...")
            
            response = self.call_llm(messages=messages)
        
        elif strategy == "reflexion":
            system_prompt = self.reflexion_chat_instruction
            
            # 构造多轮对话
            memory_context = "\n".join([f"[past reflection {i}]: {mem}" for i, mem in enumerate(memory)])
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.reflexion_few_shot},
                {"role": "assistant", "content": prev_answer},
                {"role": "user", "content": f"[evaluation feedback]:\n{feedback}\n\n[self-reflection]:"},
                {"role": "assistant", "content": reflection},
                {"role": "user", "content": f"[past reflections]:\n{memory_context}\n\n[improved answer]:\n{query}"}
            ]
            
            if self.verbose:
                print(f"Reflexion generation - using multi-turn conversation with {len(messages)} messages")
            
            response = self.call_llm(messages=messages)
        
        else:
            raise ValueError(f"不支持的策略: {strategy}")
        
        return response.strip()
    
    def _evaluate_answer(self, answer: str, query: str) -> Tuple[bool, str]:
        """评估答案质量"""
        system_prompt = "You are an evaluator that assesses the quality of answers to general questions."
        user_prompt = f"{self.evaluation_few_shot}\n\n[query]:\n{query}\n\n[answer]:\n{answer}\n\n[evaluation]:"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.call_llm(messages=messages)
        
        # 解析评估结果
        is_passing = "PASS" in response.upper()
        feedback = response.strip()
        
        return is_passing, feedback
    
    def _generate_self_reflection(self, answer: str, feedback: str, query: str) -> str:
        """生成自我反思"""
        system_prompt = self.self_reflection_chat_instruction
        user_prompt = f"{self.self_reflection_few_shot}\n\n[query]:\n{query}\n\n[answer]:\n{answer}\n\n[evaluation feedback]:\n{feedback}\n\n[self-reflection]:"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.call_llm(messages=messages)
        return response.strip()