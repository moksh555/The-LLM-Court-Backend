from app.repositories.case_store import CaseStore
from fastapi import APIRouter, Depends
from app.schemas.court import CourtRequest, CourtResponse
from app.schemas.court import TranscriptMessage
from app.services.court_service import CourtService
from app.api.deps import get_case_store, get_court_service

router = APIRouter()

@router.post("/case/run", response_model=CourtResponse)
async def run_court(request: CourtRequest, service: CourtService = Depends(get_court_service),store: CaseStore = Depends(get_case_store),
) -> CourtResponse:
    resp = await service.run_case(request, store)

    # Store it (exact method name depends on your CaseStore)
    # Examples:
    # await store.save(resp.case_id, resp.model_dump())
    # store.save(resp.case_id, resp.model_dump())

    return resp

    