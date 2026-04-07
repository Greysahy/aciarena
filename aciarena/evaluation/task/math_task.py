from aciarena.evaluation.task.base_task import BaseTask
from math_verify import parse, verify, LatexExtractionConfig, ExprExtractionConfig

class MathTask(BaseTask):
    def __init__(self, query, ground_truth):
        super().__init__(query, ground_truth)

    def extract_answer(self, correct_answer, mas_response):
        extraction_target = (ExprExtractionConfig(), LatexExtractionConfig())
        gold = parse(f"${correct_answer}$", extraction_config=extraction_target)
        answer = parse(mas_response, extraction_config=extraction_target)

        return gold, answer

    def verify(self):
        mas_response = self.answer["response"]
        gold, answer = self.extract_answer(self.ground_truth, mas_response)
        result = float(verify(gold, answer))
        return result