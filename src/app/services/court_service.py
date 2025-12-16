from http.client import HTTPException
import json
from typing import List
import uuid
from app.repositories.case_store import CaseStore
from app.schemas.court import CourtRequest, CourtResponse, TranscriptMessage, TranscriptRes
from app.clients.openrouter import OpenRouterClient, OpenRouterRateLimitError
from app.core.config import settings
import asyncio 
from app.core.prompts.stage1_prompts import STAGE1_PLAINTIFF_SYSTEM_PROMPT, STAGE1_DEFENSE_SYSTEM_PROMPT
from app.core.prompts.stage2_prompts import (
    STAGE2_PLAINTIFF_SYSTEM_PROMPT,
    STAGE2_PLAINTIFF_USER_PROMPT,
    STAGE2_DEFENSE_SYSTEM_PROMPT,
    STAGE2_DEFENSE_USER_PROMPT,
)
from app.core.prompts.stage3_prompts import (
    STAGE3_PLAINTIFF_SYSTEM_PROMPT,
    STAGE3_PLAINTIFF_USER_PROMPT,
    STAGE3_DEFENSE_SYSTEM_PROMPT,
    STAGE3_DEFENSE_USER_PROMPT,
)
from app.core.prompts.stage4_prompts import (
    STAGE4_JURY_SYSTEM_PROMPT,
    STAGE4_JURY_USER_PROMPT,
)
from app.core.prompts.stage5_prompts import (
    STAGE5_JUDGE_MAJORITY_SYSTEM_PROMPT,
    STAGE5_JUDGE_MAJORITY_USER_PROMPT,
)

