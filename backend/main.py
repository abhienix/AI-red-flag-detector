import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_analyzer import analyze_with_ai

# Load env variables from .env
load_dotenv()

app = FastAPI(
    title="AI Red Flag Detector API",
    description="Backend service for semantic security evaluation.",
    version="1.0.0",
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text snippet or code to analyze")
    lang: str = Field("en", description="Output language: 'en' or 'hi'")


class AnalyzeResponse(BaseModel):
    verdict: str
    risk_score: int
    category: str
    reasoning: str
    confidence: float


@app.get("/")
def health_check():
    return {"status": "ok", "service": "AI Red Flag Detector API"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    lang = req.lang.lower() if req.lang and req.lang.lower() in ("en", "hi") else "en"

    try:
        return analyze_with_ai(text, lang=lang)
    except RuntimeError as err:
        raise HTTPException(status_code=500, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {str(err)}")