from fastapi import APIRouter, HTTPException,  Depends #type: ignore
from app.schemas.court import RegisterRequest
from app.api.deps import get_register_service
from app.services.authentication.exceptions import (
    RegisterFirstNameError,
    RegisterEmailError,
    RegisterPasswordError,
    UserExistsError,
    AuthDependencyError,
    RegisterDOBError
)
router = APIRouter()

@router.post("/register", status_code=201)
def register_request(payload: RegisterRequest, registerservice=Depends(get_register_service)):

    try:
        response = registerservice.register_user(payload)
        return response
    except RegisterFirstNameError:
        raise HTTPException(
            status_code=400, 
            detail="First Name is required"
        )
    except RegisterEmailError:
        raise HTTPException(
            status_code=400, 
            detail="Email Empty is required"
        )
    except RegisterPasswordError:
        raise HTTPException(
            status_code=400, 
            detail="Password Empty is required"
        )
    except UserExistsError:
        raise HTTPException(
            status_code=409, 
            detail="User with same email already exists"
        )
    except AuthDependencyError:
        raise HTTPException(
            status_code=503, 
            detail="Service temporarily unavailable"
        )
    except RegisterDOBError:
        raise HTTPException(
            status_code=400, 
            detail="Date-OF-Birth Empty Error"
        )
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server error")




    
