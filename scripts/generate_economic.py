#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Single-call OpenAI version of generate_post.py (with OpenAI-based related picks)
- RSS Source: Reuters, BBC, Investing.com, MarketWatch, Yahoo Finance, CNBC
- Exactly ONE OpenAI chat.completions call (title + body + terms + related in JSON)
- Related stocks/ETFs are proposed directly by OpenAI (no Yahoo Finance).
- Dedup via used_topics.json; fallback paths minimal for strict single-call design.
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

import frontmatter
import feedparser
import yaml

# -----------------------------
# 환경설정 (환경변수로 재정의 가능)
# -----------------------------
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "1.0"))  # gpt-5 권장 1.0
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
POSTS_DIR = Path(os.getenv("POSTS_DIR", "_posts/auto"))
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
AUTHOR = os.getenv("POST_AUTHOR", "JacksonJang")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://jacksonjang.github.io")

USED_TOPICS_FILE = Path(os.getenv("USED_TOPICS_FILE", "data/used_topics.json"))
USED_TOPICS_LIMIT = int(os.getenv("USED_TOPICS_LIMIT", "400"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.72"))  # 0~1, 높을수록 엄격

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

def ai_generate_all(item: NewsItem, today_str: str) -> Optional[Dict[str, Any]]:
    if _openai_client is None:
        print("[WARN] OpenAI client not initialized (check OPENAI_API_KEY)")
        return None

    try:
        user_prompt = f"""
다음 RSS 경제 뉴스를 기반으로 한국어 SEO 포스트를 작성하세요.
- 오늘 날짜는 {today_str} 입니다. 날짜/시점 표기는 오늘 기준으로 하세요.
- 출력은 반드시 JSON(UTF-8) 한 덩어리로 반환하세요.
- JSON 키: title(<=60자), body_md(마크다운 본문), terms(최대 12개), related(최대 6개; 각 항목은 {{symbol,name,why}})

입력 뉴스:
- 소스: {item.source}
- 제목: {item.title}
- 링크: {item.link}
- 요약: {item.summary[:800]}

본문 섹션 규칙:
# <제목>
## 오늘의 경제 이슈 한눈에 보기
## 무슨 일이 있었나
## 왜 중요한가
## 투자자 체크포인트
## 한줄 정리
## Sources
(필요 시 실제 출처로 소스명 1줄만 남기세요. 링크 생성 금지)
"""

        resp = _openai_client.responses.create(
            model=MODEL_NAME,
            tools=[{"type": "web_search"}],
            input=[
                {"role": "system", "content": SEO_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            format="json",
        )

        txt = resp.output_text.strip()
        data = json.loads(txt)

        if not isinstance(data, dict) or "title" not in data or "body_md" not in data:
            print("[WARN] AI 응답 형식 불일치:", data)
            return None

        # 제목 길이 정규화
        title = str(data["title"]).strip().strip("「」\"' ")
        if len(title) > 60:
            title = title[:57].rstrip() + "…"
        data["title"] = title

        # terms 정규화
        terms = data.get("terms") or []
        if not isinstance(terms, list):
            terms = []
        data["terms"] = [str(t).strip() for t in terms if str(t).strip()][:12]

        # related 정규화
        related = data.get("related") or []
        norm_related: List[Dict[str, str]] = []
        if isinstance(related, list):
            for it in related[:6]:
                if not isinstance(it, dict):
                    continue
                sym = str(it.get("symbol") or it.get("ticker") or "").strip()
                name = str(it.get("name") or it.get("fullname") or sym or "").strip()
                why = str(it.get("why") or it.get("reason") or "").strip()
                if sym and name:
                    norm_related.append({"symbol": sym, "name": name, "why": why})
        data["related"] = norm_related

        print("[generate_post] ✅ web_search 기반 AI 생성 성공")
        return data

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

    used_titles = load_used_topics()

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
    picked = pick_not_used(ranked, used_titles)
    if not picked:
        print("[generate_post] 유사도 회피 실패 → 최신으로 대체")
        picked = sorted(all_items, key=lambda x: x.published or now_kst(), reverse=True)[0]

    print(f"[generate_post] Picked: {picked.source}: {picked.title}")

    today = now_kst()
    today_str = today.strftime("%Y-%m-%d (%Z)")

    # === 단 한 번의 OpenAI 호출 ===
    ai_data = ai_generate_all(picked, today_str)
    if not ai_data:
        return  # 실패 시 조용히 종료(원하면 규칙기반 fallback로 바꿀 수 있음)

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
    filename = POSTS_DIR / f"{today.strftime('%Y-%m-%d')}-{slug}{OUTPUT_EXT}"

    # 프론트매터
    category = "Economy"
    tags = ["경제", "시장", "투자", "뉴스요약", "Finance"]
    post_assets_dir = f"/assets/posts/{today.strftime('%Y-%m-%d')}-{slug}"
    canonical_url = picked.link

    fm = to_markdown_frontmatter(
        title=seo_title,
        date_kst= today,
        category= category,
        tags= tags,
        post_assets_dir= post_assets_dir,
        canonical_url= canonical_url,
        source_title= picked.title,
        source_link= picked.link,
    )

    # 파일 기록
    write_post_file(filename, fm, body)

    # used_topics 갱신 (SEO 제목 기준으로 저장)
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
        "news_link": picked.link,
        "terms": terms,
        "related": related,
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[generate_post] ERROR:", e)
        traceback.print_exc()
        raise
