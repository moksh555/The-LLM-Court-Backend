from fastapi import APIRouter, HTTPException,  Depends #type: ignore
from app.schemas.court import LoginRequest
from fastapi.responses import JSONResponse #type: ignore
from app.services.authentication.login_services import LoginService
from app.services.authentication.exceptions import (
    InvalidCredentials,
    AuthError,
    OAuthOnlyAccount,
    AuthDependencyError
)
from app.api.deps import get_login_service
from app.core.config import settings

router = APIRouter()

@router.post("/login")
def login_request(user_credentials: LoginRequest, loginService=Depends(get_login_service)):
    
    try: 
        # check if username and password are there in request
        email = (user_credentials.email or "").strip()
        password = user_credentials.password or ""
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        # get token from loginservice
        token = loginService.check_login_credentials(email, password)

        if not token:
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        # logic to save the cookie in Httponly
        response = JSONResponse({"ok": True, "status": 200})
        response.set_cookie(
            key="access_token", 
            value=token, 
            httponly=True, 
            secure=settings.COOKIE_SECURE, 
            samesite=settings.COOKIE_SAMESITE, 
            max_age=30*60, 
            path="/"
        )
        return response
    
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except AuthDependencyError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server error")