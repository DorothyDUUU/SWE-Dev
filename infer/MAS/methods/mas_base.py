import json
import random
import openai
import requests
from tenacity import retry, wait_exponential, stop_after_attempt

from .utils import handle_retry_error

class MAS():

    def __init__(self, general_config, method_config_name=None):
        
        self.model_api_config = general_config["model_api_config"]
        self.model_name = general_config["model_name"]
        self.model_temperature = general_config["model_temperature"]
        self.model_max_tokens = general_config["model_max_tokens"]
        self.model_timeout = general_config["model_timeout"]
        
        # Tracking compute costs
        self.token_stats = {
            self.model_name: {"num_llm_calls": 0, "prompt_tokens": 0, "completion_tokens": 0}
        }

        self.memory_bank = {}
        self.tools = {}
        
    
    def inference(self, query):
        """
        query: Query to be passed to the MAS
        """
        response = self.call_llm(prompt=query)
        return response

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5), retry_error_callback=handle_retry_error)
    def call_llm(self, prompt=None, system_prompt=None, messages=None, model_name=None, temperature=None):
        model_name = model_name if model_name is not None else self.model_name
        model_dict = random.choice(self.model_api_config[model_name]["model_list"])
        model_name, model_url, api_key = model_dict['model_name'], model_dict['model_url'], model_dict['api_key']
        if messages is None:
            assert prompt is not None, "'prompt' must be provided if 'messages' is not provided."
            if system_prompt is not None:
                messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
            else:
                messages = [{"role": "user", "content": prompt}]
        model_temperature = temperature if temperature is not None else self.model_temperature
        if "gpt" not in model_name and "o1" not in model_name:
            llm = openai.OpenAI(base_url=model_url, api_key=api_key)
            try:
                completion = llm.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=model_temperature,
                    max_tokens=self.model_max_tokens,
                    timeout=self.model_timeout,
                    stream=True
                )
                response = ""
                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        response += content
                # response, num_prompt_tokens, num_completion_tokens = completion.choices[0].message.content, completion.usage.prompt_tokens, completion.usage.completion_tokens
            finally:
                llm.close()
            num_prompt_tokens = 0
            num_completion_tokens = 0
        else:
            payload_dict = {
                "model": model_name,
                "messages": messages,
                "max_completion_tokens": self.model_max_tokens
            }
            if "o1" not in model_name:
                payload_dict["temperature"] = model_temperature   # o1 does not support temperature
            headers = {
                'Authorization': api_key,
                'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Host': model_url,
                'Connection': 'keep-alive'
            }
            payload = json.dumps(payload_dict)
            result = requests.request("POST", f"http://{model_url}/v1/chat/completions", headers=headers, data=payload)
            response, num_prompt_tokens, num_completion_tokens = result.json()["choices"][0]["message"]["content"], result.json()["usage"]["prompt_tokens"], result.json()["usage"]["completion_tokens"]
        
        if isinstance(response, str):       # in cases where response is None or an error message
            if model_name not in self.token_stats:
                self.token_stats[model_name] = {"num_llm_calls": 0, "prompt_tokens": 0, "completion_tokens": 0}
            else:
                self.token_stats[model_name]["num_llm_calls"] += 1
                self.token_stats[model_name]["prompt_tokens"] += num_prompt_tokens
                self.token_stats[model_name]["completion_tokens"] += num_completion_tokens
        
        return response

    def get_token_stats(self):
        return self.token_stats
    
    def optimizing(self, val_data):
        """
        For methods that requires validation data such as GPTSwarm and ADAS
        """
        pass

    def retrieve_memory(self):
        pass

    def update_memory(self):
        pass
    
    def get_tool(self):
        pass