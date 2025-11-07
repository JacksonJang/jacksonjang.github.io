#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Single-call OpenAI version of generate_post.py (with OpenAI-based related picks)
- RSS Source: Reuters, BBC, Investing.com, MarketWatch, Yahoo Finance, CNBC
- Exactly ONE OpenAI chat.completions call (title + body + terms + related in JSON)
- Related stocks/ETFs are proposed directly by OpenAI (no Yahoo Finance).
- Dedup via RSS link history to avoid repeated coverage.
"""

import os
import re
import json
import html
import random
import textwrap
import traceback
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional, Dict, Any, Set

try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    BeautifulSoup = None

import frontmatter
import feedparser

# -----------------------------
# 환경설정 (환경변수로 재정의 가능)
# -----------------------------
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini") # gpt-4o-mini , gpt-5-nano , gpt-5-mini
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "1.0"))  # gpt-5 권장 1.0
MAX_OUTPUT_TOKENS = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", 3200))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
POSTS_DIR = Path(os.getenv("POSTS_DIR", "_posts/auto"))
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
AUTHOR = os.getenv("POST_AUTHOR", "JacksonJang")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://jacksonjang.github.io")

DEFAULT_USED_LINKS_PATH = "data/used_links.json"
USED_LINKS_FILE = Path(
    os.getenv("USED_LINKS_FILE")
    or os.getenv("USED_TOPICS_FILE", DEFAULT_USED_LINKS_PATH)
)
LEGACY_USED_TOPICS_FILE = Path(os.getenv("USED_TOPICS_FILE", "data/used_topics.json"))
USED_LINKS_LIMIT = int(os.getenv("USED_LINKS_LIMIT", os.getenv("USED_TOPICS_LIMIT", "400")))

# 내부 링크(있다면 자동 삽입). 없으면 비워두세요.
INTERNAL_LINKS: List[tuple[str, str]] = []

# -----------------------------
# RSS 소스 (지정한 6개)
# -----------------------------
RSS_SOURCES = [
    {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "BBC Business", "url": "http://feeds.bbci.co.uk/news/business/rss.xml"},
    {"name": "Investing.com Economic/Finance", "url": "https://www.investing.com/rss/news_25.rss"},
    {"name": "MarketWatch Top Stories", "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
    {"name": "Yahoo Finance Top Stories", "url": "https://finance.yahoo.com/news/rssindex"},
    {"name": "CNBC Top News & Analysis", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
]

# -----------------------------
# OpenAI (chat.completions) — exactly ONE call
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_openai_client = None
_openai_chat = None
try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        _openai_chat = _openai_client.chat.completions
except Exception:
    _openai_client = None
    _openai_chat = None


@dataclass
class NewsItem:
    source: str
    title: str
    link: str
    summary: str
    published: Optional[datetime]

# -----------------------------
# 유틸
# -----------------------------
def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def ensure_unique_path(base_path: Path) -> Path:
    """Return a unique path by appending a numeric suffix if needed."""

    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    counter = 2
    while True:
        candidate = base_path.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1

def now_kst() -> datetime:
    try:
        return datetime.now(ZoneInfo(TIMEZONE))
    except Exception:
        return datetime.utcnow().replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Seoul"))

def to_slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s

def load_used_links() -> List[str]:
    files_to_try = []
    if USED_LINKS_FILE.exists():
        files_to_try.append(USED_LINKS_FILE)
    if LEGACY_USED_TOPICS_FILE.exists() and LEGACY_USED_TOPICS_FILE not in files_to_try:
        files_to_try.append(LEGACY_USED_TOPICS_FILE)

    for path in files_to_try:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                cleaned = []
                for x in data:
                    s = str(x).strip()
                    if not s:
                        continue
                    if s.startswith("http://") or s.startswith("https://"):
                        cleaned.append(s)
                if cleaned:
                    return cleaned
        except Exception:
            continue
    return []


def save_used_links(links: List[str]) -> None:
    ensure_dir(USED_LINKS_FILE.parent)
    if len(links) > USED_LINKS_LIMIT:
        links = links[-USED_LINKS_LIMIT:]
    USED_LINKS_FILE.write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8")


def pick_not_used(
    candidate_items: List[NewsItem],
    used_links: List[str],
    extra_excluded: Optional[Set[str]] = None,
) -> Optional[NewsItem]:
    candidate_items = sorted(candidate_items, key=lambda x: x.published or now_kst(), reverse=True)
    blocked: Set[str] = set(link for link in used_links if link)
    if extra_excluded:
        blocked.update(extra_excluded)
    for item in candidate_items:
        if item.link and item.link not in blocked:
            return item
    return None


def _sanitize_json_text(raw: str) -> str:
    """Escape control characters inside JSON strings (e.g. bare newlines)."""

    out_chars: List[str] = []
    in_string = False
    escape_next = False

    for ch in raw:
        if not in_string:
            out_chars.append(ch)
            if ch == '"':
                in_string = True
            continue

        # We are inside a string literal
        if escape_next:
            out_chars.append(ch)
            escape_next = False
            continue

        if ch == '\\':
            out_chars.append(ch)
            escape_next = True
            continue

        if ch == '"':
            out_chars.append(ch)
            in_string = False
            continue

        if ch in {'\n', '\r'}:
            out_chars.append('\\n')
            continue

        if ord(ch) < 0x20:
            out_chars.append(f"\\u{ord(ch):04x}")
            continue

        out_chars.append(ch)

    return "".join(out_chars)

# -----------------------------
# 피드 로딩
# -----------------------------
def parse_published(entry: Any) -> Optional[datetime]:
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(TIMEZONE))
    except Exception:
        pass
    try:
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6], tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(TIMEZONE))
    except Exception:
        pass
    return None

def fetch_news_from_rss() -> List[NewsItem]:
    items: List[NewsItem] = []
    seen_links: Set[str] = set()
    for src in RSS_SOURCES:
        try:
            feed = feedparser.parse(src["url"])
            for e in feed.entries[:30]:
                title = html.unescape(getattr(e, "title", "")).strip()
                link = getattr(e, "link", "").strip()
                summary = html.unescape(getattr(e, "summary", "")).strip() if hasattr(e, "summary") else ""
                published = parse_published(e)
                if title and link and link not in seen_links:
                    seen_links.add(link)
                    items.append(NewsItem(src["name"], title, link, summary, published))
        except Exception as ex:
            print(f"[WARN] RSS 실패: {src['name']} - {ex}")
    return items


def extract_article_text(html_text: str, max_chars: int = 2000) -> str:
    if not html_text:
        return ""

    text = ""
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer"]):
            tag.decompose()
        paragraphs = [
            p.get_text(separator=" ", strip=True)
            for p in soup.find_all(["p", "li"])
            if p.get_text(strip=True)
        ]
        if paragraphs:
            text = " ".join(paragraphs)
        else:
            text = soup.get_text(separator=" ", strip=True)
    else:
        text = re.sub(r"<[^>]+>", " ", html_text)

    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "…"
    return text


def fetch_article_content(link: str, max_chars: int = 2000) -> str:
    if not link or requests is None:
        return ""
    try:
        resp = requests.get(
            link,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
            },
        )
        if resp.ok:
            return extract_article_text(resp.text, max_chars=max_chars)
    except Exception as ex:
        print(f"[WARN] 기사 본문 수집 실패: {link} - {ex}")
    return ""

# -----------------------------
# 관련 종목 추천 (OpenAI가 직접 제안)
# -----------------------------
def related_md_from_ai(related: List[Dict[str, str]]) -> str:
    """ai_generate_all()가 반환한 related 목록을 이용해 MD 섹션 생성"""
    picks = related or []
    if not picks:
        picks = [
            {"symbol": "SPY", "name": "SPDR S&P 500", "why": "미국 대형주 분산"},
            {"symbol": "ACWI", "name": "MSCI ACWI", "why": "글로벌 분산"},
        ]
    lines = ["\n## 관련 종목", "OpenAI 제안 기반의 연관 종목/ETF입니다. (투자 권유 아님)"]
    for it in picks:
        sym = (it.get("symbol") or it.get("ticker") or "-").strip()
        nm = (it.get("name") or it.get("fullname") or sym).strip()
        why = (it.get("why") or it.get("reason") or "관련성 높은 자산").strip()
        lines.append(f"- **{sym}** — {nm} · {why}")
    return "\n".join(lines)

# -----------------------------
# 날짜 교정
# -----------------------------
def normalize_dates_in_body(body: str, picked: NewsItem, today_kst: datetime) -> str:
    src_text = f"{picked.title} {picked.summary or ''}"
    pattern = r"(20[1-2][0-9])년\s*(1[0-2]|[1-9])월"

    def repl(m):
        y, mm = m.group(1), m.group(2)
        matched = f"{y}년 {mm}월"
        if matched in src_text:
            return matched
        this_year = today_kst.year
        if int(y) != this_year:
            return f"{this_year}년 {mm}월"
        return matched

    return re.sub(pattern, repl, body)

# -----------------------------
# OpenAI: 단 한 번의 호출로 title/body/terms/related 생성
# -----------------------------
SEO_SYSTEM = (
    "You are an SEO-oriented Korean finance editor. "
    "Return strict JSON with keys: title, body_md, terms[], related[]. Keep titles <=60 chars. "
    "related must be a list of up to 6 objects with keys: symbol (ticker like TSLA/KRW=X/GC=F/SPY), "
    "name (short common name), why (1 short Korean phrase). "
    "Body must be markdown with sections: '# {title}', '## 오늘의 경제 이슈 한눈에 보기', "
    "'## 무슨 일이 있었나', '## 왜 중요한가', '## 투자자 체크포인트', '## 한줄 정리', '## Sources'. "
    "Avoid hype; be precise and neutral; cite only provided info; do not invent dates."
)

def ai_generate_all(
    item: NewsItem,
    today_str: str,
    article_context: str = "",
) -> Optional[Dict[str, Any]]:
    if _openai_client is None:
        print("[WARN] OpenAI client not initialized (check OPENAI_API_KEY)")
        return None

    # web_search는 Responses API에서만 지원. 모델은 gpt-4o 계열 권장

    extra_article = ""
    if article_context:
        extra_article = textwrap.fill(article_context.strip(), width=120)

    user_prompt = f"""
