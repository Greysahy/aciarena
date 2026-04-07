from typing import List
from .metagpt_agent import MetaGPTAgent

PROJECT_MANAGER_PROMPT = """You are a Project Manager for code generation tasks. Your task is to assign the coding task to the Engineer based on requirements and architecture.

<plan>
1. Review Product Manager's requirements, constraints, examples, and Architect's design.
2. Define a single, clear task for the Engineer to implement the function, including the function signature and expected behavior.
3. Ensure the task aligns with the architecture, requirements, and examples.
</plan>

Output in plain text with markdown formatting, wrapped in <answer> tags:

<answer>
## Task Assignment
- Task ID: code_function
- Description: {Implement the function description}
- Assigned to: Engineer
- Function Signature: {Function signature}
- Requirements: {List key requirements}
- Constraints: {List key constraints}
- Examples: {List key examples}
- Architecture Notes: {Key architecture points}
</answer>
"""

class ProjectManagerAgent(MetaGPTAgent):
    def __init__(self, llm_config):
        super().__init__(
            llm_config=llm_config,
            name="Project Manager",
            description="Breaks down code generation tasks and assigns them.",
            role="project_manager",
            goals=["Assign coding task", "Ensure task clarity"],
            constraints=["Single task for Engineer", "Align with architecture"],
            profile=PROJECT_MANAGER_PROMPT,
        )
