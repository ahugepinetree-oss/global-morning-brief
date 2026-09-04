import os
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARCHIVE_DIR = DATA_DIR / "archive"
TODAY_OUT = DATA_DIR / "today.json"
ARCHIVE_INDEX = DATA_DIR / "archive_index.json"

DATA_DIR.mkdir(exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

now = datetime.now(ZoneInfo("Asia/Seoul"))
today_iso = now.strftime("%Y-%m-%d")
today_display = now.strftime("%B %d, %Y").replace(" 0", " ")

schema = {
    "type": "object",
    "properties": {
        "date_iso": {"type": "string"},
        "date_display": {"type": "string"},
        "headline": {"type": "string"},
        "dek": {"type": "string"},
        "read_time": {"type": "string"},
        "story_title": {"type": "string"},
        "story_html": {"type": "string"},
        "b2_summary": {"type": "string"},
        "vocabulary": {
            "type": "array",
            "minItems": 7,
            "maxItems": 10,
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "meaning": {"type": "string"}
                },
                "required": ["term", "meaning"],
                "additionalProperties": False
            }
        },
        "expressions": {
            "type": "array",
            "minItems": 3,
            "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "meaning": {"type": "string"},
                    "example": {"type": "string"},
                    "type": {"type": "string"}
                },
                "required": ["term", "meaning", "example", "type"],
                "additionalProperties": False
            }
        },
        "countries": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "flag": {"type": "string"},
                    "name": {"type": "string"},
                    "focus": {"type": "string"}
                },
                "required": ["flag", "name", "focus"],
                "additionalProperties": False
            }
        },
        "common_theme": {"type": "string"},
        "concept": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "explanation": {"type": "string"}
            },
            "required": ["title", "explanation"],
            "additionalProperties": False
        },
        "quiz": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "options": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {"type": "string"}
                },
                "answer_index": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 2
                },
                "explanation": {"type": "string"}
            },
            "required": ["question", "options", "answer_index", "explanation"],
            "additionalProperties": False
        },
        "one_sentence": {"type": "string"},
        "sources": {
            "type": "array",
            "minItems": 4,
            "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "region": {"type": "string"},
                    "title": {"type": "string"},
                    "url": {"type": "string"}
                },
                "required": ["name", "region", "title", "url"],
                "additionalProperties": False
            }
        }
    },
    "required": [
        "date_iso",
        "date_display",
        "headline",
        "dek",
        "read_time",
        "story_title",
        "story_html",
        "b2_summary",
        "vocabulary",
        "expressions",
        "countries",
        "common_theme",
        "concept",
        "quiz",
        "one_sentence",
        "sources"
    ],
    "additionalProperties": False
}

prompt = f"""
Create today's Global Morning Brief for one Korean adult learner.
Korea date: {today_iso}.

Cover ONLY these four economies:
- United States
- China
- Japan
- South Korea

RESEARCH:
Search recent reputable economic/business news, mainly from the last 24 hours.
Use English, Chinese, Japanese, and Korean sources where useful.
Identify ONE important theme that genuinely connects at least two of the four economies.
Do not invent consensus if the stories differ.
Use only 4-6 sources total.

LEARNING DESIGN:
- Main article: 380-430 words.
- Main article level: natural C1 financial/news English.
- Main article must NOT be simplified to B2.
- B2 summary: 90-120 words, optional support only.
- Vocabulary: 7-10 items.
- Include institutions and economic terms the learner may not know.
- Korean meanings must explain simply first, then technical Korean in parentheses if useful.
- Expressions: 3-4 useful multiword news chunks.
- Explain one economic concept simply.
- One three-option quiz.
- One memorable sentence.

COUNTRY ORDER MUST BE:
1. United States 🇺🇸
2. China 🇨🇳
3. Japan 🇯🇵
4. South Korea 🇰🇷

STYLE:
- Keep all sections concise except the 380-430 word main article.
- Do not copy article sentences.
- Synthesize in original wording.
- story_html should contain 4-6 <p>...</p> paragraphs only.
- read_time should normally be "8 min".
- expression type must be "phrase".
- source URLs must be real pages used in research.
"""

response = client.responses.create(
    model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
    tools=[
        {
            "type": "web_search",
            "search_context_size": "low"
        }
    ],
    input=prompt,
    max_output_tokens=5000,
    text={
        "format": {
            "type": "json_schema",
            "name": "global_morning_brief",
            "strict": True,
            "schema": schema
        }
    }
)

if not response.output_text:
    raise RuntimeError("Structured response returned no output_text")

data = json.loads(response.output_text)

# Force the current Korean date even if the model returns a different date.
data["date_iso"] = today_iso
data["date_display"] = today_display

payload = json.dumps(data, ensure_ascii=False, indent=2)

# Today's live brief
TODAY_OUT.write_text(payload, encoding="utf-8")

# Permanent archive
archive_path = ARCHIVE_DIR / f"{today_iso}.json"
archive_path.write_text(payload, encoding="utf-8")

# Rebuild archive index
archive_items = []

for p in sorted(ARCHIVE_DIR.glob("*.json"), reverse=True):
    try:
        archived = json.loads(p.read_text(encoding="utf-8"))
        archive_items.append({
            "date_iso": archived.get("date_iso", p.stem),
            "date_display": archived.get("date_display", p.stem),
            "headline": archived.get("headline", "Untitled brief"),
            "file": f"data/archive/{p.name}"
        })
    except Exception as exc:
        print(f"Skipping unreadable archive {p.name}: {exc}")

ARCHIVE_INDEX.write_text(
    json.dumps(archive_items, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"Live brief updated: {TODAY_OUT}")
print(f"Archive saved: {archive_path}")
print(f"Archive index updated: {ARCHIVE_INDEX}")
