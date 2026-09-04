import secrets

from business_object.game import Game
from business_object.game_mode.game_mode import GameMode


class DiceMode(GameMode):

    def play(self, p1, p2):
        d1 = secrets.choice(range(1, 7))
        d2 = secrets.choice(range(1, 7))

        if d1 > d2:
            winner = p1
        elif d2 > d1:
            winner = p2
        else:
            winner = None

        winner_name = winner.username if winner else "Draw"

        description = (
            f"dice between {p1.username} and {p2.username}. "
            f"Winner: {winner_name}"
        )

        return Game(
            player1=p1,
            player2=p2,
            winner=winner,
            game_mode="dice",
            description=description
        )