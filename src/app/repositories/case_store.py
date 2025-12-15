from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import uuid

from app.schemas.court import TranscriptMessage

@dataclass
class CaseRecord:
    case: str
    messages: List[TranscriptMessage]

class CaseStore:
    """
    Dev-only in-memory store.
    In prod you’ll replace this with DynamoDB/S3/Postgres.
    """
    def __init__(self):
        self._db: Dict[str, CaseRecord] = {}

    def create_with_id(self, case_id: str, case: str) -> str:
        self._db[case_id] = CaseRecord(case=case, messages=[])
        return case_id

    def create(self, case: str, messages: List[TranscriptMessage]) -> str:
        case_id = str(uuid.uuid4())
        self._db[case_id] = CaseRecord(case=case, messages=list(messages))
        return case_id

    def get(self, case_id: str) -> Optional[CaseRecord]:
        return self._db.get(case_id)

    def append(self, case_id: str, messages: List[TranscriptMessage]) -> None:
        rec = self._db[case_id]
        if rec is None:
            raise KeyError(f"Case id not found: {case_id}")
        rec.messages.extend(messages)
