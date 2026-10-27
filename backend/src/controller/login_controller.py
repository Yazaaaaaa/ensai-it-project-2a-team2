from fastapi import APIRouter, Depends, HTTPException, status
from schema.user_model_model import UserLoginModel
from service.user_service import UserService

from service.connection_history_service import ConnectionHistoryService
from utils.log_utils import get_logger

router = APIRouter(prefix="/login", tags=["Login"])
logger = get_logger(__name__)


def get_user_service():
    """Dependency provider."""
    return UserService()


def get_connection_service():
    """Dependency provider for connection history."""
    return ConnectionHistoryService()


@router.post(
    "/",
    summary="Authenticate a user and record the connection",
    response_model=dict
)
async def login(
    credentials: UserLoginModel,
    user_service: UserService = Depends(get_user_service),
    connection_service: ConnectionHistoryService = Depends(get_connection_service)
):
    """Authenticates a user.
    Args:
        credentials: id and password.
        service: User service
    Returns:
        dict: containing id_user and access_token
    Raises:
        HTTPException: 401 error if the credentials are invalid or the user does not exist."""
    logger.info(f"Login attempt for user: {credentials.id_user}")
    user = user_service.login(credentials.id_user, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            details="Invalid credentials"
        )
        try:
            connection = connection_service.create(user.id_user)
            if not connection:
                logger.warning(f"Failed to create connection history for user {user.id_user}")
            else:
                logger.info(f"Connection history created for user {user.id_user}")
        except Exception as e:
            logger.error(f"Error creating connection history: {e}")
        return {
            "id_user": user.id_user,
            "access_token": user.access_token,
        }
