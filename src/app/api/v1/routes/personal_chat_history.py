from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException #type: ignore
from boto3.dynamodb.types import TypeDeserializer #type: ignore
from app.api.auth_deps import get_current_user
from app.core.config import settings
import boto3 #type: ignore
from fastapi import Depends #type: ignore

router = APIRouter()

_deser = TypeDeserializer()

def _unwrap_ddb(val: Any) -> Any:
    """
    Handles BOTH formats:
    1) DynamoDB low-level format: {"M": {"k": {"S": "v"}}}
    2) Boto3 resource format: {"k": "v"}
    """
    if not isinstance(val, dict):
        return val

    # low-level typed format
    if len(val) == 1 and next(iter(val.keys())) in {"S", "N", "M", "L", "BOOL", "NULL", "SS", "NS"}:
        return _deser.deserialize(val)

    # already "normal" python dict
    return val

def _normalize_history(raw_list: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_list, list):
        return []

    out: List[Dict[str, Any]] = []

    for entry in raw_list:
        e = _unwrap_ddb(entry)

        # if still nested as {"M": {...}}
        if isinstance(e, dict) and "M" in e:
            e = _unwrap_ddb(e)

        if not isinstance(e, dict):
            continue

        case_id = e.get("case_id")
        case_title = e.get("case_title")
        created_at = e.get("case_created_at")
        created_epoch = e.get("case_created_at_epoch")
        case_text = e.get("case")  # optional (usually don't need in sidebar)

        # convert epoch if present as string/Decimal
        try:
            if created_epoch is not None:
                created_epoch = int(created_epoch)
        except Exception:
            created_epoch = None

        out.append(
            {
                "case_id": case_id,
                "case_title": case_title,
                "case_created_at": created_at,
                "case_created_at_epoch": created_epoch,
                # keep case only if you want it for preview
                # "case": case_text,
            }
        )

    # sort newest-first (prefer epoch)
    out.sort(key=lambda x: x.get("case_created_at_epoch") or 0, reverse=True)

    # dedupe by case_id (keep newest)
    seen = set()
    deduped = []
    for x in out:
        cid = x.get("case_id")
        if not cid or cid in seen:
            continue
        seen.add(cid)
        deduped.append(x)

    return deduped


@router.get("/users/chat_history")
def get_chat_history(current_user=Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    dynamo = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
    user_table = dynamo.Table(settings.USER_TABLE_NAME)

    resp = user_table.get_item(Key={"user_id": user_id})
    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="User not found")

    history_raw = item.get("chat_history", [])
    history = _normalize_history(history_raw)[::-1]

    return {"user_id": user_id, "chat_history": history}
