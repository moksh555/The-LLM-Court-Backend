from app.core.config import settings
import jwt #type: ignore
from app.services.Jwt_files.jwt_exceptions import (
    ExpiredToken,
    InvalidToken,
)

class JwtService:
    def __init__(self):
        self.jwt_secret = settings.JWT_SECRET_KEY
        self.jwt_algorithm = settings.JWT_ALGORITHM

    def create_token(self, payload):
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def decode_and_verify_token(self,token):
        try:
            decoded_payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm],
                options={"require": ["exp", "iat", "sub"]}
            )
            return decoded_payload
        except jwt.ExpiredSignatureError:
            raise ExpiredToken("Token Expired")
        except jwt.InvalidTokenError as e:
            raise InvalidToken("Invalid Token") from e
    