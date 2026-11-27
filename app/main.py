from fastapi import FastAPI
from app.schemas import ScreenRequest, ScreenResponse, Verdict

app = FastAPI(title="PromptShield", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/screen", response_model=ScreenResponse)
async def screen(req: ScreenRequest):
    return ScreenResponse(verdict=Verdict.allow, score=0.0, reasons=[])

    