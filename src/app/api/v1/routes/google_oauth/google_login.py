from fastapi import APIRouter #type: ignore
from fastapi.responses import RedirectResponse #type: ignore
import secrets
from app.core.config import settings
import urllib.parse

router = APIRouter()

@router.get("/google/login")
def google_login_request():
    state = secrets.token_urlsafe(64)
    print(settings.GOOGLE_REDIRECT_URI,)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }

    url = f"{settings.GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    resp = RedirectResponse(url, status_code=302)

    resp.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=settings.COOKIE_SECURE,   
        samesite=settings.COOKIE_SAMESITE, 
        max_age=10 * 60,
        domain=settings.COOKIE_DOMAIN or None,
        path="/",
    )

    return resp