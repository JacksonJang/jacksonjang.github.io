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
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "1.0"))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1400"))  # chat.completions 용
POSTS_DIR = os.getenv("POSTS_DIR", "_posts/auto")
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://jacksonjang.github.io")
MIN_WORDS = int(os.getenv("MIN_WORDS", "450"))
INTERNAL_LINKS_COUNT = int(os.getenv("INTERNAL_LINKS_COUNT", "3"))

# --- Similarity thresholds ---
SIM_RATIO_THRESHOLD = float(os.getenv("SIM_RATIO_THRESHOLD", "0.82"))
SIM_JACCARD_THRESHOLD = float(os.getenv("SIM_JACCARD_THRESHOLD", "0.60"))

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

# Evergreen(상시) 토픽 후보 (뉴스 실패 시 사용)
EVERGREEN_TOPICS = [
    ("영어 이메일 클로징 멘트", "업무 메일에서 바로 쓰는 마무리 표현 모음"),
    ("면접에서 자주 나오는 영어 질문", "실전 답변 패턴과 자연스러운 대답 예시"),
    ("회의에서 유용한 영어 표현", "의견 제시·동의·반대·정리 한 번에"),
    ("일상 회화 핵심 패턴", "자연스러운 말문 트이는 필수 표현"),
    ("비즈니스 협상 영어표현", "가격·조건·일정 협상에 쓰는 문장들"),
]

# =====================================

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client:
    print("ERROR: OPENAI_API_KEY is not set.", file=sys.stderr)
    # 그래도 파일은 만들어야 하므로 계속 진행


# ---------- Time & IO ----------
def today_kst() -> dt.datetime:
    return dt.datetime.now(ZoneInfo(TIMEZONE))


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
    parts = []
    if source_title:
        parts.append(_clean_headline(source_title))
    if title:
        parts.append(title)
    text = " // ".join([p for p in parts if p]).lower()

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


# ---------- News SEO helpers ----------
_BRAND_STOP = {"reuters","bbc","ap","bloomberg","cnn","nytimes","nyt","washington","guardian","yahoo","forbes","wsj","post"}

def _clean_publisher_trail(s: str) -> str:
    s = re.sub(r"\s*-\s*[A-Za-z0-9 .,'’“”&]+$", "", s)
    s = re.sub(r"\s*\|.*$", "", s)
    s = re.sub(r"\s*\(.*?\)\s*$", "", s)
    return s.strip()


def _extract_news_keywords(headline: str, max_terms: int = 3) -> list[str]:
    h = _clean_publisher_trail(headline)
    h = re.sub(r"[\"“”’'`]+", "", h)
    h = re.sub(r"[^\w\s\-&:/]", " ", h).lower()
    stop = _STOPWORDS | _BRAND_STOP | {
        "breaking","live","update","analysis","exclusive","opinion","video","photos",
        "says","set","sets","new","plan","plans","after","amid","ahead","over","as","from","by","with","for"
    }
    toks = [t for t in re.split(r"\s+|/|:|–|-", h) if t]
    toks = [t for t in toks if (t not in stop and not re.fullmatch(r"\d+", t) and len(t) >= 3)]
    toks = sorted(set(toks), key=lambda x: (len(x) >= 6, len(x)), reverse=True)
    return toks[:max_terms]


def _join_news_keyword_phrase(keywords: list[str]) -> str:
    def cap(w: str) -> str:
        return w if not w.isalpha() else (w[:1].upper() + w[1:])
    if not keywords:
        return ""
    if len(keywords) >= 3:
        head = ", ".join(cap(w) for w in keywords[:2])
        tail = cap(keywords[2])
        return f"{head}, {tail}"
    return ", ".join(cap(w) for w in keywords)


# ---------- SEO Title/SubTitle Optimizer ----------
SEO_MIN_LEN = 32
SEO_MAX_LEN = 58

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _has_keyword_early(title: str, keyword: str, early_chars: int = 18) -> bool:
    return _normalize(keyword).lower() in _normalize(title).lower()[:early_chars]


