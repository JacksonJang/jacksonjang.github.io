import os
import re
import random
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import frontmatter

# --- OpenAI (v0 스타일) ---
# pip install openai
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# -----------------------------
# 유틸
# -----------------------------
def to_slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)     # 특수문자 제거
    s = re.sub(r"\s+", "-", s)         # 공백 -> 하이픈
    s = re.sub(r"-+", "-", s)          # 연속 하이픈 -> 하나
    return s

def choose_keyword(date_seed: str) -> dict:
    """
    날짜 기반으로 안정적으로 키워드 선택 (매일 다른 주제)
    """
    pool = [
        {"cat": "English", "tagset": ["English", "Expressions", "Daily Conversation"], "kw": "daily native English expressions"},
        {"cat": "Business English", "tagset": ["English", "Business", "Email"], "kw": "email expressions for work"},
        {"cat": "Travel", "tagset": ["English", "Travel", "Airport"], "kw": "English phrases at the airport"},
        {"cat": "Meetings", "tagset": ["English", "Meetings", "Office"], "kw": "useful English phrases for meetings"},
        {"cat": "Feelings", "tagset": ["English", "Idioms", "Feelings"], "kw": "English idioms for emotions"},
        {"cat": "Casual Talk", "tagset": ["English", "Slang", "Casual"], "kw": "casual English phrases with examples"},
        {"cat": "Phone", "tagset": ["English", "Phone", "Conversation"], "kw": "phone call expressions in English"},
        {"cat": "Restaurant", "tagset": ["English", "Restaurant", "Ordering"], "kw": "ordering food in English phrases"},
    ]
    # 날짜 문자열을 시드로 사용해 매일 같은 선택이 되게 함
    rnd = random.Random(date_seed)
    return rnd.choice(pool)

# -----------------------------
# 본문 생성 프롬프트
# -----------------------------
def build_prompt(title: str, subtitle: str, keyword: str):
    return f"""
You are writing an SEO-optimized blog post for a GitHub Pages (Jekyll) site.
TITLE: {title}
SUBTITLE: {subtitle}
PRIMARY KEYWORD: {keyword}

Write ONLY the markdown **body** (no front matter).
Rules:
- One friendly intro (50–80 words).
- Then 5 sections (H2 level) each for ONE expression:
  - H2: the expression (in quotes)
  - 2–3 sentence explanation (concise, practical)
  - 1–2 example lines in blockquote style
  - A **Korean translation line** like: **Korean:** …
- Use simple, natural, everyday English.
- Keep it helpful for Korean learners.
- Use <br /> between big blocks to improve readability.
- End with a short, encouraging conclusion.

Tone: warm, practical, native-like.
"""

# -----------------------------
# 본문 생성 (OpenAI)
# -----------------------------
def generate_body(title: str, subtitle: str, keyword: str) -> str:
    prompt = build_prompt(title, subtitle, keyword)

    # gpt-4o-mini 예시 (기존 Actions 예제와 호환)
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp["choices"][0]["message"]["content"].strip()

# -----------------------------
# 메인 생성기
# -----------------------------
def main():
    # 한국 시간 기준
    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
    date_ymd = now_kst.strftime("%Y-%m-%d")
    date_full = now_kst.strftime("%Y-%m-%d %H:%M:%S")

    # 키워드/카테고리/태그 선택
    pick = choose_keyword(date_ymd)
    category = pick["cat"]
    tags = pick["tagset"]
    primary_kw = pick["kw"]

    # 제목/부제목
    title = f"[English Expression] 5 Essential Daily Phrases You Should Know"
    # 원하는 경우 날짜를 제목에 노출하려면 아래로 교체:
    # title = f"[English Expression] 5 Essential Phrases ({date_ymd})"
    subtitle = "Sound like a native speaker with these simple yet powerful expressions"

    # 파일/에셋 경로
    post_assets = f"/assets/posts/{date_ymd}"
    # 파일명용 슬러그 (날짜 + 주제)
    basename = f"{date_ymd}-daily-english-expression"
    slug = to_slug(basename)

    # 본문 생성
    body_md = generate_body(title, subtitle, primary_kw)

    # Front Matter 구성 (요청 양식 그대로)
    fm = {
        "layout": "post",
        "title": title,
        "subtitle": subtitle,
        "date": date_full,
        "author": "JacksonJang",
        "post_assets": post_assets,
        "catalog": True,
        "categories": [category],
        "tags": tags,
    }

    # 포스트 객체 생성
    post = frontmatter.Post(body_md, **fm)

    # 저장 경로: _posts/auto/YYYY-MM-DD-xxx.md
    out_dir = Path("_posts/auto")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.md"

    with open(out_path, "w", encoding="utf-8") as f:
        frontmatter.dump(post, f)

    print(f"✅ Auto post created: {out_path}")

if __name__ == "__main__":
    """
    GitHub Actions 예시와 함께 사용 가정:
      - env: OPENAI_API_KEY
      - pip: openai, python-frontmatter
    """
    main()
