"""把一个「写日记」Issue 转成 entries/YYYY/日期-用户名.md。

由 .github/workflows/issue-to-entry.yml 调用，从 GITHUB_EVENT_PATH 读取事件。
结果写入 GITHUB_OUTPUT：status(ok/rejected/invalid)、message、path。
"""
import json
import os
import re
from datetime import date, datetime, timedelta, timezone

from common import ROOT, load_config

ALLOWED = {"OWNER", "MEMBER", "COLLABORATOR"}


def emit(**kw):
    line = "".join(f"{k}={str(v).replace(chr(10), ' ')}\n" for k, v in kw.items())
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as f:
            f.write(line)
    print(line)


def sections(body: str) -> dict:
    parts = re.split(r"^### (.+?)[ \t]*$", body or "", flags=re.M)
    out = {}
    for i in range(1, len(parts) - 1, 2):
        v = parts[i + 1].strip()
        out[parts[i].strip()] = "" if v == "_No response_" else v
    return out


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        issue = json.load(f)["issue"]

    if issue.get("author_association") not in ALLOWED:
        return emit(status="rejected", message="⚠️ 只有仓库成员/协作者才能提交日记。请联系仓库所有者把你加为 Collaborator。")

    sec = sections(issue.get("body"))
    content = sec.get("日记内容", "")
    if not content:
        return emit(status="invalid", message="⚠️ 日记内容为空，没有保存。")

    tz = timezone(timedelta(hours=load_config().get("timezone_offset", 8)))
    created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00")).astimezone(tz).date()
    raw = sec.get("日期", "")
    try:
        d = date.fromisoformat(raw) if raw else created
    except ValueError:
        return emit(status="invalid", message=f"⚠️ 日期「{raw}」格式不对，请用 YYYY-MM-DD，例如 2026-10-05。")
    if d > created + timedelta(days=1):
        return emit(status="invalid", message="⚠️ 日期在未来，没有保存。")

    login = re.sub(r"[^A-Za-z0-9_-]", "", issue["user"]["login"]) or "user"
    mood = sec.get("心情", "").replace("\n", " ")

    folder = ROOT / "entries" / str(d.year)
    folder.mkdir(parents=True, exist_ok=True)
    path, n = folder / f"{d}-{login}.md", 2
    while path.exists():  # 同一天写多篇
        path = folder / f"{d}-{login}-{n}.md"
        n += 1

    path.write_text(f"---\ndate: {d}\nauthor: {login}\nmood: {mood}\n---\n\n{content}\n", encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()
    emit(status="ok", path=rel, message=f"✅ 已保存为 `{rel}`，约一分钟后网站会更新。")


if __name__ == "__main__":
    main()
