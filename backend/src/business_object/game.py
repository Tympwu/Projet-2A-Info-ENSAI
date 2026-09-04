
class Game:

    def __init__(self, player1, player2, winner, game_mode, description):
        self.id = None
        self.player1 = player1
        self.player2 = player2
        self.winner = winner
        self.game_mode = game_mode
        self.description = description

    def __str__(self):
        return (
            f"{self.game_mode} between "
            f"{self.player1.username} and {self.player2.username}. "
            f"Winner: {self.winner.username if self.winner else 'Draw'}"
        )