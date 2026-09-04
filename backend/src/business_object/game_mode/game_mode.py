from abc import ABC, abstractmethod


class GameMode(ABC):

    @abstractmethod
    def play(self, p1, p2):
        pass 