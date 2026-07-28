# Registry format reference / 登记册格式参考

`registry.yaml` tells the tool where your tiers live and how to read them. It
imposes no structure on your notes: you describe what you already have.

`registry.yaml` 告诉工具你的三层在哪、怎么读。它不对你的笔记强加结构，
你只是描述你已有的东西。

Start from [`examples/registry.example.yaml`](../examples/registry.example.yaml).

## Tiers

Three tiers, all optional except the one you care about. An undeclared tier
yields an empty set rather than an error, so a registry with only `cited` still
reconciles.

| Tier | Meaning |
| --- | --- |
| `cited` | the citation set your manuscript compiles against — authoritative |
| `candidates` | what you are still choosing from — undecided |
| `library` | everything you read to build understanding |

## Tier types

### `bibtex`

```yaml
cited:
  type: bibtex
  path: paper/refs.bib
```

Extracts entry keys and DOIs. This is not a full BibTeX parser and does not need
to be: a regex tolerates the formatting variety real `.bib` files contain, and
only keys and DOIs are used.

### `markdown_table`

```yaml
library:
  type: markdown_table
  path: notes/library.md
  section: "Read manifest"   # optional; omit to scan the whole file
  key_column: 2              # 1-based
  columns:                   # optional labels, shown in reports
    3: year
    4: first_author
```

Reads a pipe table. Header and separator rows are skipped automatically, as is
any row whose key cell does not look like an identifier. Backticks around a key
are stripped, so both `` `key2020a` `` and `key2020a` work.

`section` matches a Markdown heading **containing** the given text, at any level,
and stops at the next heading of the same or shallower level. So `"Read
manifest"` matches `## 1. Read manifest (current)`.

### `markdown_inline_keys`

```yaml
candidates:
  type: markdown_inline_keys
  path: notes/reading_plan.md
  section: "Candidate citations"
  key_pattern: "`([a-zA-Z][a-zA-Z0-9]*\d{4}[a-zA-Z0-9]*)`"
```

Collects every identifier matching `key_pattern` — useful when your candidate
list is prose rather than a table.

The default pattern catches backticked keys shaped `nameYYYYsuffix`
(`smith2019damping`). Override it if your keys look different. The pattern needs
exactly one capture group, and remember YAML needs the backslashes escaped.

默认模式匹配形如 `nameYYYYsuffix` 的反引号键。你的键长得不一样就覆盖它。
正则须恰好一个捕获组，且 YAML 里反斜杠要转义。

## Vault

```yaml
vault:
  sources_dir: "C:/Users/you/Vault/my-project/sources"
```

One Markdown file per key, YAML frontmatter carrying at least `bibkey`. Forward
slashes work on Windows. See [`templates/`](../templates/).

Fill `doi` too. Without it, matching a search result against your notes falls
back to comparing normalised titles — workable, but strictly worse than a DOI.

## Aliases

```yaml
aliases:
  refPD: pratt1995sea
```

Manuscript-side key on the left, library-side key on the right.

This exists because bibliography keys and note keys drift apart the moment you
rename anything. Every comparison canonicalises through this map first. Skip it
and the report shows a false positive for every key you ever renamed — in
practice this was the single largest source of noise before aliases existed.

别名存在的原因：一旦你改名，`.bib` 侧的键和笔记侧的键就会分家。
所有比较都先经此归一。不声明别名，每个改过名的键都会变成假阳性——
实测中这是加入别名机制之前最大的噪声来源。
