from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.court import router as court_router
from app.api.v1.routes.court_streaming import router as court_streaming_router  
from app.api.v1.routes.add_user_temp import router as add_user_temp



api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(court_router, prefix="/court", tags=["court"])
api_router.include_router(court_streaming_router, prefix="/court", tags=["court_streaming"])
api_router.include_router(add_user_temp, prefix="/court", tags=["court_streaming"])