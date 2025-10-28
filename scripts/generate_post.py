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
import xml.etree.ElementTree as ET

from openai import OpenAI
import frontmatter

# ========= Editable defaults =========
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5")
FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
TEMPERATURE = 1.0  # gpt-5 only supports 1.0
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1400"))
POSTS_DIR = os.getenv("POSTS_DIR", "_posts")
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://jacksonjang.github.io")
TOPIC_CONFIG = os.getenv("TOPIC_CONFIG", "scripts/daily_config.yml")
MIN_WORDS = int(os.getenv("MIN_WORDS", "650"))
INTERNAL_LINKS_COUNT = int(os.getenv("INTERNAL_LINKS_COUNT", "3"))

# News options
NEWS_LOOKBACK_HOURS = int(os.getenv("NEWS_LOOKBACK_HOURS", "72"))
NEWS_MAX_ITEMS = int(os.getenv("NEWS_MAX_ITEMS", "50"))
DEFAULT_NEWS_FEEDS = [
    "https://feeds.reuters.com/reuters/topNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
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
                stem = f.stem
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
    out = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return out
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        ts = _parse_pubdate(pub)
        if title and link:
            out.append({"title": title, "link": link, "published_ts": ts})
    return out

def _parse_pubdate(pubdate: str) -> float:
    try:
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
    pool.sort(key=lambda x: x["published_ts"], reverse=True)
    return pool[:max_items]

def _clean_headline(h: str) -> str:
    h = re.sub(r"\s*-\s*[A-Za-z0-9 .,'’“”&]+$", "", h)
    h = re.sub(r"\s*\|.*$", "", h)
    h = re.sub(r"\s*\(.*?\)\s*$", "", h)
    return h.strip()[:120]

def choose_news_topic(news_items: list) -> dict | None:
    if not news_items:
        return None
    idx = (today_kst().timetuple().tm_yday - 1) % len(news_items)
    chosen = news_items[idx]
    headline = _clean_headline(chosen["title"])
    link = chosen["link"]
    # 한국어 메타
    return {
        "title": f"요즘 뉴스로 배우는 영어표현: {headline}",
        "subtitle": "실제 이슈를 바탕으로 바로 써먹는 자연스러운 영어 표현",
        "primary_keyword": f"뉴스 영어표현 {headline.lower()}",
        "tags": ["영어", "표현", "뉴스영어", "ESL"],
        "category": "English",
        "news_headline": headline,
        "news_link": link
    }

# ---------- Prompting (한국어) ----------
def build_prompt(title: str, subtitle: str, keyword: str, internal_links: list, news_meta: dict | None) -> str:
    links_md = ""
    if internal_links:
        links_md = "\n".join([f"- [{it['title']}]({it['url']})" for it in internal_links[:INTERNAL_LINKS_COUNT]])

    news_context = ""
    if news_meta:
        news_context = f"""
배경(기사 전문을 인용하지 말고, 주제만 참고):
- 오늘의 이슈: "{news_meta.get('news_headline','')}"
- 참고 링크(인용 금지, 맥락만 파악용): {news_meta.get('news_link','')}
""".strip()

    return f"""
당신은 한국어로 글을 쓰는 실용적인 ESL(영어 학습) 콘텐츠 라이터입니다.
본문은 **한국어**로 설명하되, 예시 문장은 **영어 문장 + (짧은 한국어 번역)** 형태로 제공합니다.
주요 SEO 키워드: "{keyword}"

{news_context}

작성 규칙:
- 분량: 700–1000단어. 문장은 간결하고 실용적으로.
- 섹션 구조(H2/### 사용):
  - 훅(도입): 2–3문장, 헤딩 없이
  - ## 의미 & 뉘앙스
  - ## 상황별 대체 표현 (10–25개)
    - 각 항목: **영어 표현** — 한 줄 용도 설명(한국어) + *예문 1문장(영어) (간단 번역)*
  - ## 미니 대화 (6–8턴, 자연스러운 일상 회화)
    - 각 턴: 영어 대사 (한 줄 한국어 번역)
  - ## 흔한 실수 (Don’t say… → Say…)
  - ## 빠른 Q&A (키워드를 자연스럽게 포함한 2–3개)
  - ## 핵심 정리 (3–5개 불릿)
- 뉴스 텍스트를 그대로 인용하지 말고, 주제 전반에 적용 가능한 보편적 표현으로 작성.
- 필요 시 3–5개 표현을 비교하는 작은 마크다운 표를 추가.

메타데이터:
- 제목: {title}
- 부제목: {subtitle}

내부 링크(있다면):
{links_md}
""".strip()

def _extract_text_from_response(resp) -> str:
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
    try:
        if hasattr(resp, "choices") and resp.choices:
            msg = resp.choices[0].message
            if hasattr(msg, "content"):
                return (msg.content or "").strip()
    except Exception:
        pass
    return ""

def _call_responses(prompt: str, model: str, temperature: float):
    try:
        return client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
            max_output_tokens=MAX_TOKENS,
        )
    except TypeError:
        return client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
            max_tokens=MAX_TOKENS,
        )

