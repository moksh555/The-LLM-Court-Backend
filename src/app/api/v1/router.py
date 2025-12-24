from fastapi import APIRouter #type: ignore
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.court import router as court_router
from app.api.v1.routes.court_streaming import router as court_streaming_router  
from app.api.v1.routes.add_user_temp import router as add_user_temp
from app.api.v1.routes.personal_chat_history import router as personal_chat_history
from app.api.v1.routes.chats import router as chats_router
from app.api.v1.routes.login import router as login_router
from app.api.v1.routes.logout import router as logout_router
from app.api.v1.routes.register import router as register_router
from app.api.v1.routes.get_user import router as get_user_router
from app.api.v1.routes.google_oauth.google_callback import router as get_google_callback
from app.api.v1.routes.google_oauth.google_login import router as get_google_login

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(court_router, prefix="/court", tags=["court"])
api_router.include_router(court_streaming_router, prefix="/court", tags=["court_streaming"])
api_router.include_router(add_user_temp, prefix="/court", tags=["court_streaming"])
api_router.include_router(personal_chat_history, prefix="/court", tags=["personal_history"])
api_router.include_router(chats_router, prefix="/court", tags=["chats"])
api_router.include_router(get_user_router, prefix="/court", tags=["get_user"])

# Auth apis
api_router.include_router(get_google_login, prefix="/auth", tags=["auth"])
api_router.include_router(get_google_callback, prefix="/auth", tags=["auth"])
api_router.include_router(login_router, prefix="/auth", tags=["auth"])
api_router.include_router(register_router, prefix="/auth", tags=["auth"])
api_router.include_router(logout_router, prefix="/auth", tags=["auth"])

