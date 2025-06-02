import os
import re
import json
import shutil
from pathlib import Path

from ..mas_base import MAS
from ..utils import load_config
from .prompt import *

class MetaGPT(MAS):
    def __init__(self, general_config, method_config_name="config"):
        super().__init__(general_config)
        
        self.method_config = load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", f"{method_config_name}.yaml"))
        
        self.model_name = self.model_dict_list[0]['model_name']
        self.code_review_rounds = self.method_config['n_rounds']
        self.dataset_name = self.general_config['test_dataset_name']
        self.path = None
        
    def inference(self, query):
        # Initialize the directory structure
        path = Path("results") /self.dataset_name/ self.model_name / 'metagpt' /query[:20]
        self.path=path
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)
        # Storing documents at all stages
        (path / 'docs').mkdir()
        # Storing Generated Code Resources
        (path / 'resources').mkdir()
        self._save_file('docs/requirement.txt', query)

        # Multi-stage processing
        prd = self._process_stage(query, PRD_TEMPLATE, 'prd.json', "PRD complete")
        if not prd: return
        design = self._process_stage(prd, DESIGN_TEMPLATE, 'design.json', "design complete")
        if not design: return
        tasks = self._process_stage(design, TASKS_TEMPLATE, 'tasks.json', "tasks generated")
        if not tasks: return
        # Code Generation and Review Stage
        self._process_code(design, tasks)
    
    def _process_stage(self, input_data, template, output_file, success_msg):
        # Using LLM to Generate Current Stage Documentation
        query = CONTEXT_TEMPLATE.format(requirements=input_data)
        result = self.get_result(query, template)
        if result:
            self._save_file(f'docs/{output_file}', result)
            print(success_msg)
        return result
    
    def _process_code(self, design, tasks):
        task_data = json.loads(tasks)
        if not isinstance(task_data, dict):
            raise ValueError("Root element must be a dictionary")
        # Storing the context of generated code
        code_context=[]
        for file in task_data.get("Task list", []):
            # Generate initial code
            code = self._generate_code(design, tasks, file,"\n".join(code_context))
            # Multiple rounds of code review
            for _ in range(self.code_review_rounds):
                result, code = self._review_code(design, tasks, code, file,"\n".join(code_context))
                if "LGTM" in result:
                    break
            self._save_file(f'resources/{file}', code)
            code_context.append(f"----- {file}\n```{code}```")
            print(f'{file} saved')
    
    def get_result(self, query, prompt_template):
        prompt = prompt_template.format(context=query)
        response = self.call_llm(prompt=prompt)
        # Extracting target content using regular expressions
        if match := re.search(r'\[CONTENT\](.*?)\[/CONTENT\]', response, re.DOTALL):
            return match.group(1).strip()
    
    def _generate_code(self, design, task, filename, code_context, lang=""):
        # Generate new code based on current design documents, task descriptions, and existing code contexts
        prompt = CODE_TEMPLATE.format(
            design=design,
            task=task,
            filename=filename,
            code_context=code_context
        )
        code = self.call_llm(prompt=prompt)
        # Extract the contents of the code block (if there is a code wrap marker)
        if match := re.search(rf"```{lang}.*?\s+(.*?)```", code, re.DOTALL):
            return match.group(1)
        return code
    
    def _review_code(self, design, tasks, code, filename,code_context,lang=''):
        # Constructing a review context
        format_example = FORMAT_EXAMPLE.format(filename=filename)
        ctx_list = [
            "## System Design\n" + str(design)+ "\n",
            "## Task\n" + tasks+ "\n",
            "## Code Files\n"+ code_context + "\n",
        ]
        
        context_prompt = PROMPT_TEMPLATE.format(
            context="\n".join(ctx_list),
            code=code,
            filename=filename,
        )
        
        cr_prompt = EXAMPLE_AND_INSTRUCTION.format(format_example=format_example)
        cr_rsp = self.call_llm(context_prompt + cr_prompt)
        print(cr_rsp)
        result = self._extract_review_result(cr_rsp)
        
        if "LGTM" in result:
            return result, code
        
        # rewrite the code
        rewrite_prompt = f"{context_prompt}\n{cr_rsp}\n{REWRITE_CODE_TEMPLATE.format(filename=filename)}"
        code_rsp = self.call_llm(rewrite_prompt)
        # Extracting newly generated code blocks
        if match := re.search(rf"```{lang}.*?\s+(.*?)```", code_rsp, re.DOTALL):
            code_rsp= match.group(1)
        return self._extract_review_result(cr_rsp), code_rsp
    
    def _extract_review_result(self, text):
        if results := re.findall(r'## Code Review Result\s*\n([\s\S]*?)(?=\n## |\Z)', text):
            return results[0].strip()
        return ""
    
    def _save_file(self, relative_path, content):
        # Generic file saving method, supports JSON and plain text
        path = self.path / relative_path
        if isinstance(content, (dict, list)):
            with path.open('w') as f:
                json.dump(content, f)
        else:
            with path.open('w') as f:
                f.write(str(content))
