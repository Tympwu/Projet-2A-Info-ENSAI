import os
from datetime import datetime

from business_object.player import Player


class Game:
    """
    Classe générale permettant de créer un jeu
    """

    def __init__(
        self,
        player1: Player,
        player2: Player,
        game_mode: str,
        winner: Player,
        description: str,
        timestamp: datetime,
    ):
        self.id_game = None
        self.p1 = player1
        self.p2 = player2
        assert game_mode in os.environ["GAME_SUPPORTED"], "Le jeu n'est pas reconnu"
        self.game_mode: str = game_mode
        self.winner: Player | None = winner
        self.description = description
        self.timestamp = timestamp

    def __str__(self):
        return f"{self.game_mode} between {self.p1.username} and {self.p2.username}.Winner : {self.winner}"
