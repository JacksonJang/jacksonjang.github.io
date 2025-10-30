#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_post.py
- 경제 뉴스 전용 자동 포스팅 스크립트
- RSS Source: Reuters Business, BBC Business, Investing.com, MarketWatch, Yahoo Finance, CNBC Top News & Analysis
- SEO 최적화된 제목/본문 생성 (OpenAI → 실패 시 규칙기반 대체)
- used_topics.json 로 중복/유사도 회피
- Jekyll용 Markdown 출력 (_posts/auto/YYYY-MM-DD-슬러그.md)
"""

import os
import re
import json
import time
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
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5")        # 필요 시 gpt-4o-mini 등
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "1.0"))  # gpt-5는 1.0만 허용되는 경우가 많음
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1400"))

TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
POSTS_DIR = Path(os.getenv("POSTS_DIR", "_posts/auto"))
OUTPUT_EXT = os.getenv("OUTPUT_EXT", ".md")
AUTHOR = os.getenv("POST_AUTHOR", "JacksonJang")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://jacksonjang.github.io")

USED_TOPICS_FILE = Path(os.getenv("USED_TOPICS_FILE", "data/used_topics.json"))
USED_TOPICS_LIMIT = int(os.getenv("USED_TOPICS_LIMIT", "400"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.72"))  # 0~1, 높을수록 엄격

# 내부 링크(있다면 자동 삽입). 없으면 비워두세요.
INTERNAL_LINKS = [
    # 예: (앵커텍스트, 상대링크)
    ("Spring Boot 예외 처리 가이드", "/spring-boot-exception-handler/"),
    ("GitHub Actions로 자동 글쓰기", "/automation-with-github-actions/"),
    ("ChatGPT 프롬프트 모음", "/best-chatgpt-prompts/"),
]

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
# OpenAI (chat.completions로 안전하게)
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_openai_client = None
_openai_chat = None
try:
    if OPENAI_API_KEY:
        # 구버전/신버전 호환: chat.completions 우선 사용
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
    return datetime.now(ZoneInfo(TIMEZONE))

def to_slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)  # 특수문자 제거
    s = re.sub(r"\s+", "-", s)      # 공백 -> 하이픈
    s = re.sub(r"-+", "-", s)       # 중복 하이픈 제거
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
    # 길이 제한 유지
    if len(titles) > USED_TOPICS_LIMIT:
        titles = titles[-USED_TOPICS_LIMIT:]
    USED_TOPICS_FILE.write_text(json.dumps(titles, ensure_ascii=False, indent=2), encoding="utf-8")

def is_similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def is_duplicate_or_similar(title: str, used_list: List[str]) -> bool:
    if title in used_list:
        return True
    for t in used_list[-200:]:  # 최근 200개만 엄격 비교
        if is_similar(title, t) >= SIMILARITY_THRESHOLD:
            return True
    return False

def pick_not_used(candidate_items: List[NewsItem], used_titles: List[str]) -> Optional[NewsItem]:
    # 최신순 정렬 후, 중복/유사도 아닌 첫 항목 선택
    candidate_items = sorted(candidate_items, key=lambda x: x.published or now_kst(), reverse=True)
    for item in candidate_items:
        if not is_duplicate_or_similar(item.title, used_titles):
            return item
    return None

# -----------------------------
# 피드 로딩
# -----------------------------
def parse_published(entry: Any) -> Optional[datetime]:
    # feedparser가 제공하는 published_parsed 우선
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(TIMEZONE))
    except Exception:
        pass
    # updated_parsed 백업
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
# SEO 타이틀/본문 생성
# -----------------------------
SEO_TITLE_SYSTEM = (
    "You are an SEO editor. Create concise, high-CTR Korean titles for a Korean tech/finance blog. "
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
        prompt = f"""아래 뉴스로부터 한국어 SEO 제목을 만들어 주세요.
