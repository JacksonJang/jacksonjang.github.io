#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_post.py
- 경제 뉴스 전용 자동 포스팅 스크립트
- RSS Source: Reuters Business, BBC Business, Investing.com, MarketWatch, Yahoo Finance, CNBC Top News & Analysis
- SEO 최적화된 제목/본문 생성 (OpenAI → 실패 시 규칙기반 대체)
- used_topics.json 로 중복/유사도 회피
- Jekyll용 Markdown 출력 (_posts/auto/YYYY-MM-DD-슬러그.md)
- '용어 풀이' 섹션 제거, '관련 종목' 섹션은 Yahoo Finance 검색 기반 자동 추천
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
from difflib import SequenceMatcher
from typing import List, Optional, Dict, Any

import requests
import frontmatter
import feedparser
import yaml

# -----------------------------
# 환경설정 (환경변수로 재정의 가능)
# -----------------------------
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # 필요 시 gpt-4o-mini 등
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "1.0"))  # gpt-5는 1.0 권장
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
POSTS_DIR = Path(os.getenv("POSTS_DIR", "_posts/auto"))
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
AUTHOR = os.getenv("POST_AUTHOR", "JacksonJang")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://jacksonjang.github.io")

USED_TOPICS_FILE = Path(os.getenv("USED_TOPICS_FILE", "data/used_topics.json"))
USED_TOPICS_LIMIT = int(os.getenv("USED_TOPICS_LIMIT", "400"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.72"))  # 0~1, 높을수록 엄격

# 내부 링크(있다면 자동 삽입). 없으면 비워두세요.
INTERNAL_LINKS = []

# 검색 기반 관련 종목 켜기/끄기
USE_WEB_SEARCH = os.getenv("USE_WEB_SEARCH", "true").lower() == "true"

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
# OpenAI (chat.completions)
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

# ↓ 기존 상단 util 근처에 추가
def normalize_dates_in_body(body: str, picked: NewsItem, today_kst: datetime) -> str:
    """
    본문 내 'YYYY년 M월' 같은 절대 날짜가 원문에 명시되어 있지 않은데
    과거 연도(예: 2023)가 들어가면 게시일(오늘) 기준으로 교정한다.
    - 원문(title/summary)에 같은 연-월 문자열이 있으면 그대로 둔다(사실 보존).
    """
    src_text = f"{picked.title} {picked.summary or ''}"
    # 찾을 패턴: 2019~2024년, (1~12)월
    pattern = r"(20[1-2][0-9])년\s*(1[0-2]|[1-9])월"

    def repl(m):
        y, mm = m.group(1), m.group(2)
        matched = f"{y}년 {mm}월"
        if matched in src_text:
            return matched  # 원문에 있으면 보존
        # 원문에 없는데 과거 연도면 오늘의 연도로 교정
        this_year = today_kst.year
        if int(y) != this_year:
            return f"{this_year}년 {mm}월"
        return matched

    return re.sub(pattern, repl, body)

def now_kst() -> datetime:
    # 혹시 런너에 tzdata가 없어도 KST 오프셋 포함되게 보정
    try:
        return datetime.now(ZoneInfo(TIMEZONE))
    except Exception:
        # tzdata 미설치 대비: +09:00 수동 보정 (표시용)
        return datetime.utcnow().replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Seoul"))

def to_slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s

def load_used_topics() -> List[str]:
    if USED_TOPICS_FILE.exists():
        try:
            data = json.loads(USED_TOPICS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []

def save_used_topics(titles: List[str]) -> None:
    ensure_dir(USED_TOPICS_FILE.parent)
    if len(titles) > USED_TOPICS_LIMIT:
        titles = titles[-USED_TOPICS_LIMIT:]
    USED_TOPICS_FILE.write_text(json.dumps(titles, ensure_ascii=False, indent=2), encoding="utf-8")

def is_similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def is_duplicate_or_similar(title: str, used_list: List[str]) -> bool:
    if title in used_list:
        return True
    for t in used_list[-200:]:
        if is_similar(title, t) >= SIMILARITY_THRESHOLD:
            return True
    return False

def pick_not_used(candidate_items: List[NewsItem], used_titles: List[str]) -> Optional[NewsItem]:
    candidate_items = sorted(candidate_items, key=lambda x: x.published or now_kst(), reverse=True)
    for item in candidate_items:
        if not is_duplicate_or_similar(item.title, used_titles):
            return item
    return None

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
    for src in RSS_SOURCES:
        try:
            feed = feedparser.parse(src["url"])
            for e in feed.entries[:30]:
                title = html.unescape(getattr(e, "title", "")).strip()
                link = getattr(e, "link", "").strip()
                summary = html.unescape(getattr(e, "summary", "")).strip() if hasattr(e, "summary") else ""
                published = parse_published(e)
                if title and link:
                    items.append(NewsItem(src["name"], title, link, summary, published))
        except Exception as ex:
            print(f"[WARN] RSS 실패: {src['name']} - {ex}")
    return items

# -----------------------------
# 검색 기반 관련 종목 추천 (Yahoo Finance Search)
# -----------------------------
YF_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"

def extract_query_terms(item: NewsItem, seo_title: str) -> List[str]:
    """제목/요약에서 검색어 후보(기업/상품/테마) 3~12개 추출"""
    base = f"{seo_title} {item.title} {item.summary}"
    terms: List[str] = []

    # 1) OpenAI로 엔터티 추출(가능 시)
    if _openai_chat is not None:
        try:
            prompt = f"""아래 문장에서 주식/ETF/원자재/환율 관련 '검색 키워드' 5~8개만 콤마로 출력.
기업명(영문/국문), 제품/서비스, 티커/약칭, 자산(금·유가·달러 등) 중심. 군더더기 금지.

문장:
{base[:1500]}"""
            resp = _openai_chat.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You extract finance-related search terms."},
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0,
                n=1
            )
            raw = resp.choices[0].message.content.strip()
            terms = [t.strip() for t in raw.replace("\n", ",").split(",") if t.strip()]
        except Exception:
            terms = []

    # 2) 규칙 기반 보완
    extra = set()
    for w in re.findall(r"[A-Za-z][A-Za-z0-9&.\-]{1,20}", base):
        if len(w) >= 2 and not w.isdigit():
            extra.add(w)
    for w in re.findall(r"[가-힣A-Za-z0-9&.\-]{2,20}", base):
        if len(w) >= 2:
            extra.add(w)

    macro = ["금리", "달러", "환율", "유가", "비트코인", "인플레이션", "채권", "국채",
             "반도체", "AI", "엔비디아", "삼성전자", "TSMC", "애플", "마이크로소프트", "구글", "아마존"]
    extra.update(macro)

    merged = []
    seen = set()
    for t in (terms + list(extra)):
        t2 = t.strip()
        if t2 and t2.lower() not in seen:
            merged.append(t2)
            seen.add(t2.lower())
        if len(merged) >= 12:
            break
    return merged

def yf_search_one(q: str, lang="ko-KR", region="KR", quotes_count=5) -> List[dict]:
    """Yahoo Finance 검색 1회"""
    try:
        r = requests.get(
            YF_SEARCH_URL,
            params={"q": q, "lang": lang, "region": region, "quotesCount": quotes_count, "newsCount": 0},
            timeout=6,
        )
        if r.status_code == 200:
            js = r.json()
            return js.get("quotes", []) or []
    except Exception:
        pass
    return []

def score_quote(q: dict) -> float:
    """검색 결과 스코어링: 종목/ETF 우선, 거래소 가중치, 매칭 강도"""
    score = 0.0
    qt = (q.get("quoteType") or "").upper()
    exch = (q.get("exchDisp") or "").upper()
    nm = (q.get("shortname") or q.get("longname") or q.get("symbol") or "").lower()

    if qt in {"EQUITY", "ETF"}:
        score += 2.0
    if any(x in exch for x in ["KOREA", "KOSPI", "KOSDAQ", "NYSE", "NASDAQ"]):
        score += 1.0
    score += max(0.0, 1.0 - (len(nm) / 60.0))
    return score

def dedup_quotes(quotes: List[dict], limit=6) -> List[dict]:
    out = []
    seen = set()
    for q in sorted(quotes, key=score_quote, reverse=True):
        sym = q.get("symbol")
        nm = q.get("shortname") or q.get("longname") or ""
        key = (sym, nm)
        if sym and key not in seen:
            out.append(q)
            seen.add(key)
        if len(out) >= limit:
            break
    return out

def search_related_stocks(item: NewsItem, seo_title: str) -> List[tuple]:
    """
    검색 기반 추천: (SYMBOL, NAME, WHY) 리스트
    - KR → US 순서로 검색
    - 실패 시 기본값 반환
    """
    if not USE_WEB_SEARCH:
        return []
    terms = extract_query_terms(item, seo_title)
    all_quotes: List[dict] = []

    for region in ["KR", "US"]:
        for t in terms:
            if len(t) < 2:
                continue
            qs = yf_search_one(t, lang="ko-KR", region=region, quotes_count=5)
            for q in qs:
                qt = (q.get("quoteType") or "").upper()
                if qt in {"EQUITY", "ETF", "CRYPTOCURRENCY", "INDEX"}:
                    all_quotes.append(q)

    picks = dedup_quotes(all_quotes, limit=6)
    if not picks:
        return [("SPY", "SPDR S&P 500", "미국 대형주 분산"), ("ACWI", "MSCI ACWI", "글로벌 분산")]

    results = []
    for q in picks:
        sym = q.get("symbol")
        nm = q.get("shortname") or q.get("longname") or sym
        qt = (q.get("quoteType") or "").upper()
        why = {
            "EQUITY": "핵심 관련 기업",
            "ETF": "관련 테마/섹터 ETF",
            "CRYPTOCURRENCY": "디지털 자산 테마",
            "INDEX": "관련 지수",
        }.get(qt, "관련 자산")
        results.append((sym, nm, why))
    return results

def related_stocks_md(item: NewsItem, seo_title: str) -> str:
    picks = search_related_stocks(item, seo_title)
    if not picks:
        picks = [("SPY", "SPDR S&P 500", "미국 대형주 분산"), ("ACWI", "MSCI ACWI", "글로벌 분산")]

    lines = ["\n## 관련 종목", "검색 기반으로 연관성이 높은 종목/ETF를 제안합니다. (투자 권유 아님)"]
    for tk, nm, why in picks:
        lines.append(f"- **{tk}** — {nm} · {why}")
    return "\n".join(lines)

# -----------------------------
# SEO 타이틀/본문 생성
# -----------------------------
SEO_TITLE_SYSTEM = (
    "You are an SEO editor. Create concise, high-CTR Korean titles for a Korean finance blog. "
    "Keep it under 60 characters, avoid clickbait, include the main keyword early, and prefer entity names."
)

SEO_BODY_SYSTEM = (
    "You are a finance/economy editor writing in Korean for an educated general audience. "
    "Write clear, structured, and scannable posts with short paragraphs and bullet points. "
    "Tone: neutral, explanatory, practical. Avoid hype. Include concrete numbers if present in the brief."
)

def ai_generate_title(item: NewsItem) -> Optional[str]:
    if _openai_chat is None:
        return None
    try:
        prompt = f"""아래 경제 뉴스로부터 한국어 SEO 제목을 만들어 주세요.
- 55~60자 이내
- 핵심 키워드를 앞부분에
- 불필요한 수식/기호 금지

뉴스 제목: {item.title}
소스: {item.source}
링크: {item.link}
요약(있다면): {item.summary[:500]}
"""
        resp = _openai_chat.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SEO_TITLE_SYSTEM},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0,
            n=1
        )
        text = resp.choices[0].message.content.strip()
        title = text.splitlines()[0].strip("「」\"' ")
        if len(title) > 60:
            title = title[:57].rstrip() + "…"
        return title
    except Exception as e:
        print("[WARN] AI 제목 생성 실패:", e)
        return None

