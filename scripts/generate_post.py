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
from difflib import SequenceMatcher

from openai import OpenAI
import frontmatter

# ========= Editable defaults =========
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
TEMPERATURE = 1.0  # gpt-5 only supports 1.0
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1400"))
POSTS_DIR = os.getenv("POSTS_DIR", "_posts/auto")
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://jacksonjang.github.io")
TOPIC_CONFIG = os.getenv("TOPIC_CONFIG", "scripts/daily_config.yml")
MIN_WORDS = int(os.getenv("MIN_WORDS", "450"))
INTERNAL_LINKS_COUNT = int(os.getenv("INTERNAL_LINKS_COUNT", "3"))

# --- Similarity thresholds (tunable via env) ---
SIM_RATIO_THRESHOLD = float(os.getenv("SIM_RATIO_THRESHOLD", "0.82"))      # SequenceMatcher
SIM_JACCARD_THRESHOLD = float(os.getenv("SIM_JACCARD_THRESHOLD", "0.60"))  # token Jaccard

# --- Used topics log file ---
USED_TOPICS_PATH = os.getenv("USED_TOPICS_PATH", str(Path(POSTS_DIR) / ".used_topics.json"))

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

# ---------- Time & IO ----------
def today_kst() -> dt.datetime:
    return dt.datetime.now(ZoneInfo("Asia/Seoul"))

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

# ---------- Normalization / Slug ----------
def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "post"

def _clean_headline(h: str) -> str:
    h = re.sub(r"\s*-\s*[A-Za-z0-9 .,'’“”&]+$", "", h)  # “ - Reuters”
    h = re.sub(r"\s*\|.*$", "", h)                      # “ | BBC”
    h = re.sub(r"\s*\(.*?\)\s*$", "", h)                # trailing parentheses
    return h.strip()[:160]

# ---------- Similarity helpers ----------
_STOPWORDS = {
    "a","an","the","to","of","in","on","for","and","or","but","with","by","at",
    "from","as","is","are","was","were","be","been","being","that","this","those",
    "these","it","its","into","over","about","after","before","up","down","out",
    "off","than"
}

def _canonical_text(title: str | None, source_title: str | None) -> str:
    """
    유사도 비교용 표준 문자열:
    - news_headline(=source_title)을 우선
    - 없으면 title
    - 둘 다 있으면 "source_title // title"
    - 숫자 통일(14k -> 14000 변환 등 간단화), 기호 제거
    """
    parts = []
    if source_title:
        parts.append(_clean_headline(source_title))
    if title:
        parts.append(title)
    text = " // ".join([p for p in parts if p]).lower()

    # 숫자 단순 정규화: 14k -> 14000, 1.2m -> 1200000
    def _expand_num(m):
        num, suffix = m.group(1), m.group(2).lower()
        try:
            base = float(num.replace(",", ""))
        except ValueError:
            return m.group(0)
        if suffix == "k":
            base *= 1_000
        elif suffix == "m":
            base *= 1_000_000
        elif suffix == "b":
            base *= 1_000_000_000
        return str(int(base))
    text = re.sub(r"(\d+(?:\.\d+)?)([kKmMbB])\b", _expand_num, text)

    # 기호 축소
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _tokenize(s: str) -> set[str]:
    toks = [t for t in re.split(r"\s+", s) if t]
    toks = [t for t in toks if t not in _STOPWORDS]
    return set(toks)

def _seq_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def _jaccard(a: str, b: str) -> float:
    A, B = _tokenize(a), _tokenize(b)
    if not A and not B:
        return 1.0
    if not A or not B:
        return 0.0
    inter = len(A & B)
    union = len(A | B)
    return inter / union if union else 0.0

def is_similar(a_text: str, b_text: str) -> bool:
    r = _seq_ratio(a_text, b_text)
    j = _jaccard(a_text, b_text)
    return (r >= SIM_RATIO_THRESHOLD) or (j >= SIM_JACCARD_THRESHOLD)

# ---------- Topic key ----------
def _topic_key(title: str | None, source_title: str | None = None) -> str:
    parts = []
    if source_title:
        parts.append(_clean_headline(source_title))
    if title:
        parts.append(title)
    if not parts:
        return ""
    return slugify(" // ".join(parts))

# ---------- Existing keys & used log ----------
def _read_post_keys_from_file(fpath: Path) -> tuple[list[str], list[str]]:
    """
    returns: (keys, canonical_texts)
    """
    keys, ctexts = [], []
    try:
        post = frontmatter.load(fpath)
        title = (post.get("title") or "").strip()
        source_title = (post.get("source_title") or "").strip()
        if title or source_title:
            keys.append(_topic_key(title, source_title))
            ctexts.append(_canonical_text(title, source_title))
    except Exception:
        stem = fpath.stem
        try:
            slug = "-".join(stem.split("-")[3:]) or stem
        except Exception:
            slug = stem
        keys.append(slugify(slug))
        ctexts.append(slugify(slug))
    return [k for k in keys if k], [c for c in ctexts if c]

