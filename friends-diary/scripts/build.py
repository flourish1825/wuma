"""把 entries/、summaries/、config.json 打包进 web/index.html，输出到 _site/。"""
import html
import json
import os

from common import ROOT, load_config, load_entries, load_summaries


def main():
    cfg = load_config()
    members = cfg.get("members", {})
    entries = load_entries()
    for e in entries:
        e["name"] = members.get(e["author"], e["author"])

    data = {
        "config": {
            "title": cfg.get("title", "朋友日记"),
            "subtitle": cfg.get("subtitle", ""),
            "repo": os.environ.get("GITHUB_REPOSITORY") or cfg.get("repo", ""),
        },
        "entries": entries,
        "summaries": load_summaries(),
    }
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")

    page = (ROOT / "web" / "index.html").read_text("utf-8")
    page = page.replace("__TITLE__", html.escape(data["config"]["title"])).replace("__DATA__", payload)

    out = ROOT / "_site"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / ".nojekyll").write_text("")
    print(f"已生成 {out / 'index.html'}：{len(entries)} 篇日记，{len(data['summaries'])} 份总结")


if __name__ == "__main__":
    main()
