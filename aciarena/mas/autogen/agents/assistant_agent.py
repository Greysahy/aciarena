from aciarena.agent_components import BaseAgent
from aciarena.mas.autogen.prompt import ASSISTANT_AGENT_SYSTEM_MESSAGE, ASSISTANT_AGENT_SYSTEM_MESSAGE_CODER, DEFAULT_USER_PROXY_AGENT_SYSTEM_MESSAGE
from typing import List, Dict

class AssistantAgent(BaseAgent):
    def __init__(self, llm_config, code_execute=False):
        super().__init__(llm_config=llm_config)
        self.name = "assistant"
        if code_execute:
            self.profile = ASSISTANT_AGENT_SYSTEM_MESSAGE_CODER
        else: 
            self.profile = ASSISTANT_AGENT_SYSTEM_MESSAGE
        
        self.update_memory(role="system", content=self.profile)

    def step(self, query: str, *args, **kwargs) -> str:
            self.memory.conversation[0]["content"] = self.profile
            self.update_memory(role="user", content=query)
            messages = self.retrieve_memory()
            response = self.llm.call_llm(messages)
            self.update_memory(role="assistant", content=response)

            return response

    def retrieve_memory(self) -> List[Dict]:
        return self.memory.conversation

    def update_memory(self, role, content) -> None:
        self.memory.conversation.append({"role": role, "content": content})
