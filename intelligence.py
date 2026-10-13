
"""
CivicFix — Intelligence Module

Prototype functions for AI-assisted civic complaint analysis.
Severity and resolution estimates are heuristic estimates, not validated
municipal predictions or official service-level agreements.
"""

import json
import math
import mimetypes
import os
import re
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path


CATEGORIES = ["pothole", "open_manhole"]
SEVERITIES = ["Low", "Medium", "High"]

VLM_MODEL = "gemini-3.8-flash"

_VALID_CATEGORIES = set(CATEGORIES)
_VALID_SEVERITIES = set(SEVERITIES)

_BASE_DAYS = {
    "pothole": 6,
    "open_manhole": 2,
}

_SEVERITY_FACTORS = {
    "Low": 1.6,
    "Medium": 1.0,
    "High": 0.6,
}

_DEPARTMENT_FACTORS = {
    "PWD": 1.2,
    "Municipal Corporation": 1.0,
    "Electricity Board": 0.9,
    "Jal Board": 1.1,
    "Sanitation": 0.8,
}

_CATEGORY_HI = {
    "pothole": "सड़क पर गड्ढा",
    "open_manhole": "खुला मैनहोल",
    "unknown": "अज्ञात समस्या",
}

_SEVERITY_HI = {
    "Low": "कम",
    "Medium": "मध्यम",
    "High": "अधिक",
}

_URGENCY_EN = {
    "Low": "Routine attention is recommended.",
    "Medium": "Timely action is recommended.",
    "High": "Prompt inspection and action are recommended.",
}

_URGENCY_HI = {
    "Low": "सामान्य रूप से ध्यान देने की आवश्यकता है।",
    "Medium": "समय पर कार्रवाई करने की आवश्यकता है।",
    "High": "शीघ्र निरीक्षण और कार्रवाई की आवश्यकता है।",
}


def _number(value, default=0.0):
    """Convert a value to a finite float, using a fallback if invalid."""
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def _confidence(value):
    """Clamp confidence to the range 0–1."""
    return max(0.0, min(1.0, _number(value)))


def _valid_category(value):
    return value if value in _VALID_CATEGORIES else "unknown"


def _valid_severity(value):
    return value if value in _VALID_SEVERITIES else "Medium"


def _parse_json(text):
    """Parse a JSON object, including one surrounded by Markdown fences."""
    if not isinstance(text, str):
        return {}

    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        result = json.loads(text)
        return result if isinstance(result, dict) else {}
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError:
            pass

    return {}


def vlm_analyze(image_path):
    """
    Analyze an image using Google's Gemini API.

    Requires the google-genai package and GEMINI_API_KEY environment variable.
    Returns a safe fallback result when the API is unavailable.
    """
    fallback = {
        "category": "unknown",
        "severity": "Medium",
        "description": "Image analysis unavailable.",
        "confidence": 0.0,
        "ok": False,
    }

    try:
        path = Path(image_path)

        if not path.is_file():
            return {**fallback, "description": "Image file not found."}

        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            return {**fallback, "description": "Unsupported image format."}

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {**fallback, "description": "GEMINI_API_KEY is not set."}

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt = """
Analyze this civic issue photograph. Return ONLY a JSON object with:
{
  "category": "pothole" or "open_manhole" or "unknown",
  "severity": "Low" or "Medium" or "High",
  "description": "short factual description of visible evidence",
  "confidence": 0.0
}
Do not claim facts that cannot be seen in the image.
Use unknown if the image does not clearly show either supported category.
Confidence must be a number between 0 and 1.
"""

        image_bytes = path.read_bytes()
        response = client.models.generate_content(
            model=VLM_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
            ],
        )

        result = _parse_json(getattr(response, "text", "") or "")
        category = _valid_category(result.get("category"))
        severity = _valid_severity(result.get("severity"))
        description = str(result.get("description", "")).strip()

        if category == "unknown":
            return {
                **fallback,
                "description": description or "Issue could not be identified.",
            }

        return {
            "category": category,
            "severity": severity,
            "description": description or "Visible civic issue detected.",
            "confidence": _confidence(result.get("confidence", 0.5)),
            "ok": True,
        }

    except Exception as exc:
        # Do not expose API keys or other secret configuration in error text.
        print(f"VLM analysis unavailable: {type(exc).__name__}")
        return fallback



