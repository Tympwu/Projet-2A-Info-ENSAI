from abc import ABC, abstractmethod

from backend.src.business_object.game import Game, Player


class GameMode(ABC):
    @abstractmethod
    def play(self, p1: Player, p2: Player, **kwargs) -> Game:
        """
        Executes the game logic between two players.
        **kwargs allows passing specific parameters like 'choice' for coinflip.
        """
        pass
