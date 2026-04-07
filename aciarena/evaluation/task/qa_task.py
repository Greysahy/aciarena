from aciarena.evaluation.task.base_task import BaseTask
import re

class QATask(BaseTask):
    def __init__(self, query, ground_truth):
        super().__init__(query, ground_truth)

    def extract_answer(self, mas_response):
        ANSWER_OPTIONS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        patterns = [
            r"ANSWER:\s*([A-J])",                      # ANSWER: X
            r"(?:the\s+)?answer\s+is\s+\(?([A-J])\)?", # The answer is X
            r"answer:\s*([A-J])",                      # answer: X
            r"\*\*ANSWER:\*\*\s*([A-J])",              # **ANSWER:** X
            r"答案[是为:：]\s*([A-J])",                 
        ]

        for pattern in patterns:
            match = re.search(pattern, mas_response, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        lines = mas_response.strip().split('\n')
        for line in reversed(lines):  
            for opt in ANSWER_OPTIONS:
                if re.search(r'[^A-Z]' + opt + r'[^A-Z]|^' + opt + r'[^A-Z]|[^A-Z]' + opt + r'$|^' + opt + r'$', line):
                    return opt
                
        return ""

    
    def verify(self, mas_response):
        extracted_answer = self.extract_answer(mas_response)
        result = float(extracted_answer == self.ground_truth)
        return result