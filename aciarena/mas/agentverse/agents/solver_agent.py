from aciarena.agent_components import BaseAgent

SOLVER_PREPEND_PROMPT = """Solve the following problem: 
{query} 

This problem can be answered without any extra information. You should not ask for any extra information."""

SOLVER_APPEND_PROMPT = """You are {role_description}. Using the information in the chat history and your knowledge, you should provide the correct solution to the problem. Explain your reasoning."""


class SolverAgent(BaseAgent):
    def __init__(self, llm_config, name = "", profile = None):
        super().__init__(llm_config, name, profile)
        self.profile = SOLVER_APPEND_PROMPT
        self.system_prompt = self.profile

    def set_profile(self, args):
        try:
            self.system_prompt = self.profile.format(**args)
        except Exception as e:
            self.system_prompt = self.profile

    def step(self, query, *args, **kwargs) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
        ] + kwargs.get("history", []) + [
            {"role": "user", "content": SOLVER_PREPEND_PROMPT.format(query=query)},
        ]

        response = self.llm.call_llm(messages=messages)
        return response