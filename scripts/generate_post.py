import os
import re
import sys
import json
import yaml
import time
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import urlopen, Request
from urllib.parse import quote
import xml.etree.ElementTree as ET

from openai import OpenAI
import frontmatter

# ========= Editable defaults =========
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5")
FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
TEMPERATURE = 1.0  # gpt-5 only supports 1.0
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1400"))
POSTS_DIR = os.getenv("POSTS_DIR", "_posts/auto")
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://jacksonjang.github.io")
TOPIC_CONFIG = os.getenv("TOPIC_CONFIG", "scripts/daily_config.yml")
MIN_WORDS = int(os.getenv("MIN_WORDS", "650"))
INTERNAL_LINKS_COUNT = int(os.getenv("INTERNAL_LINKS_COUNT", "3"))

# News options (환경변수로 커스터마이즈 가능)
NEWS_LOOKBACK_HOURS = int(os.getenv("NEWS_LOOKBACK_HOURS", "72"))
NEWS_MAX_ITEMS = int(os.getenv("NEWS_MAX_ITEMS", "50"))

# 기본 RSS 목록 (API 키 불필요)
DEFAULT_NEWS_FEEDS = [
    "https://feeds.reuters.com/reuters/topNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    # Google News 글로벌 Top (영문). 지역/언어 바꾸고 싶으면 NID 인자 생략하고 hl, gl만 사용
    f"https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
]
USER_NEWS_FEEDS = [u for u in (os.getenv("NEWS_FEEDS", "").split(",")) if u.strip()]
NEWS_FEEDS = USER_NEWS_FEEDS or DEFAULT_NEWS_FEEDS
# =====================================

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client:
    print("ERROR: OPENAI_API_KEY is not set.", file=sys.stderr)
    sys.exit(1)


# ---------- Utilities ----------
def today_kst() -> dt.datetime:
    return dt.datetime.now(ZoneInfo("Asia/Seoul"))

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
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
            canonical = post.get("canonical_url")
            if not canonical:
                stem = f.stem  # YYYY-MM-DD-slug
                try:
                    y, m, d, *_ = stem.split("-")
                    slug = "-".join(stem.split("-")[3:])
                    canonical = f"{SITE_BASE_URL}/{y}/{m}/{d}/{slug}/"
                except Exception:
                    canonical = SITE_BASE_URL
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


# ---------- News fetchers ----------
def _http_get(url: str, timeout=10) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (DailyPostBot)"})
    with urlopen(req, timeout=timeout) as r:
        return r.read()

def _parse_rss(xml_bytes: bytes) -> list:
    """
    Returns list of dicts: {title, link, published_ts}
    """
    out = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return out

    # RSS items live under channel/item
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        ts = _parse_pubdate(pub)
        if title and link:
            out.append({"title": title, "link": link, "published_ts": ts})
    return out

def _parse_pubdate(pubdate: str) -> float:
    # Try common RFC822-like formats; fallback to now
    try:
        # Example: Tue, 28 Oct 2025 09:34:00 GMT
        from email.utils import parsedate_to_datetime
        dt_obj = parsedate_to_datetime(pubdate)
        return dt_obj.timestamp()
    except Exception:
        return time.time()

def fetch_trending_news(feeds: list, lookback_hours: int, max_items: int) -> list:
    cutoff = time.time() - lookback_hours * 3600
    pool = []
    for url in feeds:
        try:
            xml_bytes = _http_get(url)
            items = _parse_rss(xml_bytes)
            for it in items:
                if it["published_ts"] >= cutoff:
                    pool.append(it)
        except Exception:
            continue
    # 정렬: 최신순
    pool.sort(key=lambda x: x["published_ts"], reverse=True)
    return pool[:max_items]

