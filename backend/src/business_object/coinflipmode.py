# fichier : business_object/game_mode/coinflipmode.py

import secrets
from datetime import datetime
from business_object.game import Game
from business_object.game_mode import GameMode


class CoinFlipMode(GameMode):
    """
    Mode de jeu : pile ou face. Le joueur qui devine juste gagne.
    """

    def play(self, p1, p2, choice="heads", **kwargs) -> Game:
        result = secrets.choice(["heads", "tails"])
        winner = p1 if result == choice else p2

        game = Game(
            player1=p1,
            player2=p2,
            game_mode="coinflip",
            winner=winner
        )

        return game