def ai_generate_body(item: NewsItem, seo_title: str) -> Optional[str]:
    if _openai_chat is None:
        return None
    try:
        prompt = f"""아래 경제 뉴스를 기반으로 한국어 md 본문을 작성하세요.
형식/섹션(고정):
# {seo_title}
## 오늘의 경제 이슈 한눈에 보기

주의:
- 모든 날짜/시점 서술은 게시일({today_kst}) 기준으로 작성하세요.
- 원문에 '구체적 과거 날짜(연/월/일)'가 명시된 경우에만 그 과거 날짜를 인용하세요.
- 과장, 확정적 표현 금지. 전망은 '가능성' 수준.
- 마크다운 문법 준수, 한국어 작성.
- '용어 풀이' 섹션은 포함하지 말 것.

## 핵심 요약
(핵심 2~3줄)

## 무슨 일이 있었나
(사실 위주 요약: 수치/날짜/주체)

## 왜 중요한가
(맥락·파급효과: 거시/업종/기업 관점)

## 투자자 체크포인트
- 불릿 3~5개 (금리/환율/수요·공급/밸류에이션/리스크 등)

## 간단 Q&A
- **Q:** (핵심 의문 1)
  **A:** (간결 답변)
- **Q:** (핵심 의문 2)
  **A:** (간결 답변)

## 한줄 정리
(요지 1문장)

## Sources
- {item.source}

주의:
- 과장, 확정적 표현 금지. 전망은 '가능성' 수준.
- 마크다운 문법 준수, 한국어 작성.
- '용어 풀이' 섹션은 포함하지 말 것.
입력:
원문 제목: {item.title}
요약(있다면): {item.summary[:800]}
링크: {item.link}
소스: {item.source}
"""
        resp = _openai_chat.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SEO_BODY_SYSTEM},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0,
            n=1
        )
        body = resp.choices[0].message.content.strip()
        return body
    except Exception as e:
        print("[WARN] AI 본문 생성 실패:", e)
        return None

