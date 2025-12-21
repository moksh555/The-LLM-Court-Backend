import boto3 #type: ignore
from app.core.config import settings
from app.services.authentication.exceptions import (
    UserUnAuthorizedNoToken,
    UserUnAuthorizedNoId,
    UserUnAuthorizedInvalidToken,
    AuthDependencyError
)

from botocore.exceptions import BotoCoreError, ClientError  # type: ignore

from app.services.Jwt_files.jwt_services import JwtService

class AuthenticationService:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.user_table_name = settings.USER_TABLE_NAME
        self.jwtService = JwtService()

    def authenticate_token(self, token):
        if not token:
            raise UserUnAuthorizedNoToken("No Token Attached User Un-Authorized")
        
        response = self.jwtService.decode_and_verify_token(token)
        user_id = response.get("sub")
        user_email = response.get("email")

        if not user_id:
            raise UserUnAuthorizedNoId("Token missing user id (sub)")
        if not user_email:
            raise UserUnAuthorizedInvalidToken("Token missing email")
        
        return self.check_user_against_id_email(user_id, user_email)

    
    def check_user_against_id_email(self, user_id, user_email):
        
        try: 
            user_table = self.dynamodb.Table(self.user_table_name)
            response = user_table.get_item(
                Key={'user_id': user_id,}
            )

            user = response.get("Item")

            if not user:    
                raise UserUnAuthorizedNoId("No user with user_id")  

            if user.get("email") != user_email:
                raise UserUnAuthorizedInvalidToken("User id and user mail does not match")
            
            payload = {
                "user_id": user.get("user_id"),
                "email": user.get("email"),
                "date_of_birth": user.get("date_of_birth"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name") 
            }
            return payload
        except (ClientError, BotoCoreError) as e:
            raise AuthDependencyError("User store unavailable: AuthenticationService") from e