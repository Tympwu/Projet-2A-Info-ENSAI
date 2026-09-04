# fichier : business_object/game_mode/dice_mode.py

import secrets
from business_object.game import Game
from business_object.game_mode import GameMode


class DiceMode(GameMode):
    """
    Mode de jeu : chaque joueur lance un dé, le plus haut score gagne.
    """

    def play(self, p1, p2, **kwargs) -> Game:
        d1 = secrets.choice(range(1, 7))
        d2 = secrets.choice(range(1, 7))
        if d1 > d2:
            winner = p1
        elif d2 > d1:
            winner = p2
        game = Game(
            player1=p1,
            player2=p2,
            game_mode="dice",
            winner=winner
        )

        return game


