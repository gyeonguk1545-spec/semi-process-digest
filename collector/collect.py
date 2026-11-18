"""반도체 공정 기술 뉴스·논문 수집기 (AI 미사용).

하는 일
  1. config/sources.yaml 의 RSS · Google 뉴스 · arXiv 를 읽는다.
  2. config/taxonomy.yaml 키워드로 공정 태그를 붙인다.
  3. 이미 모은 글(링크·제목 기준)은 건너뛴다.
  4. data/items/YYYY-MM.jsonl 에 한 줄에 한 글씩 추가한다.

실행
  .venv\\Scripts\\python collector\\collect.py            # 수집
  .venv\\Scripts\\python collector\\collect.py --dry-run  # 저장 없이 결과만 출력
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
DATA = ROOT / "data" / "items"
UA = {"User-Agent": "Mozilla/5.0 (compatible; semi-process-digest/0.1)"}
SUMMARY_MAX = 300  # 저장할 요약 길이 (원문 전체를 저장하지 않음)


# ---------------------------------------------------------------- 태그
def load_taxonomy(path: Path) -> dict[str, list[re.Pattern]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    compiled: dict[str, list[re.Pattern]] = {}
    for tag, keywords in raw.items():
        pats = []
        for kw in keywords:
            kw = str(kw)
            esc = re.escape(kw)
            if kw.isascii():
                # 영문은 단어 경계로. 대문자 약어(ALD, CMP …)는 대소문자 구분.
                flags = 0 if (kw.isupper() and len(kw) <= 6) else re.IGNORECASE
                pats.append(re.compile(rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])", flags))
            else:
                pats.append(re.compile(esc, re.IGNORECASE))
        compiled[tag] = pats
    return compiled


def tag_text(text: str, taxonomy: dict[str, list[re.Pattern]]) -> list[str]:
    return [tag for tag, pats in taxonomy.items() if any(p.search(text) for p in pats)]


# ---------------------------------------------------------------- 정리 도구
def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def norm_title(title: str) -> str:
    # Google 뉴스 제목 끝의 " - 언론사" 제거 후 공백·기호 제거 → 중복 판정용
    title = re.sub(r"\s+-\s+[^-]{1,30}$", "", title)
    return re.sub(r"[\W_]+", "", title).lower()


def entry_time(e) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        t = e.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def fetch(url: str, timeout: int, retries: int = 2):
    for attempt in range(retries + 1):
        r = requests.get(url, headers=UA, timeout=timeout)
        if r.status_code == 429 and attempt < retries:  # 요청 과다 → 잠시 쉬고 재시도
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        return feedparser.parse(r.content)


# ---------------------------------------------------------------- 출처별
def iter_sources(cfg: dict):
    """(출처이름, 종류, url, filter여부) 를 차례로 돌려준다."""
    for s in cfg.get("rss", []):
        if s.get("enabled", True):
            yield s["name"], "news", s["url"], s.get("filter", True)
    for g in cfg.get("google_news", []):
        if g.get("enabled", True):
            q = quote_plus(g["query"])
            if g.get("lang") == "ko":
                url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
            else:
                url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
            yield f"Google뉴스: {g['query']}", "news", url, True
    ax = cfg.get("arxiv", {})
    for q in ax.get("queries", []):
        url = ("http://export.arxiv.org/api/query?search_query=" + quote_plus(q["q"])
               + f"&sortBy=submittedDate&sortOrder=descending&max_results={ax.get('max_results', 25)}")
        yield f"arXiv: {q['name']}", "paper", url, False


# ---------------------------------------------------------------- 저장소
def load_seen(months: int = 3) -> tuple[set[str], set[str]]:
    ids, titles = set(), set()
    for f in sorted(DATA.glob("*.jsonl"))[-months:]:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                ids.add(d["id"])
                titles.add(norm_title(d["title"]))
    return ids, titles


def save(items: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    by_month: dict[str, list[dict]] = {}
    for it in items:
        by_month.setdefault(it["collected_at"][:7], []).append(it)
    for month, rows in by_month.items():
        with open(DATA / f"{month}.jsonl", "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- 메인
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="저장하지 않고 결과만 출력")
    args = ap.parse_args()

    cfg = yaml.safe_load((CONFIG / "sources.yaml").read_text(encoding="utf-8"))
    taxonomy = load_taxonomy(CONFIG / "taxonomy.yaml")
    st = cfg.get("settings", {})
    timeout = st.get("request_timeout", 20)
    cutoff = datetime.now(timezone.utc) - timedelta(days=st.get("max_age_days", 30))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    seen_ids, seen_titles = load_seen()
    new_items: list[dict] = []
    report: list[tuple[str, str]] = []
    failures = 0

    for name, kind, url, use_filter in iter_sources(cfg):
        try:
            feed = fetch(url, timeout)
        except Exception as e:  # 한 출처가 실패해도 나머지는 계속
            failures += 1
            report.append((name, f"실패 ({type(e).__name__})"))
            continue
        added = skipped_old = skipped_dup = skipped_filter = 0
        for e in feed.entries:
            title = clean(e.get("title", ""))
            link = e.get("link", "")
            if not title or not link:
                continue
            published = entry_time(e)
            if published and published < cutoff:
                skipped_old += 1
                continue
            uid = hashlib.sha1(link.encode()).hexdigest()[:16]
            nt = norm_title(title)
            if uid in seen_ids or nt in seen_titles:
                skipped_dup += 1
                continue
            summary = clean(e.get("summary", ""))
            tags = tag_text(f"{title} {summary}", taxonomy)
            if use_filter and not tags:
                skipped_filter += 1
                continue
            new_items.append({
                "id": uid,
                "kind": kind,
                "source": name,
                "title": title,
                "link": link,
                "published": published.isoformat() if published else None,
                "summary": summary[:SUMMARY_MAX],
                "tags": tags or ["미분류"],
                "collected_at": now,
            })
            seen_ids.add(uid)
            seen_titles.add(nt)
            added += 1
        report.append((name, f"새 글 {added} · 중복 {skipped_dup} · 오래됨 {skipped_old} · 키워드없음 {skipped_filter}"))
        if name.startswith("arXiv"):
            time.sleep(st.get("arxiv_delay_sec", 3))
        elif name.startswith("Google"):
            time.sleep(st.get("google_delay_sec", 3))

    # ---- 결과 출력
    print(f"\n[수집 결과] {now}")
    for name, msg in report:
        print(f"  {name:34s} {msg}")
    counts: dict[str, int] = {}
    for it in new_items:
        for t in it["tags"]:
            counts[t] = counts.get(t, 0) + 1
    print(f"\n새 글 합계 {len(new_items)}건 / 태그별:")
    for t, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {t:10s} {n}")

    if args.dry_run:
        print("\n(--dry-run: 저장하지 않음)")
    elif new_items:
        save(new_items)
        print(f"\n저장: {DATA.relative_to(ROOT)}")

    total = sum(1 for _ in iter_sources(cfg))
    return 1 if failures == total else 0  # 전부 실패했을 때만 오류


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
