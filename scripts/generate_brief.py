import os, json, re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "today.json"

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

prompt = f"""
Create today's DAILY GLOBAL ECONOMIC ENGLISH BRIEF for one Korean adult learner.
Korea date: {today}

SCOPE — ONLY FOUR ECONOMIES:
1. United States
2. China
3. Japan
4. South Korea

RESEARCH:
- Search only enough current sources to identify ONE important economic theme connecting at least 2 of the 4 economies.
- Use roughly the last 24 hours where possible.
- Prefer authoritative and major established sources.
- Use English, Chinese, Japanese, and Korean sources where useful.
- Keep the source list to 4-6 pages total.
- Do NOT research the UK or Europe unless briefly necessary for context.
- Do not fabricate a common theme. If today's stories differ, state the strongest real connection.

LEARNING DESIGN:
- Main story: about 380-430 words.
- Writing level: natural C1-quality financial/news English.
- Do NOT simplify the main story to B2.
- Provide a short optional B2 summary of about 90-120 words.
- Choose 7-10 vocabulary items, including economic institutions or terms if a learner may not know them.
- Korean explanations must be plain and easy first; technical Korean may appear in parentheses afterward.
- Choose 3-4 useful multiword news expressions.
- Explain one economic concept simply.
- Include one 3-option quiz.
- Include one memorable sentence from the day's theme.

IMPORTANT COST/TOKEN RULES:
- Be concise outside the 400-word story.
- Country focus: max 12 words per country.
- Source list: max 6 sources.
- Vocabulary meaning: max 30 Korean words each.
- Expression meaning: max 30 Korean words each.
- Concept explanation: max 90 English words.
- Do not include long source summaries.
- Return ONLY valid JSON. No markdown.

JSON schema:
{{
  "date_display": "...",
  "headline": "...",
  "dek": "...",
  "read_time": "8 min",
  "story_title": "...",
  "story_html": "<p>...</p><p>...</p><p>...</p><p>...</p>",
  "b2_summary": "...",
  "vocabulary": [
    {{"term":"...","meaning":"..."}}
  ],
  "expressions": [
    {{"term":"...","meaning":"...","example":"...","type":"phrase"}}
  ],
  "countries": [
    {{"flag":"🇺🇸","name":"United States","focus":"..."}},
    {{"flag":"🇨🇳","name":"China","focus":"..."}},
    {{"flag":"🇯🇵","name":"Japan","focus":"..."}},
    {{"flag":"🇰🇷","name":"South Korea","focus":"..."}}
  ],
  "common_theme":"...",
  "concept": {{
    "title":"...",
    "explanation":"..."
  }},
  "quiz": {{
    "question":"...",
    "options":["...","...","..."],
    "answer_index":0,
    "explanation":"..."
  }},
  "one_sentence":"...",
  "sources": [
    {{"name":"...","region":"...","title":"...","url":"https://..."}}
  ]
}}
"""

resp = client.responses.create(
    model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
    tools=[{
        "type": "web_search",
        "search_context_size": "low"
    }],
    input=prompt,
    max_output_tokens=5000,
)

text = resp.output_text.strip()
text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S)
match = re.search(r"\{.*\}", text, flags=re.S)
if not match:
    raise RuntimeError("No JSON object returned")

data = json.loads(match.group(0))

required = [
    "headline","story_html","b2_summary","vocabulary","expressions",
    "countries","common_theme","concept","quiz","one_sentence","sources"
]
missing = [k for k in required if k not in data]
if missing:
    raise RuntimeError(f"Missing keys: {missing}")

OUT.write_text(
    json.dumps(data, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"Wrote {OUT}")
