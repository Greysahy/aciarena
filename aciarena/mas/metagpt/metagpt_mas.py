from aciarena.mas import BaseMAS
from aciarena.mas.metagpt.agents import *
from aciarena.utils.factory import register_mas
from typing import List
import re

@register_mas("metagpt")
class MetaGPT(BaseMAS):
    def __init__(self, llm_config, malicious_agents=['product_manager'], logger=None, max_turn=3):
        super().__init__(llm_config, malicious_agents, logger, max_turn)
        self.malicious_agents = malicious_agents

    def init_agents(self):
        agents = {
            "product_manager": ProductManagerAgent(self.llm_config),
            "architect": ArchitectAgent(self.llm_config),
            "project_manager": ProjectManagerAgent(self.llm_config),
            "engineer": EngineerAgent(self.llm_config),
            "qa_engineer": QAEngineerAgent(self.llm_config),
        }

        return agents

    def _log_step(self, sender, receiver, message):
        if self.logger:
            self.logger.log_message(sender=sender, receiver=receiver, message=message)
        
    def _extract_bugs(self, qa_content: str) -> List[str]:
        bugs_match = re.search(r"## Bugs Found\n- ([^\n]+)", qa_content)
        if bugs_match and bugs_match.group(1) != "None":
            return [bugs_match.group(1)]
        return []

    def _extract_suggestions(self, qa_content: str) -> List[str]:
        suggestions_match = re.search(r"## Improvement Suggestions\n- ([^\n]+)", qa_content)
        if suggestions_match and suggestions_match.group(1) != "None":
            return [suggestions_match.group(1)]
        return []

    def _need_iteration(self, qa_content: str) -> bool:
        return bool(self._extract_bugs(qa_content) or self._extract_suggestions(qa_content))

    def bootstrap(self, query: str):
        self._log_step(sender="user", receiver="product_manager", message=query)
        args = {
            "query": query,
            "response": None
        }
        terminate = False
        return args, terminate

    def step(self, args):
        terminate = False
        product_manager_response = self.get_agent("product_manager").run_step(query=args["query"])
        self._log_step("product_manager", "architect", product_manager_response)

        architect_response = self.get_agent("architect").run_step(query={
            "product_manager_response": product_manager_response,
        })
        self._log_step("architect", "project_manager", architect_response)

        project_manager_response = self.get_agent("project_manager").run_step(query={
            "architect_response": architect_response,
        })
        self._log_step("project_manager", "engineer", project_manager_response)

        engineer_response = self.get_agent("engineer").run_step(query={
            "project_manager_response": project_manager_response,
        })
        self._log_step("engineer", "qa_engineer", engineer_response)

        qa_engineer_response = self.get_agent("qa_engineer").run_step(query={
            "engineer_response": engineer_response,
        })
        self._log_step("qa_engineer", "system", qa_engineer_response)

        args["response"] = qa_engineer_response
        if not self._need_iteration(args["response"]):
            return args, True

        args["qa_feedback"] = {
            "bugs": self._extract_bugs(qa_engineer_response),
            "suggestions": self._extract_suggestions(qa_engineer_response),
        }

        return args, terminate
    
    def conclude(self, args):
        conversation = {}
        for agent_name in self.agents:
            agent = self.get_agent(agent_name)
            conversation[agent_name] = agent.retrieve_memory()

        args["conversation"] = conversation
        return args
