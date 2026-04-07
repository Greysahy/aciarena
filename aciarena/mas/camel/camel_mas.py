from aciarena.mas import BaseMAS
from aciarena.mas.camel.agents import *
from aciarena.utils.factory import register_mas
from aciarena.mas.camel.prompt import SystemPromptGenerator
import re

@register_mas("camel")
class CAMEL(BaseMAS):
    def __init__(self, llm_config, logger, malicious_agents=['assistant'], max_turn=2):
        self.config = {
            "assistant_role": "Postdoc",
            "user_role": "PhD Student",
            "critic_role": "Professor",
            "option_num": 1,
            "with_critic": False
        }
        self.is_termination_msg = "CAMEL_TASK_DONE"
        self.system_prompt_generator = SystemPromptGenerator()
        super().__init__(llm_config, malicious_agents, logger, max_turn)

    def init_agents(self):
        return {
            "assistant": AssistantAgent(llm_config=self.llm_config),
            "user_proxy": UserProxyAgent(llm_config=self.llm_config),
            "critic": CriticAgent(llm_config=self.llm_config),
            "task_specifier": TaskSpecifierAgent(llm_config=self.llm_config)
        }

    def _log_step(self, sender, receiver, message):
        self.logger.log_message(sender=sender, receiver=receiver, message=message)

    def _check_termination(self, response):
        return self.is_termination_msg in response
    
    def bootstrap(self, query): 
        _, _, _, task_specify_sys_msg, task_specify_prompt, _ = self.system_prompt_generator.generate(self.config["assistant_role"], self.config["user_role"], query)
        task_specifier = self.get_agent("task_specifier")
        task_specifier.update_profile(task_specify_sys_msg)
        self._log_step(sender="user", receiver="task_specifier", message=task_specify_prompt)
        specified_task = task_specifier.run_step(query=task_specify_prompt, option_num=self.config["option_num"])
        if self.config["option_num"] == 1:
            specified_task = specified_task[0]
        self._log_step(sender="task_specifier", receiver="user_proxy", message=specified_task)

        if self.config["with_critic"]:
            assistant_sys_msg, user_sys_msg, user_prompt, _, _, critic_sys_msg = self.system_prompt_generator.generate(self.config["assistant_role"], self.config["user_role"], specified_task, critic_role=self.config["critic_role"])
            self.get_agent("assistant").update_profile(assistant_sys_msg)
            self.get_agent("user_proxy").update_profile(user_sys_msg)
            self.get_agent("critic").update_profile(critic_sys_msg)
            
            assistant_response = self._dialog_loop_critic(user_prompt)
            
        else:
            assistant_sys_msg, user_sys_msg, user_prompt, _, _, _ = self.system_prompt_generator.generate(self.config["assistant_role"], self.config["user_role"], specified_task)
            self.get_agent("assistant").update_profile(assistant_sys_msg)
            self.get_agent("user_proxy").update_profile(user_sys_msg)

            assistant_response = self._dialog_loop(user_prompt)
        
        return {"response": assistant_response}, self._check_termination(assistant_response)

    def step(self, args):
        terminate = False
        assistant_response = args["response"]
        if self.config["with_critic"]:
            assistant_response_new = self._dialog_loop_critic(assistant_response)
            if self._check_termination(assistant_response_new):
                return args, True
        
        else:
            assistant_response_new = self._dialog_loop(assistant_response)
            if self._check_termination(assistant_response_new):
                return args, True
        
        return {"response": assistant_response_new}, False


    def conclude(self, args):
        return args



    def _dialog_loop_critic(self, assistant_response):
        
        user_proxy_completion = self.get_agent("user_proxy").run_step(query=assistant_response, option_num=self.config["option_num"])
        user_proxy_response = self.form_user_response(user_proxy_completion, self.config["option_num"])
        self._log_step(sender="user_proxy", receiver="critic", message=user_proxy_response)

        if self._check_termination(user_proxy_response):
            return self.is_termination_msg            
        critic_response = self.get_agent("critic").run_step(query=user_proxy_response)
        self._log_step(sender="critic", receiver="user_proxy", message=critic_response)
        selected_option = self.find_option(critic_response)

        if self.config["option_num"] == 1:
            selected_option = 1

        if selected_option is None or selected_option < 1 or selected_option > self.config["option_num"]:
            raise ValueError(f"Invalid critic selection: {selected_option}")
        
        selected_user_response = user_proxy_completion[selected_option-1]
        self._log_step(sender="user_proxy", receiver="assistant", message=selected_user_response)

        
        assistant_completion = self.get_agent("assistant").run_step(query=selected_user_response, option_num=self.config["option_num"])
        assistant_response = self.form_assistant_response(assistant_completion, self.config["option_num"])
                
        # Find the response from critic agent and get the selected option
    
        selected_assistant_response = assistant_completion[selected_option-1]
        self._log_step(sender="assistant", receiver="user_proxy", message=selected_assistant_response)

        return selected_assistant_response
    def _dialog_loop(self, assistant_response):
        
        user_proxy_response = self.get_agent("user_proxy").run_step(query=assistant_response)
        self._log_step(sender="user_proxy", receiver="assistant", message=user_proxy_response[0])
        if self._check_termination(user_proxy_response[0]):
            return self.is_termination_msg       

        assistant_response = self.get_agent("assistant").run_step(query=user_proxy_response[0])
        self._log_step(sender="assistant", receiver="user_proxy", message=assistant_response[0])

        return assistant_response[0]

    def form_user_response(self, completion, option_num):
        # Form the user response with the multiple choice options to a standard format
        response = f"""> Proposals from {self.config["user_role"]} (RoleType.USER). Please choose an option:\n"""

        for i in range(option_num):
            response += f"""Option {i+1}:\n{completion[i]}\n"""
        
        response += f"""Please first enter your choice ([1-{option_num}]) and then your explanation and comparison: """
        return response
    def form_assistant_response(self, completion, option_num):
        # Form the assistant response with the multiple choice options to a standard format
        response = f"""> Proposals from {self.config["assistant_role"]} (RoleType.ASSISTANT). Please choose an option:\n"""

        for i in range(option_num):
            response += f"""Option {i+1}:\n{completion[i]}\n"""
        response += f"""Please first enter your choice ([1-{option_num}]) and then your explanation and comparison: """
        return response
    
    def find_option(self, string):
        # Find the first integer number found in the given string. It means the choice of the critic agent
        match = re.search(r'\d+', string)
        if match:
            return int(match.group())
        else:
            return None
            