def _length_ok(title: str) -> bool:
    l = len(_normalize(title))
    return SEO_MIN_LEN <= l <= SEO_MAX_LEN


def _clean_quotes(s: str) -> str:
    return re.sub(r"[\"“”’'`]+", "", s or "")


def _clip_no_ellipsis(s: str, max_len: int = SEO_MAX_LEN) -> str:
    s = _normalize(s)
    return s[:max_len] if len(s) > max_len else s


def is_seo_title_good(title: str, keyword: str) -> bool:
    t = _normalize(title)
    return bool(
        t and
        _length_ok(t) and
        _has_keyword_early(t, "뉴스 영어표현")
    )


def _extract_angle_from_news(news_meta: dict | None) -> str:
    if not news_meta:
        return ""
    headline = (news_meta.get("news_headline") or "").strip()
    if not headline:
        return ""
    toks = re.findall(r"[A-Za-z가-힣0-9]{3,}", headline)[:2]
    return " / ".join(toks)


def _news_title_candidates(kw_phrase: str, year: int) -> list[str]:
    return [
        f"뉴스 영어표현: {kw_phrase} — 예문으로 바로 익히기",
        f"뉴스 영어표현: {kw_phrase} 핵심표현 정리 ({year})",
        f"뉴스 영어표현: {kw_phrase} 자연스럽게 말하는 법",
        f"뉴스 영어표현: {kw_phrase} 필수 패턴 20가지",
        f"뉴스 영어표현: {kw_phrase} 네이티브식 표현 모음",
    ]


def optimize_title(title: str, keyword: str, news_meta: dict | None) -> str:
    year = dt.datetime.now().year
    raw = _clean_quotes(_normalize(title))
    if news_meta and news_meta.get("news_headline"):
        kws = news_meta.get("news_keywords") or _extract_news_keywords(news_meta["news_headline"], 3)
        kw_phrase = _join_news_keyword_phrase(kws) or "핵심 이슈"
        if is_seo_title_good(raw, keyword):
            return _clip_no_ellipsis(raw)
        for cand in _news_title_candidates(kw_phrase, year):
            cand = _clip_no_ellipsis(cand)
            if is_seo_title_good(cand, keyword):
                return cand
        return _clip_no_ellipsis(f"뉴스 영어표현: {kw_phrase} 핵심표현 정리")
    else:
        if is_seo_title_good(raw, keyword):
            return _clip_no_ellipsis(raw)
        # evergreen용 기본 타이틀
        base = f"뉴스 영어표현: {keyword}"
        return _clip_no_ellipsis(base)


def optimize_subtitle(subtitle: str, keyword: str) -> str:
    sub = _clean_quotes(_normalize(subtitle))
    if not sub or len(sub) < 22:
        sub = f"{keyword} — 실전 예문과 패턴으로 10분 만에 정리"
    sub = _clip_no_ellipsis(sub, 90)
    if "뉴스 영어표현" not in sub:
        sub = _clip_no_ellipsis(f"{sub} · 뉴스 영어표현", 90)
    return sub


# ---------- Topic choosers ----------
def choose_news_topic(news_items: list, existing_keys: set[str], existing_canonicals: list[str]) -> dict | None:
    if not news_items:
        return None
    idx = (today_kst().timetuple().tm_yday - 1) % len(news_items)

    for i in range(len(news_items)):
        cand = news_items[(idx + i) % len(news_items)]
        headline = _clean_headline(cand["title"])
        kws = _extract_news_keywords(headline, max_terms=3)
        kw_phrase = _join_news_keyword_phrase(kws) or headline[:50]
        base_title = f"뉴스 영어표현: {kw_phrase}"

        if not _dup_or_similar(base_title, headline, existing_keys, existing_canonicals):
            return {
                "title": base_title,
                "subtitle": "실제 이슈를 바탕으로 바로 써먹는 자연스러운 영어 표현",
                "primary_keyword": f"뉴스 영어표현 {kw_phrase}",
                "tags": ["영어", "표현", "뉴스영어", "ESL"],
                "category": "English",
                "news_headline": headline,
                "news_link": cand["link"],
                "news_keywords": kws
            }
    return None