def choose_news_topic(news_items: list) -> dict | None:
    """
    Deterministically choose one item by day-of-year to keep daily stability.
    """
    if not news_items:
        return None
    idx = (today_kst().timetuple().tm_yday - 1) % len(news_items)
    chosen = news_items[idx]
    headline = _clean_headline(chosen["title"])
    link = chosen["link"]
    # ESL 주제 메타 구성
    return {
        "title": f"Talking About: {headline}",
        "subtitle": "Practical English for discussing today’s news (no fluff, just useful phrases)",
        "primary_keyword": f"english phrases about {headline.lower()}",
        "tags": ["english", "news", "phrases", "real-world"],
        "category": "English",
        "news_headline": headline,
        "news_link": link
    }

def _clean_headline(h: str) -> str:
    # 괄호나 매체명, 너무 긴 꼬리 제거
    h = re.sub(r"\s*-\s*[A-Za-z0-9 .,'’“”&]+$", "", h)      # " - Reuters" 꼬리 제거
    h = re.sub(r"\s*\|.*$", "", h)                           # " | BBC News" 꼬리 제거
    h = re.sub(r"\s*\(.*?\)\s*$", "", h)                     # 말미 괄호 제거
    return h.strip()[:120]


# ---------- Prompting ----------
def build_prompt(title: str, subtitle: str, keyword: str, internal_links: list, news_meta: dict | None) -> str:
    links_md = ""
    if internal_links:
        links_md = "\n".join([f"- [{it['title']}]({it['url']})" for it in internal_links[:INTERNAL_LINKS_COUNT]])

    news_context = ""
    if news_meta:
        # 뉴스 텍스트를 직접 인용하지 말고 '주제'로만 활용하도록 분명히 지시
        news_context = f"""
Context (do NOT quote any article; paraphrase broadly):
- Today’s theme: "{news_meta.get('news_headline','')}"
- Reference link (for background only, do not quote): {news_meta.get('news_link','')}
"""

    return f"""
You are a crisp, practical ESL content writer for a GitHub Pages blog.
Write in **English** only. Optimize for the primary SEO keyword: "{keyword}".

{news_context}

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
- Avoid fake facts. Do not quote or reproduce news text verbatim; keep it generic.

Metadata:
- Title: {title}
- Subtitle: {subtitle}

If helpful, add a small table (Markdown) comparing 3–5 similar phrases.

""".strip()


def _extract_text_from_response(resp) -> str:
    # Responses API (new)
    try:
        text = (getattr(resp, "output_text", None) or "").strip()
        if text:
            return text
        if hasattr(resp, "output") and resp.output:
            parts = []
            for block in resp.output:
                for c in getattr(block, "content", []) or []:
                    if getattr(c, "type", "") == "output_text" and getattr(c, "text", ""):
                        parts.append(c.text)
            joined = "\n".join(parts).strip()
            if joined:
                return joined
    except Exception:
        pass
    # Chat Completions
    try:
        if hasattr(resp, "choices") and resp.choices:
            msg = resp.choices[0].message
            if hasattr(msg, "content"):
                return (msg.content or "").strip()
    except Exception:
        pass
    return ""


def _call_responses(prompt: str, model: str, temperature: float):
    # Try Responses API with flexible kwargs for SDK variations
    try:
        # Prefer max_output_tokens name; if TypeError, caller will retry with alt params
        return client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
            max_output_tokens=MAX_TOKENS,
        )
    except TypeError:
        # Some SDKs use max_tokens instead
        return client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
            max_tokens=MAX_TOKENS,
        )


def _call_chat(prompt: str, model: str, temperature: float):
    # Fallback to Chat Completions API
    try:
        return client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": "You write clear, accurate ESL posts that feel helpful, modern, and concise."},
                {"role": "user", "content": prompt},
            ],
        )
    except TypeError:
        # Very old SDKs might not accept temperature/max_tokens; try minimal
        return client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You write clear, accurate ESL posts that feel helpful, modern, and concise."},
                {"role": "user", "content": prompt},
            ],
        )


