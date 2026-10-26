from fastapi import APIRouter, Depends, HTTPException, status
from schema.user_model_model import UserLoginModel
from service.user_service import UserService

from utils.log_utils import get_logger

router = APIRouter(prefix="/login", tags=["Login"])
logger = get_logger(__name__)


def get_user_service():
    """Dependency provider."""
    return UserService()


@router.post(
    "/",
    summary="",
    response_model=dict
)
def login(credentials: UserLoginModel, service: UserService = Depends(get_user_service)):
    """Authenticates a user.
    Args:
        credentials: id and password.
        service: User service
    Returns:
        dict: containing id_user and access_token
    Raises:
        HTTPException: 401 error if the credentials are invalid or the user does not exist."""
    logger.info("Login")
    user = service.login(credentials.id, credentials.password)
    if user:
        return {
            "id_user": user.id_user,
            "access_token": user.access_token,
        }
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
