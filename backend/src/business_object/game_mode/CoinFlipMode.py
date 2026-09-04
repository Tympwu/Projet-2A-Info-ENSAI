import random

from backend.src.business_object.game import Game, Player
from backend.src.business_object.game_mode.game_mode import GameMode


class CoinFlipMode(GameMode):
    def play(self, p1: Player, p2: Player, choice: str) -> Game:
        # On récupère le choix (ex: "heads" ou "tails") via les kwargs
        # Si pas de choix fourni, on ne peut pas décider du gagnant proprement

        if not choice:
            raise ValueError("CoinFlipMode requires a 'choice' parameter ('heads' or 'tails')")

        # Simulation du lancer : 0 = heads, 1 = tails
        result = random.choice(["heads", "tails"])

        # On suppose ici que si p1 a choisi "heads" et que ça tombe sur "heads", il gagne.
        # C'est une logique simplifiée, à adapter selon ton ancien GameService.
        winner = None
        description = f"Result was {result}."

        # Logique arbitraire pour l'exemple :
        # On vérifie si le choix du joueur 1 correspond au résultat
        # (Il faudrait idéalement que chaque joueur ait un choix, mais restons simple)
        if choice == result:
            winner = p1
            description += f" {p1.name} guessed correctly!"
        else:
            # Si p1 perd, on regarde si p2 gagne (logique à ajuster selon tes règles)
            description += f" {p1.name} guessed wrong."

        return Game(
            player1=p1, player2=p2, game_mode="coinflip", winner=winner, description=description
        )
