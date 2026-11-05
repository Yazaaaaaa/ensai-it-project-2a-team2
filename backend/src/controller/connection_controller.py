from fastapi import APIRouter, Depends, HTTPException, status

from business_object.user import User
from controller.dependencies import get_current_user
from schema.connection_model import ConnectionReadModel
from service.connection_history_service import ConnectionHistoryService
from utils.log_utils import get_logger

router = APIRouter(prefix="/connections", tags=["Connections"])
logger = get_logger(__name__)


def get_connection_service():
    """Dependency Injection provider for ConnectionHistoryService."""
    return ConnectionHistoryService()


@router.post(
    "/",
    response_model=ConnectionReadModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new connection",
    tags=["Connections"])
async def create_connection(id_user: int, connection_service: ConnectionHistoryService = Depends(get_connection_service)) -> ConnectionReadModel:
    """Create a new line in the login history table"""
    logger.info(f"Creation of a new connexion for the user {id_user}")
    connection = connection_service.create(id_user)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failure in the creation of a new connection."
        )
    return ConnectionReadModel.from_orm(connection)


@router.get(
    "/users/{id_user}",
    response_model=list[ConnectionReadModel],
    summary="Get the connexions of a user",
    tags=["Connections"])
async def connections_by_id(id_user: int, connection_service: ConnectionHistoryService = Depends(get_connection_service)) -> list[ConnectionReadModel]:
    """Find connections by a user unique ID.
    Args:
        id_user (int)
        connection_service (ConnectionHistoryService): The service used to interact connections data
    Returns:
        list[ConnectionReadModel]: The user connections data if found
    Raises:
        HTTPException: 404 error if no connection is find
    """
    logger.info("Find connections by the user ID")
    connections = connection_service.find_by_id_user(id_user)
    if not connections:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No connection found for the user (id={id_player}).")
    return [ConnectionReadModel.from_orm(conn) for conn in connections]


@router.get(
    "/",
    response_model=list[ConnectionReadModel],
    summary="Get all connections",
    tags=["Connections"])
async def all_connections(current_user: User = Depends(get_current_user), connection_service: ConnectionHistoryService = Depends(get_connection_service)) -> list[ConnectionReadModel]:
    """Find all connections if the user is an administrator.
    Args:
        current_user: the user asking for the connections
        connection_service (ConnectionHistoryService): The service used to interact connections data
    Returns:
        List[ConnectionReadModel]: Connections data if found
    Raises:
        HTTPException: 404 error if no connection is find
    """
    logger.info("Find all connections")
    connections = connection_service.find_all()
    if not connections:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No connection found for the user (id={id_user}).")
    if current_user.role_user != "admin":
        connections = [conn for conn in connections if conn.id_user == current_user.id_user]
    return [ConnectionReadModel.model_validate(conn, from_attributes=True) for conn in connections]
