from app.api.auth_deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException  #type: ignore


router = APIRouter()

@router.get("/user/information/me")
def get_user_information(getCurrentUser=Depends(get_current_user)):

    if not  getCurrentUser.get("user_id"):
        raise HTTPException(status_code=401, detail="UnAuthorized")
    
    return getCurrentUser


