import asyncio
import json
import time
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request # type: ignore
from fastapi.responses import StreamingResponse # type: ignore


from app.schemas.court import CourtRequest, CourtResponse
from app.repositories.case_store import CaseStore
from app.api.deps import get_case_store, get_court_service
from app.services.court_service import CourtService
from app.core.config import settings
import boto3 # type: ignore


router = APIRouter()

@router.post("/case/stream")
async def stream_court_updates(request: CourtRequest, service: CourtService = Depends(get_court_service), CaseStore = Depends(get_case_store)) -> StreamingResponse:
    """
    Endpoint to stream real-time court updates for a given request ID.
    """
    
    if not request.case or not request.case.strip():
        raise HTTPException(status_code=400, detail="Case description cannot be empty.")


    return StreamingResponse(
        event_generator(request, service, CaseStore),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
        )


async def event_generator(request: CourtRequest, service: CourtService, store: CaseStore) -> AsyncGenerator[str, None]:
    """
    Generator function to yield court updates as server-sent events.
    """
    try:
        dyanmo_db = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        user_table = dyanmo_db.Table(settings.USER_TABLE_NAME)
        chat_table = dyanmo_db.Table(settings.CHAT_TABLE_NAME)

        title_task = None
        title_task = asyncio.create_task(service.generate_case_title(request.case))

        # Stage 1
        yield f"data: {json.dumps({'type': 'Waiting for Opening Statements'})}\n\n"
        stage1_result = await service.stage_1_execution_opening_statement(request)
        yield f"data: {json.dumps({'type': 'Done with Opening Statements', 'data': [m.model_dump() for m in stage1_result]})}\n\n"

        # Stage 2   
        yield f"data: {json.dumps({'type': 'Waiting for Plaintiff and Defendant Arguments'})}\n\n"
        stage2_result = await service.stage_2_execution_argument(request, stage1_result)
        yield f"data: {json.dumps({'type': 'Done with Plaintiff and Defendant Arguments', 'data': [m.model_dump() for m in stage2_result]})}\n\n"

        #stage 3
        yield f"data: {json.dumps({'type': 'Waiting for Closing Statements'})}\n\n"
        stage3_result = await service.stage_3_execution_closing_statement(request, stage2_result)
        yield f"data: {json.dumps({'type': 'Done with Closing Statements', 'data': [m.model_dump() for m in stage3_result]})}\n\n"

        #stage 4
        yield f"data: {json.dumps({'type': 'Waiting for Jury Deliberation'})}\n\n"
        stage4_result = await service.stage_4_jury_deliberation(request, stage1_result, stage2_result, stage3_result)
        yield f"data: {json.dumps({'type': 'Done with Jury Deliberation', 'data': [m.model_dump() for m in stage4_result]})}\n\n"

        # TODO:SHOWCASE VERDICT FROM JURY

        #stage 5
        yield f"data: {json.dumps({'type': 'Waiting for Judge Closing Remarks'})}\n\n"
        stage5_result = await service.stage_5_judge_closing_remarks(request, stage4_result)
        yield f"data: {json.dumps({'type': 'Done with Judge Closing Remarks', 'data': [m.model_dump() for m in stage5_result]})}\n\n"

        # TODO: Save the complete court session to the DynamoDB CaseStore here
        if title_task:
            court_title = await title_task
            yield f"data: {json.dumps({'type': 'court_title', 'data': court_title})}\n\n"
        yield f"data: {json.dumps({'type': 'Court Sets'})}\n\n"

        #preparing data to save
        try:
            chat_table.put_item(Item={
                "chat_id": request.case_id,
                "user_id": request.user_id,
                "case_date_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "case_title": court_title,
                "stage1_results":[m.model_dump() for m in stage1_result],
                "stage2_results":[m.model_dump() for m in stage2_result],
                "stage3_results":[m.model_dump() for m in stage3_result],
                "stage4_results":[m.model_dump() for m in stage4_result],
                "stage5_results":[m.model_dump() for m in stage5_result],
                'case':request.case,})
        except Exception as e:
            print(f"Error saving chat session: {e}")
        yield f"data: {json.dumps({'type': 'data saved'})}\n\n"

        user = user_table.get_item(Key={'user_id': request.user_id})
        user_item = user.get('Item')
        try:
            created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            history_entry = {
                "case_id": request.case_id,
                "case_title": court_title,
                "case_created_at": created_at,          # readable
                "case": request.case,}

            user_table.update_item(
                Key={"user_id": request.user_id},
                UpdateExpression="SET chat_history = list_append(if_not_exists(chat_history, :empty), :new)",
                ExpressionAttributeValues={
                    ":empty": [],
                    ":new": [history_entry],
                },
                # Optional safety: fail if user doesn't exist
                ConditionExpression="attribute_exists(user_id)",
            )
        except Exception as e:
            print(f"Error updating user chat history: {e}")

        
    except asyncio.CancelledError:
        # If the stream is cancelled, make sure we stop child tasks too
        if title_task is not None and not title_task.done():
            title_task.cancel()
        raise

    except Exception as e:
        if title_task is not None and not title_task.done():
            title_task.cancel()
            try:
                await title_task
            except Exception:
                pass

        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"