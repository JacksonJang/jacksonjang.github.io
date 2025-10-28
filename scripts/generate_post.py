import os
import re
import sys
import json
import yaml
import time
import random
import datetime as dt
from pathlib import Path

from openai import OpenAI
import frontmatter

# ========= Editable defaults =========
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5")
FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
TEMPERATURE = 1.0
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1400"))
POSTS_DIR = os.getenv("POSTS_DIR", "_posts")              # Jekyll default
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://jacksonjang.github.io")
TOPIC_CONFIG = os.getenv("TOPIC_CONFIG", "scripts/daily_config.yml")
MIN_WORDS = 450  # 안전 하한
INTERNAL_LINKS_COUNT = 3
# =====================================

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client:
    print("ERROR: OPENAI_API_KEY is not set.", file=sys.stderr)
    sys.exit(1)


# ---------- Utilities ----------
def today_kst() -> dt.datetime:
    return dt.datetime.utcnow() + dt.timedelta(hours=9)

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "post"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def list_recent_posts(n=10):
    p = Path(POSTS_DIR)
    if not p.exists():
        return []
    files = sorted(p.glob(f"*{OUTPUT_EXT}"), reverse=True)
    items = []
    for f in files[:n]:
        try:
            post = frontmatter.load(f)
            title = post.get("title")
            date_str = post.get("date")
            if not title or not date_str:
                continue
            # Canonical URL이 있으면 사용, 없으면 추정
            canonical = post.get("canonical_url")
            if not canonical:
                # from filename: YYYY-MM-DD-slug.ext
                stem = f.stem
                y, m, d, *_ = stem.split("-")
                slug = "-".join(stem.split("-")[3:])
                canonical = f"{SITE_BASE_URL}/{y}/{m}/{d}/{slug}/"
            items.append({"title": title, "url": canonical})
        except Exception:
            continue
    return items

def load_topic_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data

def pick_topic(config: dict) -> dict:
    """
    daily_config.yml (optional)
    ---
    defaults:
      category: "English"
      tags: ["English", "Expressions"]
      primary_keyword: "natural English expressions"
    topics:
      - title: "10 Better Ways to Say 'I'm tired'"
        subtitle: "Sound natural, not textbook"
        primary_keyword: "ways to say i'm tired"
        tags: ["english", "alternatives", "speaking"]
        category: "English"
    """
    # Built-in rotation buckets if config is missing/empty
    builtin = [
        {
            "title": "10 Better Ways to Say “I’m sorry”",
            "subtitle": "Natural apologies for real life",
            "primary_keyword": "ways to say i'm sorry",
            "tags": ["english", "alternatives", "apologizing"],
            "category": "English"
        },
        {
            "title": "Stop Saying “Very” — 25 Stronger Words",
            "subtitle": "Sound concise and confident",
            "primary_keyword": "alternatives to very",
            "tags": ["english", "vocabulary", "concise"],
            "category": "English"
        },
        {
            "title": "‘I think’ Alternatives for Polite Opinions",
            "subtitle": "Soften your tone without sounding weak",
            "primary_keyword": "i think alternatives",
            "tags": ["english", "speaking", "politeness"],
            "category": "English"
        },
        {
            "title": "‘I’m busy’—Natural Ways to Decline",
            "subtitle": "Stay friendly while saying no",
            "primary_keyword": "polite ways to say no",
            "tags": ["english", "phrases", "polite"],
            "category": "English"
        },
    ]

    defaults = (config.get("defaults") or {})
    topics = (config.get("topics") or []) or builtin
    idx = (today_kst().timetuple().tm_yday - 1) % len(topics)
    chosen = topics[idx]

    return {
        "title": chosen.get("title") or "Daily English Expressions",
        "subtitle": chosen.get("subtitle") or "Natural, concise, modern",
        "primary_keyword": chosen.get("primary_keyword") or defaults.get("primary_keyword") or "english expressions",
        "tags": chosen.get("tags") or defaults.get("tags") or ["english", "expressions"],
        "category": chosen.get("category") or defaults.get("category") or "English",
    }


# ---------- Prompting ----------
def build_prompt(title: str, subtitle: str, keyword: str, internal_links: list) -> str:
    links_md = ""
    if internal_links:
        links_md = "\n".join([f"- [{it['title']}]({it['url']})" for it in internal_links[:INTERNAL_LINKS_COUNT]])

    return f"""
You are a crisp, practical ESL content writer for a GitHub Pages blog.
Write in **English** only. Optimize for the primary SEO keyword: "{keyword}".

Constraints:
- 700–1000 words; tight sentences; developer-friendly tone (no fluff).
- Structure (use H2/###):
  - Hook (2–3 sentences, no heading)
  - ## Meaning & Nuance
  - ## Top Alternatives (10–25 items)
    - bullet list, each with a one-line use-case and a **short example sentence**
  - ## Mini Dialogue (6–8 turns, natural, casual)
  - ## Common Mistakes (Don’t say… → Say…)
  - ## Quick Q&A (2–3 concise Q&As that include the keyword naturally)
  - ## Takeaways (3–5 bullets)
- Avoid fake facts. No self-references.

Metadata:
- Title: {title}
- Subtitle: {subtitle}

If helpful, add a small table (Markdown) comparing 3–5 similar phrases.
At the end, add this section verbatim if list is non-empty:

## Further reading
{links_md}
    """.strip()


