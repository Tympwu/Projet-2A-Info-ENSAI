from abc import ABC, abstractmethod

from business_object.game import Game


class GameMode(ABC):
    """
    Classe abstraite contenant la structure générique d'un mode de jeu
    """

    @abstractmethod
    def play(self, p1, p2, **kwargs) -> Game:
        """
        Méthode abstraite permettant de lancer une partie du jeu
        """
        pass
