from aciarena.agent_components.base_agent import BaseAgent

class DebateAgent(BaseAgent):
    """
    Agent that participates in the debate by providing responses to queries.
    Each agent maintains its own memory and can see other agents' responses.
    """
    
    def __init__(self, llm_config, name: str = "debater"):
        super().__init__(llm_config, name)
        self.profile = "You are a helpful AI assistant."
        self.update_memory(role="system", content=self.profile)
    
    def step(self, query: str, *args, **kwargs) -> str:
        """
        Generate a response to the query.
        The query can be the original question or a message containing other agents' responses.
        """
        self.memory.conversation[0]['content'] = self.profile
        self.update_memory(role="user", content=query)
        messages = self.retrieve_memory()
        response = self.llm.call_llm(messages)
        self.update_memory(role="assistant", content=response)
        
        return response
    
    def get_latest_response(self) -> str:
        """Get the latest response from this agent."""
        memory = self.retrieve_memory()
        if memory and memory[-1]["role"] == "assistant":
            return memory[-1]["content"]
        return ""