def choose_evergreen_topic(existing_keys: set[str], existing_canonicals: list[str]) -> dict:
    # 날짜 기반으로 순환
    idx = (today_kst().timetuple().tm_yday - 1) % len(EVERGREEN_TOPICS)
    for i in range(len(EVERGREEN_TOPICS)):
        title_kw, sub = EVERGREEN_TOPICS[(idx + i) % len(EVERGREEN_TOPICS)]
        base_title = f"뉴스 영어표현: {title_kw}"
        if not _dup_or_similar(base_title, None, existing_keys, existing_canonicals):
            return {
                "title": base_title,
                "subtitle": sub,
                "primary_keyword": f"뉴스 영어표현 {title_kw}",
                "tags": ["영어", "표현", "뉴스영어", "ESL"],
                "category": "English",
                "news_headline": "",
                "news_link": "",
                "news_keywords": [title_kw]
            }
    # 전부 겹치면 날짜 스탬프 포함 타이틀로 강제 고유화
    stamp = today_kst().strftime("%Y%m%d-%H%M")
    return {
        "title": f"뉴스 영어표현: 실전 패턴 모음 {stamp}",
        "subtitle": "실전에서 바로 쓰는 자연스러운 표현",
        "primary_keyword": "뉴스 영어표현 실전 패턴",
        "tags": ["영어", "표현", "뉴스영어", "ESL"],
        "category": "English",
        "news_headline": "",
        "news_link": "",
        "news_keywords": ["expression", "pattern"]
    }


# ---------- Prompting ----------
def build_prompt(title: str, subtitle: str, keyword: str, internal_links: list, news_meta: dict | None) -> str:
    links_md = ""
    if internal_links:
        links_md = "\n".join(
            f"- [{it['title']}]({it['url']})" for it in internal_links[:INTERNAL_LINKS_COUNT]
        )

    # 웹검색 도구 의존 제거(가용성 문제 방지). 출처는 일반 가이드로 표기하게 유도.
    return f"""
You are an SEO-optimized ESL writer for Korean learners.
Write in Korean (explanations) with English examples plus short Korean translations.

== PAGE METADATA ==
Title: {title}
Subtitle: {subtitle}
Primary SEO Keyword: "{keyword}"

== RULES ==
- Length: 900–1200 words.
- Tone: clear, practical, concise.
- Structure (use H2/H3):
  (Intro, no heading): 2–3 sentences explaining why "{keyword}" matters and typical contexts.
  ## 의미 & 뉘앙스
    - 핵심 정의, 격식/구어 구분, 흔한 collocations 6–10개
  ## 상황별 대체 표현 (12–20개)
    - 각 항목: **표현** — 한 줄 용도(ko)
      - 예문 1: EN
      - 번역 1: (ko)
  ## 간단 회화 (6–8턴)
    - 각 턴: EN 한 줄 + (ko 번역)
  ## FAQ (SEO)
    - 3–4개(질문에 "{keyword}" 포함). 각 2–3문장.
  ## 핵심 정리
    - 불릿 5개. 키워드 자연스럽게 반복(밀도 ~1.5–2%).
  ## References
    - 일반 사전·교육기관·대형 매체 3–6개를 목록으로 (설명 위주, 복붙 금지)

- Formatting:
  - 굵게는 '표현 키워드'에만 사용. 예문은 굵게 금지.
  - 표는 최대 1개만 사용.

- Constraints:
  - 뉴스/사전 본문을 복사하지 말고 창작으로 작성.
  - 현대 영어로 자연스럽게.

== INTERNAL LINKS ==
{links_md}
"""


