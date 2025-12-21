import boto3 # type: ignore
from app.core.config import settings
from boto3.dynamodb.conditions import Key # type: ignore
import bcrypt # type: ignore
from app.services.Jwt_files.jwt_services import JwtService
#dyanamoDB table for user 
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
from app.services.authentication.exceptions import (
    InvalidCredentials, 
    AuthDependencyError
)
import datetime

class LoginService:
    def __init__(self):
        self.table_name_for_user = settings.USER_TABLE_NAME
        self.dynamo_db = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.jwt = JwtService()

    def check_login_credentials(self, email, entered_password):
        """
        Returns a JWT string on success.
        Raises:
          - InvalidCredentials
          - OAuthOnlyAccount
          - AuthDependencyError
        """
        try: 
            # first get the user from dyanamodb TABLE
            user_table = self.dynamo_db.Table(self.table_name_for_user)

            #email is GSI in dyanamo users table
            response = user_table.query(
                IndexName = "email-index",
                KeyConditionExpression=Key("email").eq(email.lower().strip()),
                Limit=1
            )
        except (ClientError, BotoCoreError) as e:
            # log.exception("DynamoDB query failed for email=%s", normalized_email)
            raise AuthDependencyError("User store unavailable") from e

        items = response.get("Items")
        if not items:
            raise InvalidCredentials("Email or password incorrect")
            
        user = items[0]
        hash_saved_password = user.get("password")
        if not hash_saved_password:
            raise InvalidCredentials("Email or password incorrect") # can also be changed to OauthOnlyAccount
            
        if not self.check_passwords(entered_password, hash_saved_password):
            raise InvalidCredentials("Email or password incorrect")   
            
        now = datetime.datetime.now(datetime.timezone.utc)
        payload = {
            "sub": str(user.get("user_id")),
            "email": user.get("email"),
            "iat": now,
            "exp": now + datetime.timedelta(minutes=35)
        }
        
        try:
            return self.jwt.create_token(payload)
        except Exception as e:
            raise AuthDependencyError("Token service unavailable")


    def check_passwords(self, entered_password, hash_saved_password):
        return bcrypt.checkpw(
            entered_password.encode("utf-8"), 
            hash_saved_password.encode("utf-8"))