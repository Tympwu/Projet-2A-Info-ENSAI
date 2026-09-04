import secrets
from datetime import time

from game import Game
from game_mode import GameMode


class DiceMode(GameMode):
    """
    Jeu permettant de lancer un dé, le joueur ayant le plus haut résultat gagne
    """

    def play(p1, p2) -> Game:
        """
        Fonction principale permettant de lancer la partie
        """
        p1_roll = secrets.choice(range(1, 7))
        p2_roll = secrets.choice(range(1, 7))
        if p1_roll > p2_roll:
            winner = p1
        elif p2_roll > p1_roll:
            winner = p2
        else:
            winner = None

        dice_game = Game(
            player1=p1,
            player2=p2,
            game_mode="dice",
            winner=winner,
            description="A tight game",
            timestamp=time,
        )
        return dice_game
