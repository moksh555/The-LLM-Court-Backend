from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone
import uuid

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings  # adjust import to your project

router = APIRouter()

# Create ONE dynamodb resource and reuse it
dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
user_table = dynamodb.Table(settings.USER_TABLE_NAME)


class DevCreateUserRequest(BaseModel):
    user_id: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    loginMethod: str = Field(default="password")


@router.post("/dev/users")
async def dev_create_user(body: DevCreateUserRequest):
    user_id = body.user_id or f"user-{uuid.uuid4()}"
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    item = {
        "user_id": user_id,
        "email": str(body.email) if body.email else None,
        "full_name": body.full_name,
        "loginMethod": body.loginMethod,
        "created_at": created_at,
        "chat_history": [],
    }
    # DynamoDB doesn't like None values
    item = {k: v for k, v in item.items() if v is not None}

    try:
        user_table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(user_id)"  # don't overwrite
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(status_code=409, detail="User already exists")
        raise

    return {"ok": True, "user": item}
