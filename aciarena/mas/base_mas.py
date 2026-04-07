from abc import ABC, abstractmethod
from typing import Dict
from aciarena.agent_components import BaseAgent
from aciarena.agent_components.base_agent import get_llm
from aciarena.agent_components.base_agent import Message

class BaseMAS(ABC):
    def __init__(self, llm_config, malicious_agents=[], logger=None, max_turn=3):
        self.llm_config = llm_config
        self.logger = logger
        self.max_turn = max_turn
        self.agents = self.init_agents()

        for malicious_agent in malicious_agents:
            if malicious_agent not in self.agents:
                raise ValueError(f"Malicious agent '{malicious_agent}' not found in self.agents.")
        self.malicious_agents = malicious_agents

    @abstractmethod
    def init_agents(self) -> Dict[str, BaseAgent]:
        """
        Initialize and return a dictionary of agents involved in the MAS.
        Each agent must be a subclass of BaseAgent.
        """
        raise NotImplementedError("Subclasses must implement the init_agents() method.")

    def get_agent(self, name: str) -> BaseAgent:
        if name not in self.agents:
            raise ValueError(f"Agent '{name}' not found in self.agents. Available agents: {list(self.agents.keys())}")
        return self.agents[name]

    def get_token_usage(self):
        input_tokens = 0
        output_tokens = 0

        for agent_name in self.agents:
            agent = self.get_agent(agent_name)
            input_tokens += agent.llm.input_tokens
            output_tokens += agent.llm.output_tokens

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }

    def run(self, query):
        """
        Running of the MAS can be split into three phases:
        1. Bootstrap: Initialize the MAS with the initial query.
        2. Step: Process the query through the MAS for a number of turns.
        3. Conclude: Finalize the MAS with the results from the last step.
        """
        args, terminate = self.bootstrap(query)
        if not terminate:
            for _ in range(self.max_turn):
                args, terminate = self.step(args)
                if terminate:
                    break
        args = self.conclude(args)

        return args

    @abstractmethod
    def bootstrap(self, query: str):
        """
        Bootstrap the MAS with the initial query.
        This method can be overridden by subclasses to customize the bootstrap process.
        """
        raise NotImplementedError("Subclasses must implement the bootstrap() method.")

    @abstractmethod
    def step(self, args):
        """
        Perform a single step in the MAS with the given query.
        """
        raise NotImplementedError("Subclasses must implement the step() method.")
    
    @abstractmethod
    def conclude(self, args):
        """
        Conclude the MAS with the final arguments.
        This method can be overridden by subclasses to customize the conclusion process.
        """
        raise NotImplementedError("Subclasses must implement the conclude() method.")