from app.config import BLOCK_THRESHOLD, FLAG_THRESHOLD
from app.detectors import regex_rules
from app.schemas import ScreenResponse, Verdict


def combine(scores) -> float:
    remaining = 1.0
    for s in scores:
        remaining *= 1 - s
    return 1 - remaining


async def run_pipeline(prompt: str) -> ScreenResponse:
    results = [regex_rules.detect(prompt)]  # more detectors join this list later

    score = round(combine(r.score for r in results), 3)
    reasons = [reason for r in results for reason in r.reasons]

    if score >= BLOCK_THRESHOLD:
        verdict = Verdict.block
    elif score >= FLAG_THRESHOLD:
        verdict = Verdict.flag
    else:
        verdict = Verdict.allow

    return ScreenResponse(verdict=verdict, score=score, reasons=reasons)
