"""共用工具：读取配置、解析日记文件（Markdown + 简易 front matter）。"""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONT = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n?(.*)\Z", re.S)
NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:-(.+))?$")


def load_config():
    p = ROOT / "config.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else {}


def parse_entry(path: Path):
    text = path.read_text("utf-8").lstrip("﻿")
    meta, body = {}, text
    m = FRONT.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip("\"'")
        body = m.group(2)
    nm = NAME_RE.match(path.stem)
    d = meta.get("date") or (nm.group(1) if nm else "")
    try:
        date.fromisoformat(d)
    except ValueError:
        print(f"跳过（日期无效）: {path}")
        return None
    author = meta.get("author") or (nm.group(2) if nm and nm.group(2) else "匿名")
    author = re.sub(r"-\d+$", "", author)  # 同一天多篇时文件名带 -2、-3
    return {
        "id": path.relative_to(ROOT).as_posix(),
        "date": d,
        "author": author,
        "mood": meta.get("mood", ""),
        "body": body.strip(),
    }


def load_entries():
    out = []
    for p in sorted((ROOT / "entries").rglob("*.md")):
        e = parse_entry(p)
        if e and e["body"]:
            out.append(e)
    return out


def load_summaries():
    d = ROOT / "summaries"
    if not d.exists():
        return {}
    return {p.stem: p.read_text("utf-8").strip() for p in d.glob("*.md")}
