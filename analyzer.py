"""AI crop analysis via Google Gemini."""
import json, mimetypes, os, re, time
from dataclasses import dataclass
from pathlib import Path
import google.genai as genai
import google.genai.types as gtypes

_client = None
_MODELS = ["gemini-2.5-flash","gemini-2.0-flash","gemini-2.0-flash-lite"]

def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("GEMINI_API_KEY")
        if not key: raise EnvironmentError("GEMINI_API_KEY not set.")
        _client = genai.Client(api_key=key)
    return _client

def _extract_text(response):
    try:
        parts = response.candidates[0].content.parts
        return "".join(p.text for p in parts if not (hasattr(p,"thought") and p.thought) and isinstance(p.text,str)).strip() or None
    except: return None

@dataclass
class Detection:
    name: str; confidence: float; severity: str; description: str

@dataclass
class AnalysisResult:
    health_score: float; overall_status: str; crop_type: str; growth_stage: str
    detections: list; recommendations: list; summary: str; error: str = None

def _prompt(lang="fr"):
    lang_instruction = {
        "fr": "Réponds en français.",
        "rn": "Subiza mu Kirundi.",
        "en": "Respond in English.",
    }.get(lang, "Réponds en français.")
    return f'''You are an expert agronomist. Analyse the crop image.
{lang_instruction} All text values (crop_type, growth_stage, descriptions, recommendations, summary) must be in that language.
Return ONLY valid JSON — no markdown, no extra text:
{{"health_score":<0-100>,"overall_status":<"healthy"|"at_risk"|"diseased"|"critical">,
"crop_type":<str>,"growth_stage":<str>,
"detections":[{{"name":<str>,"confidence":<0-1>,"severity":<"none"|"low"|"medium"|"high"|"critical">,"description":<str max 120 chars>}}],
"recommendations":[<str>],"summary":<1-2 sentences>}}
If not a crop: health_score=0,overall_status="healthy",crop_type="Unknown",detections=[],recommendations=[],summary="No crop detected."'''

def analyse_image(image_path, lang="fr"):
    path = Path(image_path)
    try: raw = path.read_bytes()
    except OSError as e: return _err(f"Cannot read file: {e}")
    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    try: client = _get_client()
    except EnvironmentError as e: return _err(str(e))
    image_part = gtypes.Part.from_bytes(data=raw, mime_type=mime)
    last_error = ""; text = ""
    for i, model in enumerate(_MODELS):
        try:
            resp = client.models.generate_content(
                model=model, contents=[image_part, _prompt(lang)],
                config=gtypes.GenerateContentConfig(max_output_tokens=4096, temperature=0.1))
            text = _extract_text(resp) or ""
            if text: break
        except Exception as e:
            last_error = str(e)
            if ("503" in last_error or "429" in last_error or "unavailable" in last_error.lower()) and i < len(_MODELS)-1:
                time.sleep(3); continue
            break
    if not text: return _err(f"API error: {last_error}")
    text = re.sub(r"^```[a-z]*\n?","",text); text = re.sub(r"\n?```$","",text)
    try: data = json.loads(text)
    except json.JSONDecodeError as e: return _err(f"Malformed JSON: {e}\nRaw: {text[:300]}")
    try:
        return AnalysisResult(
            health_score=float(data["health_score"]), overall_status=str(data["overall_status"]),
            crop_type=str(data["crop_type"]), growth_stage=str(data["growth_stage"]),
            detections=[Detection(**d) for d in data.get("detections",[])],
            recommendations=[str(r) for r in data.get("recommendations",[])],
            summary=str(data["summary"]))
    except Exception as e: return _err(f"Parse error: {e}")

def _err(msg):
    return AnalysisResult(health_score=0,overall_status="critical",crop_type="Unknown",
        growth_stage="Unknown",detections=[],recommendations=[],
        summary="Analysis could not be completed.",error=msg)
