from aciarena.agent_components import BaseAgent
from aciarena.mas.autogen.prompt import DEFAULT_USER_PROXY_AGENT_SYSTEM_MESSAGE
import re
import sys
import io
import subprocess
from typing import List, Dict

class UserProxyAgent(BaseAgent):
    def __init__(self, llm_config, code_execute=False):
        super().__init__(llm_config=llm_config)
        self.name = "user_proxy"
        self.profile = DEFAULT_USER_PROXY_AGENT_SYSTEM_MESSAGE
        self.code_execute = code_execute
        self.update_memory(role="system", content=self.profile)

    def step(self, query: str, *args, **kwargs) -> str:
        self.update_memory(role="user", content=query)

        # optional code execution
        if self.code_execute:
            is_code, code_output = self.process_code_response(query)
            if is_code:
                reply = "The output of your code is:\n" + code_output
                self.update_memory(role="assistant", content=reply)
                return reply

        # otherwise normal LLM response
        messages = self.retrieve_memory()
        response = self.llm.call_llm(messages)
        self.update_memory(role="assistant", content=response)
        
        return response

    def retrieve_memory(self) -> List[Dict]:
        return self.memory.conversation

    def update_memory(self, role: str, content: str) -> None:
        self.memory.conversation.append({"role": role, "content": content})

    def process_code_response(self, response: str) -> (bool, str):
        """
        Parses response and executes code if found.
        Returns (is_code, output)
        """
        python_pattern = r'```python\n(.*?)\n```'
        shell_pattern = r'```sh\n(.*?)\n```'

        python_code = re.findall(python_pattern, response, re.DOTALL)
        shell_code = re.findall(shell_pattern, response, re.DOTALL)

        if python_code:
            return True, self.run_code(python_code[0], "python")
        elif shell_code:
            return True, self.run_code(shell_code[0], "sh")
        else:
            return False, ""

    def run_code(self, code: str, code_type: str) -> str:
        try:
            if code_type == "python":
                local_vars = {}
                stdout_buffer = io.StringIO()
                sys.stdout = stdout_buffer
                exec(code, {}, local_vars)
                sys.stdout = sys.__stdout__
                return stdout_buffer.getvalue()
            elif code_type == "sh":
                result = subprocess.run(code, shell=True, capture_output=True, text=True)
                return result.stdout
            else:
                return f"Unsupported code type: {code_type}"
        except Exception as e:
            sys.stdout = sys.__stdout__
            return f"Error during code execution: {str(e)}"
