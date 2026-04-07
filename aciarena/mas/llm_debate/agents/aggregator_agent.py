from aciarena.agent_components.base_agent import BaseAgent
from typing import List

class AggregatorAgent(BaseAgent):
    """
    Agent responsible for aggregating all debate responses into a final answer.
    """
    
    def __init__(self, llm_config, name: str = "aggregator"):
        super().__init__(llm_config, name)
        self.profile = "You are an aggregator agent that is responsible for aggregating all debate responses into a final answer."
    
    def step(self, query: str, *args, **kwargs) -> str:
        """
        Aggregate multiple answers into a final response.
        
        Args:
            query: The original question
            answers: List of answers from all debate agents
        """
        messages = [
            {"role": "system", "content": self.profile},
            {"role": "user", "content": query}
        ]
        response = self.llm.call_llm(messages)
        return response