# -----------------------------
# 대체(백업) 생성기: AI 실패 시 사용
# -----------------------------
def fallback_seo_title(item: NewsItem) -> str:
    base = item.title
    base = re.sub(r"[-–—:|]+", " ", base).strip()
    base = re.sub(r"\s{2,}", " ", base)
    if len(base) > 60:
        base = base[:57].rstrip() + "…"
    return base

def fallback_body(item: NewsItem, seo_title: str) -> str:
    parts = []
    parts.append(f"# {seo_title}")
    parts.append("## 오늘의 경제 이슈 한눈에 보기\n")
    parts.append(f"- 원문: {item.source}")
    parts.append("")
    parts.append("## 무슨 일이 있었나")
    parts.append(textwrap.fill((item.summary or item.title), width=80))
    parts.append("")
    parts.append("## 왜 중요한가")
    parts.append("- 거시(금리·환율)와 업종/기업 실적에 파급효과가 있을 수 있습니다.")
    parts.append("- 투자심리/밸류에이션 변수로 작용할 수 있습니다.")
    parts.append("")
    parts.append("## 투자자 체크포인트")
    parts.append("- 핵심 지표(금리·물가·환율) 방향")
    parts.append("- 업종/테마별 수혜·피해 분화")
    parts.append("- 변동성 구간의 리스크 관리")
    parts.append("- 현금흐름/밸류에이션 점검")
    parts.append("")
    parts.append("## 간단 Q&A")
    parts.append("- **Q:** 이번 이슈의 변곡점은?")
    parts.append("  **A:** 정책/지표 발표 일정과 가이던스 변화가 관건입니다.")
    parts.append("- **Q:** 단기 대응은?")
    parts.append("  **A:** 이벤트 전후 변동성 확대에 대비해 분할/분산이 유효합니다.")
    parts.append("")
    parts.append("## 한줄 정리")
    parts.append("핵심 정보를 바탕으로 균형 잡힌 시각을 유지하세요.")
    parts.append("")
    parts.append("## Sources")
    parts.append(f"- {item.source}")
    return "\n".join(parts)

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
        "date": date_kst.strftime("%Y-%m-%d %H:%M:%S %z"),  # +0900 포함
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
def main():
    ensure_dir(POSTS_DIR)

    print("[generate_post] Fetching RSS…")
    all_items = fetch_news_from_rss()
    if not all_items:
        raise RuntimeError("RSS에서 항목을 찾지 못했습니다.")

    used_titles = load_used_topics()

    KEYWORDS = [
        "Fed", "연준", "금리", "CPI", "인플레이션", "환율", "달러", "엔", "유가",
        "주가", "코스피", "나스닥", "S&P", "실적", "실업", "성장", "GDP", "ECB",
        "채권", "수익률", "비트코인", "테슬라", "삼성", "TSMC", "엔비디아"
    ]

    def score_item(it: NewsItem) -> int:
        t = f"{it.title} {it.summary}".lower()
        score = sum(1 for k in KEYWORDS if k.lower() in t)
        score += 1 if it.source in ["Reuters Business", "MarketWatch Top Stories", "CNBC Top News & Analysis"] else 0
        return score

    ranked = sorted(all_items, key=score_item, reverse=True)[:40]
    picked = pick_not_used(ranked, used_titles)
    if not picked:
        print("[generate_post] 유사도 회피 실패 → 최신으로 대체")
        picked = sorted(all_items, key=lambda x: x.published or now_kst(), reverse=True)[0]

    print(f"[generate_post] Picked: {picked.source}: {picked.title}")
    seo_title = ai_generate_title(picked) or fallback_seo_title(picked)
    today = now_kst()
    body = ai_generate_body(picked, seo_title) or fallback_body(picked, seo_title)
    body = normalize_dates_in_body(body, picked, today)  # ← 추가

    # 검색 기반 '관련 종목' 섹션 추가
    body += "\n" + related_stocks_md(picked, seo_title)

    # 내부링크(옵션)
    body += build_internal_links()

    # 파일명/슬러그
    today = now_kst()
    slug = to_slug(seo_title)
    filename = POSTS_DIR / f"{today.strftime('%Y-%m-%d')}-{slug}{OUTPUT_EXT}"

    # 프론트매터
    category = "Economy"
    tags = ["경제", "시장", "투자", "뉴스요약", "Finance"]
    post_assets_dir = f"/assets/posts/{today.strftime('%Y-%m-%d')}-{slug}"
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

    # used_topics 갱신
    used_titles.append(seo_title)
    save_used_topics(used_titles)

    # 로그 출력
    print(json.dumps({
        "file": str(filename),
        "title": seo_title,
        "category": category,
        "tags": tags,
        "source": picked.source,
        "news_title": picked.title,
        "news_link": picked.link
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[generate_post] ERROR:", e)
        traceback.print_exc()
        raise
