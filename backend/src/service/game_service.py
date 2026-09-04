from fastapi import HTTPException

from business_object.game_mod_factory import GameModFactory
from business_object.score_strategy import ScoringStrategy
from dao.player_dao import PlayerDao
from utils.log_utils import log


class GameService:
    """Service that manages games."""

    @log
    def play(self, id_player: int, id_opponent: int, game_mode: str, **kwargs):
        """Executes a single round of a coin-flip game between two players.
        Args:
            id_player (int): The unique identifier of the first player.
            id_opponent (int): The unique identifier of the opponent.
            choice (str, optional): The player's choice ('heads' or 'tails'). Defaults to "heads".
        Returns:
            dict: A dictionary containing the match details and new elo
        Raises:
            HTTPException: 400 if the two players are the same.
            HTTPException: 404 if one or both players are not found in the database.
        """
        # Recherche des joueurs concernés et prise en compte des erreurs
        if id_player == id_opponent:
            raise HTTPException(status_code=400, detail="Two different players required")

        p1 = PlayerDao().find_by_id(id_player)
        p2 = PlayerDao().find_by_id(id_opponent)

        if not p1 or not p2:
            raise HTTPException(status_code=404, detail="Player not found")

        # Création du jeu et lancement de ce dernier
        game = GameModFactory().get_mode(game_mode)
        result_game = game.play(p1, p2, **kwargs)

        # Mise à jour de l'élo de chaque joueur
        ScoringStrategy().update_player_ratings(result_game)

        PlayerDao().update(p1)
        PlayerDao().update(p2)

        return result_game
