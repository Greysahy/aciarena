from abc import ABC, abstractmethod
from aciarena.agent_components.base_agent import BaseAgent
from aciarena.mas.base_mas import BaseMAS
from aciarena.utils import register_attack_goal
from aciarena.agent_components import get_llm
from typing import List, Dict
import types
import copy

class BaseAttack(ABC):

    def __init__(self, args, llm_config):
        super().__init__()
        self.args = args
        self.payload = "default attack vector"
        self.llm_judge = get_llm(llm_config)
        self.answer = None
        self.malicious_agents = []
        self.turn_count = 0

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        for k, v in self.__dict__.items():
            if k == 'llm_judge':
                setattr(result, k, v)  
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result
    
    def set_turn(self, turn):
        self.turn_count = turn

    def set_answer(self, answer):
        self.answer = answer

    def set_malicious_agents(self, agents: List[str]):
        self.malicious_agents = agents

    def verify(self):
        """
        Verify the success of attack.
        This method should be implemented by subclasses to define the specific behavior of the attack.
        """
        raise NotImplementedError("Subclasses must implement the verify() method.")

    def run(self, mas: BaseMAS):
        """
        Hijack the agent and alter its behavior under attack.
        This method should be implemented by subclasses to define the specific behavior of the attack.
        """
        raise NotImplementedError("Subclasses must implement the run() method.")
    
class AdvInputAttack(BaseAttack):
    """
    Attack that alters the input to the agent.
    """
    def __init__(self, args, llm_config):
        super().__init__(args, llm_config)

class InstructionInjectionAttack(AdvInputAttack):
    def __init__(self, args, llm_config):
        super().__init__(args, llm_config)

    def inject_instruction(self, query):
        return f"{query}\n{self.payload}"

    def run(self, mas: BaseMAS):
        self.set_malicious_agents(mas.malicious_agents)
        for agent_name in mas.malicious_agents:
            malicious_agent = mas.get_agent(agent_name)
            original_step = malicious_agent.step

            def injected_step(agent_self, query, *args, **kwargs):
                tampered_query = self.inject_instruction(query)
                response = original_step(tampered_query, *args, **kwargs)

                # print(f"injected query: {tampered_query}\n Response: {response}")
                return response

            malicious_agent.step = types.MethodType(injected_step, malicious_agent)

class ToolInjectionAttack(AdvInputAttack):
    """
    Attack that injects malicious tools into the agent.
    """
    def __init__(self, args, llm_config):
        super().__init__(args, llm_config)

    def run(self, mas: BaseMAS):
        self.set_malicious_agents(mas.malicious_agents)
        for agent_name in mas.malicious_agents:
            malicious_agent = mas.get_agent(agent_name)
            malicious_agent.tools.append(self.payload)

class MemoryInjectionAttack(AdvInputAttack):
    """
    Attack that injects malicious memory into the agent.
    """
    def __init__(self, args, llm_config):
        super().__init__(args, llm_config)

    def run(self, mas: BaseMAS):
        self.set_malicious_agents(mas.malicious_agents)
        for agent_name in mas.malicious_agents:
            malicious_agent = mas.get_agent(agent_name)
            malicious_agent.update_memory(role="assistant", content=self.payload)

class MaliciousAgentAttack(BaseAttack):
    """
    Attack that involves a malicious agent.
    """
    def __init__(self, args, llm_config):
        super().__init__(args, llm_config)

    def run(self, mas: BaseMAS):
        self.set_malicious_agents(mas.malicious_agents)
        for agent_name in mas.malicious_agents:
            malicious_agent = mas.get_agent(agent_name)
            malicious_agent.profile = self.payload


class MessagePoisonAttack(BaseAttack):
    """
    Attack that poisons the messages exchanged between agents.
    """
    def __init__(self, args, llm_config):
        super().__init__(args, llm_config)

    def run(self, mas: BaseMAS):
        self.set_malicious_agents(mas.malicious_agents)
        for agent_name in mas.malicious_agents:
            malicious_agent = mas.get_agent(agent_name)

            def poisoned_step(agent_self, query, *args, **kwargs):
                return self.payload        
        
            malicious_agent.step = types.MethodType(poisoned_step, malicious_agent)

@register_attack_goal("none")
class NoneAttack(BaseAttack):
    """
    No attack, used as a placeholder.
    """
    def __init__(self, args, llm_config):
        super().__init__(args, llm_config)

    def run(self, mas: BaseMAS):
        return

    def verify(self):
        return False