def _extract_text_from_responses(resp) -> str:
    # responses API (unified)
    text = getattr(resp, "output_text", None)
    if text:
        return text.strip()
    # output 배열
    for block in getattr(resp, "output", []) or []:
        for c in getattr(block, "content", []) or []:
            if getattr(c, "type", "") == "output_text" and getattr(c, "text", ""):
                return c.text.strip()
    # choices 호환
    if hasattr(resp, "choices") and resp.choices:
        msg = getattr(resp.choices[0], "message", None)
        if msg and getattr(msg, "content", ""):
            return msg.content.strip()
    return ""


def call_openai_safe(prompt: str, model=MODEL_NAME, temperature=TEMPERATURE) -> str:
    # 1) responses.create (안전 파라미터만 — tools, system 등 불확실 요소 제거)
    try:
        resp = client.responses.create(
            model=model,
            input=prompt,
            tools=[{"type": "web_search"}],
            temperature=temperature,
            max_output_tokens=MAX_TOKENS,
        )
        text = _extract_text_from_responses(resp)
        if text:
            return text
    except Exception as e:
        print(f"[warn] responses.create failed: {e}", file=sys.stderr)

    # 2) chat.completions.create 폴백
    try:
        resp2 = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful ESL writing assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=MAX_TOKENS,
        )
        if resp2 and getattr(resp2, "choices", None):
            txt = resp2.choices[0].message.content or ""
            if txt.strip():
                return txt.strip()
    except Exception as e:
        print(f"[warn] chat.completions.create failed: {e}", file=sys.stderr)

    # 3) 최후 수단: 빈 문자열 반환 (상위에서 로컬 스켈레톤으로 보완)
    return ""


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


