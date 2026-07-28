# Third-Party Notices / 第三方声明

## InstSci

This project's **closed-access acquisition stage is not implemented here.** It is delegated
entirely to the InstSci command-line tool, which this project treats as an optional external
dependency and invokes as a subprocess.

本项目的**闭源全文获取环节并非自行实现**，而是完全委托给 InstSci 命令行工具。
本项目将其视为可选的外部依赖，通过子进程调用。

| Project | Role here | License |
|---|---|---|
| [Rimagination/instsci](https://github.com/Rimagination/instsci) | Upstream. Metadata search and institutional / Open-Access full-text retrieval. | MIT — Copyright (c) 2025 InstSci contributors |
| [deathcats4/instsci-workflow](https://github.com/deathcats4/instsci-workflow) | Fork. Adds the `publisher-batch` browser-download path, Zotero hand-off commands, Chinese-portal routing, and the three-layer status contract (`file_status` / `standard_status` / `result_evidence`) that this project's reports reuse. | MIT — Copyright (c) 2025 InstSci contributors |

**No source code from either project is vendored, copied, or redistributed here.**
Users install InstSci themselves; this project only documents how to call it and how to
map its manifest output into a Zotero library and a Markdown note vault.

**本仓库不包含、不复制、不再分发上述任一项目的源代码。** 用户自行安装 InstSci；
本项目只记录如何调用它，以及如何把它的 manifest 输出映射进 Zotero 文库与 Markdown 笔记库。

The status vocabulary `file_status` / `standard_status` / `result_evidence` used in this
project's reconciliation reports originates from `deathcats4/instsci-workflow`. It is
reused as an interface contract so that reports remain comparable across tools.

本项目对账报告中使用的 `file_status` / `standard_status` / `result_evidence` 状态词汇
来自 `deathcats4/instsci-workflow`，作为接口契约复用，以保持报告可比。

### A note on a known upstream issue

This project's troubleshooting guide describes a login-detection defect in InstSci's
`carsi.py` and the workaround for it. **The patch itself is intentionally not distributed**,
because the recommended workflow (`instsci publisher-batch`) does not go through that code
path at all. Only the observation and the workaround are documented — no derived code.

本项目故障排查文档记录了 InstSci `carsi.py` 中的一处登录检测缺陷及其绕法。
**补丁本身有意不予分发**，因为推荐流程（`instsci publisher-batch`）根本不经过该代码路径。
文档只记录现象与绕法，不含任何衍生代码。

## Other tools referenced

These are ordinary runtime dependencies or optional integrations, installed by the user:

| Tool | Purpose | License (as published upstream) |
|---|---|---|
| [pyzotero](https://github.com/urschrei/pyzotero) | Zotero Web API client | Blue Oak Model License 1.0.0 |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | PDF text extraction | AGPL-3.0 / commercial dual |
| [Obsidian](https://obsidian.md) | Markdown note vault (not required; any editor works) | Proprietary, free for personal use |
| [Zotero](https://www.zotero.org) + [Better BibTeX](https://retorque.re/zotero-better-bibtex/) | Reference manager and citation-key pinning | AGPL-3.0 / MIT respectively |

> **PyMuPDF is AGPL-3.0.** It is used only as an optional local text-extraction helper and is
> not bundled. If AGPL is incompatible with your use, substitute another extractor —
> `ledger/zot.py` isolates the dependency to a single function.
>
> **PyMuPDF 是 AGPL-3.0 许可。** 本项目仅将其作为可选的本地抽文工具，不打包分发。
> 若 AGPL 与你的用途不兼容，可替换为其他抽文库——`ledger/zot.py` 已把该依赖隔离在单个函数内。

## Metadata sources

Bibliographic metadata is retrieved from public APIs under their respective terms of use:
[Semantic Scholar](https://www.semanticscholar.org/product/api),
[OpenAlex](https://openalex.org/),
[Crossref](https://www.crossref.org/services/metadata-retrieval/),
[Unpaywall](https://unpaywall.org/).
Please supply a contact e-mail in your configuration so requests land in each service's
polite pool.

题录元数据取自上述公共 API，遵循各自的使用条款。请在配置中填写联系邮箱，
以便请求进入各服务的 polite pool。
