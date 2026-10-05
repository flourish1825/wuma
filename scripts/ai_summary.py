"""可选：用 Claude 为某周/某月/某年生成总结，写入 summaries/{kind}-{key}.md。

没有设置 ANTHROPIC_API_KEY 时直接跳过。
用法：
  python scripts/ai_summary.py                       # 自动：周一总结上周，1 号总结上月，1/1 总结去年
  python scripts/ai_summary.py --kind week --key 2026-W40 [--force]
"""
import argparse
import calendar
import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone

from common import ROOT, load_config, load_entries

BUDGET = 60000  # 送给模型的日记总字符预算
LENGTH = {"week": "300～500 字", "month": "500～800 字", "year": "800～1200 字"}
NAME = {"week": "这一周", "month": "这个月", "year": "这一年"}

SYSTEM = """你是一个朋友圈共享日记本的温柔编辑。读完大家在{span}写的日记后，用中文写一份总结，长度{length}，用 Markdown，结构如下：
## 主线
这段时间整体发生了什么、气氛如何。
## 每个人的亮点
每位朋友一两句，点到他/她最具体的经历或变化。
## 共同的话题
大家共同在意的事、有趣的巧合或呼应（没有就省略此节）。
## 情绪与节奏
心情的起伏与变化。
## 给下个阶段的小建议
1～2 条，轻松、具体。
要求：只依据日记内容，不编造；不评判、不说教；语气像懂你们的老朋友；不要复述隐私细节。"""


def span(kind, key):
    if kind == "week":
        y, w = key.split("-W")
        s = date.fromisocalendar(int(y), int(w), 1)
        return s, s + timedelta(days=6)
    if kind == "month":
        y, m = map(int, key.split("-"))
        return date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])
    return date(int(key), 1, 1), date(int(key), 12, 31)


def auto_periods(today):
    res = []
    if today.weekday() == 0:
        iso = (today - timedelta(days=7)).isocalendar()
        res.append(("week", f"{iso[0]}-W{iso[1]:02d}"))
    if today.day == 1:
        res.append(("month", (today - timedelta(days=1)).strftime("%Y-%m")))
        if today.month == 1:
            res.append(("year", str(today.year - 1)))
    return res


def call_claude(system, user):
    base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    req = urllib.request.Request(
        base + "/v1/messages",
        data=json.dumps({
            "model": os.environ.get("SUMMARY_MODEL", "claude-sonnet-5-5"),
            "max_tokens": 2000,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }).encode(),
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    return "".join(b.get("text", "") for b in data["content"]).strip()


def summarize(kind, key, entries, members, force):
    out = ROOT / "summaries" / f"{kind}-{key}.md"
    if out.exists() and not force:
        print(f"已存在，跳过 {out.name}")
        return False
    s, e = span(kind, key)
    picked = [x for x in entries if s.isoformat() <= x["date"] <= e.isoformat()]
    if not picked:
        print(f"{kind}-{key} 没有日记，跳过")
        return False
    per = max(300, BUDGET // len(picked))
    text = "\n\n".join(
        f"【{x['date']} {members.get(x['author'], x['author'])} {x['mood']}】\n{x['body'][:per]}" for x in picked
    )
    system = SYSTEM.format(span=NAME[kind], length=LENGTH[kind])
    result = call_claude(system, f"共 {len(picked)} 篇日记：\n\n{text}")
    out.parent.mkdir(exist_ok=True)
    out.write_text(result + "\n", encoding="utf-8")
    print(f"已生成 {out.name}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default=os.environ.get("SUMMARY_KIND", ""), choices=["", "week", "month", "year"])
    ap.add_argument("--key", default=os.environ.get("SUMMARY_KEY", ""))
    ap.add_argument("--force", action="store_true", default=os.environ.get("SUMMARY_FORCE") == "true")
    a = ap.parse_args()

    changed = False
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("未设置 ANTHROPIC_API_KEY，跳过 AI 总结")
    else:
        cfg = load_config()
        tz = timezone(timedelta(hours=cfg.get("timezone_offset", 8)))
        entries, members = load_entries(), cfg.get("members", {})
        todo = [(a.kind, a.key)] if a.kind and a.key else auto_periods(datetime.now(tz).date())
        for kind, key in todo:
            changed |= summarize(kind, key, entries, members, a.force)

    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