- 55~60자 이내
- 핵심 키워드를 앞부분에
- 불필요한 수식/기호 금지
- 예: "연준 금리 동결, 인플레이션 우려 속 시장은 혼조"

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
            temperature=1.0,  # gpt-5 안전값
            n=1
        )
        text = resp.choices[0].message.content.strip()
        # 한 줄만 취함
        title = text.splitlines()[0].strip("「」\"' ")
        # 너무 길면 자름
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
        prompt = f"""아래 경제 뉴스를 기반으로 한국어 블로그 본문을 작성하세요.

요구사항:
- 900~1400자
- 섹션 구성:
  1) TL;DR (3줄 이내 핵심 요약)
  2) 무슨 일이 있었나 (사실 위주 요약)
  3) 왜 중요한가 (맥락·파급효과)
  4) 투자자 체크포인트 (불릿 3~5개)
  5) 용어 풀이 (있으면 2~4개)
  6) 마무리 한줄
- 과장/예측은 지양, 출처는 마지막에 'Sources' 섹션에서 링크 텍스트만 표기
- 자연스러운 한국어, 존중체(해요체/합니다체) 혼용 가능하나 과장 금지

입력:
SEO 제목: {seo_title}
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
            temperature=1.0,  # gpt-5 안전값
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
    # 간단 규칙 기반: 핵심 키워드 뽑아 재배열
    base = item.title
    base = re.sub(r"[-–—:|]+", " ", base).strip()
    base = re.sub(r"\s{2,}", " ", base)
    # 너무 길면 자르기
    if len(base) > 60:
        base = base[:57].rstrip() + "…"
    return base

def fallback_body(item: NewsItem, seo_title: str) -> str:
    parts = []
    parts.append("## TL;DR")
    parts.append("- 핵심 포인트를 중심으로 요약했습니다.")
    parts.append(f"- 원문: {item.source} 보도")
    parts.append("")
    parts.append("## 무슨 일이 있었나")
    parts.append(textwrap.fill((item.summary or item.title), width=80))
    parts.append("")
    parts.append("## 왜 중요한가")
    parts.append("- 거시경제·금리·환율 등과 연결되어 시장에 영향을 줄 수 있습니다.")
    parts.append("- 기업 실적, 업종 밸류에이션, 투자심리에 파급효과가 있습니다.")
    parts.append("")
    parts.append("## 투자자 체크포인트")
    parts.append("- 관련 지표(금리·물가·환율) 추이")
    parts.append("- 업종/테마별 수혜·피해 구분")
    parts.append("- 변동성 확대 구간의 리스크 관리")
    parts.append("- 장기 관점의 포트폴리오 균형")
    parts.append("")
    parts.append("## 용어 풀이")
    parts.append("- 변동성: 자산 가격의 등락 폭을 의미합니다.")
    parts.append("- 밸류에이션: 기업가치를 평가하는 지표(예: PER, PBR 등)입니다.")
    parts.append("")
    parts.append("## 한줄 정리")
    parts.append("핵심 정보만 추려 균형 잡힌 판단에 도움이 되도록 정리했습니다.")
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
    canonical_url: Optional[str] = None
) -> Dict[str, Any]:
    fm = {
        "layout": "post",
        "title": title,
        "subtitle": "",
        "date": date_kst.strftime("%Y-%m-%d %H:%M:%S"),
        "author": AUTHOR,
        "catalog": True,
        "categories": [category],
        "tags": tags,
    }
    if post_assets_dir:
        fm["post_assets"] = post_assets_dir
    if canonical_url:
        fm["canonical_url"] = canonical_url
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

    # 후보 필터링: 제목/요약에 시장/금리/환율/기업 키워드 가중치(가볍게)
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

    # 상위 스코어 40개 내에서 중복/유사도 회피하여 1개 선택
    ranked = sorted(all_items, key=score_item, reverse=True)[:40]
    picked = pick_not_used(ranked, used_titles)
    if not picked:
        # 그래도 없으면 최신 순에서 고름
        print("[generate_post] 유사도 회피 실패 → 최신으로 대체")
        latest_sorted = sorted(all_items, key=lambda x: x.published or now_kst(), reverse=True)
        picked = latest_sorted[0]

    # AI 생성
    print(f"[generate_post] Picked: {picked.source}: {picked.title}")
    seo_title = ai_generate_title(picked) or fallback_seo_title(picked)
    body = ai_generate_body(picked, seo_title) or fallback_body(picked, seo_title)

    # 내부링크 추가
    body += build_internal_links()

    # 파일명/슬러그
    today = now_kst()
    slug = to_slug(seo_title)
    filename = POSTS_DIR / f"{today.strftime('%Y-%m-%d')}-{slug}{OUTPUT_EXT}"

    # 프론트매터
    category = "Economy"
    tags = ["경제", "시장", "투자", "뉴스요약", "Finance"]
    post_assets_dir = f"/assets/posts/{today.strftime('%Y-%m-%d')}-{slug}"
    canonical_url = picked.link  # 원문 링크를 정식 출처로

    fm = to_markdown_frontmatter(
        title=seo_title,
        date_kst=today,
        category=category,
        tags=tags,
        post_assets_dir=post_assets_dir,
        canonical_url=canonical_url
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