# ---------- Main ----------
def main():
    existing_keys, existing_canonicals = collect_existing_topics(POSTS_DIR, USED_TOPICS_PATH)

    # 1) 뉴스 시도
    news_items = fetch_trending_news(NEWS_FEEDS, NEWS_LOOKBACK_HOURS, NEWS_MAX_ITEMS)
    topic = choose_news_topic(news_items, existing_keys, existing_canonicals)

    # 2) 실패/중복이면 evergreen으로 전환 (절대 종료하지 않음)
    if topic is None:
        topic = choose_evergreen_topic(existing_keys, existing_canonicals)

    now_kst = today_kst()
    internal_links = list_recent_posts(12)

    # === [SEO] 제목/부제목 자동 교정 ===
    fixed_title = optimize_title(topic["title"], topic["primary_keyword"], topic if topic.get("news_headline") else None)
    fixed_subtitle = optimize_subtitle(topic["subtitle"], topic["primary_keyword"])

    # 최종 중복 시 강제 고유화(시간 스탬프 덧붙임)
    if _dup_or_similar(fixed_title, topic.get("news_headline"), existing_keys, existing_canonicals):
        fixed_title = f"{fixed_title} ({now_kst.strftime('%H%M%S')})"

    meta = {
        "title": fixed_title,
        "subtitle": fixed_subtitle,
        "primary_keyword": topic["primary_keyword"],
        "tags": topic.get("tags", []),
        "category": topic.get("category", "English"),
        "date_obj": now_kst,
        "date_iso": now_kst.strftime("%Y-%m-%d %H:%M:%S %z").strip(),
        "canonical_url": f"{SITE_BASE_URL}/{now_kst.strftime('%Y')}/{now_kst.strftime('%m')}/{now_kst.strftime('%d')}/{slugify(fixed_title)}/",
        "lang": "ko",
        "keywords": [topic["primary_keyword"]] + [t for t in topic.get("tags", []) if t != topic["primary_keyword"]],
        "description": fixed_subtitle,
        "news_link": topic.get("news_link"),
        "news_headline": topic.get("news_headline"),
    }

    print(f"[generate_post] model={MODEL_NAME}, temp={TEMPERATURE}, title='{meta['title']}'")

    prompt = build_prompt(meta["title"], meta["subtitle"], meta["primary_keyword"], internal_links, topic if topic.get("news_headline") else None)
    body_md = ""
    if client:
        body_md = call_openai_safe(prompt, model=MODEL_NAME, temperature=TEMPERATURE)

    # 본문 안전 보강: 최소 길이 미달 또는 실패 시 로컬 스켈레톤로 대체(파일은 반드시 생성)
    if (not body_md) or (len(body_md.split()) < MIN_WORDS):
        pk = meta["primary_keyword"]
        body_md = f"""\
(자동 생성 안내) — API 연결이 불안정하여 템플릿 기반으로 본문을 제공합니다. 곧 정상 본문으로 대체될 예정입니다.

## 의미 & 뉘앙스
- "{pk}"의 핵심 개념과 사용 맥락을 간단히 정리합니다.
- 격식/구어 구분과 자주 쓰이는 연결 표현(collocations)을 예고합니다.

## 상황별 대체 표현
- 실무/일상에서 바로 쓰기 좋은 표현들을 정리합니다.
- 각 표현에는 짧은 예문(EN)과 한국어 번역을 제공합니다.

## 간단 회화
- 실제 대화 흐름 속에서 "{pk}"를 자연스럽게 사용하는 예시를 보여줍니다.

## 흔한 실수 (Don’t say → Say)
- 한국어식 직역에서 자주 틀리는 포인트를 교정합니다.

## 미니 퀴즈
1) 빈칸 채우기 ___
2) 표현 바꾸기 ___
3) 의미 고르기 ___
4) 올바른 collocation 고르기 ___
5) 문장 자연스럽게 고치기 ___

## FAQ (SEO)
- "{pk}"는 어디서 가장 자주 쓰이나요?
- 비슷한 표현과의 차이는 무엇인가요?
- 업무 이메일에서 자연스러운 대체 표현은?

## 핵심 정리
- {pk}의 의미·뉘앙스 요약
- 자주 쓰는 collocations
- 상황별 대체 표현
- 흔한 실수와 올바른 예
- 바로 써먹는 패턴 모음

## References
- Cambridge / Merriam-Webster / Oxford / British Council 등 공인 사전·교육기관
"""

    out_path = write_post_file(meta, body_md)
    print(f"[generate_post] Wrote: {out_path}")

    # used_topics.json 기록 (항상 기록)
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
        # 어떤 경우에도 프로세스가 실패 코드로 종료되지 않도록 마지막 방어선
        print(f"[generate_post] FATAL (but recovered): {e}", file=sys.stderr)
        try:
            now_kst = today_kst()
            ensure_dir(Path(POSTS_DIR))
            title = f"뉴스 영어표현: 임시 포스트 {now_kst.strftime('%Y%m%d-%H%M%S')}"
            meta = {
                "title": title,
                "subtitle": "임시 생성 문서 — 추후 본문 대체 예정",
                "primary_keyword": "뉴스 영어표현 임시",
                "tags": ["영어","표현","뉴스영어","ESL"],
                "category": "English",
                "date_obj": now_kst,
                "date_iso": now_kst.strftime("%Y-%m-%d %H:%M:%S %z").strip(),
                "canonical_url": f"{SITE_BASE_URL}/{now_kst.strftime('%Y')}/{now_kst.strftime('%m')}/{now_kst.strftime('%d')}/{slugify(title)}/",
            }
            body_md = "(자동 복구) 시스템 예외가 발생했으나 게시 중단을 방지하기 위해 임시 본문을 생성했습니다."
            out_path = write_post_file(meta, body_md)
            print(f"[generate_post] Rescued Wrote: {out_path}")
            print(json.dumps({"file": str(out_path), "title": meta["title"]}, ensure_ascii=False))
        except Exception as e2:
            # 이중 실패라도 0으로 종료 (무조건 실패 방지)
            print(f"[generate_post] DOUBLE FAIL: {e2}", file=sys.stderr)
            # 마지막으로라도 0으로 종료
            pass
