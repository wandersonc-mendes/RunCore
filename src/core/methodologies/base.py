from abc import ABC
from abc import abstractmethod


class TrainingMethodology(ABC):

    @abstractmethod
    def easy(self, vdot):
        pass

    @abstractmethod
    def marathon(self, vdot):
        pass

    @abstractmethod
    def threshold(self, vdot):
        pass

    @abstractmethod
    def interval(self, vdot):
        pass

    @abstractmethod
    def repetition(self, vdot):
        pass