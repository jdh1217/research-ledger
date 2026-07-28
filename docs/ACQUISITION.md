# Acquiring full text / 取全文

**This repository downloads nothing from publishers.** It is a ledger, not a
downloader. This page describes the order that works and the boundaries that
matter.

**本仓库不从任何出版商下载文件。** 它是账本，不是下载器。
本页说明可行的顺序与不可越过的边界。

## The order

### 1. Open Access first — always check before anything else

Every record from `ledger.discover` carries an `oa_pdf` field, populated from
Semantic Scholar and OpenAlex. [Unpaywall](https://unpaywall.org/) is worth a
second check.

Institutional repositories frequently host an author manuscript even when the
publisher version is behind a paywall. A paper marked closed by one source is
sometimes freely available from the authors institution. Checking costs one
request and often saves the entire problem.

机构库常有作者版，即便出版商版本收费。查一次只花一个请求，却常常直接解决问题。

### 2. Closed access — only what you are entitled to read

If your institution subscribes, retrieve it using your own credentials, through
your own browser session, one paper at a time.

External tools exist for this — see [NOTICE.md](../NOTICE.md). This project
delegates to them and deliberately implements none of it.

## Boundaries

> - **Individual papers you personally have the right to read.** Nothing beyond
>   that.
> - **Terms of service prohibit systematic or bulk downloading.** Tripping a
>   publishers detection typically blocks the **entire institutions IP range**.
>   Your colleagues lose access, not just you. This is the practical reason the
>   rule matters, quite apart from the contractual one.
> - **One paper at a time, each a deliberate decision.** Do not point a batch
>   job at a DOI list.
> - **Never automate human verification.** A login, 2FA prompt or CAPTCHA is a
>   request for a human. Answer it yourself.
> - **For text mining at scale, use the publishers TDM API.** Most large
>   publishers offer one. It is the sanctioned path and it does not put your
>   institution at risk.

> - **只取你个人有权阅读的单篇文献。**
> - **出版商条款禁止系统性/批量下载。** 触发检测封锁的通常是**整个机构的 IP 段**，
>   失去访问权的是你的同事，不只是你。这是这条规则在合同之外的现实理由。
> - **一次一篇，每篇都是明确的决定。** 不要把批处理指向 DOI 列表。
> - **绝不自动化人工验证。** 登录、2FA、验证码是在要求一个人来回答，请你自己答。
> - **规模化文本挖掘走出版商官方 TDM API。**

## Practical notes

These cost real time to discover, so they are recorded here.

**Federated login is not a VPN.** Shibboleth / OpenAthens / CARSI authenticate
you at the publisher using your institutional account. Several institutions own
guides say to turn the VPN **off** when using federated login — running both
confuses the access detection and makes failures harder to diagnose.

**Aggressive bot detection rejects non-browser HTTP clients outright.** If a
cookies-plus-`requests` approach returns `418` or an abrupt TLS teardown while a
browser on the same machine works fine, that is a client-fingerprint block, not
an authentication failure. Correct cookies will not help. Do not conclude the
site cannot be accessed; conclude that it must be accessed through a real
browser session.

**A local fake-IP proxy causes confusing intermittent failures.** If `nslookup`
returns an address in `198.18.0.0/15` — an RFC 2544 benchmarking range, not a
real destination — DNS is being intercepted locally. Browsers cope; Python HTTP
clients see sporadic SSL errors that look like network flakiness.

**联邦认证不等于 VPN**，多校指南明写用联邦认证时要关掉 VPN。
**反爬严格的站点直接拒绝非浏览器客户端**：同机浏览器正常而 `requests` 返回 418
或 TLS 突断，那是客户端指纹被拦、不是认证失败，cookie 再对也没用。
**本机 fake-IP 代理**（`nslookup` 返回 `198.18.0.0/15`）会让 Python 侧间歇性 SSL 失败。

## After the file is on disk

```bash
python -m ledger.zot create --doi <DOI> --collection <alias> --bibkey <key> --dry-run
python -m ledger.zot create --doi <DOI> --collection <alias> --bibkey <key>
python -m ledger.zot attach <itemKey> /path/to/file.pdf
```

`attach` links by default rather than uploading, so your cloud storage quota
stays free. Zotero storage quota limits **file attachments only** — item
metadata syncs without limit — so linking sidesteps the quota entirely while
keeping full-text search, annotation and reading in Zotero.

`attach` 默认链接而非上传。Zotero 的存储配额**只限制文件附件**，
条目元数据同步不受限，所以链接方式完全绕开配额，同时保留全文检索、标注与阅读。
