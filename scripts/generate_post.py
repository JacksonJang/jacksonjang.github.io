import os
import re
import sys
import json
import yaml
import datetime as dt
from pathlib import Path

from openai import OpenAI
import frontmatter

# ========= Editable defaults =========
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1200"))  # model may ignore
POSTS_DIR = os.getenv("POSTS_DIR", "_posts")              # Jekyll default
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")            # metadata only
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://example.github.io")
# Optional topic config file (if absent, script falls back to defaults)
TOPIC_CONFIG = os.getenv("TOPIC_CONFIG", "scripts/daily_config.yml")
# =====================================

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client:
    print("ERROR: OPENAI_API_KEY is not set.", file=sys.stderr)
    sys.exit(1)


# ---------- Utilities ----------
def today_kst() -> dt.datetime:
    # GitHub Actions runner is UTC; for filename we usually want "today" (UTC).
    # If you want strict KST date in filename, adjust hours (+9).
    # Here we use KST for date stamp to match the user's local publish date.
    return dt.datetime.utcnow() + dt.timedelta(hours=9)


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "post"


def load_topic_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def pick_topic(config: dict) -> dict:
    """
    Structure of daily_config.yml (example):
    ---
    defaults:
      category: "Dev"
      tags: ["automation", "python"]
      primary_keyword: "automation"
    topics:
      - title: "How to Automate Daily Writing with GitHub Actions"
        subtitle: "From idea to published post"
        primary_keyword: "github actions blog"
        tags: ["github", "actions", "blog"]
        category: "Automation"
    """
    if not config:
        return {
            "title": "Automating Daily Writing with GitHub Actions",
            "subtitle": "From idea capture to published post",
            "primary_keyword": "GitHub Actions blog automation",
            "tags": ["automation", "GitHub", "Python"],
            "category": "Automation"
        }

    defaults = config.get("defaults", {}) or {}
    topics = config.get("topics", []) or []

    if topics:
        # Simple rotation: pick by day of year
        idx = (today_kst().timetuple().tm_yday - 1) % len(topics)
        chosen = topics[idx]
    else:
        # Only defaults exist
        chosen = {}

    return {
        "title": chosen.get("title") or "Daily Tech Notes",
        "subtitle": chosen.get("subtitle") or "Practical notes for busy builders",
        "primary_keyword": chosen.get("primary_keyword") or defaults.get("primary_keyword") or "software productivity",
        "tags": chosen.get("tags") or defaults.get("tags") or ["notes", "dev"],
        "category": chosen.get("category") or defaults.get("category") or "Notes",
    }


# ---------- Prompting ----------
def build_prompt(title: str, subtitle: str, keyword: str) -> str:
    return f"""
You are a concise, practical technical writer for a personal dev blog (GitHub Pages).
Write a Markdown blog post in English that feels friendly and expert, optimized for SEO around the primary keyword: "{keyword}".

Constraints:
- Target length: 600–900 words.
- Use clear section headings (##), short paragraphs, and bullet lists where helpful.
- Include 3–5 specific code or command snippets if relevant.
- Start with a one-paragraph hook (2–3 sentences), no heading.
- End with a brief "Takeaways" section using bullets.
- Avoid fluffy filler and avoid hallucinating facts or APIs.
- No self-promotion, no generic “as an AI model” phrasing.

Blog meta:
- Title: {title}
- Subtitle: {subtitle}
- Primary keyword: {keyword}

Tone:
- Clear, actionable, slightly playful but professional.
- Assume readers are developers with limited time.

Now produce only the Markdown body (no YAML front matter).
    """.strip()


def generate_body(title: str, subtitle: str, keyword: str) -> str:
    prompt = build_prompt(title, subtitle, keyword)
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": "You write crisp, accurate technical posts."},
            {"role": "user", "content": prompt},
        ],
    )
    content = resp.choices[0].message.content or ""
    return content.strip()


# ---------- File writers ----------
def build_front_matter(meta: dict, body: str) -> frontmatter.Post:
    """
    Returns a frontmatter.Post with YAML FM and Markdown content.
    Jekyll expects at least: layout, title, date.
    """
    post = frontmatter.Post(body)
    # minimal set
    post["layout"] = meta.get("layout", "post")
    post["title"] = meta["title"]
    post["subtitle"] = meta["subtitle"]
    post["date"] = meta["date_iso"]
    post["tags"] = meta.get("tags", [])
    post["categories"] = [meta.get("category", "Notes")]
    post["canonical_url"] = meta.get("canonical_url")
    post["lang"] = meta.get("lang", "en")
    post["timezone"] = TIMEZONE
    # Optional SEO
    post["description"] = meta.get("description") or meta["subtitle"]
    post["keywords"] = meta.get("keywords") or meta.get("tags") or []
    return post


def write_post_file(meta: dict, body_md: str) -> Path:
    ensure_dir(Path(POSTS_DIR))

    date = meta["date_obj"]
    slug = slugify(meta["title"])
    filename = f"{date.strftime('%Y-%m-%d')}-{slug}{OUTPUT_EXT}"
    out_path = Path(POSTS_DIR) / filename

    post = build_front_matter(meta, body_md)
    with out_path.open("w", encoding="utf-8") as f:
        frontmatter.dump(post, f, sort_keys=False)

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
    category = topic.get("category", "Notes")

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
        "keywords": [primary_kw] + tags if primary_kw not in tags else tags,
        "description": subtitle,
    }

    # 3) Generate body
    print(f"[generate_post] model={MODEL_NAME}, temp={TEMPERATURE}, title='{title}'")
    body_md = generate_body(title, subtitle, primary_kw)

    if not body_md or len(body_md.split()) < 50:
        print("WARNING: Generated body seems too short. Will still write the file.", file=sys.stderr)

    # 4) Write file
    out_path = write_post_file(meta, body_md)
    print(f"[generate_post] Wrote: {out_path}")

    # 5) Print minimal JSON for logs
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