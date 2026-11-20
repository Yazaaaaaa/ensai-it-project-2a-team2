from fastapi import APIRouter, Depends, HTTPException, status

from schema.user_model import UserLoginModel
from service.connection_history_service import ConnectionHistoryService
from service.user_service import UserService
from utils.log_utils import get_logger

router = APIRouter(prefix="/login", tags=["Login"])
logger = get_logger(__name__)


def get_user_service():
    """Dependency provider.

    Returns:
        UserService: Service instance used for user authentication.
    """
    return UserService()


def get_connection_service():
    """Dependency provider for connection history.

    Returns:
        ConnectionHistoryService: Service instance used to record connection events.
    """
    return ConnectionHistoryService()


@router.post("/", summary="Authenticate a user and record the connection", response_model=dict)
async def login(
    credentials: UserLoginModel,
    user_service: UserService = Depends(get_user_service),
    connection_service: ConnectionHistoryService = Depends(get_connection_service),
):
    """Authenticates a user with email and password and returns an access token.

    Args:
        credentials (UserLoginModel): User login payload containing email and password.
        user_service (UserService): Service handling credential verification and token generation.
        connection_service (ConnectionHistoryService): Service logging the connection event.

    Returns:
        dict: Dictionary containing the authenticated user ID and access token.

    Raises:
        HTTPException: 401 if the credentials are invalid or the user cannot log in.
    """
    logger.info("Login attempt")
    user = user_service.login(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Record login history without blocking authentication if history logging fails
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
        "access_token": user.token,
    }
