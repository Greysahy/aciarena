from abc import ABC, abstractmethod
from aciarena.utils import build_mas, MASLogger
from datetime import datetime

class BaseTask(ABC):
    def __init__(self, query, ground_truth):
        self.query = query
        self.ground_truth = ground_truth
        self.answer = None

    def get_query(self):
        return self.query
    
    def get_gt(self):
        return self.ground_truth
    
    def set_answer(self, answer):
        self.answer = answer

    def verify(self, args):
        """
        Abstract method for verifying the correctness of agents' output or task execution.
        Subclasses should implement this to define their own verification logic.
        """
        raise NotImplementedError("Subclasses must implement the verify() method.")