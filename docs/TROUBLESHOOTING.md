# Troubleshooting / 故障排查

Failures observed in real use, with the actual cause rather than the first guess.

真实使用中遇到的故障，给出真实原因而非第一直觉。

## Configuration

**`Missing config.json`** — copy `config.example.json` and fill it in. Same for
`registry.yaml` and `collections.yaml` from `examples/`.

**`zotero.api_key ... is still a placeholder`** — read-only subcommands need no
key at all; only `create`, `attach` and `pin` do. Generate one at
<https://www.zotero.org/settings/keys> with library **and write** access.

**`Unknown collection alias`** — the error lists the aliases you have declared.
Get your real 8-character keys with `python -m ledger.zot collections`.

## Zotero

**A write succeeds but a read cannot find the item.** Writes go through the Web
API (cloud); reads go through the local API (your desktop client). The client
has to sync before a local read sees a cloud write. Nothing is wrong; wait for
the sync, or verify against the Web API directly.

**写入成功但读不到**：写走 Web API（云端）、读走 local API（本地客户端），
客户端同步之后本地才看得到。不是故障。

**Connection refused on port 23119.** The Zotero desktop client is not running,
or the local API is off. Enable *Settings → Advanced → Allow other applications
on this computer to communicate with Zotero*. Write operations are unaffected.

**"My cloud storage is full, so none of this will work."** Storage quota limits
**file attachments only**. Item metadata — the part this tool creates — syncs
without limit. Use `zot attach` in its default linked mode and the quota never
enters the picture.

**「云端存储满了，所以用不了」**：配额只限制**文件附件**，条目元数据不受限。
用 `zot attach` 的默认链接模式即可完全绕开。

**Attachment rejected by the API.** Not all Zotero deployments accept
`linked_file` attachments over the Web API. Add it from the desktop app instead:
right-click the item → Add Attachment → Attach Link to File.

## Discovery

**`refs-of` returns nothing for a DOI that clearly has references.** Some
publishers require Semantic Scholar to elide the references field; the response
is `{"data": null}`, not an empty list. The tool detects this and falls back to
Crossref automatically — you will see a note saying so. If all three sources
come up empty, the reference list simply is not deposited anywhere public, and
the PDF is the only route.

**Every request returns 429.** The anonymous Semantic Scholar quota. Requests
back off exponentially and the other two sources still answer, so results are
usually complete but slower. Add `semantic_scholar_api_key` to `config.json` if
you hit it constantly.

**Results are thin or oddly ranked.** Fill in `contact_email`. It puts Crossref
and OpenAlex requests in their polite pools, which materially improves both rate
limits and reliability.

## Screening and reconciliation

**A paper you definitely have is reported as `NEW`.** Matching prefers DOI. If
your library table has no DOI column and your note lacks a `doi` field, the
comparison falls back to normalised titles, which misses when the two spellings
differ enough. Fix: put `doi` in your note frontmatter.

**A short generic title matches the wrong paper.** Containment matching requires
the two titles to be of comparable length precisely to prevent this. If it still
happens, the titles really are near-identical; add DOIs.

**The report flags dozens of things and none of them look wrong.** Check your
tiers. If your reading library is declared as `cited`, then every paper you read
but did not cite becomes a defect. `cited` must point at the bibliography your
manuscript actually compiles against — nothing else.

**报告告警几十条却看着都不像问题**：检查分层。若把学习库声明成了 `cited`，
那么每一篇你读过却没引的文献都会变成缺陷。`cited` 必须指向稿件真正编译所用的
参考文献表。

**Every renamed key shows up as missing.** Declare it in `aliases`.

## Notes and vault

**Notes are not picked up.** `vault.sources_dir` must point at the directory
holding the `.md` files themselves, not the vault root. Each note needs YAML
frontmatter delimited by `---` on its own line, with a `bibkey`. Notes without
frontmatter fall back to using the filename as the key.

## Platform

**`UnicodeEncodeError` on Windows.** Should not occur — every entry point calls
`utf8_stdout()` first. If you see it, you are importing a module directly rather
than running it as `python -m ledger.<name>`.

**PyMuPDF will not install, or its licence is a problem.** It is AGPL-3.0 and
optional. Only `zot text` uses it, and only in one function. Everything else
works without it; substitute any extractor you prefer.