def merge_results(yolo_result, vlm_result):
    """
    Merge YOLO and VLM predictions.
    Confidence is a heuristic score, not a calibrated probability.
    """
    yolo = yolo_result if isinstance(yolo_result, dict) else {}
    vlm = vlm_result if isinstance(vlm_result, dict) else {}

    # Accept either category or issue as the input key.
    yolo_category = _valid_category(
        yolo.get("issue", yolo.get("category", yolo.get("class")))
    )
    vlm_category = _valid_category(
        vlm.get("issue", vlm.get("category"))
    )

    yolo_conf = _confidence(
        yolo.get("confidence", yolo.get("score", 0.0))
    )
    vlm_conf = _confidence(
        vlm.get("confidence", vlm.get("score", 0.0))
    )

    yolo_valid = yolo_category != "unknown"
    vlm_valid = (
        vlm_category != "unknown"
        and vlm.get("ok") is not False
    )

    review = False
    reason = "Results are consistent."

    if not yolo_valid and not vlm_valid:
        category = "unknown"
        confidence = 0.0
        severity = "Medium"
        description = "Issue could not be reliably identified."
        review = True
        reason = "No reliable category was identified."

    elif yolo_valid and not vlm_valid:
        category = yolo_category
        confidence = yolo_conf * 0.9
        severity = _valid_severity(yolo.get("severity"))
        description = str(
            yolo.get(
                "description",
                "Issue detected by object detector."
            )
        )
        review = True
        reason = "VLM result unavailable or inconclusive."

    elif vlm_valid and not yolo_valid:
        category = vlm_category
        confidence = vlm_conf * 0.8
        severity = _valid_severity(vlm.get("severity"))
        description = str(
            vlm.get("description", "Issue identified by VLM.")
        )
        review = True
        reason = "Object detector result unavailable or inconclusive."

    elif yolo_category == vlm_category:
        category = yolo_category
        confidence = min(
            0.95,
            0.6 * yolo_conf + 0.4 * vlm_conf
        )

        severity_rank = {"Low": 1, "Medium": 2, "High": 3}
        yolo_severity = _valid_severity(yolo.get("severity"))
        vlm_severity = _valid_severity(vlm.get("severity"))

        severity = max(
            [yolo_severity, vlm_severity],
            key=lambda value: severity_rank[value]
        )

        description = str(
            vlm.get("description")
            or yolo.get("description")
            or "Civic issue detected."
        )

        if confidence < 0.4:
            review = True
            reason = "Agreement exists, but confidence is weak."

    else:
        # Different categories mean a manual review is necessary.
        if yolo_conf >= vlm_conf:
            category = yolo_category
            severity = _valid_severity(yolo.get("severity"))
            description = str(
                yolo.get("description", "Conflicting assessments.")
            )
        else:
            category = vlm_category
            severity = _valid_severity(vlm.get("severity"))
            description = str(
                vlm.get("description", "Conflicting assessments.")
            )

        confidence = min(yolo_conf, vlm_conf) * 0.5
        review = True
        reason = "YOLO and VLM disagree about the issue category."

    # IMPORTANT: return must be outside all if/elif/else branches.
    return {
        "issue": category,
        "category": category,
        "severity": severity,
        "confidence": round(_confidence(confidence), 3),
        "description": description,
        "needs_review": review,
        "review_reason": reason,
    }


