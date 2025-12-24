from fastapi import APIRouter, Depends #type: ignore
from app.schemas.court import CourtRequest, CourtResponse
from app.services.court_service import CourtService
from app.api.deps import get_court_service

router = APIRouter()

@router.post("/case/run", response_model=CourtResponse)
async def run_court(request: CourtRequest, service: CourtService = Depends(get_court_service)
) -> CourtResponse:
    resp = await service.run_case(request)


    return resp

    