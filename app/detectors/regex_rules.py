import re
import unicodedata
from pathlib import Path

import yaml

from app.schemas import DetectorResult

RULES_PATH = Path(__file__).resolve().parent.parent / "rules" / "patterns.yaml"


def _load_rules():
    with open(RULES_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return [
        {**r, "regex": re.compile(r["pattern"], re.IGNORECASE | re.MULTILINE)}
        for r in raw
    ]


RULES = _load_rules()  # compiling only once at startup not per request


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)  # fullwidth/lookalike chars -> plain
    text = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", text)  # strip zero-width chars
    text = re.sub(r"[ \t]+", " ", text)  # collapse spaces
    return text


def detect(prompt: str) -> DetectorResult:
    text = normalize(prompt)
    remaining = 1.0
    reasons = []
    for rule in RULES:
        if rule["regex"].search(text):
            remaining *= 1 - rule["weight"]
            reasons.append(f"regex:{rule['id']}")
    return DetectorResult(score=round(1 - remaining, 3), reasons=reasons)
