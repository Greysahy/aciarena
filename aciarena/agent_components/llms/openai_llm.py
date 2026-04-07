from aciarena.agent_components.llms.base_llm import BaseLLM
from openai import OpenAI, AsyncOpenAI
from openai import OpenAIError, RateLimitError, APIConnectionError, Timeout, BadRequestError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential, AsyncRetrying, RetryError
from pydantic import BaseModel

class AgentResponseSchema(BaseModel):
    response: str
    memory: str

class OpenAILLM(BaseLLM):
    def __init__(self, model_name="gpt-3.5-turbo", temperature=0.0, max_tokens=1024, seed=42):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.client = None
        self.async_client = None

        self.input_tokens = 0
        self.output_tokens = 0

    def from_config(self, config: dict):
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.openai.com/v1")

        if not api_key:
            raise ValueError("API key is required to initialize OpenAI client.")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        self.model_name = config.get("model_name", self.model_name)
        self.temperature = config.get("temperature", self.temperature)
        self.max_tokens = config.get("max_tokens", self.max_tokens)
        self.seed = config.get("seed", self.seed)
        return self

    @retry(
        retry=retry_if_exception_type((RateLimitError, Timeout, APIConnectionError, OpenAIError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def call_llm(self, messages, temperature=None, json_output=False, option_num=None, is_multi_options=False) -> str:
        if temperature is not None:
            params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": temperature,
                "seed": self.seed
            }
        else:
            params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "seed": self.seed
            }
        if json_output:
            params["response_format"] = {"type": "json_object"}
        
        try:
            if is_multi_options and option_num is not None:
                params["n"] = option_num
                response = self.client.chat.completions.create(**params)
                self.calculate_token_usage(response)
                return response
            else:    
                response = self.client.chat.completions.create(**params)
                self.calculate_token_usage(response)
                return response.choices[0].message.content if response.choices else "[Empty response]"
        except BadRequestError as e:
            raise RuntimeError(f"Bad request to OpenAI API: {e}")
        except OpenAIError as e:
            raise RuntimeError(f"OpenAI error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unhandled error: {e}")

    async def async_call_llm(self, messages) -> str:
        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type((RateLimitError, Timeout, APIConnectionError, OpenAIError)),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                stop=stop_after_attempt(3),
                reraise=True
            ):
                with attempt:
                    response = await self.async_client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        seed=self.seed
                    )
            return response.choices[0].message.content if response.choices else "[Empty response]"
        except BadRequestError as e:
            raise RuntimeError(f"Bad request to OpenAI API: {e}")
        except OpenAIError as e:
            raise RuntimeError(f"OpenAI error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unhandled error: {e}")

    def calculate_token_usage(self, response):
        self.input_tokens += response.usage.prompt_tokens
        self.output_tokens += response.usage.completion_tokens