def call_openai(prompt: str, model=MODEL_NAME, temperature=TEMPERATURE, max_retries=4) -> str:
    delay = 3
    active_model = model
    active_temp = temperature
    for attempt in range(max_retries):
        try:
            # Try Responses API first
            try:
                resp = _call_responses(prompt, active_model, active_temp)
            except Exception:
                # If Responses API not available/compatible, try Chat Completions
                resp = _call_chat(prompt, active_model, active_temp)
            text = _extract_text_from_response(resp)
            if not text:
                raise RuntimeError("empty_output_text")
            return text
        except Exception as e:
            msg = str(e).lower()
            # resilient backoff + model fallback
            if any(key in msg for key in ["rate", "429", "quota", "empty_output_text", "unsupported_value", "timeout"]):
                time.sleep(delay)
                delay = min(delay * 2, 30)
                if attempt >= max_retries // 2 and active_model != FALLBACK_MODEL:
                    active_model = FALLBACK_MODEL
                    active_temp = 0.7  # fallback 모델은 자유롭게 온도 사용
                continue
            raise


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
    # 뉴스 출처(참고용 링크) 추가 - 템플릿에 따라 표시하지 않을 수도 있음
    if meta.get("news_link"):
        post["source_link"] = meta["news_link"]
    if meta.get("news_headline"):
        post["source_title"] = meta["news_headline"]
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


# ---------- Topic selection ----------
def pick_topic_from_config_or_builtin(config: dict) -> dict:
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


# ---------- Main ----------
def main():
    config = load_topic_config(TOPIC_CONFIG)

    # 1) 뉴스에서 주제 선택 (우선 시도)
    news_items = fetch_trending_news(NEWS_FEEDS, NEWS_LOOKBACK_HOURS, NEWS_MAX_ITEMS)
    topic = choose_news_topic(news_items)

    # 2) 실패 시 config/builtin에서 선택
    if not topic:
        topic = pick_topic_from_config_or_builtin(config)

    now_kst = today_kst()

    internal_links = list_recent_posts(12)

    # 메타 구성
    meta = {
        "title": topic["title"],
        "subtitle": topic["subtitle"],
        "primary_keyword": topic["primary_keyword"],
        "tags": topic.get("tags", []),
        "category": topic.get("category", "English"),
        "date_obj": now_kst,
        "date_iso": now_kst.strftime("%Y-%m-%d %H:%M:%S %z").strip(),
        "canonical_url": f"{SITE_BASE_URL}/{now_kst.strftime('%Y')}/{now_kst.strftime('%m')}/{now_kst.strftime('%d')}/{slugify(topic['title'])}/",
        "lang": "en",
        "keywords": [topic["primary_keyword"]] + [t for t in topic.get("tags", []) if t != topic["primary_keyword"]],
        "description": topic["subtitle"],
        # 뉴스 정보(있다면)
        "news_link": topic.get("news_link"),
        "news_headline": topic.get("news_headline"),
    }

    print(f"[generate_post] model={MODEL_NAME}, temp={TEMPERATURE}, title='{meta['title']}'")

    # 본문 생성
    prompt = build_prompt(meta["title"], meta["subtitle"], meta["primary_keyword"], internal_links, topic if topic.get("news_headline") else None)
    body_md = call_openai(prompt)

    # 길이 점검 + 폴백
    too_short = (not body_md) or (len(body_md.split()) < MIN_WORDS)
    if too_short:
        print("WARNING: Generated body seems too short. Retrying with fallback...", file=sys.stderr)
        body_md = call_openai(prompt, model=FALLBACK_MODEL, temperature=0.7)
        if (not body_md) or (len(body_md.split()) < MIN_WORDS):
            pk = meta["primary_keyword"]
            body_md = f"""\
**Temporary note**: Generation failed today. Here’s a short outline so the page isn’t empty.

## Meaning & Nuance
- A post about "{pk}" will be here.

## Top Alternatives
- Coming soon.

## Mini Dialogue
- A: …
- B: …

## Takeaways
- …
"""

    out_path = write_post_file(meta, body_md)
    print(f"[generate_post] Wrote: {out_path}")
    print(json.dumps({
        "file": str(out_path),
        "title": meta["title"],
        "tags": meta["tags"],
        "category": meta["category"],
        "news_headline": meta.get("news_headline"),
        "news_link": meta.get("news_link"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[generate_post] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
