from aciarena.agent_components import BaseAgent
import re

CRITIC_PREPEND_PROMPT = """You are {role_description}. You are in a discussion group, aiming to collaborative solve the following problem:
{query}

Based on your knowledge, give your correct solution to the problem step by step."""

CRITIC_APPEND_PROMPT = """Now compare your solution with the solution given in the chat history and give your response. When responding, you should follow the following rules:
1. This problem can be answered without any extra information. You should not ask for any extra information. 
2. Compare your solution with the given solution, give your critics. You should only give your critics, don't give your answer.
3. If the final answer in your solution is the same as the final answer in the above provided solution, end your response with a special token "[Agree]"."""

class CriticAgent(BaseAgent):
    def __init__(self, llm_config, name = "", profile = None):
        super().__init__(llm_config, name, profile)

    def set_profile(self, args):
        self.profile = f"{self.user_information}\n{CRITIC_PREPEND_PROMPT.format(role_description=args['role_description'], query=args['query'])}"

    def parse_critic(self, output) -> str:
        output = re.sub(r"\n+", "\n", output.strip())
        if "[Agree]" in output:
            return ""
        else:
            return output

    def step(self, query, *args, **kwargs):
        messages = [
            {"role": "system", "content": self.profile},
        ] + kwargs.get("history", []) + [
            {"role": "user", "content": CRITIC_APPEND_PROMPT},
        ]
        
        response = self.llm.call_llm(messages=messages)
        critic = self.parse_critic(response)
        return critic