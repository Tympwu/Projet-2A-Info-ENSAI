# fichier : business_object/game_mode/game_mode.py

from abc import ABC, abstractmethod
from business_object.game import Game


class GameMode(ABC):
    """
    Contrat abstrait que tout mode de jeu doit respecter.
    Cette classe ne sera jamais instanciée directement.
    """

    @abstractmethod
    def play(self, p1, p2, **kwargs) -> Game:
        """
        Joue une partie entre p1 et p2 et retourne un objet Game.

        Args:
            p1 (Player): premier joueur
            p2 (Player): second joueur
            **kwargs: arguments additionnels propres à certains modes
                      (ex: choice="heads" pour CoinFlipMode)

        Returns:
            Game: l'objet représentant la partie jouée
        """
        pass