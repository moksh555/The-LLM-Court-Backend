from app.services.court_service import CourtService
from app.clients.openrouter import OpenRouterClient
from app.services.authentication.login_services import LoginService
from app.services.authentication.register_service import RegisterService
from app.services.authentication.authentication_service import AuthenticationService
from functools import lru_cache
from fastapi import Depends, HTTPException, Request  # type: ignore



@lru_cache
def get_openrouter_client() -> OpenRouterClient:
    return OpenRouterClient()

def get_court_service():
    return CourtService(llm=get_openrouter_client())

def get_login_service():
    return LoginService()

def get_register_service():
    return RegisterService()

def get_authentication_service():
    return AuthenticationService()


