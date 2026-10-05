# 📔 朋友日记

和好朋友一起写日记的小网站。纯 GitHub 方案：**免服务器、免费**。

- ✍️ 朋友们在网页/手机上填一张表就能提交当天日记
- 📅 网站按 **日 / 周 / 月 / 年** 浏览，日历、搜索、按成员筛选
- 📊 每个周期自动统计（篇数、谁写得多、心情分布）
- ✨ 可选：用 Claude 自动生成每周 / 每月 / 每年总结

## 工作原理

```
朋友填「写日记」表单(Issue) → Actions 存成 entries/年/日期-用户名.md → 重新构建 → GitHub Pages 更新
```

## 部署（约 5 分钟）

1. 在 GitHub 新建仓库（建议 Public），把本项目**所有文件**（含隐藏的 `.github` 文件夹）上传：
   ```bash
   git init && git add -A && git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/你的用户名/仓库名.git
   git push -u origin main
   ```
2. 仓库 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。
3. 到 **Actions** 页，手动运行一次「构建并发布网站」（Run workflow）。完成后网址是 `https://你的用户名.github.io/仓库名/`。
4. **Settings → Collaborators** 邀请朋友（只有所有者和协作者提交的日记才会被接收）。
5. 编辑 `config.json`：改标题，并在 `members` 里把朋友的 GitHub 用户名映射成显示名。
6. 删除示例内容：`entries/2026/` 下的示例 `.md` 和 `summaries/week-2026-W40.md`。

## 怎么写日记

- 网站右上角「✍️ 写日记」按钮 → 填写 → Submit new issue；
- 或仓库 Issues → New issue → 「写日记」。手机装 GitHub App 也行。
- 日期留空 = 今天；补写以前的日记就填那天日期。可以直接拖图片进内容框。
- 提交后机器人会回复并关闭 Issue，约 1 分钟网站更新。同一天写多篇也可以。

高级：也可以直接在 `entries/年份/` 下新建 `.md`：

```markdown
---
date: 2026-10-05
author: 你的GitHub用户名
mood: 😊 开心
---

今天……
```

## 周/月/年总结

- **统计**：网站自动生成，无需配置。
- **AI 总结（可选）**：
  1. 仓库 Settings → Secrets and variables → Actions → New secret：`ANTHROPIC_API_KEY`
  2. 之后每天北京时间 00:30 自动检查：周一总结上周，每月 1 号总结上月，1 月 1 号总结去年。
  3. 想补某一期：Actions → 「AI 周/月/年总结」→ Run workflow，填 `week` + `2026-W40`（或 `month` + `2026-09`、`year` + `2026`）。
  4. 可选变量（Variables）：`SUMMARY_MODEL` 改模型，`ANTHROPIC_BASE_URL` 改接口地址。
  - 注意：日记内容会发送给 Anthropic API 来生成总结。

## 隐私须知 ⚠️

- GitHub Pages 网站**任何知道网址的人都能访问**（私有仓库的 Pages 站点也是公开可访问的，除非 Enterprise）。
- 公开仓库里的 Issue 和 `entries/` 同样公开可见。
- 所以请只写**愿意公开**的内容；如需真正私密，可再加客户端加密（如 StatiCrypt）或改用私有部署，告诉我我可以接着做。

## 本地预览

```bash
python scripts/build.py
python -m http.server -d _site 8000   # 打开 http://localhost:8000
```

## 目录结构

```
.github/ISSUE_TEMPLATE/diary.yml   日记表单
.github/workflows/                 入库、构建发布、AI 总结
entries/                           所有日记（Markdown）
summaries/                         AI 总结（week-2026-W40.md / month-2026-09.md / year-2026.md）
web/index.html                     网站前端（单文件，无依赖）
scripts/                           构建与入库脚本（仅用 Python 标准库）
config.json                        标题与成员名
```
