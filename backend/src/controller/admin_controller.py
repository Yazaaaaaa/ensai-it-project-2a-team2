from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status

from typing import Optional

from business_object.user import User
from controller.dependencies import get_admin_service, require_admin
from service.admin_service import AdminService
from utils.log_utils import get_logger

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger(__name__)


@router.post(
    "/users/{id_user}/ban",
    summary="Ban a user",
    status_code=status.HTTP_204_NO_CONTENT,
)
def ban_user(
    id_user: int,
    admin: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Bans a user and closes his session.

    Raises:
        HTTPException: 400 if the user is unknown, is an admin or is the caller.
    """
    try:
        banned = admin_service.ban_user(admin, id_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not banned:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ban failed",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _run_import(admin_service: AdminService, admin: User) -> None:
    """Runs in the background: the outcome is only visible in the logs."""
    try:
        result = admin_service.run_data_import(admin)
    except RuntimeError as e:
        logger.warning(f"Data import not started: {e}")
        return
    if result["success"]:
        logger.info("Data import finished successfully")
    else:
        logger.error(f"Data import failed: {result['stderr']}")


@router.post(
    "/import",
    summary="Run the data import in the background",
    status_code=status.HTTP_202_ACCEPTED,
)
def import_data(
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Starts utils.import_all_data without waiting for it to finish.

    Raises:
        HTTPException: 409 if an import is already running.
    """
    if admin_service.is_import_running():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An import is already running",
        )
    background_tasks.add_task(_run_import, admin_service, admin)
    return {"detail": "Import started"}


@router.get(
    "/connections",
    summary="Connection history of one user or of all users",
)
def get_connection_history(
    id_user: int | None = None,
    admin: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Returns the connection history, filtered by user if `id_user` is given.

    Raises:
        HTTPException: 404 if `id_user` is given and unknown.
    """
    try:
        return admin_service.get_connection_history(admin, id_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))