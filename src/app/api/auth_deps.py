from fastapi import Depends, HTTPException, Request  # type: ignore
from app.api.deps import get_authentication_service
from app.services.authentication.exceptions import (
    UserUnAuthorizedNoToken,
    UserUnAuthorizedNoId,
    UserUnAuthorizedInvalidToken,
    AuthDependencyError,
)
from app.services.Jwt_files.jwt_exceptions import ExpiredToken, InvalidToken

def get_current_user(
        request: Request, 
        authenticationService = Depends(get_authentication_service)
    ):
    token = request.cookies.get("access_token")

    try:
        return authenticationService.authenticate_token(token)
    except (UserUnAuthorizedNoToken, UserUnAuthorizedNoId, UserUnAuthorizedInvalidToken,ExpiredToken,InvalidToken): 
        raise HTTPException(status_code=401, detail="Unauthorized")
    except AuthDependencyError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


    