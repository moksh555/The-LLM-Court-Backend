import boto3 #type: ignore
from boto3.dynamodb.conditions import Key # type: ignore
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
import bcrypt # type: ignore
from app.core.config import settings
from app.schemas.court import RegisterRequest
from app.services.authentication.exceptions import (
    RegisterFirstNameError,
    RegisterEmailError,
    RegisterPasswordError,
    UserExistsError,
    AuthDependencyError,
    RegisterDOBError
)
import uuid


class RegisterService:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.user_table_name = settings.USER_TABLE_NAME
        

    def register_user(self,payload: RegisterRequest):
        self.check_payload(payload)
        
        
        try:
           
            normalized_email=payload.email.lower().strip()
            user_table = self.dynamodb.Table(self.user_table_name)
            # first check if user with same email exists
            response = user_table.query(
                IndexName = "email-index",
                KeyConditionExpression=Key("email").eq(normalized_email),
                Limit=1
            )
            item = response.get("Items")
            if item:
                raise UserExistsError("User with same email already exists: Register Service")
            
            #put item to dynamodb users_table 
            hashed_password = self.hash_password(payload.password) 
            user_id = str(uuid.uuid4())
            response = user_table.put_item(
                Item={
                    "user_id": user_id,
                    "email": normalized_email,
                    "password": hashed_password,
                    "date_of_birth": payload.date_of_birth,
                    "first_name": payload.first_name,
                    "last_name": payload.last_name 
                }
            )
            return {"ok": True, "user_id":  user_id}
        except (ClientError, BotoCoreError) as e:
            raise AuthDependencyError("User store unavailable: Register Service") from e
    
    def check_payload(self, payload):
        first_name = payload.first_name
        email = payload.email
        password = payload.password
        date_of_birth = payload.date_of_birth

        if not first_name:
            raise RegisterFirstNameError("First Name Empty Error: Register Service")
        
        if not email:
            raise RegisterEmailError("Email Empty Error: Register Service")
        
        if not password:
            raise RegisterPasswordError("Password Empty Error: Register Service")
        
        if not date_of_birth:
            raise RegisterDOBError("Date-OF-Birth Empty Error: Register Service")
        
        return {"status": "ok", "message": "payload checked"}
    
    def hash_password(self, password):
        password_encoded=password.encode("utf-8")
        hashed_password = bcrypt.hashpw(password_encoded,bcrypt.gensalt())
        return hashed_password.decode("utf-8")