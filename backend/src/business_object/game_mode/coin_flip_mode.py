import secrets

from business_object.game import Game
from business_object.game_mode.game_mode import GameMode


class CoinFlipMode(GameMode):

    def play(self, p1, p2, choice):
        result = secrets.choice(["heads", "tails"])

        winner = p1 if result == choice else p2

        description = (
            f"coinflip between {p1.username} and {p2.username}. "
            f"Winner: {winner.username}"
        )

        return Game(
            player1=p1,
            player2=p2,
            winner=winner,
            game_mode="coinflip",
            description=description
        )