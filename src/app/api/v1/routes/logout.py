from fastapi import APIRouter, Depends, HTTPException, Response  # type: ignore
from app.api.auth_deps import get_current_user
from app.core.config import settings

router = APIRouter()

@router.post("/logout")
def logout_user(response: Response):

    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.COOKIE_DOMAIN or None,
    )

    return {"status": "logged_out"}
