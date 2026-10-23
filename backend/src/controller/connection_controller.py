from fastapi import APIRouter, Depends, HTTPException, status

from schema.user_model import ConnectionReadModel
from service.connection_history_service import ConnectionHistoryService
from utils.log_utils import get_logger

router = APIRouter(prefix="/connections", tags=["Connections"])
logger = get_logger(__name__)

@router.post(
    "/",
    response_model=ConnectionReadModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new connection",
    tags=["Connections"])
async def create_connection(
    id_user: int,
    connection_service: ConnectionHistoryService = Depends(get_connection_service)
) -> ConnectionReadModel:
    """
    Crée une nouvelle entrée dans l'historique des connexions.
    **À appeler depuis le controller de login après une authentification réussie.**
    """
    logger.info(f"Création d'une nouvelle connexion pour l'utilisateur {id_user}")
    connection = connection_service.create(id_user)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Échec de la création de la connexion."
        )
    return ConnectionReadModel.from_orm(connection)  # Supposons que ConnectionReadModel a un from_orm


def get_connection_service():
    """Dependency Injection provider for ConnectionHistoryService."""
    return ConnectionHistoryService()

@router.get("/{connections_by_user_id}", response_model=ConnectionReadModel, tags=["Users"])
async def connections_by_id(id_user: int, connection_service=Depends(get_connection_service)):
    """Find connections by a user unique ID.
    Args:
        id_user (int)
        connection_service (ConnectionHistoryService): The service used to interact connections data
    Returns:
        ConnectionReadModel: The user connections data if found
    Raises:
        HTTPException: 404 error if no connection is find
    """
    logger.info("Find connections by the user ID")
    connections = connection_service.find_by_id_user(id_user)
    if not connections:
        raise HTTPException(status_code=404, detail="No connection found for the user (id={id_player}).")
    return connections

@router.get("/{all_connections}", response_model=ConnectionReadModel, tags=["Users"])
async def all_connections(id_user: int, connection_service=Depends(get_connection_service)):
    """Find all connections.
    Args:
        id_user (int)
        connection_service (ConnectionHistoryService): The service used to interact connections data
    Returns:
        ConnectionReadModel: Connections data if found
    Raises:
        HTTPException: 404 error if no connection is find
        HTTPException: 403 error if the user is not an admin
    """
    logger.info("Find all connections")
    connections = connection_service.find_by_id_user(id_user)
    if not connections:
        raise HTTPException(status_code=404, detail="No connection found for the user (id={id_player}).")
    return connections