def call_openai(messages, model=MODEL_NAME, temperature=TEMPERATURE, max_retries=4):
    delay = 3
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=messages,
                max_tokens=MAX_TOKENS
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            msg = str(e).lower()
            if "insufficient_quota" in msg or "rate" in msg or "429" in msg:
                time.sleep(delay)
                delay = min(delay * 2, 30)
                # simple fallback once we hit half of retries
                if attempt >= max_retries // 2 and model != FALLBACK_MODEL:
                    model = FALLBACK_MODEL
                    temperature = 0.7  # fallback model 보통 허용
                continue
            raise

def generate_body(title: str, subtitle: str, keyword: str, internal_links: list) -> str:
    prompt = build_prompt(title, subtitle, keyword, internal_links)
    messages = [
        {"role": "system", "content": "You write clear, accurate ESL posts that feel helpful, modern, and concise."},
        {"role": "user", "content": prompt},
    ]
    content = call_openai(messages)
    return content


# ---------- File writers ----------
def build_front_matter(meta: dict, body: str) -> frontmatter.Post:
    post = frontmatter.Post(body)
    post["layout"] = meta.get("layout", "post")
    post["title"] = meta["title"]
    post["subtitle"] = meta["subtitle"]
    post["date"] = meta["date_iso"]
    post["tags"] = meta.get("tags", [])
    post["categories"] = [meta.get("category", "English")]
    post["canonical_url"] = meta.get("canonical_url")
    post["lang"] = "en"
    post["timezone"] = TIMEZONE
    post["description"] = meta.get("description") or meta["subtitle"]
    post["keywords"] = meta.get("keywords") or meta.get("tags") or []
    return post

def unique_out_path(title: str, date: dt.datetime) -> Path:
    ensure_dir(Path(POSTS_DIR))
    slug = slugify(title)
    base = Path(POSTS_DIR) / f"{date.strftime('%Y-%m-%d')}-{slug}{OUTPUT_EXT}"
    if not base.exists():
        return base
    i = 2
    while True:
        cand = Path(POSTS_DIR) / f"{date.strftime('%Y-%m-%d')}-{slug}-{i}{OUTPUT_EXT}"
        if not cand.exists():
            return cand
        i += 1

def write_post_file(meta: dict, body_md: str) -> Path:
    out_path = unique_out_path(meta["title"], meta["date_obj"])
    post = build_front_matter(meta, body_md)
    text = frontmatter.dumps(post, sort_keys=False)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(text)
    return out_path


# ---------- Main ----------
def main():
    # 1) Load topic
    config = load_topic_config(TOPIC_CONFIG)
    topic = pick_topic(config)

    # 2) Build meta
    now_kst = today_kst()
    title = topic["title"]
    subtitle = topic["subtitle"]
    primary_kw = topic["primary_keyword"]
    tags = topic.get("tags", [])
    category = topic.get("category", "English")

    # internal links (last posts)
    internal_links = list_recent_posts(12)

    meta = {
        "title": title,
        "subtitle": subtitle,
        "primary_keyword": primary_kw,
        "tags": tags,
        "category": category,
        "date_obj": now_kst,
        "date_iso": now_kst.strftime("%Y-%m-%d %H:%M:%S %z").strip(),
        "canonical_url": f"{SITE_BASE_URL}/{now_kst.strftime('%Y')}/{now_kst.strftime('%m')}/{now_kst.strftime('%d')}/{slugify(title)}/",
        "lang": "en",
        "keywords": [primary_kw] + [t for t in tags if t != primary_kw],
        "description": subtitle,
    }

    # 3) Generate body
    print(f"[generate_post] model={MODEL_NAME}, temp={TEMPERATURE}, title='{title}'")
    body_md = generate_body(title, subtitle, primary_kw, internal_links)

    # 4) Basic sanity check
    if not body_md or len(body_md.split()) < MIN_WORDS:
        print("WARNING: Generated body seems too short.", file=sys.stderr)

    # 5) Write file
    out_path = write_post_file(meta, body_md)
    print(f"[generate_post] Wrote: {out_path}")

    # 6) CI logs
    print(json.dumps({
        "file": str(out_path),
        "title": title,
        "tags": tags,
        "category": category
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[generate_post] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
