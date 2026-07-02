import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from llm_analyzer import analyze_with_ai

load_dotenv()

app = FastAPI(
    title="Red Flag Detector API",
    description="AI analyst layer for the Red Flag Detector — catches semantic red flags that regex heuristics miss.",
    version="1.0.0",
)

# Tighten allow_origins to your actual frontend origin before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str
    lang: str = "en"  # "en" | "hi" — which language the AI memo should be written in


class AnalyzeResponse(BaseModel):
    verdict: str          # "clear" | "suspicious" | "flagged"
    risk_score: int        # 0-100
    category: str
    reasoning: str
    confidence: float      # 0.0-1.0


@app.get("/")
def health_check():
    return {"status": "ok", "service": "red-flag-detector-api"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    lang = req.lang if req.lang in ("en", "hi") else "en"

    try:
        result = analyze_with_ai(req.text, lang=lang)
    except RuntimeError as e:
        # Missing API key etc. — a config problem, not a server crash
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {e}")

    return result