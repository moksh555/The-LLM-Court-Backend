from fastapi import APIRouter, Depends, HTTPException, Response  # type: ignore
from app.api.auth_deps import get_current_user
from app.core.config import settings

router = APIRouter()

@router.post("/logout")
def logout_user(response: Response, current_user=Depends(get_current_user)):
    if not current_user.get("user_id"):
        raise HTTPException(status_code=401, detail="UnAuthorized")

    response.delete_cookie(
        key="access_token",
        path="/",
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )

    return {"status": "logged_out"}
