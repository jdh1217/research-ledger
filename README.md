# research-ledger

**Keep your literature and your manuscript in agreement.**
**让你的文献与你的稿件对得上账。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

A small, auditable toolkit for the part of research nobody builds tools for: not
finding papers, but keeping track of which ones you actually cite, which ones you
are still considering, and which ones you merely read — and noticing when those
three drift apart.

> **Stands on two existing projects.** Full-text acquisition is **not**
> reimplemented here — it is delegated to
> [**Rimagination/instsci**](https://github.com/Rimagination/instsci) (metadata
> search and institutional / Open-Access retrieval) and its fork
> [**deathcats4/instsci-workflow**](https://github.com/deathcats4/instsci-workflow)
> (browser-based download path, Zotero hand-off, and the three-layer status
> vocabulary these reports reuse). Both are MIT-licensed. Neither is bundled or
> redistributed here — see [NOTICE.md](NOTICE.md).
>
> **本项目建立在两个既有项目之上。** 取全文环节**并非**自行实现，而是委托给
> [**Rimagination/instsci**](https://github.com/Rimagination/instsci)（元数据检索与
> 机构/开放获取取全文）及其 fork
> [**deathcats4/instsci-workflow**](https://github.com/deathcats4/instsci-workflow)
> （浏览器下载通道、Zotero 对接，以及本项目报告复用的三层状态词汇）。
> 两者均为 MIT 许可。本仓库不打包、不再分发其任何代码——见 [NOTICE.md](NOTICE.md)。

**[English](#english) · [中文](#中文)**

---

## English

### The problem

Reference managers tell you what is in your library. Search engines tell you what
exists. Neither tells you the thing that bites at submission time:

> Your notes say this paper is central to your argument. Your `.bib` has never
> heard of it.

That drift is silent and it accumulates. But the naive fix — diffing your reading
library against your bibliography — produces a wall of noise, because **reading
70 papers does not mean citing 70 papers.** Most of the gap is healthy.

This toolkit takes the position that there are **three different sets**, and only
some differences between them are defects:

| Tier | What it is | Authority |
| --- | --- | --- |
| `cited` | the citation set your manuscript compiles against | authoritative |
| `candidates` | the pool you are still choosing from | undecided |
| `library` | everything you read to build understanding | not tied to any one paper |

"In `library` but not in `cited`" is **normal**. The reconciler will not report it
as a problem. It reports only four things:

| | Defect | Why it matters |
| --- | --- | --- |
| `X1` | in `cited`, absent from `library` | you cite something you have no record of reading |
| `X2` | in `candidates`, absent from `library` | planned but never logged |
| `X3` | a note exists, absent from `library` | the note ran ahead of the record |
| `X4` | a pool member has no pinned citation key | the identifier spine is broken |

On a real project this cut a 45-row report down to 3 real findings.

### The spine: one identifier, five places

```text
Zotero item      Extra: "Citation Key: author2020topic"
     |
your .bib        @article{author2020topic, ...}
     |
library table    | 12 | author2020topic | 2020 | ... |
     |
note file        sources/author2020topic.md  (frontmatter: bibkey, doi, zotero_key)
     |
acquisition log  runs/... manifest row for the DOI
```

If any link is missing, `reconcile` says so. Aliases (`refPD` -> `pratt1995sea`)
are declared once and resolved before anything is compared — without that, every
key you ever renamed shows up as a false positive.

### Pipeline

```text
1 discover  →  2 screen  →  3 acquire  →  4 file  →  5 read  →  6 note  →  7 reconcile
```

| Stage | Command | What it does |
| --- | --- | --- |
| 1 | `ledger.discover` | search Semantic Scholar + OpenAlex + Crossref; traverse the citation graph |
| 2 | `ledger.screen` | mark each candidate against your registries; only `NEW` is worth acquiring |
| 3 | *(external)* | Open Access first; closed access via **your own** subscription, one paper at a time |
| 4 | `ledger.zot create` | create the item in a named collection with a pinned citation key |
| 5 | `ledger.zot text` / `annotations` | extract PDF text; export the highlights **you** made |
| 6 | *(you write it)* | a Markdown note per key |
| 7 | `ledger.reconcile` | cross-check and report drift |

Stage 6 is deliberately manual. Stage 5's `annotations` exists so that *your*
reading judgement — the passages you chose to highlight — enters the note, rather
than a model's guess at what mattered.

### Citation-graph traversal

`discover refs-of --keep-order` answers a question no reference manager does:
**"which paper is `[19]` in this article?"**

Crossref reference lists carry a `key` field shaped like `ref19`, preserving the
original numbering. Neither Semantic Scholar nor OpenAlex exposes it, so Crossref
is the preferred source here, with the other two as fallbacks and for enrichment.

> Some publishers require Semantic Scholar to elide the references field
> entirely; the response is then `{"data": null}` rather than an empty list. The
> tool detects this and falls back automatically.

**Google Scholar is deliberately not used.** It has no public API and blocks
automated access. What it uniquely offers — citation counts and a "cited by"
graph — is covered by Semantic Scholar and OpenAlex, both of which publish APIs.

### Install

```bash
git clone https://github.com/jdh1217/research-ledger.git
cd research-ledger
pip install -r requirements.txt

cp config.example.json               config.json
cp examples/registry.example.yaml    registry.yaml
cp examples/collections.example.yaml collections.yaml
```

Then edit all three. They are gitignored: `config.json` holds a Zotero API key,
and the other two describe your private research structure.

#### Zotero setup

1. Enable the local API: *Settings → Advanced → Allow other applications on this
   computer to communicate with Zotero*.
2. Create a Web API key at <https://www.zotero.org/settings/keys> with
   *Allow library access* and *Allow write access*. Put it in `config.json`.
3. Install [Better BibTeX](https://retorque.re/zotero-better-bibtex/) if you want
   pinned citation keys to survive export.
4. If your cloud storage quota is tight, set *Settings → Advanced → Files and
   Folders → Linked Attachment Base Directory* and mirror it in
   `config.json` → `zotero.linked_base`. Attachments then link instead of upload.

Get your real collection keys with:

```bash
python -m ledger.zot collections
```

### Quick start

```bash
# 1. Find things
python -m ledger.discover search "flexible link vibration suppression" --limit 25

# 2. See which are actually new
python -m ledger.screen runs/candidates_search_*.json --only NEW

# 3. Trace one paper's references, with the original numbering
python -m ledger.discover refs-of 10.1000/example --keep-order

# 4. File one (always dry-run first)
python -m ledger.zot create --doi 10.1000/example \
       --collection passivity --bibkey author2020topic --dry-run

# 5. Attach a local PDF without consuming cloud quota
python -m ledger.zot attach ABCD1234 /path/to/paper.pdf

# 6. Pull out the highlights you made while reading
python -m ledger.zot annotations ABCD1234

# 7. Check the books
python -m ledger.reconcile
```

### Relationship to InstSci

Stage 3 is the hard part of literature work, and it is already solved. This
project does not compete with that solution — it starts where it stops.

| | [instsci](https://github.com/Rimagination/instsci) + [instsci-workflow](https://github.com/deathcats4/instsci-workflow) | research-ledger (this repo) |
| --- | --- | --- |
| Metadata search | yes — same three sources | plus **citation-graph traversal** with original reference numbering |
| Open-Access retrieval | **yes** | delegated |
| Closed-access retrieval | **yes** — browser session reusing your institutional entitlement | delegated |
| Acquisition audit trail | **yes** — `file_status` / `standard_status` / `result_evidence` | consumed as an interface contract |
| Chinese-portal routing | **yes** (fork) | delegated |
| Screening against what you own | no | **yes** — five-state check across your registries |
| Filing with a *pinned semantic* citation key | hand-off queue / manifest import | **yes** — direct, into a named sub-collection, de-duplicated by DOI |
| Linked (non-uploading) attachments | supported | **yes** — default mode, to keep storage quota free |
| Reading notes | no | **yes** — templated Markdown, plus your own Zotero highlights |
| **Agreement with your manuscript** | no | **yes** — three-tier reconciliation |

The short version: **InstSci gets the PDF onto your disk. This keeps the ledger
that says why it is there.** Install both; they compose.

The one thing worth copying even if you use neither: **their status vocabulary.**
Recording *how* a file was obtained (`oa_direct`, `browser_verified`,
`not_verified`, …) rather than just *whether* it was obtained turns a folder of
mystery PDFs into something you can audit months later.

### Driving it from a coding agent

The whole pipeline was built to be operated in natural language from a coding
agent (Claude Code, Codex, Cursor, and similar). Three design choices make that
safe rather than reckless:

- **every stage is a plain CLI** with a stable, parseable stdout, so an agent can
  chain them without screen-scraping a GUI;
- **every write has `--dry-run`**, so the agent can show you exactly what would
  change before anything does;
- **nothing writes to your manuscript.** The tool touches Zotero and its own
  report files. Your `.bib`, your notes and your paper are edited by you.

Things you can just say:

| You say | The agent runs |
| --- | --- |
| "look into passivity of compliant joints, show me what is new" | `discover search` → `screen --only NEW` |
| "what is reference [19] in this paper?" | `discover refs-of <doi> --keep-order` |
| "who has cited this since?" | `discover cited-by <doi>` |
| "file this one under passivity as `author2020topic`" | `zot create ... --dry-run`, then the real write after you confirm |
| "attach the PDF I just downloaded" | `zot attach` in linked mode |
| "pull my highlights out of that paper" | `zot annotations` |
| "are my citations and my notes in agreement?" | `reconcile` |

**Guardrails worth writing into your agent's project instructions.** Paste
something like this into `CLAUDE.md`, `AGENTS.md`, or a skill definition:

```text
- The agent proposes; the human decides. Never decide what to cite.
- Show the NEW list and let the human pick. Do not select papers autonomously.
- Always run a write command with --dry-run first and show the output.
- Closed-access retrieval: one paper at a time, confirmed each time.
  Never point a batch job at a DOI list. Never automate a login or CAPTCHA.
- Screening may rely on abstracts. Conclusions may not — read the full text
  before claiming what a paper means for the argument.
- Notes must quote the source verbatim and cite page numbers. Do not paraphrase
  a claim into something stronger than the original.
```

That last pair is not boilerplate. An agent that is allowed to conclude from
abstracts will confidently mis-read a paper whose title resembles your
contribution, and an agent that is allowed to choose citations will optimise for
looking thorough rather than for being right.

### Acquiring full text

**This repository does not download anything from publishers.** Stage 3 is
delegated to the external [InstSci](https://github.com/Rimagination/instsci) CLI
(or its [fork](https://github.com/deathcats4/instsci-workflow)), which is not
bundled here — see [NOTICE.md](NOTICE.md).

The order that works:

1. **Open Access first.** Every discovered record carries an `oa_pdf` field from
   Semantic Scholar / OpenAlex. Institutional repositories often host an author
   copy even when the publisher version is paywalled. Check
   [Unpaywall](https://unpaywall.org/) before trying anything else.
2. **Closed access — only what you are entitled to read.** If your institution
   subscribes, use your own credentials through your own browser session.

> ### ⚠️ Read this before automating anything against a publisher
>
> - **This is for retrieving individual papers you personally have the right to
>   read.** Nothing more.
> - **Publisher terms of service prohibit systematic or bulk downloading.**
>   Tripping their detection typically blocks the **entire institution's IP
>   range**, not your personal account. Your colleagues lose access because of
>   you.
> - **One paper at a time, each one a deliberate decision.** Do not point a batch
>   job at a DOI list.
> - **Never automate a human verification step.** If a login, 2FA or CAPTCHA
>   appears, complete it yourself.
> - **For genuine text mining at scale, use the publisher's own TDM API.** Most
>   large publishers offer one. That is the sanctioned path and it does not put
>   your institution at risk.
> - This project ships **no** paywall-circumvention technique, and none will be
>   accepted as a contribution.

Some practical notes, learned the hard way:

- Institutional federated login (Shibboleth / OpenAthens / CARSI) is usually the
  right path, and it is **not** the same as a VPN. Several institutions' own
  guides say to turn the VPN **off** when using federated login — running both
  confuses the publisher's access detection.
- Publishers with aggressive bot detection reject non-browser HTTP clients
  outright, regardless of how correct your cookies are. If a
  cookie-plus-`requests` approach returns `418` or an abrupt TLS teardown, that is
  a client-fingerprint block, not an authentication failure. A real browser
  session is required.
- If `nslookup` returns an address in `198.18.0.0/15` (an RFC 2544 benchmarking
  range), a local fake-IP proxy is intercepting DNS. It will not stop a browser,
  but it causes intermittent SSL failures for Python HTTP clients.

### What this does not do

- It does not write your paper, and it does not decide what you should cite.
- It does not judge relevance. `discover` returns candidates; **you** pick.
- It does not read for you. Stage 5 gives you text and your own highlights;
  the note in stage 6 is yours to write.
- It does not require Obsidian. Notes are plain Markdown with YAML frontmatter;
  any editor works.

### A limitation worth stating plainly

At the discovery stage you only have titles and abstracts. That is enough to
decide **whether a paper is worth acquiring**. It is not enough to decide **what
the paper means for your argument.**

Abstracts routinely omit exactly what matters: which port or coordinate frame a
theorem is stated in, what the standing assumptions are, the frequency or gain
range where a result holds, whether validation was simulation or hardware, and
the authors' own stated limitations. A paper whose title looks like a direct
threat to your contribution can turn out, on a full read, to *support* it — and
the reverse.

So: screen on abstracts, conclude on full text. Mark abstract-only reads
distinctly in your library and never let one carry an argument.

### License

MIT — see [LICENSE](LICENSE). Third-party attributions in [NOTICE.md](NOTICE.md).

---

## 中文

### 要解决的问题

文献管理器告诉你库里有什么，搜索引擎告诉你世上有什么。但投稿时真正咬人的那件事，
两者都不管：

> 你的笔记说这篇是你论证的核心。你的 `.bib` 里根本没有它。

这种漂移是静默的，而且会累积。可是最直觉的做法——把学习库和参考文献表做差集
——只会产出一墙噪声，因为**读了 70 篇不等于要引 70 篇**，绝大部分差额是健康的。

本工具的立场是：这里有**三个不同的集合**，它们之间只有部分差异才是缺陷。

| 层 | 是什么 | 权威性 |
| --- | --- | --- |
| `cited` | 稿件实际编译所用的引用集 | 权威 |
| `candidates` | 仍在挑选的候选池 | 待决 |
| `library` | 为建立理解而读过的全部文献 | 不隶属任何单篇稿件 |

**「在 `library` 而不在 `cited`」是正常状态**，对账不会把它报成问题。它只报四类：

| | 缺陷 | 为什么要紧 |
| --- | --- | --- |
| `X1` | 在 `cited` 却不在 `library` | 引用了却无阅读记录，答辩时无据可查 |
| `X2` | 在 `candidates` 却不在 `library` | 规划要引却从未记录 |
| `X3` | 有笔记却不在 `library` | 笔记跑到了记录前面 |
| `X4` | 候选池条目未 pin citation key | 标识脊椎断裂 |

在一个真实项目上，这个分层把 45 行的报告收敛成了 3 条真发现。

### 脊椎：一个标识，贯穿五处

```text
Zotero 条目      Extra: "Citation Key: author2020topic"
     |
你的 .bib        @article{author2020topic, ...}
     |
学习库表格       | 12 | author2020topic | 2020 | ... |
     |
笔记文件         sources/author2020topic.md （frontmatter: bibkey, doi, zotero_key）
     |
取全文日志       runs/... 对应该 DOI 的 manifest 行
```

任一环缺失，`reconcile` 都会报出来。别名（`refPD` -> `pratt1995sea`）声明一次即可，
比较之前先归一——不做这一步，每个你改过名的键都会变成假阳性。

### 流水线

```text
1 检索  →  2 筛查  →  3 取全文  →  4 入库  →  5 精读  →  6 写笔记  →  7 对账
```

| 阶段 | 命令 | 做什么 |
| --- | --- | --- |
| 1 | `ledger.discover` | 三源检索（Semantic Scholar + OpenAlex + Crossref）与引文图遍历 |
| 2 | `ledger.screen` | 逐条比对登记册；只有 `NEW` 才值得取全文 |
| 3 | *（外部工具）* | OA 优先；闭源仅用**你自己的**订阅，一次一篇 |
| 4 | `ledger.zot create` | 在指定分类下建条目并 pin 语义 citation key |
| 5 | `ledger.zot text` / `annotations` | 抽 PDF 全文；导出**你自己**划的重点 |
| 6 | *（你来写）* | 每个键一篇 Markdown 笔记 |
| 7 | `ledger.reconcile` | 交叉对账并报告漂移 |

阶段 6 有意保持手工。阶段 5 的 `annotations` 存在的意义是：让**你的**阅读判断
（你选择高亮的那些段落）进入笔记，而不是让模型去猜什么重要。

### 引文图遍历

`discover refs-of --keep-order` 能回答一个文献管理器都答不了的问题：
**「这篇文章里的 `[19]` 是哪一篇？」**

Crossref 的参考文献列表带有形如 `ref19` 的 `key` 字段，保留了原文编号。
Semantic Scholar 与 OpenAlex 都不给编号，所以这里以 Crossref 为首选源，
另两者作回退与信息补全。

> 部分出版商要求 Semantic Scholar 完全屏蔽 references 字段，此时返回的是
> `{"data": null}` 而非空列表。本工具会识别这种情况并自动降级。

**有意不使用 Google Scholar**：无公开 API 且强反爬。它独有的引用数排序与
cited-by 已被 Semantic Scholar 与 OpenAlex 覆盖，且两者都有正式 API。

### 安装

```bash
git clone https://github.com/jdh1217/research-ledger.git
cd research-ledger
pip install -r requirements.txt

cp config.example.json               config.json
cp examples/registry.example.yaml    registry.yaml
cp examples/collections.example.yaml collections.yaml
```

三个文件都要改。它们均已 gitignore：`config.json` 含 Zotero API key，
另两个描述你的私有研究结构。

#### Zotero 配置

1. 开启本地 API：*设置 → 高级 → 允许本机其他应用与 Zotero 通信*。
2. 在 <https://www.zotero.org/settings/keys> 生成 Web API key，勾选
   *Allow library access* 与 *Allow write access*，填进 `config.json`。
3. 想让 pinned citation key 在导出时保持不变，装
   [Better BibTeX](https://retorque.re/zotero-better-bibtex/)。
4. 云端存储配额紧张时，设置 *设置 → 高级 → 文件和文件夹 → 链接附件基准目录*，
   并在 `config.json` 的 `zotero.linked_base` 填同一路径。附件就会以链接方式挂载，
   不上传。

取你自己的真实分类 key：

```bash
python -m ledger.zot collections
```

### 快速上手

```bash
# 1. 找文献
python -m ledger.discover search "flexible link vibration suppression" --limit 25

# 2. 看哪些是真的新
python -m ledger.screen runs/candidates_search_*.json --only NEW

# 3. 追某篇的参考文献，保留原文编号
python -m ledger.discover refs-of 10.1000/example --keep-order

# 4. 入库（务必先 dry-run）
python -m ledger.zot create --doi 10.1000/example \
       --collection passivity --bibkey author2020topic --dry-run

# 5. 挂本地 PDF，不占云端配额
python -m ledger.zot attach ABCD1234 /path/to/paper.pdf

# 6. 导出你读的时候划的重点
python -m ledger.zot annotations ABCD1234

# 7. 对账
python -m ledger.reconcile
```

### 与 InstSci 的关系

阶段 3 是文献工作里最难的一环，而它已经被解决了。本项目不与那个方案竞争——
它从那个方案结束的地方开始。

| | [instsci](https://github.com/Rimagination/instsci) + [instsci-workflow](https://github.com/deathcats4/instsci-workflow) | research-ledger（本仓库） |
| --- | --- | --- |
| 元数据检索 | 有——同样是那三个源 | 另加**引文图遍历**，且保留原文参考文献编号 |
| 开放获取取全文 | **有** | 委托 |
| 闭源取全文 | **有**——浏览器会话复用你的机构授权 | 委托 |
| 取全文审计链 | **有**——`file_status` / `standard_status` / `result_evidence` | 作为接口契约消费 |
| 中文库路由（知网/万方） | **有**（fork） | 委托 |
| 与「你已经拥有什么」比对筛查 | 无 | **有**——跨登记册五状态判定 |
| 以**pinned 语义** citation key 入库 | 对接队列 / manifest 导入 | **有**——直投指定子分类，按 DOI 去重 |
| 链接式（不上传）附件 | 支持 | **有**——默认模式，为省云端配额 |
| 阅读笔记 | 无 | **有**——模板化 Markdown，含你自己的 Zotero 高亮 |
| **与稿件对账** | 无 | **有**——三层语义对账 |

一句话：**InstSci 负责把 PDF 弄到你硬盘上；本项目负责记住它为什么在那里。**
两个都装，互补。

即使你两个都不用，也值得抄走的一点是**它的状态词汇**。记录一份文件是**怎么**
拿到的（`oa_direct`、`browser_verified`、`not_verified`……），而不只是**有没有**
拿到，能把一堆来历不明的 PDF 变成几个月后还查得清的东西。

### 用 coding agent 以自然语言驱动

整条流水线从一开始就是为了在 coding agent（Claude Code、Codex、Cursor 等）里
用自然语言操作而设计的。三条设计取舍让这件事**稳妥**而不是**莽撞**：

- **每个阶段都是普通 CLI**，stdout 稳定可解析，agent 可以串起来，不需要去刮 GUI；
- **每个写操作都有 `--dry-run`**，agent 能在任何东西被改动之前先给你看清楚会改什么；
- **任何环节都不写你的稿件。** 本工具只碰 Zotero 和它自己的报告文件。
  你的 `.bib`、你的笔记、你的论文，都由你自己改。

你可以直接这么说：

| 你说 | agent 执行 |
| --- | --- |
| 「调研一下柔性关节无源性，给我看有什么新的」 | `discover search` → `screen --only NEW` |
| 「这篇文章里的 [19] 是哪一篇？」 | `discover refs-of <doi> --keep-order` |
| 「之后谁引用过它？」 | `discover cited-by <doi>` |
| 「把这篇按 `author2020topic` 归到 passivity 分类」 | 先 `zot create ... --dry-run`，你确认后再实写 |
| 「把我刚下的 PDF 挂上去」 | `zot attach`，链接模式 |
| 「把那篇我划的重点导出来」 | `zot annotations` |
| 「我的引用和笔记对得上吗？」 | `reconcile` |

**值得写进 agent 项目指令的护栏。** 把类似下面这段贴进 `CLAUDE.md`、`AGENTS.md`
或一个 skill 定义里：

```text
- agent 提议，人决定。永远不要替我决定引什么。
- 把 NEW 清单给我，由我挑。不要自主选定文献。
- 写操作一律先跑 --dry-run 并把输出给我看。
- 闭源取全文：一次一篇，每篇都要我确认。
  绝不把批处理指向 DOI 列表。绝不自动化登录或验证码。
- 筛查可以只凭摘要；下结论不行——声称一篇论文对论证意味着什么之前，必须读全文。
- 笔记必须逐字引用原文并给页码。不要把原文的声明改写成更强的说法。
```

最后那两条不是套话。**允许 agent 凭摘要下结论**，它就会对一篇标题酷似你贡献的
论文给出自信的误读；**允许 agent 自己挑引用**，它会朝「看起来很周全」优化，
而不是朝「正确」优化。

### 取全文

**本仓库不从任何出版商下载文件。** 阶段 3 委托给外部的
[InstSci](https://github.com/Rimagination/instsci)（或其
[fork](https://github.com/deathcats4/instsci-workflow)）命令行工具，
本仓库不打包它——见 [NOTICE.md](NOTICE.md)。

可行的顺序：

1. **OA 优先。** 每条检索记录都带来自 Semantic Scholar / OpenAlex 的 `oa_pdf`
   字段。即使出版商版本收费，机构库也常有作者版。先查
   [Unpaywall](https://unpaywall.org/)，再考虑别的。
2. **闭源——只取你确实有权阅读的。** 若你所在机构已订阅，用你自己的凭据、
   在你自己的浏览器会话里取。

> ### ⚠️ 对出版商做任何自动化之前，请读这一段
>
> - **这是为了取阅你个人有权阅读的单篇文献**，仅此而已。
> - **出版商条款禁止系统性/批量下载。** 触发其检测通常封锁的是**整个机构的
>   IP 段**，不是你的个人账号。因你而失去访问权的是你的同事。
> - **一次一篇，每篇都是一次明确的决定。** 不要把批处理指向一份 DOI 列表。
> - **绝不自动化人工验证步骤。** 出现登录、2FA 或验证码，请你自己完成。
> - **真要做规模化文本挖掘，走出版商官方的 TDM API。** 多数大出版商都提供。
>   那是被许可的通道，也不会让你的机构承担风险。
> - 本项目**不包含**任何绕过付费墙的技术，也不会接受此类贡献。

几条踩过坑才知道的实务：

- 机构联邦认证（Shibboleth / OpenAthens / CARSI）通常是正确路径，它**不等于**
  VPN。多所机构的自家指南都写明用联邦认证时要**关掉** VPN——两者同开会让
  出版商的访问识别混乱。
- 反爬严格的出版商会直接拒绝非浏览器 HTTP 客户端，**无论你的 cookie 多正确**。
  若「cookie + `requests`」的做法返回 `418` 或 TLS 突然中断，那是客户端指纹被拦，
  不是认证失败——必须用真实浏览器会话。
- 若 `nslookup` 返回 `198.18.0.0/15` 段内地址（RFC 2544 基准测试保留段），
  说明本机有 fake-IP 代理在劫持 DNS。它不会挡住浏览器，但会让 Python 的 HTTP
  客户端间歇性 SSL 失败。

### 本工具不做什么

- 不替你写论文，也不替你决定该引什么。
- 不判断相关性。`discover` 只给候选，**由你挑**。
- 不替你读。阶段 5 给你全文与你自己的高亮；阶段 6 的笔记由你写。
- 不依赖 Obsidian。笔记就是带 YAML frontmatter 的普通 Markdown，任何编辑器都行。

### 一条必须说明白的局限

检索阶段你手上只有标题和摘要。这足以判断**这篇值不值得取全文**，
但**不足以判断这篇对你的论证意味着什么**。

摘要系统性地省略掉恰恰最要紧的东西：定理陈述在哪个端口或哪套坐标下、
成立的前提假设是什么、结论在什么频率或增益范围内有效、验证是仿真还是硬件、
以及作者自陈的局限。一篇标题看起来直接威胁你贡献的论文，读完全文可能反而
**支持**你——反过来也一样。

所以：**用摘要筛选，用全文定论。** 在学习库里把「仅摘要级」单独标出，
永远不要让这类记录承载论证。

### 许可

MIT，见 [LICENSE](LICENSE)。第三方归属见 [NOTICE.md](NOTICE.md)。
