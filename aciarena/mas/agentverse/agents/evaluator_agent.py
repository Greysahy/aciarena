from aciarena.agent_components import BaseAgent
from typing import List, Tuple
import re

EVALUATOR_PREPEND_PROMPT = """Experts: {all_role_description}
Problem: {query}
Solution: 
```
{solution}
```"""

EVALUATOR_APPEND_PROMPT = """You are an experienced Problem Solver. As a good assistant, you carefully check the correctness of the given solution on a problem. When the solution is wrong, you should output a correctness of 0 and give your advice on how to correct the solution. When it is correct, output a correctness of 1 and why it is correct. You should also give some suggestion on on what experts should recruit in the next round.

You should respond in the following format:
Correctness: (0 or 1, 0 is wrong, and 1 is correct)
Response: (advice to correct the answer or why it is correct)"""

class EvaluatorAgent(BaseAgent):
    def __init__(self, llm_config, name = "", profile = None):
        super().__init__(llm_config, name, profile)
        self.profile = EVALUATOR_APPEND_PROMPT

    def parse_evaluator(self, output) -> Tuple[int, str]:
        correctness_match = re.search(r"Correctness:\s*(\d)", output)
        if correctness_match:
            correctness = int(correctness_match.group(1))
        else:
            correctness = 0

        advice_match = re.search(r"Response:\s*(.+)", output, re.DOTALL)  
        if advice_match:
            advice = advice_match.group(1).strip()  
            clean_advice = re.sub(r"\n+", "\n", advice.strip())
        else:
            clean_advice = output
 
        return correctness, clean_advice

    def step(self, query, *args, **kwargs):
        role_descriptions = kwargs.get("role_descriptions", [])
        solution = kwargs.get("solution", "")
        messages = [
            {"role": "system", "content": self.profile},
            {"role": "user", "content": EVALUATOR_PREPEND_PROMPT.format(query=query, all_role_description=role_descriptions, solution=solution)}
        ]
        response = self.llm.call_llm(messages)
        return response