class CourtService:
    def __init__(self, llm: OpenRouterClient):
        self.llm = llm

    async def run_case(self, request: CourtRequest, store: CaseStore) -> CourtResponse:
        print("Logged in run_case")
        case = (request.case or "").strip()
        if not case:
            raise HTTPException(status_code=400, detail="Case description cannot be empty.")
        case_id = request.case_id
        case_id = request.case_id or str(uuid.uuid4())
        store.create_with_id(case_id, case)

        stage1_result = await self.stage_1_execution_opening_statement(request)
        store.append(case_id, stage1_result)

        stage2_result = await self.stage_2_execution_argument(request, stage1_result)
        store.append(case_id, stage2_result)

        stage3_result = await self.stage_3_execution_closing_statement(request, stage2_result)
        store.append(case_id, stage3_result)

        stage4_result = await self.stage_4_jury_deliberation(request, stage1_result, stage2_result, stage3_result)
        store.append(case_id, stage4_result)

        stage5_result = await self.stage_5_judge_closing_remarks(request, stage4_result)
        store.append(case_id, [stage5_result])
        print("Completed run_case")
        return CourtResponse(
            case=case,
            case_id=case_id,
            case_title=await self.generate_case_title(case),
            stage1=stage1_result,
            stage2=stage2_result,
            stage3=stage3_result,
            stage4=stage4_result,
            stage5=stage5_result,
            metadata={},
        )

    def find_message_by_role(self, messages: List[TranscriptMessage], role: str) -> TranscriptMessage:
        for message in messages:
            if message.role == role:
                return message
        return None
    
    def build_jury_map(self, stage4_result: List[TranscriptMessage]) -> dict:
        jury_map = {}
        for m in stage4_result:
            jury_map[m.res.model or "unknown_model"] = (m.res.content if m.res else "")
        return jury_map

    async def generate_case_title(self, case: str) -> str:
        message = [
            {"role": "system", "content": "You are a helpful assistant that generates concise and descriptive titles for legal cases."},
            {"role": "user", "content": f"Generate a concise strict 3-5 words maximum and descriptive title for the following legal case:\n\n{case}"}]
        try:
            response = await self.llm.query_model(
                model=settings.CASE_TITLE_MODEL,
                messages=message,
            )
            if response is None or "content" not in response:
                raise HTTPException(status_code=502, detail="LLM returned no content for case title.")  
            return response["content"].strip().strip('"')
        except OpenRouterRateLimitError as e:
            raise HTTPException(status_code=429, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")        

    async def stage_1_execution_opening_statement(self, request: CourtRequest) -> List[TranscriptMessage]:
            print("Starting stage 1 execution")
            case = (request.case or "").strip()
            if not case:
                raise HTTPException(status_code=400, detail="Case description cannot be empty.")
            
            plaintiff_messages = [
            {"role": "system", "content": STAGE1_PLAINTIFF_SYSTEM_PROMPT},
            {"role": "user", "content": case},
            ]

            defense_messages = [
            {"role": "system", "content": STAGE1_DEFENSE_SYSTEM_PROMPT},
            {"role": "user", "content": case},
            ]

            try:
                # Prepare case for stage 1 for Plaintiff opening statement                
                plaintiff_task = self.llm.query_model(
                    model=settings.OPENROUTER_STAGE_1_PLAINTIFF_MODEL,
                    messages=plaintiff_messages,
                )
                # Prepare case for stage 1 for Defense opening statement
                defense_task = self.llm.query_model(
                    model=settings.OPENROUTER_STAGE_1_DEFENSE_MODEL,
                    messages=defense_messages,
                )
                
                response_plaintiff, response_defense = await asyncio.gather(plaintiff_task, defense_task)
                
            except OpenRouterRateLimitError as e:
            # Return the real status to the frontend instead of a fake "invalid case"
                raise HTTPException(status_code=429, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
            

            result: List[TranscriptMessage] = []
            for role, resp in [("plaintiff", response_plaintiff), ("defense", response_defense)]:
                transcript_message = TranscriptMessage(
                    stage="stage1",
                    role=role,
                    res=TranscriptRes(
                        content=resp["content"],
                        model=settings.OPENROUTER_STAGE_1_PLAINTIFF_MODEL if role == "plaintiff" else settings.OPENROUTER_STAGE_1_DEFENSE_MODEL,
                        reasoning_details=resp["reasoning_details"],
                    )
                )
                result.append(transcript_message)
            print("Completed stage 1 execution")
            return result

    async def stage_2_execution_argument(self, request: CourtRequest, stage1_result: List[TranscriptMessage]) -> List[TranscriptMessage]:
        print("Starting stage 2 execution")
        #need to add context from stage 1 result to prompt
        case = (request.case or "").strip()
        if not case:
            raise HTTPException(status_code=400, detail="Case description cannot be empty.")
        
        #loadprevious messages from stage 1
        stage1_plaintiff_opening = self.find_message_by_role(stage1_result, "plaintiff").res.content
        stage1_defense_opening = self.find_message_by_role(stage1_result, "defense").res.content


        plaintiff_messages = [
            {"role": "system", "content": STAGE2_PLAINTIFF_SYSTEM_PROMPT},
            {"role": "user", "content": STAGE2_PLAINTIFF_USER_PROMPT.format(
                case=case,
                stage1_plaintiff_opening=stage1_plaintiff_opening,
                stage1_defense_opening=stage1_defense_opening,
            )},
        ]
        try:
            plaintiff_response = await self.llm.query_model(
                model=settings.OPENROUTER_STAGE_1_PLAINTIFF_MODEL,
                messages=plaintiff_messages,
            )
            
            defense_messages = [
                {"role": "system", "content": STAGE2_DEFENSE_SYSTEM_PROMPT},
                {"role": "user", "content": STAGE2_DEFENSE_USER_PROMPT.format(
                    case=case,
                    stage1_plaintiff_opening=stage1_plaintiff_opening,
                    stage1_defense_opening=stage1_defense_opening,
                    stage2_plaintiff_argument=plaintiff_messages,  # ideally plaintiff_response["content"]
                )},
            ]

            try :
                defense_response = await self.llm.query_model(
                    model=settings.OPENROUTER_STAGE_1_DEFENSE_MODEL,
                    messages=defense_messages,
                )
                result = []
                for role, resp in [("plaintiff", plaintiff_response), ("defense", defense_response)]:
                    transcript_message = TranscriptMessage(
                        stage="stage2",
                        role=role,
                        res = TranscriptRes(
                            content=resp["content"],
                            model=settings.OPENROUTER_STAGE_1_PLAINTIFF_MODEL if role == "plaintiff" else settings.OPENROUTER_STAGE_1_DEFENSE_MODEL,
                            reasoning_details=resp["reasoning_details"],
                        )
                    )
                    result.append(transcript_message)
                print("Completed stage 2 execution")
                return result
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"LLM call failed at stage2 defense: {e}")
        except OpenRouterRateLimitError as e:
            # Return the real status to the frontend instead of a fake "invalid case"
            raise HTTPException(status_code=429, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM call failed at stage2 plaintiff: {e}")
    
    async def stage_3_execution_closing_statement(self, request: CourtRequest, stage2_result: List[TranscriptMessage]) -> List[TranscriptMessage]:
        print("Starting stage 3 execution")
        case = (request.case or "").strip()
        if not case:
            raise HTTPException(status_code=400, detail="Case description cannot be empty.")
        
        try:
            #gather stage2 arguments from both parties
            stage2_plaintiff_argument = self.find_message_by_role(stage2_result, "plaintiff")
            stage2_defense_argument = self.find_message_by_role(stage2_result, "defense")
            if not stage2_plaintiff_argument or not stage2_defense_argument:
                raise HTTPException(
                    status_code=400,
                    detail="Stage 2 results must include both plaintiff and defense arguments.",
            )

            # mkae the messages for both parties
            plaintiff_messages = [
                {"role": "system", "content": STAGE3_PLAINTIFF_SYSTEM_PROMPT},
                {"role": "user", "content": STAGE3_PLAINTIFF_USER_PROMPT.format(
                    case=case,
                    stage2_plaintiff_argument=stage2_plaintiff_argument,
                    stage2_defense_argument=stage2_defense_argument,
                )},
            ]

            defense_messages = [
                {"role": "system", "content": STAGE3_DEFENSE_SYSTEM_PROMPT},
                {"role": "user", "content": STAGE3_DEFENSE_USER_PROMPT.format(
                    case=case,
                    stage2_plaintiff_argument=stage2_plaintiff_argument,
                    stage2_defense_argument=stage2_defense_argument,
                )},
            ]

            plaintiff_task = self.llm.query_model(
                model=settings.OPENROUTER_STAGE_1_PLAINTIFF_MODEL,
                messages=plaintiff_messages,
            )
            defense_task = self.llm.query_model(
                model=settings.OPENROUTER_STAGE_1_DEFENSE_MODEL,
                messages=defense_messages,
            )
            #get repsonse from mdoels
            response_plaintiff, response_defense = await asyncio.gather(plaintiff_task, defense_task)
            
            # make result ready to return
            result: List[TranscriptMessage] = []
            for role, resp in [("plaintiff", response_plaintiff), ("defense", response_defense)]:
                transcript_message = TranscriptMessage(
                    stage="stage3",
                    role=role,
                    res=TranscriptRes(
                        content=resp["content"],
                        model=settings.OPENROUTER_STAGE_1_PLAINTIFF_MODEL if role == "plaintiff" else settings.OPENROUTER_STAGE_1_DEFENSE_MODEL,
                        reasoning_details=resp["reasoning_details"],
                    )
                )
                result.append(transcript_message)
            print("Completed stage 3 execution")
            return result   
        except OpenRouterRateLimitError as e:
            # Return the real status to the frontend instead of a fake "invalid case"
            raise HTTPException(status_code=429, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
        

    async def stage_4_jury_deliberation(self, request: CourtRequest, stage1_result: List[TranscriptMessage], stage2_result: List[TranscriptMessage], stage3_result: List[TranscriptMessage]) -> List[TranscriptMessage]:
        print("Starting stage 4 execution")
        case = (request.case or "").strip()
        if not case:
            raise HTTPException(status_code=400, detail="Case description cannot be empty.")
        
        # build jury system prompt and user prompt
        stage1_p = self.find_message_by_role(stage1_result, "plaintiff")
        stage1_d = self.find_message_by_role(stage1_result, "defense")
        stage2_p = self.find_message_by_role(stage2_result, "plaintiff")
        stage2_d = self.find_message_by_role(stage2_result, "defense")
        stage3_p = self.find_message_by_role(stage3_result, "plaintiff")
        stage3_d = self.find_message_by_role(stage3_result, "defense")
        
        #  please create prompts clear
        jury_messages = [
            {"role": "system", "content": STAGE4_JURY_SYSTEM_PROMPT},
            {"role": "user", "content": STAGE4_JURY_USER_PROMPT.format(
                case=case,
                stage1_plaintiff_opening=stage1_p,
                stage1_defense_opening=stage1_d,
                stage2_plaintiff_argument=stage2_p,
                stage2_defense_argument=stage2_d,
                stage3_plaintiff_closing=stage3_p,
                stage3_defense_closing=stage3_d,
            )},
        ]
        try:
            response = await self.llm.query_model_parallel(
                models=settings.JURY_MODELS,
                message=jury_messages,
            )

            result = []
            for model, resp in response.items():
                if resp is not None:
                    transcript_message = TranscriptMessage(
                        stage="stage4",
                        role="jury",
                        res=TranscriptRes(
                            content=resp["content"],
                            model=model,
                            reasoning_details=resp["reasoning_details"],
                        )
                    )
                    result.append(transcript_message)
            print("Completed stage 4 execution")
            return result

        except OpenRouterRateLimitError as e:
            # Return the real status to the frontend instead of a fake "invalid case"
            raise HTTPException(status_code=429, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
        
    async def stage_5_judge_closing_remarks(self, request: CourtRequest, stage4_result: List[TranscriptMessage]) -> List[TranscriptMessage]:
        print("Starting stage 5 execution")
        case = (request.case or "").strip()
        if not case:
            raise HTTPException(status_code=400, detail="Case description cannot be empty.")
        jury_map = self.build_jury_map(stage4_result)
        stage4_jury_map_text = json.dumps(jury_map, indent=2, ensure_ascii=False)
        judge_messages = [
        {"role": "system", "content": STAGE5_JUDGE_MAJORITY_SYSTEM_PROMPT},
        {"role": "user", "content": STAGE5_JUDGE_MAJORITY_USER_PROMPT.format(
            case=case,
            stage4_jury_map=stage4_jury_map_text,
        )},
    ]
        try:
            response = await self.llm.query_model(
                model=settings.JUDGE_MODEL,
                messages=judge_messages,
            )

            transcript_message = TranscriptMessage(
                stage="stage5",
                role="judge",
                res=TranscriptRes(
                    content=response["content"],
                    model=settings.JUDGE_MODEL,
                    reasoning_details=response["reasoning_details"],
                )
            )
            print("Completed stage 5 execution")
            return [transcript_message] # sending list to be consistent with other stages
        except OpenRouterRateLimitError as e:
            # Return the real status to the frontend instead of a fake "invalid case"
            raise HTTPException(status_code=429, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
        
        
        
