import yaml
import os
import re
from typing import List, Dict, Any, Tuple

from ..mas_base import MAS
from .prompt_package import (
    SIMPLE_CHAT_INSTRUCTION,
    REFLEXION_CHAT_INSTRUCTION,
    SELF_REFLECTION_CHAT_INSTRUCTION,
    EVALUATION_FEW_SHOT,
    SELF_REFLECTION_FEW_SHOT,
    REFLEXION_FEW_SHOT
)

class ReflexionPackage(MAS):
    def __init__(self, general_config, method_config_name=None):
        super().__init__(general_config, method_config_name)
        
        # Load configuration file
        config_path = os.path.join(os.path.dirname(__file__), "config", "reflexion_main.yaml")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.max_iters = self.config.get("max_iters", 2)
        self.verbose = self.config.get("verbose", True)
        self.task_type = self.config.get("task_type", "code_completion")  # Task type

        # Prompt templates
        self.simple_chat_instruction = SIMPLE_CHAT_INSTRUCTION
        self.reflexion_chat_instruction = REFLEXION_CHAT_INSTRUCTION
        self.self_reflection_chat_instruction = SELF_REFLECTION_CHAT_INSTRUCTION
        self.evaluation_few_shot = EVALUATION_FEW_SHOT
        self.self_reflection_few_shot = SELF_REFLECTION_FEW_SHOT
        self.reflexion_few_shot = REFLEXION_FEW_SHOT

    def inference(self, query: str, file_code: dict) -> dict:
        """
        Entry function for code completion
        Args:
            query: Requirement description
            file_code: Dictionary of code files to be completed {file_path: code_content}
        Returns:
            Updated code file dictionary
        """
        self.current_code = file_code.copy()
        current_answer = ""
        
        # Main iteration loop
        for iteration in range(self.max_iters):
            # Generate code completion
            current_answer = self._generate_answer(
                strategy="simple" if iteration == 0 else "reflexion",
                query=query,
                prev_answer=current_answer,
                feedback=getattr(self, 'last_feedback', ''),
                reflection=getattr(self, 'last_reflection', ''),
                memory=getattr(self, 'memory', [])
            )
            print(current_answer)
            # Update code state
            self._update_code_blocks(current_answer)
            
            # Evaluate code quality
            is_passing, feedback = self._evaluate_code(query)
            self.last_feedback = feedback
            
            if self.verbose:
                status = "PASS" if is_passing else "FAIL"
                print(f"Iteration {iteration+1}/{self.max_iters} {status}")
                
            # Early exit condition
            if is_passing:
                break
                
            # Generate self-reflection
            reflection = self._generate_self_reflection(current_answer, feedback, query)
            self.last_reflection = reflection
            self.memory = getattr(self, 'memory', []) + [reflection]

        return self.current_code

    def _generate_answer(self, strategy: str, **kwargs) -> str:
        """Generate code completion"""
        if strategy == "simple":
            messages = [
                {"role": "system", "content": f"{self.simple_chat_instruction}\nCurrent code state:\n{self._format_code_context()}"},
                {"role": "user", "content": f"""
Output format description:\n  ## STRICT OUTPUT FORMAT:
Answer: 
@ {{relative_path/filename_1}}
```python
[COMPLETE file code including ALL original code plus your implementations]
```
@ {{relative_path/filename_2}}
```python
[COMPLETE file code including ALL original code plus your implementations]
```
@ {{relative_path/filename_3}}
```python
[COMPLETE file code including ALL original code plus your implementations]
```

Requirement description:\n{kwargs['query']}\nFiles to be completed:\n{list(self.current_code.keys())}"""}
            ]
        elif strategy == "reflexion":
            messages = [
                {"role": "system", "content": self.reflexion_chat_instruction},
                {"role": "user", "content": f"""
Output format description:\n  ## STRICT OUTPUT FORMAT:
Answer: 
@ {{relative_path/filename_1}}
```python
[COMPLETE file code including ALL original code plus your implementations]
```
@ {{relative_path/filename_2}}
```python
[COMPLETE file code including ALL original code plus your implementations]
```
@ {{relative_path/filename_3}}
```python
[COMPLETE file code including ALL original code plus your implementations]
```
               
Requirement description:\n{kwargs['query']}\nCurrent code:\n{self._format_code_context()}
                 """},
                {"role": "assistant", "content": kwargs['prev_answer']},
                {"role": "user", "content": f"Feedback:\n{kwargs['feedback']}\nReflection:\n{kwargs['reflection']}"}
            ]
        
        return self.call_llm(messages=messages).strip()

    def _update_code_blocks(self, response: str):
        """Extract and update code blocks from response
        New format example:
        @ absl/flags/_helpers.py
        ```python 
        [complete code]
        ```
        """
        # Match pattern: @ path + python code block
        pattern = r'@\s*([^\n]+?)\s*\n```python\s*\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if not matches and self.verbose:
            print(f"[DEBUG] No valid code block matched\nResponse snippet:\n{response[:300]}...")
        
        for file_path, code in matches:
            file_path = file_path.strip()
            if file_path in self.current_code:
                # Keep code indentation and remove leading/trailing whitespace
                self.current_code[file_path] = code.strip('\n')
            elif self.verbose:
                print(f"[WARNING] Unknown file path: {file_path}")


    def _evaluate_code(self, query: str) -> Tuple[bool, str]:
        """Evaluate code quality"""
        system_prompt = "You are a code quality evaluation expert. Check the code according to the following criteria:\n1. Fulfills the query requirements\n2. Reasonable code structure\n3. No syntax errors\nIf all three criteria are met, answer PASS, otherwise answer FAIL\n\n"
        user_prompt = f"""
        Output format:1.PASS or FAIL;
        2. Evaluation conclusion\n\n
        Query requirements:\n{query}\n\nCurrent code:\n{self._format_code_context()}\n\nEvaluation conclusion:"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.call_llm(messages=messages).strip()
        print(response)
        return ("PASS" in response.upper()), response

    def _generate_self_reflection(self, answer: str, feedback: str, query: str) -> str:
        """Generate code improvement reflection"""
        system_prompt = self.self_reflection_chat_instruction
        user_prompt = f"Requirement description:\n{query}\nGenerated code:\n{answer}\nEvaluation feedback:\n{feedback}\nImprovement reflection:"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.call_llm(messages=messages).strip()

    def _format_code_context(self) -> str:
        """Format code context"""
        return "\n\n".join([f"File path: {path}\nCode content:\n{code}" for path, code in self.current_code.items()])