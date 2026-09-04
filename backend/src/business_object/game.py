from datetime import datetime


class Player:
    def __init__(self, id_player: int, name: str):
        self.id_player = id_player
        self.name = name

    def __str__(self) -> str:
        return self.name


class Game:
    def __init__(
        self,
        player1: Player,
        player2: Player,
        game_mode: str,
        winner: Player | None,
        description: str,
        timestamp: datetime | None = None,
    ):
        self.id = None  # Will be set once persisted in the database
        self.player1 = player1
        self.player2 = player2
        self.game_mode = game_mode  # "coinflip" or "dice"
        self.winner = winner  # Player instance, or None if it's a draw
        self.description = description
        self.timestamp = timestamp or datetime.now()

    def __str__(self) -> str:
        winner_name = self.winner.name if self.winner else "Draw"
        return (
            f"Game #{self.id} [{self.game_mode}] - "
            f"{self.player1.name} vs {self.player2.name} - "
            f"Winner: {winner_name} - "
            f"{self.timestamp:%Y-%m-%d %H:%M}"
        )


p1 = Player(1, "Rémi")
p2 = Player(2, "Baptiste")
game = Game(p1, p2, "coinflip", p1, "Rémi won by heads")
print(game)
