from fastapi import APIRouter, Depends, HTTPException, Response, status

from business_object.user import User
from controller.dependencies import get_current_user, get_token, get_user_service
from schema.user_model import UserCreateModel, UserResponseModel
from service.user_service import EmailAlreadyUsedError, UserService
from utils.log_utils import get_logger

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger(__name__)


def _to_response(user: User) -> UserResponseModel:
    return UserResponseModel(
        id_user=user.id_user,
        email=user.email,
        role_user=user.role_user,
        created_at=user.created_at,
    )


@router.post(
    "/",
    summary="Create an account",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponseModel,
)
def register(
    data: UserCreateModel,
    user_service: UserService = Depends(get_user_service),
):
    """Creates an account.

    Raises:
        HTTPException: 409 if the email is already used, 422 if the data is invalid.
    """
    try:
        user = user_service.create_account(data.email, data.password)
    except EmailAlreadyUsedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already used")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except RuntimeError:
        logger.exception("Account creation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account creation failed",
        )

    logger.info(f"Account created for user {user.id_user}")
    return _to_response(user)


@router.post("/logout", summary="Log out the current user", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token: str = Depends(get_token),
    user_service: UserService = Depends(get_user_service),
):
    """Closes the session associated with the token.

    Raises:
        HTTPException: 401 if the token is unknown or already closed.
    """
    if not user_service.logout(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", summary="Get the current user", response_model=UserResponseModel)
def read_me(current_user: User = Depends(get_current_user)):
    return _to_response(current_user)