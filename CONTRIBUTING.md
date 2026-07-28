# Contributing / 参与贡献

Thanks for taking a look. This is a small, opinionated tool; the fastest way to
get a change merged is to know which opinions are load-bearing.

感谢关注。这是一个小而有主张的工具；想让改动顺利合入，先了解哪些主张是承重的。

## What this project will not accept

**No paywall circumvention.** Not credential sharing, not bot-detection evasion,
not proxy pools, not anything whose purpose is to obtain content the user is not
entitled to. Full-text acquisition is delegated to an external tool precisely so
that this repository stays on the right side of that line, and it will stay
there.

**No bulk downloading from publishers.** Publisher terms of service prohibit
systematic downloading, and tripping their detection blocks the entire
institution, not the individual. Any change that makes batch acquisition easier
or less deliberate will be declined. If you need scale, use a publisher TDM API.

**No scraping Google Scholar.** It has no public API and blocks automated
access. Semantic Scholar and OpenAlex cover the same ground with documented APIs.

**本项目不接受**：任何绕过付费墙的技术（凭据共享、绕过 bot 检测、代理池等）；
任何让批量下载更容易或更不经思考的改动——出版商条款禁止系统性下载，
触发检测封锁的是整个机构而非个人，规模化需求请走出版商的 TDM API；
爬取 Google Scholar。

## The three tiers are the point

The reconciler distinguishes `cited` / `candidates` / `library` and reports
"in library but not cited" as **normal**, not as a defect. This is not a
configuration choice, it is the thesis of the tool.

The first version of this reconciler did report that gap as the top-severity
finding. On a real project it produced 45 alarming rows, three of which were
real problems and 42 of which were a researcher reading properly. Please do not
reintroduce that.

三层区分是本工具的论点，不是配置项。第一版曾把「在 library 而不在 cited」
报成最高危，在真实项目上产出 45 条告警，其中 3 条是真问题、42 条只是
一个研究者在正常地读书。请不要把它加回来。

## Design constraints worth knowing

- **The tool never writes your manuscript.** It touches Zotero and its own
  reports. Your `.bib`, notes and paper are yours to edit. A PR that has the
  tool edit a bibliography will be declined.
- **Every write has `--dry-run`.** New write paths must have one too. This is
  what makes the tool safe to drive from an agent.
- **Read via the local API, write via the Web API.** Reads need no credentials;
  keep it that way so that read-only use requires no key at all.
- **Registry parsing stays declarative.** No user note format may be hard-coded.
  If you need a new source format, add a `type` to `load_tier()` and document it
  in `examples/registry.example.yaml`.
- **Aliases are resolved before any comparison.** Any new comparison must go
  through the same canonicalisation, or it will emit a false positive for every
  renamed key.

## Practical stuff

- Python 3.10+. Standard library plus `requests`, `PyYAML`, `pyzotero`;
  `PyMuPDF` only for optional text extraction, isolated to one function because
  it is AGPL.
- No test suite yet. Until there is one, say in your PR what you actually ran
  and paste the output. "It should work" is not a test result.
- Keep comments explaining **why**, especially for anything that looks
  redundant. Several guards in this codebase exist because of a specific
  real-world failure; removing them as dead code would reintroduce the bug.
  If a guard looks pointless, ask before deleting it.
- Bilingual docs: English first, Chinese for anything a user must not
  misunderstand. You do not need to write both — open the PR in whichever you
  are comfortable with.

## Reporting a problem

Include: what you ran, what happened, what you expected, and your OS and Python
version. If it involves a publisher or an institution, **redact credentials,
cookies, session traces and institution-identifying URLs** before pasting logs.

报告问题时请附：执行的命令、实际结果、预期结果、操作系统与 Python 版本。
若涉及出版商或机构，粘贴日志前**务必抹去凭据、cookie、会话痕迹与可识别机构的 URL**。

## Licence

By contributing you agree your contribution is licensed under the MIT Licence,
as in [LICENSE](LICENSE).

贡献即表示同意你的贡献以 MIT 许可发布，见 [LICENSE](LICENSE)。
