import os, json, re, sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "today.json"
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
prompt = f"""
You create a DAILY GLOBAL ECONOMIC ENGLISH BRIEF for one Korean adult learner.
Date in Korea: {today}.

RESEARCH:
Search the web for major economic/business developments from roughly the last 24 hours.
Cover the United States, United Kingdom, Euro area/Europe, Japan, China, and South Korea.
Actively use credible sources in English, Japanese, Chinese, and Korean where useful.
Prefer primary/authoritative sources and major established financial/news organizations.
Identify ONE cross-market or globally important theme that is genuinely prominent today.
Do not fabricate consensus. If countries are focused on different things, explain the strongest connecting theme carefully.

LEARNING DESIGN:
- Main brief should be original, natural C1-quality financial/news English, NOT simplified B2 English.
- Do not copy article wording. Synthesize in your own wording.
- Provide a short B2 help summary only as optional support.
- Choose 7-10 vocabulary items the learner may plausibly not know, INCLUDING economic institutions/terms even if common to experts.
- Korean meanings must be plain-language first, then technical Korean in parentheses only if useful. Avoid unexplained translations like "차입 비용".
- Choose 3-5 useful multiword news expressions/chunks.
- Explain one economic concept simply in Korean-friendly English.
- One quiz and one memorable sentence.
- Source list: 6-12 real source pages used, with name, region, article title, URL.

Return ONLY one valid JSON object. No markdown fences.
Schema:
{{
 "date_display": "...",
 "headline": "...",
 "dek": "...",
 "read_time": "8 min",
 "story_title": "...",
 "story_html": "<p>...</p><p>...</p>",
 "b2_summary": "...",
 "vocabulary":[{{"term":"...","meaning":"..."}}],
 "expressions":[{{"term":"...","meaning":"...","example":"...","type":"phrase"}}],
 "countries":[
   {{"flag":"🇺🇸","name":"United States","focus":"..."}},
   {{"flag":"🇬🇧","name":"United Kingdom","focus":"..."}},
   {{"flag":"🇪🇺","name":"Europe","focus":"..."}},
   {{"flag":"🇯🇵","name":"Japan","focus":"..."}},
   {{"flag":"🇨🇳","name":"China","focus":"..."}},
   {{"flag":"🇰🇷","name":"South Korea","focus":"..."}}
 ],
 "common_theme":"...",
 "concept":{{"title":"...","explanation":"..."}},
 "quiz":{{"question":"...","options":["...","...","..."],"answer_index":0,"explanation":"..."}},
 "one_sentence":"...",
 "sources":[{{"name":"...","region":"...","title":"...","url":"https://..."}}]
}}
"""

resp = client.responses.create(
    model=os.getenv("OPENAI_MODEL", "gpt-5.6-terra"),
    tools=[{"type":"web_search"}],
    input=prompt,
)
text = resp.output_text.strip()
text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I|re.S)
m = re.search(r"\{.*\}", text, flags=re.S)
if not m:
    print(text)
    raise RuntimeError("No JSON object returned")
data = json.loads(m.group(0))

required = ["headline","story_html","vocabulary","expressions","countries","common_theme","quiz","sources"]
missing = [k for k in required if k not in data]
if missing:
    raise RuntimeError(f"Missing keys: {missing}")

OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {OUT}")
