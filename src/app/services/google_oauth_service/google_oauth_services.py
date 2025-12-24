from app.services.google_oauth_service.google_oauth_services_exception import (
    StateMismatchError,
    NoCookieStateError,
    MissingSUBError,
    EmailNotVerfiedError
)
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
from google.oauth2 import id_token #type: ignore
from google.auth.transport import requests as grequests #type: ignore
from boto3.dynamodb.conditions import Attr  # type: ignore 
from app.services.authentication.exceptions import AuthDependencyError
import boto3 #type: ignore
from boto3.dynamodb.conditions import Key # type: ignore
from app.core.config import settings
from app.services.Jwt_files.jwt_services import JwtService
import uuid, time

class GoogleOAuthServices:
    def __init__(self):
        self.user_table_name = settings.USER_TABLE_NAME
        self.dynamoDB = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.jwt = JwtService()

    def checkState(self, callbackState, cookieState):
        if not (callbackState == cookieState):
            raise StateMismatchError("States from callback and cookie does not match: Google Oauth Service")
        return {"status": "ok", "messages": "states macthed"}
    
    def ensureCookieState(self, cookieState: str | None):
        if not cookieState:
            raise NoCookieStateError("OAuth state cookie missing.")
        return {"status": "ok", "messages": "no errors in Oauth"}
    
    def verify_google_id_token(self, token):
        request = grequests.Request()
        id_info = id_token.verify_oauth2_token(token, request, settings.GOOGLE_CLIENT_ID)
        return id_info
    
    def validateClaims(self, claims):
        google_sub = claims.get("sub")
        if not google_sub:
            raise MissingSUBError("Invalid Google token: missing sub.")

        email = claims.get("email")    
        email_verified = claims.get("email_verified", False)

        if email and not email_verified:
            raise EmailNotVerfiedError("Google email not verified.")
        return {"status": "ok", "message": "validated required field"}
    
    def ensureUser(self, claims):
        i = 0
        print("moksh" + str(i))
        i+=1
        user_table = self.dynamoDB.Table(self.user_table_name)
        print("moksh" + str(i))
        i+=1
        google_sub = claims.get("sub")
        print("moksh" + str(i))
        i+=1
        email = claims.get("email").lower().strip()
        print("moksh" + str(i))
        i+=1
        email_verified = claims.get("email_verified")
        print("moksh" + str(i))
        i+=1
        first_name = claims.get("given_name")
        print("moksh" + str(i))
        i+=1
        last_name = claims.get("family_name")
        print("moksh" + str(i))
        i+=1

        # resp = user_table.query(
        #     IndexName="google_sub-index",
        #     KeyConditionExpression="google_sub = :gs",
        #     ExpressionAttributeValues={":gs": google_sub},
        #     Limit=1,
        # )

        resp = user_table.scan(
        FilterExpression=Attr("google_sub").eq(google_sub),
        Limit=1,
        )
        print("moksh" + str(i))
        i+=1
        items = resp.get("Items", [])
        print("moksh" + str(i))
        i+=1
        if items:
            user = items[0]
            print("moksh" + str(i))
            i+=1
            return user
        else:
            now = int(time.time())
            user_id = str(uuid.uuid4())

            new_user = {
                "user_id": user_id,
                "google_sub": google_sub,
                "email": email,
                "email_verified": bool(email_verified),
                "first_name": first_name,
                "last_name":last_name,
                "created_at_epoch": now,
                "auth_provider": "google",
            }
            print("moksh" + str(i))
            i+=1
            try:
                user_table.put_item(
                    Item=new_user,
                    ConditionExpression="attribute_not_exists(user_id)",
                )
                print("moksh" + str(i))
                i+=1
                return new_user
            except (ClientError, BotoCoreError) as e:
                raise AuthDependencyError("User store unavailable: Register Service") from e

    def generate_token_OAuth(self, payload):
        try:
            return self.jwt.create_token(payload)
        except Exception as e:
            raise AuthDependencyError("Token service unavailable") from e