def _load_used_topics(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def _save_used_topic(path: str, record: dict):
    p = Path(path)
    ensure_dir(p.parent)
    data = _load_used_topics(path)
    data.append(record)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def collect_existing_topics(posts_dir: str, used_path: str):
    """
    returns:
      existing_keys: set[str]
      existing_canonicals: list[str]  (유사도 비교용)
    """
    existing_keys: set[str] = set()
    existing_canonicals: list[str] = []

    p = Path(posts_dir)
    if p.exists():
        for f in p.glob(f"*{OUTPUT_EXT}"):
            keys, ctexts = _read_post_keys_from_file(f)
            for k in keys:
                if k:
                    existing_keys.add(k)
            existing_canonicals.extend(ctexts)

    # used_topics 병합
    for rec in _load_used_topics(used_path):
        k = rec.get("key")
        c = rec.get("canonical", "")
        if k:
            existing_keys.add(k)
        if c:
            existing_canonicals.append(c)

    return existing_keys, existing_canonicals

# ---------- Recent posts for internal links ----------
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

# ---------- Config ----------
def load_topic_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data

# ---------- RSS ----------
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

# ---------- Candidate evaluation (중복 + 유사도 회피) ----------
def _dup_or_similar(candidate_title: str, candidate_source: str | None,
                    existing_keys: set[str], existing_canonicals: list[str]) -> bool:
    cand_key = _topic_key(candidate_title, candidate_source)
    if cand_key in existing_keys:
        return True
    cand_canonical = _canonical_text(candidate_title, candidate_source)
    for prev in existing_canonicals:
        if is_similar(cand_canonical, prev):
            return True
    return False

# ---------- Topic choosers ----------
def choose_news_topic(news_items: list, existing_keys: set[str], existing_canonicals: list[str]) -> dict | None:
    if not news_items:
        return None
    idx = (today_kst().timetuple().tm_yday - 1) % len(news_items)

    for i in range(len(news_items)):
        cand = news_items[(idx + i) % len(news_items)]
        headline = _clean_headline(cand["title"])
        title = f"뉴스로 배우는 영어: {headline}"
        if not _dup_or_similar(title, headline, existing_keys, existing_canonicals):
            return {
                "title": title,
                "subtitle": "실제 이슈를 바탕으로 바로 써먹는 자연스러운 영어 표현",
                "primary_keyword": f"뉴스 영어표현 {headline.lower()}",
                "tags": ["영어", "표현", "뉴스영어", "ESL"],
                "category": "English",
                "news_headline": headline,
                "news_link": cand["link"]
            }
    return None

def pick_topic_from_config_or_builtin(config: dict, existing_keys: set[str], existing_canonicals: list[str]) -> dict:
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

    for i in range(len(topics)):
        cand = topics[(idx + i) % len(topics)]
        title = cand.get("title") or "요즘 뉴스로 배우는 영어표현"
        if not _dup_or_similar(title, None, existing_keys, existing_canonicals):
            return {
                "title": title,
                "subtitle": cand.get("subtitle") or "실전 중심, 간결한 설명",
                "primary_keyword": cand.get("primary_keyword") or defaults.get("primary_keyword") or "영어 표현",
                "tags": cand.get("tags") or defaults.get("tags") or ["영어", "표현"],
                "category": cand.get("category") or defaults.get("category") or "English",
            }

    # 모두 유사/중복이면 날짜 suffix로 강제 유일화
    today = today_kst().strftime("%Y-%m-%d")
    base = topics[idx]
    base_title = (base.get("title") or "영어 표현 업데이트") + f" - {today}"
    return {
        "title": base_title,
        "subtitle": base.get("subtitle") or "실전 중심, 간결한 설명",
        "primary_keyword": base.get("primary_keyword") or "영어 표현",
        "tags": base.get("tags") or ["영어", "표현"],
        "category": base.get("category") or "English",
    }

# ---------- Prompting ----------
def build_prompt(title: str, subtitle: str, keyword: str, internal_links: list, news_meta: dict | None) -> str:
    """
    SEO 최적화형 ESL(영어 학습) 콘텐츠 프롬프트 생성 함수
    """

    INTERNAL_LINKS_COUNT = 3  # 링크 최대 3개 노출 제한

    # 내부 링크 마크다운 변환
    links_md = ""
    if internal_links:
        links_md = "\n".join(
            [f"- [{it['title']}]({it['url']})" for it in internal_links[:INTERNAL_LINKS_COUNT]]
        )

    # 뉴스 맥락 정보 (인용 금지)
    news_context = ""
    if news_meta:
        news_context = f"""
배경(기사 전문을 인용하지 말고, 주제만 참고):
- 오늘의 이슈: "{news_meta.get('news_headline', '')}"
- 참고 링크(인용 금지, 맥락만 파악용): {news_meta.get('news_link', '')}
""".strip()

    # SEO 최적화형 ESL 프롬프트
    return f"""
당신은 **SEO에 최적화된 실용 영어(ESL) 콘텐츠 라이터**입니다.
글은 **한국어 설명 중심**으로 작성하고, 예시 문장은 **영어 문장 + (짧은 한국어 번역)** 형태로 제공합니다.
**핵심 SEO 키워드:** “{keyword}”
연관 LSI 키워드(자연스럽게 포함): 영어회화, 영어표현, 영어공부, 영어뉘앙스, 자연스러운영어, 일상영어, 영어학습팁

{news_context}

작성 규칙:
- 분량: 700–1000단어. 문장은 간결하고 실용적으로.
- SEO 최적화 구조(H2/H3 사용):
  - (도입부, 헤딩 없음): 2~3문장으로 {keyword}와 연결된 상황 제시
  - ## 의미 & 뉘앙스
  - ## 핵심 단어
    - 각 항목: **영어 단어 — 간단 의미(한국어)** + 예문 1문장
  - ## 상황별 대체 표현 (10–25개)
    - 각 항목: **영어 표현** — 한 줄 용도 설명(한국어)
    - 예문: 영어 1줄 + 한국어 번역 줄바꿈
    - 필요 시 비교 표(3–5개 표현 비교)
  - ## 간단 회화 (6–8턴, 자연스러운 일상 회화)
    - 각 턴: 영어 대사 (한 줄 한국어 번역)
  - ## 흔한 실수 (Don’t say… → Say…)
    - 각 항목: 영어 문장 (한 줄 한국어 번역)
  - ## 빠른 Q&A (2–3개)
    - 질문과 답변에 “{keyword}”를 자연스럽게 포함
    - 마지막에 CTR 유도 문장(예: “이 표현, 바로 말해보세요!”)
  - ## 핵심 정리 (3–5개 불릿)
    - SEO 강화를 위해 {keyword}를 반복 포함

세부 지침(SEO 강화):
- 본문 내 “{keyword}”의 밀도를 약 1.5–2% 수준으로 유지
- H2/H3 계층 구조를 명확히 구분
- FAQ, 표, 불릿을 적극 활용해 가독성과 체류시간 향상
- 뉴스 텍스트를 인용하지 말고 주제 전반에 적용 가능한 표현으로 작성
- 모든 예문은 실용적인 일상 또는 비즈니스 상황 기반으로 작성

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
    post["lang"] = "ko"
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

# ---------- Builtins for fallback ----------
def load_config_topics(config: dict) -> list[dict]:
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
    topics = (config.get("topics") or [])
    return topics or builtin

def all_news_exhausted(news_items: list, existing_keys: set[str], existing_canonicals: list[str]) -> bool:
    if not news_items:
        return True
    for it in news_items:
        headline = _clean_headline(it["title"])
        title = f"뉴스로 배우는 영어: {headline}"
        if not _dup_or_similar(title, headline, existing_keys, existing_canonicals):
            return False
    return True


# ---------- Main ----------
def main():
    config = load_topic_config(TOPIC_CONFIG)
    existing_keys, existing_canonicals = collect_existing_topics(POSTS_DIR, USED_TOPICS_PATH)

    news_items = fetch_trending_news(NEWS_FEEDS, NEWS_LOOKBACK_HOURS, NEWS_MAX_ITEMS)
    topic = choose_news_topic(news_items, existing_keys, existing_canonicals)
    
    # 뉴스만 허용: 후보가 없거나 모두 중복/유사면 스킵 후 종료
    if (not news_items) or (topic is None) or all_news_exhausted(news_items, existing_keys, existing_canonicals):
        print("[generate_post] SKIP: 뉴스 주제가 모두 사용되었습니다(또는 최근 뉴스 없음). 포스트 생성을 건너뜁니다.")
        sys.exit(0)

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

    # 최종 충돌 방지(키 + 유사도)
    if _dup_or_similar(meta["title"], meta.get("news_headline"), existing_keys, existing_canonicals):
        print("[generate_post] SKIP: 최종 중복/유사 판정. 포스트 생성을 건너뜁니다.")
        sys.exit(0)

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

    # ---- used_topics.json에 기록 ----
    used_record = {
        "timestamp": int(time.time()),
        "date_iso": meta["date_iso"],
        "key": _topic_key(meta["title"], meta.get("news_headline")),
        "title": meta["title"],
        "source_title": meta.get("news_headline") or "",
        "canonical": _canonical_text(meta["title"], meta.get("news_headline")),
        "canonical_url": meta["canonical_url"],
    }
    _save_used_topic(USED_TOPICS_PATH, used_record)

    print(json.dumps({
        "file": str(out_path),
        "title": meta["title"],
        "tags": meta["tags"],
        "category": meta["category"],
        "news_headline": meta.get("news_headline"),
        "news_link": meta.get("news_link"),
        "used_log": USED_TOPICS_PATH
    }, ensure_ascii=False))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[generate_post] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
