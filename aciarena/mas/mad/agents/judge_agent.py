from aciarena.agent_components import BaseAgent
from typing import List, Dict

class JudgeAgent(BaseAgent):
    def __init__(self, llm_config):
        super().__init__(llm_config=llm_config)
        self.name = "judge"

    def update_profile(self, profile) -> None:
        if self.user_information:
            self.profile = f"{self.user_information}\n{profile}"
        else:
            self.profile = profile

        self.memory = self.init_memory()
        self.update_memory(role="system", content=self.profile)

    def step(self, query: str, *args, **kwargs) -> str:
        self.update_memory(role="user", content=query)
        messages = self.retrieve_memory()
        response = self.llm.call_llm(messages, json_output=True)
        self.update_memory(role="assistant", content=response)

        return response