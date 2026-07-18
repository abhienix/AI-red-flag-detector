import os
import json
import re
from typing import Dict, Any
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

# System prompt for English analysis
SYSTEM_PROMPT_EN = """You are a security analyst assistant. You will be given a piece of text \
(an email, a message, a URL, or a code snippet) that a user suspects might be malicious.

Analyze it for signs of phishing, social engineering, scams, malicious links, or malicious code \
— including subtle or novel patterns that simple keyword matching would miss. Think about intent \
and context, not just the presence of specific words.

Respond with ONLY a JSON object, no markdown fences, no extra text, in exactly this shape:

{
  "verdict": "clear" | "suspicious" | "flagged",
  "risk_score": <integer 0-100>,
  "category": "<short label for the primary concern, or 'None' if clear>",
  "reasoning": "<2-3 sentences explaining the verdict in plain language, aimed at a non-expert>",
  "confidence": <float 0.0-1.0>
}

Write the "category" and "reasoning" fields in English.

Be conservative: only flag things a careful human analyst would actually flag. If the text looks \
benign, say so plainly rather than inventing concerns."""

# System prompt for Hindi analysis (देवनागरी)
SYSTEM_PROMPT_HI = """आप एक सुरक्षा विश्लेषक सहायक हैं। आपको एक टेक्स्ट (ईमेल, संदेश, यूआरएल, या कोड स्निपेट) \
दिया जाएगा जिसे उपयोगकर्ता संदिग्ध मानता है।

फ़िशिंग, सोशल इंजीनियरिंग, स्कैम, दुर्भावनापूर्ण लिंक, या दुर्भावनापूर्ण कोड के संकेतों के लिए इसका विश्लेषण करें \
— जिसमें ऐसे सूक्ष्म या नए पैटर्न भी शामिल हैं जिन्हें सामान्य कीवर्ड मिलान पकड़ नहीं पाता। सिर्फ़ शब्दों की मौजूदगी नहीं, \
बल्कि इरादे और संदर्भ के बारे में सोचें।

केवल एक JSON ऑब्जेक्ट के साथ जवाब दें, कोई मार्कडाउन फ़ेंस नहीं, कोई अतिरिक्त टेक्स्ट नहीं, ठीक इसी रूप में:

{
  "verdict": "clear" | "suspicious" | "flagged",
  "risk_score": <पूर्णांक 0-100>,
  "category": "<मुख्य चिंता के लिए संक्षिप्त लेबल, या साफ़ होने पर 'कोई नहीं'>",
  "reasoning": "<2-3 वाक्यों में निर्णय को सरल भाषा में समझाएँ, एक सामान्य व्यक्ति के लिए>",
  "confidence": <फ़्लोट 0.0-1.0>
}

"category" और "reasoning" फ़ील्ड हिंदी में लिखें (देवनागरी लिपि में), भले ही मूल टेक्स्ट अंग्रेज़ी में हो।

सतर्क रहें: केवल वही चीज़ें चिन्हित करें जिन्हें एक सावधान मानव विश्लेषक वास्तव में चिन्हित करेगा। यदि टेक्स्ट \
निर्दोष लगता है, तो बिना झूठी चिंता गढ़े यह स्पष्ट रूप से बताएं।"""


def _get_client() -> Groq:
    """Instantiate Groq client from environment."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is missing. Set it in .env or your deployment dashboard."
        )
    return Groq(api_key=api_key)


def _extract_json(raw: str) -> Dict[str, Any]:
    """Parse JSON string and strip codeblock fences or conversational text if present."""
    # Find the outermost curly braces to isolate JSON content from conversational wrapper text
    match = re.search(r"(\{.*\})", raw, re.DOTALL)
    if match:
        raw_json = match.group(1)
    else:
        raw_json = raw

    cleaned = re.sub(r"^```(json)?|```$", "", raw_json.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def analyze_with_ai(text: str, lang: str = "en") -> Dict[str, Any]:
    """Call Groq API to evaluate text snippet."""
    client = _get_client()
    system_prompt = SYSTEM_PROMPT_HI if lang == "hi" else SYSTEM_PROMPT_EN

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text[:6000]},
        ],
        temperature=0.2,
        max_tokens=450,
    )

    raw_content = completion.choices[0].message.content
    data = _extract_json(raw_content)

    # Sanitize & normalize fields
    risk_score = int(data.get("risk_score", 0))
    confidence_val = float(data.get("confidence", 0.85))

    return {
        "verdict": str(data.get("verdict") or "suspicious").lower(),
        "risk_score": max(0, min(100, risk_score)),
        "category": str(data.get("category") or ("अनिर्दिष्ट" if lang == "hi" else "Unspecified")),
        "reasoning": str(data.get("reasoning") or (
            "कोई विवरण उपलब्ध नहीं है।" if lang == "hi" else "No detailed reasoning provided."
        )),
        "confidence": max(0.0, min(1.0, confidence_val))
    }