def _call_chat(prompt: str, model: str, temperature: float):
    try:
        return client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": "You write clear, accurate ESL posts (Korean explanations with English examples)."},
                {"role": "user", "content": prompt},
            ],
        )
    except TypeError:
        return client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You write clear, accurate ESL posts (Korean explanations with English examples)."},
                {"role": "user", "content": prompt},
            ],
        )

def call_openai(prompt: str, model=MODEL_NAME, temperature=TEMPERATURE, max_retries=4) -> str:
    delay = 3
    active_model = model
    active_temp = temperature
    for attempt in range(max_retries):
        try:
            try:
                resp = _call_responses(prompt, active_model, active_temp)
            except Exception:
                resp = _call_chat(prompt, active_model, active_temp)
            text = _extract_text_from_response(resp)
            if not text:
                raise RuntimeError("empty_output_text")
            return text
        except Exception as e:
            msg = str(e).lower()
            if any(key in msg for key in ["rate", "429", "quota", "empty_output_text", "unsupported_value", "timeout"]):
                time.sleep(delay)
                delay = min(delay * 2, 30)
                if attempt >= max_retries // 2 and active_model != FALLBACK_MODEL:
                    active_model = FALLBACK_MODEL
                    active_temp = 0.7
                continue
            raise

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
    post["lang"] = "ko"  # 한국어로 변경
    post["timezone"] = TIMEZONE
    post["description"] = meta.get("description") or meta["subtitle"]
    post["keywords"] = meta.get("keywords") or meta.get("tags") or []
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

# ---------- Topic selection fallback ----------
def pick_topic_from_config_or_builtin(config: dict) -> dict:
    builtin = [
        {
            "title": "사과를 더 자연스럽게 말하는 10가지 표현",
            "subtitle": "I'm sorry 대신 진짜 상황에 맞는 표현",
            "primary_keyword": "사과 영어표현",
            "tags": ["영어", "표현", "사과"],
            "category": "English"
        },
        {
            "title": "Very 대신 쓸 수 있는 힘 있는 단어 25",
            "subtitle": "단문으로 더 또렷하게",
            "primary_keyword": "very 대체 표현",
            "tags": ["영어", "어휘", "라이팅"],
            "category": "English"
        },
    ]
    defaults = (config.get("defaults") or {})
    topics = (config.get("topics") or []) or builtin
    idx = (today_kst().timetuple().tm_yday - 1) % len(topics)
    chosen = topics[idx]
    return {
        "title": chosen.get("title") or "요즘 뉴스로 배우는 영어표현",
        "subtitle": chosen.get("subtitle") or "실전 중심, 간결한 설명",
        "primary_keyword": chosen.get("primary_keyword") or defaults.get("primary_keyword") or "영어 표현",
        "tags": chosen.get("tags") or defaults.get("tags") or ["영어", "표현"],
        "category": chosen.get("category") or defaults.get("category") or "English",
    }

# ---------- Main ----------
def main():
    config = load_topic_config(TOPIC_CONFIG)
    news_items = fetch_trending_news(NEWS_FEEDS, NEWS_LOOKBACK_HOURS, NEWS_MAX_ITEMS)
    topic = choose_news_topic(news_items)
    if not topic:
        topic = pick_topic_from_config_or_builtin(config)

    now_kst = today_kst()
    internal_links = list_recent_posts(12)

    meta = {
        "title": topic["title"],
        "subtitle": topic["subtitle"],
        "primary_keyword": topic["primary_keyword"],
        "tags": topic.get("tags", []),
        "category": topic.get("category", "English"),
        "date_obj": now_kst,
        "date_iso": now_kst.strftime("%Y-%m-%d %H:%M:%S %z").strip(),
        "canonical_url": f"{SITE_BASE_URL}/{now_kst.strftime('%Y')}/{now_kst.strftime('%m')}/{now_kst.strftime('%d')}/{slugify(topic['title'])}/",
        "lang": "ko",
        "keywords": [topic["primary_keyword"]] + [t for t in topic.get("tags", []) if t != topic["primary_keyword"]],
        "description": topic["subtitle"],
        "news_link": topic.get("news_link"),
        "news_headline": topic.get("news_headline"),
    }

    print(f"[generate_post] model={MODEL_NAME}, temp={TEMPERATURE}, title='{meta['title']}'")

    prompt = build_prompt(meta["title"], meta["subtitle"], meta["primary_keyword"], internal_links, topic if topic.get("news_headline") else None)
    body_md = call_openai(prompt)

    too_short = (not body_md) or (len(body_md.split()) < MIN_WORDS)
    if too_short:
        print("WARNING: Generated body seems too short. Retrying with fallback...", file=sys.stderr)
        body_md = call_openai(prompt, model=FALLBACK_MODEL, temperature=0.7)
        if (not body_md) or (len(body_md.split()) < MIN_WORDS):
            pk = meta["primary_keyword"]
            body_md = f"""\
**임시 안내**: 오늘은 자동 생성에 실패했어요. 페이지가 비지 않도록 개요를 남깁니다.

## 의미 & 뉘앙스
- "{pk}" 관련 글이 여기에 게시될 예정입니다.

## 상황별 대체 표현
- 준비 중...

## 미니 대화
- A: … (번역)
- B: … (번역)

## 핵심 정리
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
