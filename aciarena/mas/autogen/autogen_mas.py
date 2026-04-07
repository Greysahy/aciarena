from aciarena.mas import BaseMAS
from aciarena.mas.autogen.agents import *
from aciarena.utils.factory import register_mas

@register_mas("autogen")
class AutoGen(BaseMAS):
    def __init__(self, llm_config, logger, malicious_agents=['assistant'], code_execute=False, max_turn=2):
        self.code_execute = code_execute
        self.is_termination_msg = "TERMINATE"
        super().__init__(llm_config, malicious_agents, logger, max_turn)

    def init_agents(self):
        return {
            "assistant": AssistantAgent(llm_config=self.llm_config, code_execute=self.code_execute),
            "user_proxy": UserProxyAgent(llm_config=self.llm_config, code_execute=self.code_execute),
        }
    
    def _log_step(self, sender, receiver, message):
        self.logger.log_message(sender=sender, receiver=receiver, message=message)

    def _check_termination(self, response):
        return self.is_termination_msg in response

    def bootstrap(self, query): 
        self._log_step(sender="user", receiver="assistant", message=query)

        assistant_response = self.get_agent("assistant").run_step(query=query)
        self._log_step(sender="assistant", receiver="user_proxy", message=assistant_response)

        return {"response": assistant_response}, self._check_termination(assistant_response)
        
    def step(self, args):
        terminate = False
        assistant_response = args["response"]

        self._log_step(sender="user", receiver="assistant", message=assistant_response)

        # UserProxyAgent response
        user_proxy_response = self.get_agent("user_proxy").run_step(query=assistant_response)
        self._log_step(sender="user_proxy", receiver="assistant", message=assistant_response)
        if self._check_termination(user_proxy_response):
            terminate = True

        # AssistantAgent response
        assistant_response = self.get_agent("assistant").run_step(query=user_proxy_response)
        self._log_step(sender="assistant", receiver="user_proxy", message=assistant_response)
        if self._check_termination(assistant_response):
            terminate = True

        return {"response": assistant_response}, terminate
        
    def conclude(self, args):
        return args