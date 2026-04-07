from aciarena.agent_components.base_agent import BaseAgent
from typing import List, Dict


class TaskSpecifierAgent(BaseAgent):
    def __init__(self, llm_config):
        super().__init__(llm_config=llm_config)
        self.name = "task_specifier"

    def update_profile(self, profile) -> None:
        if self.user_information:
            self.profile = f"{self.user_information}\n{profile}"
        else:
            self.profile = profile

        self.memory = self.init_memory()
        self.update_memory(role="system", content=self.profile)

    def step(self, query: str, *args, **kwargs) -> str:
        option_num = kwargs.get("option_num", 1)
        self.update_memory(role="user", content=query)
        messages = self.retrieve_memory()
        response = self.llm.call_llm(messages, option_num=option_num, is_multi_options=(option_num > 1))
        if option_num == 1:
            responses = []
            self.update_memory(role="assistant", content=response)
            responses.append(response)
            return responses
        else:
            choices = [choice.message.content for choice in response.choices]
            for choice in choices:
                self.update_memory(role="assistant", content=choice)
            return choices
