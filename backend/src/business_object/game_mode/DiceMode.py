import random

from backend.src.business_object.game import Game, Player
from backend.src.business_object.game_mode.game_mode import GameMode


class DiceMode(GameMode):
    def play(self, p1: Player, p2: Player) -> Game:
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)

        winner = None
        description = f"{p1.name} rolled {roll1}, {p2.name} rolled {roll2}."

        if roll1 > roll2:
            winner = p1
            description += f" {p1.name} wins!"
        elif roll2 > roll1:
            winner = p2
            description += f" {p2.name} wins!"
        else:
            description += " It's a draw!"

        return Game(
            player1=p1, player2=p2, game_mode="dice", winner=winner, description=description
        )
