"""주간 글 작성용 입력 파일 만들기 (AI 미사용).

지난 7일간 수집한 글을 태그별로 묶어 짧은 목록(markdown)으로 만든다.
Claude Code 는 전체 jsonl 대신 이 파일만 읽으면 되므로 구독 사용량이 줄어든다.

실행
  .venv\\Scripts\\python collector\\week_input.py             # 오늘 기준 지난 7일
  .venv\\Scripts\\python collector\\week_input.py --end 2026-11-23
출력
  data/weekly/<ISO주차>_input.md   (예: 2026-W47_input.md)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "data" / "items"
OUT = ROOT / "data" / "weekly"
POSTS = ROOT / "site" / "content" / "posts"
TAG_ORDER = ["노광", "식각", "증착", "배선", "트랜지스터", "메모리", "패키징",
             "계측검사", "CMP세정", "이온주입열처리", "내연구연결", "미분류"]


def item_time(d: dict) -> datetime:
    return datetime.fromisoformat(d.get("published") or d["collected_at"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--end", help="마지막 날 YYYY-MM-DD (기본: 오늘)")
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()

    end_day = date.fromisoformat(args.end) if args.end else datetime.now(timezone.utc).date()
    end = datetime.combine(end_day + timedelta(days=1), datetime.min.time(), timezone.utc)
    start = end - timedelta(days=args.days)
    year, week, _ = end_day.isocalendar()
    week_id = f"{year}-W{week:02d}"

    items = []
    for f in sorted(ITEMS.glob("*.jsonl"))[-2:]:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                if start <= item_time(d) < end:
                    items.append(d)
    items.sort(key=item_time, reverse=True)

    by_tag: dict[str, list[dict]] = {}
    for d in items:
        primary = next((t for t in TAG_ORDER if t in d["tags"]), d["tags"][0])
        by_tag.setdefault(primary, []).append(d)

    lines = [
        f"# {week_id} 주간 입력 ({start.date()} ~ {end_day}, {len(items)}건)",
        "",
        "형식: [번호] (종류·출처·날짜) 제목 — 태그 / 요약 일부 / 링크",
        "",
    ]
    n = 0
    for tag in TAG_ORDER + [t for t in by_tag if t not in TAG_ORDER]:
        rows = by_tag.get(tag)
        if not rows:
            continue
        lines.append(f"## {tag} ({len(rows)})")
        for d in rows:
            n += 1
            kind = "논문" if d["kind"] == "paper" else "뉴스"
            day = item_time(d).date()
            lines.append(f"[{n}] ({kind}·{d['source']}·{day}) {d['title']} — {','.join(d['tags'])}")
            if d.get("summary"):
                lines.append(f"    {d['summary'][:160]}")
            lines.append(f"    {d['link']}")
        lines.append("")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{week_id}_input.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"{path.relative_to(ROOT)}  ({len(items)}건)")

    counts = {t: len(by_tag[t]) for t in TAG_ORDER if t in by_tag}
    chart = POSTS / week_id / "tags.svg"
    tag_chart(counts, chart, f"{start.date()} ~ {end_day}")
    print(f"{chart.relative_to(ROOT)}  (태그별 건수 그림)")
    return 0


def tag_chart(counts: dict[str, int], path: Path, period: str) -> None:
    """주간 태그별 건수 가로 막대 그림 (글 폴더에 tags.svg 로 저장)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from matplotlib import font_manager
    installed = {f.name for f in font_manager.fontManager.ttflist}
    korean = [f for f in ("Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR") if f in installed]
    plt.rcParams["font.family"] = korean[:1] + ["DejaVu Sans"]
    plt.rcParams["svg.fonttype"] = "none"
    items = sorted(counts.items(), key=lambda x: (x[0] == "미분류", -x[1]))
    labels = [k for k, _ in items][::-1]
    values = [v for _, v in items][::-1]
    colors = ["#a0a6ad" if k == "미분류" else "#2b6cb0" for k in labels]

    fig, ax = plt.subplots(figsize=(7.5, 0.42 * len(labels) + 1.1), dpi=100)
    bars = ax.barh(labels, values, color=colors, height=0.62)
    for b, v in zip(bars, values):
        ax.text(b.get_width() + max(values) * 0.015, b.get_y() + b.get_height() / 2,
                str(v), va="center", fontsize=10, color="#1f2328")
    ax.set_title(f"이번 주 수집 글 — 대표 태그별 건수 ({period})", fontsize=12, loc="left", color="#1f2328")
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    ax.spines["left"].set_color("#c9cdd2")
    ax.tick_params(axis="x", colors="#8a9099", labelsize=9)
    ax.tick_params(axis="y", length=0, labelsize=10.5, colors="#1f2328")
    ax.xaxis.grid(True, color="#eceee9", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(values) * 1.12)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
