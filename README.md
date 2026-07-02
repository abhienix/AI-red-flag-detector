# Red Flag Detector

Paste a suspicious email, URL, or code snippet, and it gets marked up the way a security
analyst would: red-lined text, an "exhibit" for each indicator, a risk score, and a
plain-language explanation of *why* it's risky — not just a verdict.

Two detection layers work together:

| Layer | How it works | Catches |
|---|---|---|
| **Heuristic engine** (client-side, instant) | ~24 regex rules across 5 attack categories | Known patterns: urgency language, credential requests, typosquat domains, SQL/XSS/command injection, scareware, crypto scams |
| **AI Analyst** (FastAPI + Groq, opt-in) | LLM reads the text for intent and context | Novel, paraphrased, or well-disguised attacks that don't match a fixed pattern |

The heuristic layer is deterministic and explainable — every flag traces back to an exact
regex and a written reason, no black box. The AI layer is there for the cases regex
structurally can't catch: a phishing email that's well-written enough to avoid every
"urgent action required" cliché.

## Project structure

```
red-flag-detector/
├── frontend/
│   └── index.html        # Self-contained UI + heuristic engine (no build step)
├── backend/
│   ├── main.py            # FastAPI app, /api/analyze endpoint
│   ├── llm_analyzer.py     # Groq call + prompt + response validation
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## Running it

**1. Backend (AI Analyst)**

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and add a free key from https://console.groq.com
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Health check: `GET /`.

**2. Frontend**

Just open `frontend/index.html` in a browser — no build step. The heuristic engine works
immediately with zero setup. Click **"Ask AI Analyst for a second opinion"** to hit the
backend (requires step 1 to be running).

If you deploy the backend somewhere other than `localhost:8000`, set
`window.RFD_API_BASE = "https://your-api.example.com"` in a `<script>` tag before
`index.html`'s main script, or edit the `API_BASE` constant directly.

## Why this design

This mirrors the AI fallback approach used in [SecureFlow](https://github.com/abhienix) —
keep a fast, deterministic layer as the default (no API key, no network dependency, fully
auditable), and treat the LLM as a second opinion rather than the sole judge. That split
matters for a security tool specifically: a regex hit is provable and reproducible; an LLM
verdict is probabilistic and should be labeled as such, which is why the AI panel is visually
separated as a "memo" rather than merged into the exhibit list.

## Limitations

This is an educational pattern-recognition tool, not a production detection system:

- The heuristic engine only catches known patterns — a novel attack with no matching regex
  scores CLEAR even if malicious.
- The AI Analyst's verdict is a model's best guess, not a guarantee — always shown with a
  confidence score, and should be treated as a second opinion, not a final word.
- Nothing here executes or fetches any of the analyzed content (no live URL requests, no
  code execution) — it's text pattern analysis only.

## License

MIT