다음 RSS 경제 뉴스를 기반으로 한국어 SEO 포스트를 작성하세요.
- 오늘 날짜는 {today_str} 입니다. 날짜/시점 표기는 오늘 기준으로 하세요.
- 출력은 반드시 "유효한 JSON" 한 덩어리만 반환하세요. 서론/코드블록/설명 금지.
- JSON 키: title(<=60자), body_md(마크다운 본문), terms(최대 12개), related(최대 6개; 각 항목은 {{symbol,name,why}})
- 링크는 만들지 말고 Sources 섹션에는 소스명만 한 줄로 넣으세요.
- 추가 텍스트가 있다면 주요 수치와 배경을 반영해 더 깊이 있게 설명하세요.

입력 뉴스:
- 소스: {item.source}
- 제목: {item.title}
- 링크: {item.link}
- 요약: {item.summary[:800]}
{f"- 원문 추가 정보: {extra_article}" if extra_article else ""}

본문 섹션 규칙(제목 포함):
# <제목>
## 오늘의 경제 이슈 한눈에 보기
## 무슨 일이 있었나
## 왜 중요한가
## 투자자 체크포인트
## 한줄 정리
## Sources
"""

    try:
        resp = _openai_client.chat.completions.create(
            model=MODEL_NAME,                      
            temperature=min(TEMPERATURE, 0.3),
            max_tokens=max(4096, MAX_OUTPUT_TOKENS),
            # max_completion_tokens=max(4096, MAX_OUTPUT_TOKENS), # gpt-5-mini 에서 사용
            response_format={"type": "json_object"}, 
            messages=[
                {"role": "system", "content": SEO_SYSTEM},
                {"role": "user", "content": user_prompt}
            ],
        )

        # 표준 추출
        txt = resp.choices[0].message.content.strip()
        data = json.loads(txt)
        if not txt:
            try:
                blocks = getattr(resp, "output", [])
                collected: List[str] = []
                for block in blocks:
                    content_items = getattr(block, "content", []) or []
                    for content in content_items:
                        if getattr(content, "type", None) == "output_text":
                            text_obj = getattr(content, "text", None)
                            if text_obj is None:
                                continue
                            value = getattr(text_obj, "value", None)
                            if isinstance(value, str):
                                collected.append(value)
                            elif isinstance(text_obj, str):
                                collected.append(text_obj)
                if collected:
                    txt = "".join(collected)
            except Exception:
                pass
        if not txt:
            print("[WARN] Responses API: output_text 비어있음")
            return None

        txt = txt.strip()

        # 코드펜스/잡문 제거 → JSON만 추출
        import re, json as _json
        fence = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
        m = fence.match(txt)
        if m:
            txt = m.group(1).strip()
        if not (txt.startswith("{") and txt.endswith("}")):
            m2 = re.search(r"\{.*\}", txt, re.DOTALL)
            if m2:
                txt = m2.group(0).strip()

        try:
            data = _json.loads(txt)
        except _json.JSONDecodeError as decode_err:
            sanitized = _sanitize_json_text(txt)
            if sanitized != txt:
                try:
                    data = _json.loads(sanitized)
                    print("[WARN] AI JSON 개행 보정 후 파싱 성공")
                except _json.JSONDecodeError as decode_err2:
                    snippet = txt[:500]
                    print("[WARN] AI JSON 파싱 실패:", decode_err)
                    print("[WARN] 응답 일부:", snippet + ("…" if len(txt) > 500 else ""))
                    print("[WARN] 개행 보정 후에도 실패:", decode_err2)
                    return None
            else:
                snippet = txt[:500]
                print("[WARN] AI JSON 파싱 실패:", decode_err)
                print("[WARN] 응답 일부:", snippet + ("…" if len(txt) > 500 else ""))
                return None

        # 최소 유효성 검사/정규화
        if not isinstance(data, dict) or "title" not in data or "body_md" not in data:
            print("[WARN] AI 응답 형식 불일치:", type(data))
            return None

        title = str(data["title"]).strip().strip("「」\"' ")
        if len(title) > 60:
            title = title[:57].rstrip() + "…"
        data["title"] = title

        terms = data.get("terms")
        if not isinstance(terms, list): terms = []
        data["terms"] = [str(t).strip() for t in terms if str(t).strip()][:12]

        related = data.get("related")
        norm_related: List[Dict[str, str]] = []
        if isinstance(related, list):
            for it in related[:6]:
                if isinstance(it, dict):
                    sym = str(it.get("symbol") or it.get("ticker") or "").strip()
                    name = str(it.get("name") or it.get("fullname") or sym).strip()
                    why  = str(it.get("why") or it.get("reason") or "").strip()
                    if sym and name:
                        norm_related.append({"symbol": sym, "name": name, "why": why})
        data["related"] = norm_related

        print("[generate_post] ✅ web_search 기반 AI 생성 성공")
        return data

    except TypeError as te:
        print("[WARN] TypeError on responses.create:", te)
        # 만약 이 단계에서 'tools'도 지원 안 한다면, SDK가 더 오래된 것입니다.
        # 하지만 파일은 폴백으로 생성되도록 main()에서 처리하세요.
        return None
    except Exception as e:
        print("[WARN] AI 단일 호출(web_search) 실패:", repr(e))
        traceback.print_exc()
        return None


# -----------------------------
# 본문 + 프론트매터 구성
# -----------------------------
def build_internal_links(max_links: int = 3) -> str:
    if not INTERNAL_LINKS:
        return ""
    picks = random.sample(INTERNAL_LINKS, k=min(max_links, len(INTERNAL_LINKS)))
    lines = ["\n---\n", "### 더 읽어보기"]
    for text, href in picks:
        lines.append(f"- [{text}]({href})")
    return "\n".join(lines)

def to_markdown_frontmatter(
    title: str,
    date_kst: datetime,
    category: str,
    tags: List[str],
    post_assets_dir: Optional[str],
    canonical_url: Optional[str],
    source_title: str,
    source_link: str,
) -> Dict[str, Any]:
    fm = {
        "layout": "post",
        "title": title,
        "subtitle": "오늘의 경제 이슈 한눈에 보기",
        "date": date_kst.strftime("%Y-%m-%d %H:%M:%S %z"),
        "tags": tags,
        "categories": [category],
        "lang": "ko",
        "timezone": TIMEZONE,
        "canonical_url": canonical_url,
        "description": f"{title} · 경제 뉴스 요약",
        "keywords": [title] + tags,
        "source_link": source_link,
        "source_title": source_title,
        "author": AUTHOR,
        "catalog": True,
    }
    if post_assets_dir:
        fm["post_assets"] = post_assets_dir
    return fm

def write_post_file(filename: Path, fm: Dict[str, Any], body_md: str) -> None:
    post = frontmatter.Post(body_md, **fm)
    ensure_dir(filename.parent)
    filename.write_text(frontmatter.dumps(post), encoding="utf-8")
    print(f"[generate_post] Wrote: {filename}")

# -----------------------------
# 메인 로직
# -----------------------------
def extract_terms_rule_based(seo_title: str, item: NewsItem) -> List[str]:
    # (현재는 미사용. 필요 시 fallback 용도로 유지)
    base = f"{seo_title} {item.title} {item.summary}"
    extra = set()
    for w in re.findall(r"[A-Za-z][A-Za-z0-9&.\-]{1,20}", base):
        if len(w) >= 2 and not w.isdigit():
            extra.add(w)
    for w in re.findall(r"[가-힣A-Za-z0-9&.\-]{2,20}", base):
        if len(w) >= 2:
            extra.add(w)
    macro = [
        "금리", "달러", "환율", "유가", "비트코인", "인플레이션", "채권", "국채",
        "반도체", "AI", "엔비디아", "삼성전자", "TSMC", "애플", "마이크로소프트", "구글", "아마존",
    ]
    extra.update(macro)
    out, seen = [], set()
    for t in list(extra):
        t2 = t.strip()
        if t2 and t2.lower() not in seen:
            out.append(t2)
            seen.add(t2.lower())
        if len(out) >= 12:
            break
    return out

def main():
    ensure_dir(POSTS_DIR)

    print("[generate_post] Fetching RSS…")
    all_items = fetch_news_from_rss()
    if not all_items:
        raise RuntimeError("RSS에서 항목을 찾지 못했습니다.")

    used_links = load_used_links()

    KEYWORDS = [
        "Fed", "연준", "금리", "CPI", "인플레이션", "환율", "달러", "엔", "유가",
        "주가", "코스피", "나스닥", "S&P", "실적", "실업", "성장", "GDP", "ECB",
        "채권", "수익률", "비트코인", "테슬라", "삼성", "TSMC", "엔비디아",
    ]

    def score_item(it: NewsItem) -> int:
        t = f"{it.title} {it.summary}".lower()
        score = sum(1 for k in KEYWORDS if k.lower() in t)
        score += 1 if it.source in ["Reuters Business", "MarketWatch Top Stories", "CNBC Top News & Analysis"] else 0
        return score

    ranked = sorted(all_items, key=score_item, reverse=True)[:40]

    desired_posts = max(1, int(os.getenv("POST_COUNT", "5")))
    session_excluded: Set[str] = set()
    created_posts = 0

    summaries: List[Dict[str, Any]] = []

    while created_posts < desired_posts:
        picked = pick_not_used(ranked, used_links, session_excluded)
        if not picked:
            if created_posts == 0:
                print("[generate_post] 유사도 회피 실패 → OpenAI 호출 없이 종료")
            else:
                print("[generate_post] 추가로 선택할 RSS 항목이 없습니다.")
            break

        session_excluded.add(picked.link)
        print(f"[generate_post] Picked ({created_posts + 1}/{desired_posts}): {picked.source}: {picked.title}")

        today = now_kst()
        today_str = today.strftime("%Y-%m-%d (%Z)")

        # === 단 한 번의 OpenAI 호출 ===
        article_context = fetch_article_content(picked.link)
        ai_data = ai_generate_all(picked, today_str, article_context=article_context)
        if not ai_data:
            print("[generate_post] OpenAI 응답 실패로 해당 게시글 생성을 건너뜁니다.")
            continue

        seo_title = ai_data.get("title") or picked.title
        body = ai_data.get("body_md") or ""
        terms = ai_data.get("terms") or []
        related = ai_data.get("related") or []

        # 날짜 교정
        body = normalize_dates_in_body(body, picked, today)

        # 관련 종목 섹션 (OpenAI 제안 기반; 없으면 기본값)
        body += "\n" + related_md_from_ai(related)

        # 내부링크(옵션)
        body += build_internal_links()

        # 파일명/슬러그
        slug = to_slug(seo_title)
        base_filename = POSTS_DIR / f"{today.strftime('%Y-%m-%d')}-{slug}{OUTPUT_EXT}"
        filename = ensure_unique_path(base_filename)

        # 프론트매터
        category = "Economy"
        tags = ["경제", "시장", "투자", "뉴스요약", "Finance"]
        assets_stem = filename.stem
        post_assets_dir = f"/assets/posts/{assets_stem}"
        canonical_url = picked.link

        fm = to_markdown_frontmatter(
            title=seo_title,
            date_kst=today,
            category=category,
            tags=tags,
            post_assets_dir=post_assets_dir,
            canonical_url=canonical_url,
            source_title=picked.title,
            source_link=picked.link,
        )

        # 파일 기록
        write_post_file(filename, fm, body)

        # 사용한 RSS 링크 기록 (중복 방지)
        if picked.link:
            used_links.append(picked.link)
            save_used_links(used_links)

        summaries.append({
            "file": str(filename),
            "title": seo_title,
            "category": category,
            "tags": tags,
            "source": picked.source,
            "news_title": picked.title,
            "news_link": picked.link,
            "terms": terms,
            "related": related,
            "article_context_excerpt": article_context[:300] + ("…" if article_context and len(article_context) > 300 else ""),
        })

        created_posts += 1

    if summaries:
        print(json.dumps(summaries, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[generate_post] ERROR:", e)
        traceback.print_exc()
        raise
