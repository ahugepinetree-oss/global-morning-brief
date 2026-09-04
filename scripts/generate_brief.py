import os, json, re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARCHIVE_DIR = DATA_DIR / "archive"
DATA_DIR.mkdir(exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
now = datetime.now(ZoneInfo("Asia/Seoul"))
today = now.strftime("%Y-%m-%d")
display = now.strftime("%B %d, %Y").replace(" 0", " ")

prompt = f'''
Create today's global economic English brief for a Korean adult learner.
Date: {today}

Cover ONLY: United States, China, Japan, South Korea.
Find ONE important theme connecting at least two of them using current reputable sources from roughly the last 24 hours.
Use English, Chinese, Japanese, and Korean sources where useful.
Main story: 380-430 words, natural C1 financial/news English.
Also provide: optional B2 summary 90-120 words, 7-10 vocabulary items with plain Korean explanations, 3-4 multiword news expressions, one simple economic concept, one 3-option quiz, one memorable sentence, and 4-6 sources.
Keep everything concise outside the main story.
Return ONLY valid JSON.

Schema:
{{
"date_iso":"{today}",
"date_display":"{display}",
"headline":"...",
"dek":"...",
"read_time":"8 min",
"story_title":"...",
"story_html":"<p>...</p><p>...</p><p>...</p><p>...</p>",
"b2_summary":"...",
"vocabulary":[{{"term":"...","meaning":"..."}}],
"expressions":[{{"term":"...","meaning":"...","example":"...","type":"phrase"}}],
"countries":[
{{"flag":"🇺🇸","name":"United States","focus":"..."}},
{{"flag":"🇨🇳","name":"China","focus":"..."}},
{{"flag":"🇯🇵","name":"Japan","focus":"..."}},
{{"flag":"🇰🇷","name":"South Korea","focus":"..."}}
],
"common_theme":"...",
"concept":{{"title":"...","explanation":"..."}},
"quiz":{{"question":"...","options":["...","...","..."],"answer_index":0,"explanation":"..."}},
"one_sentence":"...",
"sources":[{{"name":"...","region":"...","title":"...","url":"https://..."}}]
}}
'''

resp = client.responses.create(
    model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
    tools=[{"type":"web_search","search_context_size":"low"}],
    input=prompt,
    max_output_tokens=5000,
)

text = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", resp.output_text.strip(), flags=re.I|re.S)
m = re.search(r"\\{.*\\}", text, flags=re.S)
if not m:
    raise RuntimeError("No JSON object returned")
data = json.loads(m.group(0))
data["date_iso"] = today
data["date_display"] = data.get("date_display") or display

payload = json.dumps(data, ensure_ascii=False, indent=2)
(DATA_DIR / "today.json").write_text(payload, encoding="utf-8")
(ARCHIVE_DIR / f"{today}.json").write_text(payload, encoding="utf-8")

items = []
for p in sorted(ARCHIVE_DIR.glob("*.json"), reverse=True):
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        items.append({
            "date_iso": d.get("date_iso", p.stem),
            "date_display": d.get("date_display", p.stem),
            "headline": d.get("headline", "Untitled brief"),
            "file": f"data/archive/{p.name}",
        })
    except Exception:
        pass

(DATA_DIR / "archive_index.json").write_text(
    json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("Updated today.json, dated archive, and archive_index.json")
