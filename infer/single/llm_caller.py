import litellm
from tenacity import retry, stop_after_attempt, wait_random_exponential
from openai import OpenAI
import time

class LLM:
    def __init__(self, config: dict):
        """
        Initialize the LLM API interface class.

        :param config: A dictionary containing the model configuration, including model name, API key, and base URL.
        """
        self.model_name = config.get('model')
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.temperature = config.get('temperature', 0.0)
        self.max_token = config.get('max_token', 8192)
        self.timeout = config.get('timeout', 1200)
        self.stream = config.get('stream', False)

    def completion(self, messages: list,sample_ls) -> str:
        if self.model_name in ["gpt-4o", "gpt-4o-mini"]:
            return self.closesource_completion(messages)
        else:
            return self.openesource_completion(messages,sample_ls)
    
    def closesource_completion(self, messages: list) -> str:
        content = [{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": messages}]
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        time_start = time.time()
        print(f"Calling {self.model_name} with temperature {self.temperature} and max_tokens {self.max_token}")
        response = client.chat.completions.create(
            model=self.model_name,
            messages=content,
            temperature=self.temperature,
            max_tokens=self.max_token,
            stream=self.stream,
            timeout=self.timeout
        )
        time_end = time.time()
        print(f"Received response from {self.model_name} in {time_end - time_start} seconds")
        return response.choices[0].message.content


    def opensource_completion(self, messages: list,sample_ls) -> str:
        content = [{"role": "user", "content": messages}]
        litellm.api_key = self.api_key
        if self.base_url:
            litellm.api_base = self.base_url
        count = 0
        while True:
            try:
                response = litellm.completion(
                    model=self.model_name,
                    messages=content,
                    temperature=self.temperature,
                    max_tokens=self.max_token,
                    response_format={"type": "text"}
                )
                generated_text = response['choices'][0]['message']['content']
                return generated_text
            except Exception as e:
                count = count + 1
                print(f"{sample_ls} Error generating text: {e}")
                if count >= 5:
                    return None

