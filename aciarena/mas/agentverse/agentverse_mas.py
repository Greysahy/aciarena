from aciarena.mas import BaseMAS
from aciarena.mas.agentverse.agents import *
from aciarena.utils.factory import register_mas
from typing import List

@register_mas("agentverse")
class AgentVerse(BaseMAS):
    def __init__(self, llm_config, malicious_agents=["solver"], logger=None, max_turn=3, max_criticizing_rounds=3, max_history_solver=5, max_history_critic=3, cnt_agents=2):
        self.cnt_agents = cnt_agents
        self.max_criticizing_rounds=max_criticizing_rounds
        self.malicious_agents = malicious_agents
        self.advice = "No advice yet."
        self.previous_plan = "No solution yet."
        self.max_history_solver = max_history_solver
        self.max_history_critic = max_history_critic
        self.history = []
        super().__init__(llm_config, malicious_agents, logger, max_turn)
    
    def init_agents(self):
        agents = {
            "role_assigner": RoleAssignerAgent(llm_config=self.llm_config, cnt_agents=self.cnt_agents),
            "solver": SolverAgent(llm_config=self.llm_config),
            "evaluator": EvaluatorAgent(llm_config=self.llm_config)
        }
        for i in range(self.cnt_agents - 1):
            agents[f"critic_{i}"] = CriticAgent(llm_config=self.llm_config)

        return agents

    def group_vertical_solver_first(self, query, role_descriptions):
        nonempty_reviews = []
        history_solver = []
        history_critic = []

        if not self.advice == "No advice yet.":
            self.history.append(
                {
                    "role": "assistant",
                    "content": f"[Evaluator]: {self.advice}",
                }
            )
            if len(self.history) > self.max_history_solver:
                history_solver = self.history[-self.max_history_solver:]
            else:
                history_solver = self.history

        solver = self.get_agent("solver")
        solver.set_profile(args={"role_description": role_descriptions[0]})
        solver_response = solver.run_step(query=query, history=history_solver)
        self.history.append(
            {
                "role": "assistant",
                "content": f"[{role_descriptions[0]}]: {solver_response}",
            }
        )
        if len(self.history) > self.max_history_critic:
            history_critic = self.history[-self.max_history_critic:]
        else:
            history_critic = self.history
        previous_plan = solver_response  # Set the solution as previous_plan
        
        for _ in range(self.max_criticizing_rounds):
            
            reviews = []
            for j in range(self.cnt_agents - 1):
                critic = self.get_agent(f"critic_{j}")
                critic.set_profile(args={"query": query, "role_description": role_descriptions[j+1]})
                critic_response = critic.run_step(query=query, history=history_critic)
                if "[Agree]" not in critic_response:
                    self.history.append(
                        {
                            "role": "assistant",
                            "content": f"[{role_descriptions[j+1]}]: {critic_response}",
                        }
                    )
                    if len(self.history) > self.max_history_solver:
                        history_solver = self.history[-self.max_history_solver:]
                    else:
                        history_solver = self.history
                reviews.append(critic_response)
            for review in reviews:
                if "[Agree]" not in review:
                    nonempty_reviews.append(review)
            if len(nonempty_reviews) == 0:
                break

            solver_response = self.get_agent("solver").run_step(query=query, history=history_solver)
            self.history.append(
                {
                    "role": "assistant",
                    "content": f"[{role_descriptions[0]}]: {solver_response}",
                }
            )
            if len(self.history) > self.max_history_critic:
                history_critic = self.history[-self.max_history_critic:]
            else:
                history_critic = self.history
            previous_plan = solver_response
        results = previous_plan
        return results

    def bootstrap(self, query):
        return {"query": query}, False

    def step(self, args):
        terminate = False
        role_assigner = self.get_agent("role_assigner")
        role_assigner.set_profile(args={"query": args["query"], "advice": self.advice})
        role_assigner_response = role_assigner.run_step(query=args["query"])
        role_descriptions = role_assigner.extract_role_descriptions(role_assigner_response)

        solution = self.group_vertical_solver_first(query=args["query"], role_descriptions=role_descriptions)

        evaluator_response = self.get_agent("evaluator").run_step(query=args["query"], role_descriptions=role_descriptions, solution=solution)
        result = self.get_agent("evaluator").parse_evaluator(evaluator_response)

        if isinstance(result, tuple):
            if len(result) == 2:
                score, feedback = result
            elif len(result) == 1:
                score, feedback = 0, result[0]
            else:
                raise ValueError(f"Unexpected number of return values from evaluator: {len(result)}")
        else:
            score, feedback = 0, result

        if score == 1:
            terminate = True
        else:
            self.advice = feedback

        args["response"] = solution
        return args, terminate
    
    def conclude(self, args):
        return args