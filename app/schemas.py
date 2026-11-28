from enum import Enum
from pydantic import BaseModel, Field


class Verdict(str, Enum):
    allow = "allow"
    flag = "flag"
    block = "block"


class ScreenRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=20000)


class ScreenResponse(BaseModel):
    verdict: Verdict
    score: float = Field(..., ge=0.0, le=1.0)
    reasons: list[str] = []


class DetectorResult(BaseModel):
    score: float = 0.0
    reasons: list[str] = []