def generate_complaint(issue, severity, address, language="en"):
    """Generate a short complaint draft in English or Hindi."""
    issue = _valid_category(issue)
    severity = _valid_severity(severity)
    address = str(address or "Location not provided").strip()
    today = date.today().isoformat()

    if str(language).lower().startswith(("hi", "hin")):
        issue_hi = _CATEGORY_HI.get(issue, _CATEGORY_HI["unknown"])
        severity_hi = _SEVERITY_HI[severity]
        urgency = _URGENCY_HI[severity]

        return (
            f"विषय: {issue_hi} की समस्या के समाधान हेतु शिकायत\n\n"
            f"दिनांक: {today}\n"
            f"स्थान: {address}\n"
            f"समस्या: {issue_hi}\n"
            f"गंभीरता: {severity_hi}\n\n"
            f"महोदय/महोदया,\n"
            f"उपरोक्त स्थान पर {issue_hi} की समस्या है। "
            f"{urgency} कृपया निरीक्षण करके आवश्यक कार्रवाई करें।\n\n"
            f"धन्यवाद।"
        )

    issue_en = {
        "pothole": "road pothole",
        "open_manhole": "open manhole",
        "unknown": "unknown civic issue requiring review",
    }.get(issue, "civic issue")

    return (
        f"Subject: Complaint regarding {issue_en}\n\n"
        f"Date: {today}\n"
        f"Location: {address}\n"
        f"Issue: {issue_en}\n"
        f"Severity: {severity}\n\n"
        f"Dear Sir/Madam,\n"
        f"I would like to report a {issue_en} at the location mentioned "
        f"above. { _URGENCY_EN[severity] } "
        f"Please inspect the issue and take the necessary action.\n\n"
        f"Thank you."
    )


def _haversine_m(lat1, lon1, lat2, lon2):
    """Calculate the distance between two GPS coordinates in metres."""
    earth_radius_m = 6_371_000

    lat1, lon1, lat2, lon2 = map(
        math.radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    return earth_radius_m * 2 * math.asin(
        min(1.0, math.sqrt(a))
    )


def _text_similarity(first, second):
    """Return a similarity score between 0 and 1."""
    first = str(first or "").strip().lower()
    second = str(second or "").strip().lower()

    if not first or not second:
        return 0.0

    return SequenceMatcher(None, first, second).ratio()



    


def find_duplicate(
    new_text,
    lat,
    lon,
    existing_reports,
    radius_m=50,
    similarity_threshold=0.70,
):
    """Find a similar complaint within the specified distance."""

    lat = _number(lat, float("nan"))
    lon = _number(lon, float("nan"))

    if not math.isfinite(lat) or not math.isfinite(lon):
        return None

    radius_m = max(0.0, _number(radius_m, 50))
    best_match = None
    best_score = -1.0

    for report in existing_reports:
        if not isinstance(report, dict):
            continue

        old_lat = _number(report.get("lat"), float("nan"))
        old_lon = _number(report.get("lon", report.get("lng")), float("nan"))

        if not math.isfinite(old_lat) or not math.isfinite(old_lon):
            continue

        distance = _haversine_m(lat, lon, old_lat, old_lon)

        if distance > radius_m:
            continue

        similarity = _text_similarity(
            new_text,
            report.get("text", report.get("description", "")),
        )

        if similarity < similarity_threshold:
            continue

        score = similarity * 0.6 + (
            1.0 if radius_m == 0 else 1.0 - distance / radius_m
        ) * 0.4

        if score > best_score:
            best_score = score
            best_match = report

    if best_match is None:
        return None

    return best_match.get("id")





def predict_severity(issue, confidence, area_ratio):
    """
    Estimate severity using simple prototype heuristics.

    This is not a trained or validated real-world severity classifier.
    area_ratio is expected to represent a fraction between 0 and 1.
    """
    issue = _valid_category(issue)
    confidence = _confidence(confidence)
    area_ratio = max(0.0, min(1.0, _number(area_ratio)))

    if issue == "unknown":
        return "Medium"

    if issue == "open_manhole":
        # An exposed manhole is potentially hazardous even when small.
        if confidence >= 0.75 or area_ratio >= 0.10:
            return "High"
        if confidence >= 0.40:
            return "Medium"
        return "Low"

    if area_ratio >= 0.20 and confidence >= 0.50:
        return "High"
    if area_ratio >= 0.08 or confidence >= 0.70:
        return "Medium"
    return "Low"


def predict_resolution_days(issue, severity, department):
    """
    Return an illustrative resolution-time estimate in days.

    Values are prototype heuristics, not official municipal deadlines.
    Returns None for unsupported issue categories.
    """
    if issue not in _BASE_DAYS:
        return None

    severity = _valid_severity(severity)
    department = str(department or "").strip()

    base = _BASE_DAYS[issue]
    severity_factor = _SEVERITY_FACTORS[severity]
    department_factor = _DEPARTMENT_FACTORS.get(department, 1.0)

    estimate = base * severity_factor * department_factor
    return max(1, round(estimate))
