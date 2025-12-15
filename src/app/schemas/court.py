# Backend/src/app/schemas/court.py
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional
import time
import uuid

Stage = Literal["stage1", "stage2", "stage3", "stage4", "stage5"]
Role = Literal["plaintiff", "defense", "jury", "judge"]

class CourtRequest(BaseModel):
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case: str = Field(..., min_length=1, max_length=20000)

class TranscriptRes(BaseModel):
    content: str
    reasoning_details: Optional[str] = None
    model: Optional[str]

class TranscriptMessage(BaseModel):
    chat_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: float = Field(default_factory=lambda: time.time())
    stage: Stage
    role: Role                       # "plaintiff", "defense", "jury", "judge"
    res : TranscriptRes

class CourtResponse(BaseModel):
    case: str
    case_id: str   # for later use if we wanted to save each case thread individually and show case each user hisotry of cases, same as CourtRequest case_id for persistent in dynamoDB table under user_id partition key
    ts: float = Field(default_factory=lambda: time.time())
    stage1: List[TranscriptMessage]
    stage2: List[TranscriptMessage]
    stage3: List[TranscriptMessage]
    stage4: List[TranscriptMessage]
    stage5: TranscriptMessage
    metadata: Dict[str, Any] = Field(default_factory=dict)

