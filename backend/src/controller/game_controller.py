from fastapi import APIRouter, Depends, HTTPException

from schema.game_model import GamePlayModel, GameResponse
from service.game_service import GameService
from service.player_service import PlayerService
from utils.log_utils import get_logger
from utils.security import verify_token

router = APIRouter()

logger = get_logger(__name__)


def get_game_service():
    """Dependency provider for GameService."""
    return GameService()


@router.post("/", response_model=GameResponse, tags=["Games"])
def play_game(
    req: GamePlayModel, game_service=Depends(get_game_service), current_player=Depends(verify_token)
):
    """Starts and executes a new game session.
    Args:
        req (GamePlayModel): Request containing player IDs and game mode.
        game_service (GameService): Service handling game logic.
        current_player (Player): The authenticated user.
    Returns:
        dict: Match summary including player usernames, result, winner,
            and updated ELO ratings.
    Raises:
        HTTPException: 401 if unauthenticated, 400 if invalid request.
    """
    logger.info("Play a game")
    game = game_service.play(current_player.id_player, req.id_opponent, req.game_mode, **req.params)

    return GameResponse(
        username1=game.player1.username,
        username2=game.player2.username,
        description=game.description,
        winner=game.winner.username if game.winner else None,
        new_elo1=game.player1.elo,
        new_elo2=game.player2.elo,
    )


@router.get("/", response_model=list[GameResponse], tags=["Games"])
def get_games(id_player, game_service=Depends(get_game_service), game_mode: str | None = None):
    if not PlayerService().find_by_id(id_player):
        raise HTTPException(status_code=404, detail="Player not found")

    games = game_service.find_all_by_player(id_player, game_mode)
    result = []
    for element in games:
        result.append(
            GameResponse(
                username1=element.player1.username,
                username2=element.player2.username,
                description=element.description,
                winner=element.winner.username if element.winner else None,
                new_elo1=element.player1.elo,
                new_elo2=element.player2.elo,
            )
        )
    return result
