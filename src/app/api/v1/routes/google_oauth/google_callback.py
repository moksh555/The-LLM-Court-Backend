from fastapi import APIRouter, Request, Response, HTTPException, Depends#type: ignore
from app.api.auth_deps import get_google_oauth_services
from app.api.deps import get_authentication_service
from fastapi.responses import RedirectResponse #type: ignore
router = APIRouter()
from app.core.config import settings
import urllib
from botocore.exceptions import ClientError, EndpointConnectionError #type: ignore
from boto3.dynamodb.conditions import Key  # CHANGED: needed for proper DynamoDB GSI query # type: ignore
import datetime
import httpx #type: ignore
from app.services.authentication.exceptions import AuthDependencyError


@router.get("/google/callback")
def handle_google_callback(request: Request, response: Response, googlOAuthService=Depends(get_google_oauth_services)):
    callbackCode = request.query_params.get("code")
    callbackState = request.query_params.get("state")
    callbackError = request.query_params.get("error")

    if callbackError:
        raise HTTPException(status_code=403, detail=request.query_params.get("error_description") or "Google login cancelled/denied.",)
    
    if not callbackCode or not callbackState:
        raise HTTPException(status_code=400, detail="Missing code/state from Google callback.")
    
    cookieState = request.cookies.get("oauth_state")
    print("callbackState:", callbackState)
    print("cookieState:", cookieState)
    try:
        googlOAuthService.ensureCookieState(cookieState)
        googlOAuthService.checkState(callbackState, cookieState)
    except:
        raise HTTPException(status_code=403, detail="OAuth state validation failed. Please retry.")

    token_form = {
        "code": callbackCode,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    try:
        with httpx.Client(timeout=10) as client:
            token_resp = client.post(settings.GOOGLE_TOKEN_URL, data=token_form)
            token_json = token_resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail="Google token endpoint unreachable.") from e

    if token_resp.status_code != 200 or token_json.get("error"):
        raise HTTPException(
            status_code=401,
            detail=f"Token exchange failed: {token_json.get('error_description') or token_json.get('error')}",
        )
    
    idt = token_json.get("id_token")
    if not idt:
        raise HTTPException(status_code=401, detail="No id_token returned from Google.")
    
    try:
        claims = googlOAuthService.verify_google_id_token(idt)
        googlOAuthService.validateClaims(claims)
    except:
        raise HTTPException(status_code=401, detail="Invalid Google ID token.")
    
    try:
        user = googlOAuthService.ensureUser(claims)
    except (EndpointConnectionError, ClientError):
        raise HTTPException(status_code=503, detail="DynamoDB unavaialble")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create/login user") from e
    
    print(user)
    # now create token
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user.get("user_id")),
        "email": user.get("email"),
        "iat": now,
        "exp": now + datetime.timedelta(minutes=35)
    }
    try:
        app_token = googlOAuthService.generate_token_OAuth(payload)
    except AuthDependencyError:
        raise HTTPException(status_code=503, detail="Token service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    print(app_token)
    resp = RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard", status_code=302)
    resp.set_cookie(
        key="access_token",
        value=app_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=35 * 60,
        domain=settings.COOKIE_DOMAIN or None,
        path="/",
    )
    resp.delete_cookie("oauth_state", path="/")  # cleanup

    return resp





    

