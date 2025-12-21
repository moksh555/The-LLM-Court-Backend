from typing import Any, Dict
from decimal import Decimal

from fastapi import APIRouter, HTTPException #type: ignore
from fastapi.encoders import jsonable_encoder #type: ignore
from app.api.auth_deps import get_current_user
from app.core.config import settings
import boto3 #type: ignore
from fastapi import Depends #type: ignore

router = APIRouter()

def _to_json_safe(x: Any) -> Any:
    # DynamoDB can return Decimal; convert to int/float
    if isinstance(x, Decimal):
        # keep ints as int
        if x % 1 == 0:
            return int(x)
        return float(x)
    if isinstance(x, list):
        return [_to_json_safe(v) for v in x]
    if isinstance(x, dict):
        return {k: _to_json_safe(v) for k, v in x.items()}
    return x

@router.get("/chats/{chat_id}")
def get_chat(chat_id: str, current_user=Depends(get_current_user)) -> Dict[str, Any]:
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    dynamo = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
    chat_table = dynamo.Table(settings.CHAT_TABLE_NAME)

    resp = chat_table.get_item(Key={"chat_id": chat_id})
    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if item.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Chat not found")

    # ensure JSON-safe output (Decimal -> int/float, etc.)
    item = _to_json_safe(item)

    # Return a stable shape the frontend expects
    return jsonable_encoder(
        {
            "chat_id": item.get("chat_id"),
            "user_id": item.get("user_id"),
            "case_title": item.get("case_title"),
            "case_date_time": item.get("case_date_time"),
            "case": item.get("case"),
            "stage1_results": item.get("stage1_results", []),
            "stage2_results": item.get("stage2_results", []),
            "stage3_results": item.get("stage3_results", []),
            "stage4_results": item.get("stage4_results", []),
            "stage5_results": item.get("stage5_results", []),
        }
    )
