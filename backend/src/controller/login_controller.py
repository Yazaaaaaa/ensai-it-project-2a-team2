from fastapi import APIRouter, Depends, HTTPException

from schema.player_model import PlayerLoginModel
from service.player_service import PlayerService
from utils.log_utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def get_player_service():
    """Dependency provider."""
    return PlayerService()


@router.post("/", tags=["Login"])
def login(credentials: PlayerLoginModel, service=Depends(get_player_service)):
    """Authenticates a user.
    Args:
        credentials: username and password.
    Returns:
        dict: containing id_player and username
    Raises:
        HTTPException: 401 error if the credentials are invalid or the user does not exist."""
    logger.info("Login")
    player = service.login(credentials.username, credentials.password)
    if player:
        return {
            "id_player": player.id_player,
            "username": player.username,
            "access_token": player.access_token,
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")