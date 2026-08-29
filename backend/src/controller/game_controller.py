from fastapi import APIRouter, Depends

from schema.game_model import GamePlayModel, GameResponse
from service.game_service import GameService
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
    res = game_service.play(current_player.id_player, req.id_opponent, **req.params)

    return GameResponse(
        username1=res["player1"],
        username2=res["player2"],
        description=res["description"],
        winner=res["winner"],
        new_elo1=res["new_elo1"],
        new_elo2=res["new_elo2"],
    )