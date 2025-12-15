from app.services.court_service import CourtService
from app.clients.openrouter import OpenRouterClient
from app.repositories.case_store import CaseStore
from functools import lru_cache



@lru_cache
def get_openrouter_client() -> OpenRouterClient:
    return OpenRouterClient()

@lru_cache
def get_case_store() -> CaseStore:
    return CaseStore()

def get_court_service() -> CourtService:
    return CourtService(llm=get_openrouter_client())