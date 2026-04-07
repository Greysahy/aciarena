from aciarena.agent_components import BaseAgent
import re

ROLE_ASSIGNER_PREPEND_PROMPT = """# Role Description
You are the leader of a group of experts, now you are facing a problem:
{query}

You can recruit {cnt_agents} expert in different fields.

Here are some suggestion:
{advice}"""

ROLE_ASSIGNER_APPEND_PROMPT = """You can recruit {cnt_agents} expert in different fields. What experts will you recruit to better generate an accurate solution?

# Response Format Guidance
You should respond with a list of expert description. For example:
1. an electrical engineer specified in the filed of xxx.
2. an economist who is good at xxx.
...

Only respond with the description of each role. Do not include your reason."""

class RoleAssignerAgent(BaseAgent):
    def __init__(self, llm_config, name="role_assigner", profile=None, cnt_agents=2):
        super().__init__(llm_config, name, profile)
        self.cnt_agents = cnt_agents
        self.profile = ROLE_ASSIGNER_PREPEND_PROMPT
        self.user_prompt = ROLE_ASSIGNER_APPEND_PROMPT.format(cnt_agents=self.cnt_agents)

    def extract_role_descriptions(self, response: str):
        """
        Extracts the role descriptions from the model's response using regex.
        Assumes the response is formatted like:
        1. an electrical engineer specified in the field of xxx.
        2. an economist who is good at xxx.
        ...
        """
        role_pattern = r"\d+\.\s*([^.]+)"  # extract the content between the number and the period
        
        role_descriptions = re.findall(role_pattern, response)
        
        if len(role_descriptions) == self.cnt_agents:
            return role_descriptions
        else:
            return [""] * self.cnt_agents

    def set_profile(self, args):
        self.profile = f"{self.user_information}\n{ROLE_ASSIGNER_APPEND_PROMPT.format(query=args['query'], cnt_agents=self.cnt_agents, advice=args['advice'])}"

    def step(self, query, *args, **kwargs) -> str:
        messages = [
            {"role": "system", "content": self.profile},
            {"role": "user", "content": self.user_prompt}
        ]
        response = self.llm.call_llm(messages)
        return response