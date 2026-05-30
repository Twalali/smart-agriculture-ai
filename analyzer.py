import json
import mimetypes
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import google.genai as genai
import google.genai.types as gtypes

_client: genai.Client | None = None

# Models tried in order — if one is overloaded, next is attempted
_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")
        _client = genai.Client(api_key=api_key)
    return _client


def _extract_text(response) -> str | None:
    """
    Extract text from Gemini response, skipping thought/reasoning parts.
    Gemini 2.5 Flash includes internal thought parts before the final answer.
    """
    try:
        if not response.candidates:
            return None
        parts = response.candidates[0].content.parts
        if not parts:
            return None
        text = ""
        for part in parts:
            if hasattr(part, "thought") and part.thought:
                continue
            if isinstance(part.text, str):
                text += part.text
        return text.strip() if text.strip() else None
    except Exception:
        try:
            return response.text
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Detection:
    name: str
    confidence: float
    severity: str
    description: str


@dataclass
class AnalysisResult:
    health_score: float
    overall_status: str
    crop_type: str
    growth_stage: str
    detections: list[Detection]
    recommendations: list[str]
    summary: str
    error: str | None = None


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_PROMPT = """\
You are an expert agronomist and plant pathologist.
Analyse the crop image and return ONLY a valid JSON object.
No markdown fences, no explanation, no extra text — pure JSON only.

Required JSON schema:
{
  "health_score": <integer 0-100>,
  "overall_status": <"healthy"|"at_risk"|"diseased"|"critical">,
  "crop_type": <string>,
  "growth_stage": <string>,
  "detections": [
    {
      "name": <string>,
      "confidence": <float 0.0-1.0>,
      "severity": <"none"|"low"|"medium"|"high"|"critical">,
      "description": <string, max 120 chars>
    }
  ],
  "recommendations": [<string>, ...],
  "summary": <string, 1-2 sentences>
}

Rules:
- health_score: 100 = perfectly healthy, 0 = complete crop failure.
- detections: list every disease, pest, nutrient deficiency, or stress symptom visible.
  Return an empty array if the crop looks healthy.
- recommendations: 3-5 concrete, actionable farming steps.
- If the image is not a crop or plant: health_score=0, overall_status="healthy",
  crop_type="Unknown", detections=[], recommendations=[],
  summary="No crop detected in the image."
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_image(image_path: str | Path) -> AnalysisResult:
    path = Path(image_path)

    try:
        raw = path.read_bytes()
    except OSError as exc:
        return _error_result(f"Could not read image file: {exc}")

    mime_type = mimetypes.guess_type(str(path))[0] or "image/jpeg"

    try:
        client = _get_client()
    except EnvironmentError as exc:
        return _error_result(str(exc))

    image_part = gtypes.Part.from_bytes(data=raw, mime_type=mime_type)

    # Try each model in order — if overloaded, wait briefly and try the next
    response = None
    last_error = ""

    for attempt, model in enumerate(_MODELS):
        try:
            response = client.models.generate_content(
                model=model,
                contents=[image_part, _PROMPT],
                config=gtypes.GenerateContentConfig(
                    max_output_tokens=4096,
                    temperature=0.1,
                ),
            )
            break  # success

        except Exception as exc:
            last_error = str(exc)
            is_retriable = (
                "503" in last_error
                or "unavailable" in last_error.lower()
                or "429" in last_error
                or "quota" in last_error.lower()
                or "resource_exhausted" in last_error.lower()
            )

            if is_retriable and attempt < len(_MODELS) - 1:
                time.sleep(3)   # brief pause before next model
                continue

            # Auth or unknown error — stop immediately
            return _error_result(f"API error: {last_error}")

    if response is None:
        return _error_result(
            "Google's servers are overloaded right now. "
            "Please wait 1-2 minutes and try again."
        )

    raw_text = _extract_text(response)

    if not raw_text:
        finish = response.candidates[0].finish_reason if response.candidates else "unknown"
        return _error_result(f"Model returned an empty response. Finish reason: {finish}")

    # Strip accidental markdown fences
    raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text)
    raw_text = re.sub(r"\n?```$", "", raw_text)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return _error_result(
            f"Model returned malformed JSON: {exc}\n\nRaw: {raw_text[:300]}"
        )

    try:
        return _parse_result(data)
    except (KeyError, TypeError, ValueError) as exc:
        return _error_result(f"Unexpected response structure: {exc}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_result(data: dict) -> AnalysisResult:
    detections = [
        Detection(
            name=str(d["name"]),
            confidence=float(d["confidence"]),
            severity=str(d["severity"]),
            description=str(d["description"]),
        )
        for d in data.get("detections", [])
    ]
    return AnalysisResult(
        health_score=float(data["health_score"]),
        overall_status=str(data["overall_status"]),
        crop_type=str(data["crop_type"]),
        growth_stage=str(data["growth_stage"]),
        detections=detections,
        recommendations=[str(r) for r in data.get("recommendations", [])],
        summary=str(data["summary"]),
    )


def _error_result(message: str) -> AnalysisResult:
    return AnalysisResult(
        health_score=0,
        overall_status="critical",
        crop_type="Unknown",
        growth_stage="Unknown",
        detections=[],
        recommendations=[],
        summary="Analysis could not be completed.",
        error=message,
    )
