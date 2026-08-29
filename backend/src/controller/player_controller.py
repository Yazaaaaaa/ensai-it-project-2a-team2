# controller/player_controller.py


from fastapi import APIRouter, Depends, HTTPException

from schema.player_model import PlayerModel, PlayerReadModel
from service.player_service import PlayerService
from utils.log_utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def get_player_service():
    """Dependency Injection provider for PlayerService."""
    return PlayerService()


@router.get("/", response_model=list[PlayerReadModel], tags=["Players"])
async def find_all_players(player_service=Depends(get_player_service)):
    """List all players.
    Returns:
        list[PlayerReadModel]: A list of all registered players.
    """
    logger.info("List all players")
    players_list = player_service.find_all()
    return players_list


@router.get("/{id_player}", response_model=PlayerReadModel, tags=["Players"])
async def player_by_id(id_player: int, player_service=Depends(get_player_service)):
    """Find a player by their unique ID.
    Args:
        id_player (int)
        player_service (PlayerService): The service used to interact with player data
    Returns:
        PlayerReadModel: The player data if found
    Raises:
        HTTPException: 404 error if the player is not found
    """
    logger.info("Find a player by id")
    player = player_service.find_by_id(id_player)
    if not player:
        raise HTTPException(status_code=404, detail="Player (id={id_player}) not found.")
    return player


@router.post("/", response_model=PlayerReadModel, tags=["Players"])
async def create_player(p: PlayerModel, player_service=Depends(get_player_service)):
    """Create a new player.
    Args:
        p (PlayerModel): The player data to create.
        player_service (PlayerService): The service used to interact with player data.
    Returns:
        PlayerReadModel: The newly created player data.
    Raises:
        HTTPException: 400 error if the username is already taken.
        HTTPException: 500 error if the creation process fails.
    """
    logger.info("Create a player")
    if player_service.username_already_used(p.username):
        raise HTTPException(status_code=400, detail="Username already used.")

    player = player_service.create(p.username, p.password, p.elo, p.email, p.pokemon_fan)
    if not player:
        raise HTTPException(status_code=500, detail="Error while creating player.")

    return player


@router.put("/{id_player}", response_model=PlayerReadModel, tags=["Players"])
async def update_player(id_player: int, p: PlayerModel, player_service=Depends(get_player_service)):
    """Update an existing player's information.
    Args:
        id_player (int)
        p (PlayerModel): The new data for the player.
        player_service (PlayerService): The service used to interact with player data.
    Returns:
        str: A confirmation message indicating the player was updated.
    Raises:
        HTTPException: 404 error if the player is not found.
        HTTPException: 500 error if the update process fails.
    """
    logger.info("Update a player")
    player = player_service.find_by_id(id_player)
    if not player:
        raise HTTPException(status_code=404, detail="Player (id={id_player}) not found.")

    player.username = p.username
    player.password = p.password
    player.elo = p.elo
    player.email = p.email
    player.pokemon_fan = p.pokemon_fan

    player = player_service.update(player)
    if not player:
        raise HTTPException(status_code=500, detail="Error while updating player.")

    return player


@router.delete("/{id_player}", tags=["Players"])
async def delete_player(id_player: int, player_service=Depends(get_player_service)):
    """Delete a player from the system.
    Args:
        id_player (int)
        player_service (PlayerService): The service used to interact with player data.
    Returns:
        str: A confirmation message indicating the player was deleted.
    Raises:
        HTTPException: 404 error if the player is not found.
    """
    logger.info("Delete a player")
    player = player_service.find_by_id(id_player)
    if not player:
        raise HTTPException(status_code=404, detail="Player (id={id_player}) not found.")

    player_service.delete(player)
    return f"Player {player.username} deleted"