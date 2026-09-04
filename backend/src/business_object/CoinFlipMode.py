import secrets
from datetime import time

from business_object.game import Game
from business_object.game_mode import GameMode


class CoinFlipMode(GameMode):
    """
    A game about flipping a coin
    """

    def play(p1, p2, choice) -> Game:
        """
        Méthode permettant de lancer le jeu de lancer de pièces
        """
        result = secrets.choice(["heads", "tails"])
        winner = p1 if result == choice else p2
        game_coin = Game(
            player1=p1,
            player2=p2,
            game_mode="coinflip",
            winner=winner,
            description="A truly exciting game",
            timestamp=time,
        )
        return game_coin
