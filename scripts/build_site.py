#!/usr/bin/env python3
"""Static site generator for the SfSkills catalog (GitHub Pages).

Reads ``registry/skills.json``, each skill's ``SKILL.md`` and ``docs/*.md``, and
writes a self-contained static site to ``site/_build/``:

  index.html                      what it is, canonical counts, links
  domains/<domain>.html           every skill in a domain (filterable list)
  skills/<domain>/<name>.html     one page per skill: frontmatter + rendered body
  docs/<slug>.html                rendered docs/*.md (docs/README.md -> docs/index.html)
  sitemap.xml, robots.txt, 404.html, .nojekyll

stdlib only, one inline stylesheet, no external requests. Every internal link is
relative, so the site works from a project-pages sub-path. Generated output is
not committed (``site/_build/`` is in .gitignore).

Usage:
    python3 scripts/build_site.py [--out site/_build] [--base-url URL]
                                  [--domains-only] [--no-docs]

``--base-url`` (or env ``SITE_BASE_URL``) is used for canonical links, Open Graph
URLs and the sitemap; default https://pranavnagrecha.github.io/AwesomeSalesforceSkills
"""

from __future__ import annotations

import argparse
import html
import json
import os
import posixpath
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

REPO_URL = "https://github.com/PranavNagrecha/AwesomeSalesforceSkills"
DEFAULT_BASE = "https://pranavnagrecha.github.io/AwesomeSalesforceSkills"
SITE_NAME = "SfSkills"
TAGLINE = "Salesforce AI Skill Library"

DOMAIN_BLURB = {
    "admin": "Declarative configuration: objects, fields, permission sets, sharing, reports, and the requirements work that precedes them.",
    "agentforce": "Agentforce and Einstein: agents, topics, actions, prompt templates, grounding, guardrails and evaluation.",
    "apex": "Apex and SOQL: triggers, governor limits, async processing, outbound callouts, security enforcement and tests.",
    "architect": "Solution and platform architecture: multi-org strategy, scalability, licensing, Well-Architected reviews and ADRs.",
    "data": "Data model, migration, bulk loads, query optimisation, deduplication at volume and archival.",
    "devops": "Delivery: source tracking, packaging, branching, CI/CD, environments and deployment troubleshooting.",
    "flow": "Flow Builder: record-triggered, screen, scheduled and orchestration flows, fault handling, limits and testing.",
    "integration": "Inbound integration and the API surface: REST, SOAP, Bulk API 2.0, Platform Events, CDC, Named Credentials, middleware.",
    "lwc": "Lightning Web Components: reactivity, wire adapters, communication, accessibility, performance, security, Jest.",
    "omnistudio": "OmniStudio: OmniScripts, FlexCards, DataRaptors, Integration Procedures, Business Rules Engine, DataPacks.",
    "security": "Platform security and compliance: hardening, encryption, session policy, MFA, monitoring, record-access troubleshooting.",
}

# docs/*.md that are not worth rendering (huge generated index, internal dashboard)
DOCS_SKIP = {"SKILLS.md", "queue-progress.md"}

CSS = """
:root{--bg:#fff;--fg:#1c2330;--muted:#5b6678;--line:#dde2ea;--card:#f6f8fb;--accent:#0b5cad;--code-bg:#f1f4f8;--code-fg:#1c2330}
@media (prefers-color-scheme:dark){:root{--bg:#10151d;--fg:#e4e9f1;--muted:#97a3b6;--line:#27303d;--card:#171e29;--accent:#6cb4ff;--code-bg:#1a222e;--code-fg:#e4e9f1}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}
header.site{border-bottom:1px solid var(--line);background:var(--card)}
header.site div{max-width:56rem;margin:0 auto;padding:.7rem 1rem;display:flex;flex-wrap:wrap;gap:.4rem 1.2rem;align-items:baseline}
header.site .brand{font-weight:700;font-size:1.1rem;text-decoration:none;color:var(--fg)}
header.site a{text-decoration:none}
main{max-width:56rem;margin:0 auto;padding:1rem 1rem 3rem}
h1{font-size:1.7rem;line-height:1.25;margin:1.2rem 0 .6rem}
h2{font-size:1.3rem;margin:2rem 0 .5rem;padding-top:.4rem;border-top:1px solid var(--line)}
h3{font-size:1.1rem;margin:1.5rem 0 .4rem}
h4,h5,h6{margin:1.2rem 0 .3rem}
p,ul,ol,table,pre,blockquote{margin:.7rem 0}
code{font:.88em ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--code-bg);color:var(--code-fg);padding:.1em .3em;border-radius:4px}
pre{background:var(--code-bg);color:var(--code-fg);padding:.8rem 1rem;border-radius:6px;overflow-x:auto;line-height:1.45}
pre code{background:none;padding:0;font-size:.85rem}
blockquote{border-left:3px solid var(--line);padding:.1rem 1rem;color:var(--muted)}
table{border-collapse:collapse;display:block;overflow-x:auto;max-width:100%}
th,td{border:1px solid var(--line);padding:.35rem .6rem;text-align:left;vertical-align:top}
th{background:var(--card)}
hr{border:0;border-top:1px solid var(--line);margin:1.5rem 0}
.lede{font-size:1.1rem;color:var(--muted)}
.crumbs{font-size:.9rem;color:var(--muted);margin-top:1rem}
.meta{display:flex;flex-wrap:wrap;gap:.4rem;margin:.6rem 0;padding:0;list-style:none}
.meta li,.tag{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:.1rem .65rem;font-size:.82rem;color:var(--muted)}
.tags{display:flex;flex-wrap:wrap;gap:.35rem;margin:.4rem 0;padding:0;list-style:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));gap:.8rem;padding:0;list-style:none}
.grid li{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.7rem .9rem}
.grid .n{font-size:1.5rem;font-weight:700}
.skills{padding:0;list-style:none}
.skills li{padding:.7rem 0;border-bottom:1px solid var(--line)}
.skills .d{color:var(--muted);font-size:.93rem;margin:.15rem 0}
.skills .gh{font-size:.82rem}
#filter{width:100%;padding:.55rem .7rem;font-size:1rem;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
footer{max-width:56rem;margin:0 auto;padding:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.88rem}
""".strip()


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def esc(s: str) -> str:
    return html.escape(s, quote=True)


def slugify(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s).lower()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[\s]+", "-", s.strip()) or "section"


def short_desc(text: str, limit: int = 200) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    m = re.search(r"^(.{60,}?[.!?])\s", text)
    if m and len(m.group(1)) <= limit:
        return m.group(1)
    return cut.rsplit(" ", 1)[0].rstrip(",;:") + "..."


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter dict, body). Handles scalars, quoted strings, block
    lists and inline lists; ignores anything fancier."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    fm: dict = {}
    key = None
    for line in block.splitlines():
        if re.match(r"^\s+-\s+", line) and key:
            v = re.sub(r"^\s+-\s+", "", line).strip().strip("\"'")
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(v)
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            fm[key] = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
        elif val == "":
            fm[key] = []
        else:
            fm[key] = val.strip("\"'")
    return fm, body


# --------------------------------------------------------------------------
# markdown -> html (minimal)
# --------------------------------------------------------------------------

class Markdown:
    """Headings, paragraphs, lists (nested by indent), fenced code, pipe tables,
    blockquotes, hr, inline code/bold/italic/links/images. Raw HTML is escaped."""

    def __init__(self, repo_path: str, skill_ids: set[str], depth: int, site_paths: dict[str, str] | None = None):
        self.repo_dir = posixpath.dirname(repo_path)  # repo-relative dir of the source file
        self.skill_ids = skill_ids
        self.depth = depth  # directory depth of the output page, for relative links
        self.site_paths = site_paths or {}
        self.used_ids: dict[str, int] = {}

    # -- links ----------------------------------------------------------
    def resolve_link(self, href: str) -> str:
        if re.match(r"^[a-z][a-z0-9+.-]*:", href, re.I) or href.startswith("#") or href.startswith("//"):
            return href
        path, _, frag = href.partition("#")
        if not path:
            return href
        target = posixpath.normpath(posixpath.join(self.repo_dir, path))
        if target.startswith(".."):
            return REPO_URL + "/blob/main/" + path
        up = "../" * self.depth
        m = re.match(r"^skills/([^/]+)/([^/]+)(?:/SKILL\.md)?/?$", target)
        if m and f"{m.group(1)}/{m.group(2)}" in self.skill_ids:
            return f"{up}skills/{m.group(1)}/{m.group(2)}.html" + (f"#{frag}" if frag else "")
        if target in self.site_paths:
            return up + self.site_paths[target] + (f"#{frag}" if frag else "")
        is_dir = path.endswith("/") or "." not in posixpath.basename(target)
        kind = "tree" if is_dir else "blob"
        return f"{REPO_URL}/{kind}/main/{target}" + (f"#{frag}" if frag else "")

    # -- inline ---------------------------------------------------------
    def inline(self, text: str) -> str:
        stash: list[str] = []

        def keep(s: str) -> str:
            stash.append(s)
            return f"\x00{len(stash) - 1}\x00"

        text = re.sub(r"(`+)(.+?)\1", lambda m: keep(f"<code>{esc(m.group(2).strip())}</code>"), text)
        text = esc(text)
        text = re.sub(
            r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)",
            lambda m: keep(f'<img src="{esc(self.resolve_link(html.unescape(m.group(2))))}" alt="{m.group(1)}" loading="lazy" style="max-width:100%">'),
            text,
        )
        text = re.sub(
            r"\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)",
            lambda m: keep(f'<a href="{esc(self.resolve_link(html.unescape(m.group(2))))}">{m.group(1)}</a>'),
            text,
        )
        text = re.sub(r"&lt;(https?://[^\s&]+)&gt;", lambda m: keep(f'<a href="{m.group(1)}">{m.group(1)}</a>'), text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<![\w*])__(.+?)__(?![\w*])", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
        text = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", text)
        text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
        return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)

    def heading_id(self, text: str) -> str:
        base = slugify(html.unescape(text))
        n = self.used_ids.get(base, 0)
        self.used_ids[base] = n + 1
        return base if n == 0 else f"{base}-{n}"

    # -- blocks ---------------------------------------------------------
    def render(self, md: str) -> tuple[str, str]:
        """Return (html, first_h1_text)."""
        lines = md.replace("\r\n", "\n").split("\n")
        out: list[str] = []
        i = 0
        n = len(lines)
        first_h1 = ""
        para: list[str] = []

        def flush_para():
            if para:
                out.append("<p>" + self.inline(" ".join(s.strip() for s in para)) + "</p>")
                para.clear()

        while i < n:
            line = lines[i]
            stripped = line.strip()

            fence = re.match(r"^(\s*)(`{3,}|~{3,})\s*([\w+-]*)", line)
            if fence:
                flush_para()
                marker, lang = fence.group(2), fence.group(3)
                i += 1
                buf = []
                while i < n and not lines[i].strip().startswith(marker[0] * len(marker)):
                    buf.append(lines[i])
                    i += 1
                i += 1
                cls = f' class="language-{esc(lang)}"' if lang else ""
                out.append(f"<pre><code{cls}>{esc(chr(10).join(buf))}</code></pre>")
                continue

            if not stripped:
                flush_para()
                i += 1
                continue

            if stripped.startswith("<!--"):  # html comment, possibly multi-line
                flush_para()
                while i < n and "-->" not in lines[i]:
                    i += 1
                i += 1
                continue

            h = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
            if h:
                flush_para()
                level = len(h.group(1))
                text = h.group(2)
                if level == 1 and not first_h1:
                    first_h1 = html.unescape(re.sub(r"[`*_]", "", text))
                hid = self.heading_id(text)
                out.append(f'<h{level} id="{esc(hid)}">{self.inline(text)}</h{level}>')
                i += 1
                continue

            if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
                flush_para()
                out.append("<hr>")
                i += 1
                continue

            if stripped.startswith(">"):
                flush_para()
                buf = []
                while i < n and lines[i].strip().startswith(">"):
                    buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                    i += 1
                inner, _ = Markdown.render(self, "\n".join(buf))
                out.append(f"<blockquote>{inner}</blockquote>")
                continue

            if "|" in stripped and i + 1 < n and re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", lines[i + 1]):
                flush_para()
                header = self.split_row(line)
                i += 2
                rows = []
                while i < n and "|" in lines[i] and lines[i].strip():
                    rows.append(self.split_row(lines[i]))
                    i += 1
                t = ["<table><thead><tr>" + "".join(f"<th>{self.inline(c)}</th>" for c in header) + "</tr></thead><tbody>"]
                for r in rows:
                    r = (r + [""] * len(header))[: max(len(header), len(r))]
                    t.append("<tr>" + "".join(f"<td>{self.inline(c)}</td>" for c in r) + "</tr>")
                t.append("</tbody></table>")
                out.append("".join(t))
                continue

            if re.match(r"^\s*([-*+]|\d+[.)])\s+", line):
                flush_para()
                html_list, i = self.list_block(lines, i)
                out.append(html_list)
                continue

            if re.match(r"^<[a-zA-Z/!]", stripped) and not para:
                # raw html line in markdown: show it as text rather than inject it
                para.append(stripped)
                i += 1
                continue

            para.append(line)
            i += 1
        flush_para()
        return "\n".join(out), first_h1

    @staticmethod
    def split_row(line: str) -> list[str]:
        s = line.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|") and not s.endswith("\\|"):
            s = s[:-1]
        return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]

    def list_block(self, lines: list[str], i: int) -> tuple[str, int]:
        item_re = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
        first = item_re.match(lines[i])
        base = len(first.group(1).expandtabs(4))
        ordered = first.group(2)[0].isdigit()
        tag = "ol" if ordered else "ul"
        items: list[list[str]] = []
        n = len(lines)
        while i < n:
            line = lines[i]
            m = item_re.match(line)
            if m and len(m.group(1).expandtabs(4)) == base:
                items.append([m.group(3)])
                i += 1
                continue
            if not line.strip():
                # blank line: continue the list only if the next non-blank line is indented or an item
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and (
                    (item_re.match(lines[j]) and len(item_re.match(lines[j]).group(1).expandtabs(4)) >= base)
                    or (len(lines[j]) - len(lines[j].lstrip())) > base
                ):
                    items[-1].append("")
                    i = j
                    continue
                break
            indent = len(line) - len(line.lstrip())
            if items and indent > base:
                items[-1].append(line)
                i += 1
                continue
            if items and not m and indent >= base:
                items[-1].append(line)
                i += 1
                continue
            break
        parts = [f"<{tag}>"]
        for it in items:
            head = it[0]
            rest = it[1:]
            if not rest:
                parts.append(f"<li>{self.inline(head)}</li>")
                continue
            # dedent the continuation and render recursively (handles nested lists / code)
            ind = min((len(r) - len(r.lstrip()) for r in rest if r.strip()), default=0)
            sub = "\n".join(r[ind:] if r.strip() else "" for r in rest)
            inner, _ = Markdown.render(self, sub)
            parts.append(f"<li>{self.inline(head)}{inner}</li>")
        parts.append(f"</{tag}>")
        return "".join(parts), i


# --------------------------------------------------------------------------
# page chrome
# --------------------------------------------------------------------------

class Site:
    def __init__(self, out: Path, base_url: str):
        self.out = out
        self.base = base_url.rstrip("/")
        self.pages: list[str] = []  # site-relative paths, for the sitemap

    def page(self, rel: str, title: str, description: str, body: str, depth: int, og_type: str = "website") -> None:
        up = "../" * depth
        full_title = title if title == SITE_NAME else f"{title} | {SITE_NAME}"
        url = f"{self.base}/{rel}" if rel != "index.html" else f"{self.base}/"
        desc = esc(short_desc(description, 300))
        doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{esc(url)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(full_title)}">
<meta name="twitter:description" content="{desc}">
<style>{CSS}</style>
</head>
<body>
<header class="site"><div>
<a class="brand" href="{up}index.html">{SITE_NAME}</a>
<a href="{up}index.html#domains">Domains</a>
<a href="{up}docs/index.html">Docs</a>
<a href="{REPO_URL}">GitHub</a>
</div></header>
<main>
{body}
</main>
<footer>{SITE_NAME}: {TAGLINE}. Source-available under the <a href="{REPO_URL}/blob/main/LICENSE">PolyForm Small Business License 1.0.0</a>. Generated {date.today().isoformat()} from the repository; the repository is the source of truth.</footer>
</body>
</html>
"""
        path = self.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(doc, encoding="utf-8")
        if rel != "404.html":
            self.pages.append(rel)


def li_list(items: list[str]) -> str:
    return "".join(f"<li>{x}</li>" for x in items)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "site" / "_build"))
    ap.add_argument("--base-url", default=os.environ.get("SITE_BASE_URL", DEFAULT_BASE))
    ap.add_argument("--domains-only", action="store_true", help="skip per-skill pages (size fallback)")
    ap.add_argument("--no-docs", action="store_true", help="skip docs/*.md pages")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    site = Site(out, args.base_url)

    registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    skills = sorted(registry["skills"], key=lambda s: (s["category"], s["name"]))
    skill_ids = {s["id"] for s in skills}
    by_domain: dict[str, list[dict]] = {}
    for s in skills:
        by_domain.setdefault(s["category"], []).append(s)

    try:
        from check_doc_counts import canonical_counts  # type: ignore
        counts = canonical_counts(ROOT)
    except Exception as exc:  # pragma: no cover - keep the build alive
        print(f"warning: check_doc_counts unavailable ({exc}); using registry counts", file=sys.stderr)
        counts = {
            "skills_total": registry["skill_count"],
            "domain_counts": registry["domain_counts"],
            "agents_total": 0, "build": 0, "active_runtime": 0, "deprecated": 0,
            "mcp_tools": 0, "evals_flagship": 0,
        }

    # ---- docs (rendered first so skills/index can link to them) ----------
    doc_pages: dict[str, tuple[str, str]] = {}  # repo path -> (site path, title)
    doc_sources: list[tuple[Path, str]] = []
    if not args.no_docs:
        for p in sorted((ROOT / "docs").glob("*.md")):
            if p.name in DOCS_SKIP:
                continue
            slug = "index" if p.name == "README.md" else re.sub(r"[^a-z0-9]+", "-", p.stem.lower()).strip("-")
            doc_sources.append((p, f"docs/{slug}.html"))
    site_paths = {f"docs/{p.name}": rel for p, rel in doc_sources}
    site_paths["README.md"] = "index.html"

    for p, rel in doc_sources:
        repo_path = f"docs/{p.name}"
        md = Markdown(repo_path, skill_ids, depth=1, site_paths=site_paths)
        text = p.read_text(encoding="utf-8")
        body_html, h1 = md.render(text)
        title = h1 or p.stem
        doc_pages[repo_path] = (rel, title)
        first_p = re.search(r"<p>(.*?)</p>", body_html, re.S)
        desc = html.unescape(re.sub(r"<[^>]+>", "", first_p.group(1))) if first_p else title
        crumbs = f'<p class="crumbs"><a href="../index.html">Home</a> / <a href="index.html">Docs</a> / {esc(title)}</p>'
        foot = f'<p class="crumbs"><a href="{REPO_URL}/blob/main/{repo_path}">View this file on GitHub</a></p>'
        site.page(rel, title, desc, crumbs + body_html + foot, depth=1, og_type="article")

    # ---- skill pages -----------------------------------------------------
    skill_page_count = 0
    if not args.domains_only:
        for s in skills:
            d, name = s["category"], s["name"]
            skill_dir = ROOT / s["file_location"]
            skill_md = skill_dir / "SKILL.md"
            fm, body = ({}, "")
            if skill_md.exists():
                fm, body = split_frontmatter(skill_md.read_text(encoding="utf-8"))
            repo_path = f"{s['file_location']}/SKILL.md"
            md = Markdown(repo_path, skill_ids, depth=2, site_paths=site_paths)
            body_html, h1 = md.render(body)
            title_text = h1 or name
            desc = s.get("description") or fm.get("description", "")
            tags = s.get("tags") or fm.get("tags") or []
            pillars = fm.get("well-architected-pillars") or []
            gh = f"{REPO_URL}/tree/main/{s['file_location']}"

            meta = []
            if s.get("version"):
                meta.append(f"v{esc(str(s['version']))}")
            if fm.get("salesforce-version"):
                meta.append(f"Salesforce {esc(fm['salesforce-version'])}")
            if s.get("updated"):
                meta.append(f"Updated {esc(str(s['updated']))}")
            for pl in pillars:
                meta.append(esc(pl))

            deps = [x for x in (s.get("dependencies") or []) if isinstance(x, str)]
            dep_html = ""
            if deps:
                items = []
                for x in deps:
                    items.append(f'<a href="../../skills/{x}.html">{esc(x)}</a>' if x in skill_ids else f"<code>{esc(x)}</code>")
                dep_html = f"<h2 id=\"dependencies\">Dependencies</h2><ul>{li_list(items)}</ul>"

            files = []
            for key in ("references", "templates", "scripts"):
                for f in s.get(key) or []:
                    if isinstance(f, str):
                        files.append(f'<a href="{REPO_URL}/blob/main/{esc(f)}">{esc(f.split("/", 3)[-1])}</a>')
            files_html = f'<h2 id="package-files">Package files</h2><ul>{li_list(files)}</ul>' if files else ""

            page = (
                f'<p class="crumbs"><a href="../../index.html">Home</a> / <a href="../../domains/{d}.html">{esc(d)}</a> / {esc(name)}</p>'
                f"<h1>{esc(name)}</h1>"
                f'<p class="lede">{esc(short_desc(desc, 600))}</p>'
                + (f'<ul class="meta">{li_list(meta)}</ul>' if meta else "")
                + (f'<ul class="tags">{"".join(f"<li class=tag>{esc(t)}</li>" for t in tags)}</ul>' if tags else "")
                + f'<p><a href="{gh}">Open the skill folder on GitHub</a></p>'
                + "<hr>"
                + body_html
                + dep_html
                + files_html
            )
            site.page(f"skills/{d}/{name}.html", f"{name} ({d} skill)", desc, page, depth=2, og_type="article")
            skill_page_count += 1

    # ---- domain pages ----------------------------------------------------
    for d, group in sorted(by_domain.items()):
        rows = []
        for s in group:
            name = s["name"]
            link = f'<a href="../skills/{d}/{name}.html"><strong>{esc(name)}</strong></a>' if not args.domains_only else f"<strong>{esc(name)}</strong>"
            tags = s.get("tags") or []
            tag_html = f'<ul class="tags">{"".join(f"<li class=tag>{esc(t)}</li>" for t in tags[:8])}</ul>' if tags else ""
            hay = esc((name + " " + " ".join(tags) + " " + (s.get("description") or "")).lower())
            rows.append(
                f'<li data-h="{hay}">{link}'
                f'<div class="d">{esc(short_desc(s.get("description", ""), 260))}</div>'
                f"{tag_html}"
                f'<div class="gh"><a href="{REPO_URL}/tree/main/{s["file_location"]}">Skill folder on GitHub</a></div></li>'
            )
        script = (
            "<script>(function(){var f=document.getElementById('filter');if(!f)return;"
            "var items=document.querySelectorAll('.skills li');"
            "f.addEventListener('input',function(){var q=f.value.toLowerCase().trim();"
            "items.forEach(function(li){li.hidden=q&&li.getAttribute('data-h').indexOf(q)<0;});});})();</script>"
        )
        body = (
            f'<p class="crumbs"><a href="../index.html">Home</a> / {esc(d)}</p>'
            f"<h1>{esc(d.capitalize())} skills ({len(group)})</h1>"
            f'<p class="lede">{esc(DOMAIN_BLURB.get(d, ""))}</p>'
            '<p><input id="filter" type="search" placeholder="Filter this list (needs JavaScript)" aria-label="Filter skills"></p>'
            f'<ul class="skills">{"".join(rows)}</ul>{script}'
        )
        site.page(
            f"domains/{d}.html",
            f"{d.capitalize()} skills",
            f"{len(group)} {d} skill packages for Salesforce AI assistants. {DOMAIN_BLURB.get(d, '')}",
            body,
            depth=1,
        )

    # ---- index -----------------------------------------------------------
    total = counts["skills_total"]
    dom_items = "".join(
        f'<li><a href="domains/{d}.html"><span class="n">{len(g)}</span><br><strong>{esc(d)}</strong></a>'
        f'<div class="d">{esc(DOMAIN_BLURB.get(d, ""))}</div></li>'
        for d, g in sorted(by_domain.items())
    )
    stat = lambda n, label: f'<li><span class="n">{n:,}</span><br>{label}</li>'
    intro = (
        f"{total:,} skill packages, {counts['active_runtime']} run-time agents and an MCP server that make an AI coding "
        "assistant behave like a senior Salesforce practitioner: it knows the platform's non-obvious "
        "failure modes, refuses the wrong code an LLM reliably produces, and grounds every claim in "
        "official Salesforce documentation."
    )
    body = f"""
<h1>{SITE_NAME}: {TAGLINE}</h1>
<p class="lede">{esc(intro)}</p>
<ul class="grid">
{stat(total, "skill packages")}
{stat(counts["active_runtime"], "active run-time agents")}
{stat(counts["build"], "build-time agents")}
{stat(counts["mcp_tools"], "MCP tools")}
</ul>
<h2 id="what">What it is</h2>
<p>Each skill is a reviewed package (<code>SKILL.md</code> plus references, templates and checkers) covering one
Salesforce topic: when to use it, the questions to ask first, the workflow, and the mistakes AI assistants make there.
Run-time agents apply those skills to real work and never deploy to an org. The MCP server lets the assistant ask your
actual org what already exists.</p>
<p>It is source-available under the PolyForm Small Business License 1.0.0: free for organisations under 100 people and
USD 1M revenue. See <a href="{REPO_URL}/blob/main/LICENSING.md">LICENSING.md</a>.</p>
<h2 id="domains">Browse by domain</h2>
<ul class="grid">{dom_items}</ul>
<h2 id="links">Links</h2>
<ul>
<li><a href="{REPO_URL}">Repository on GitHub</a> (install instructions are in the README)</li>
<li><a href="docs/index.html">Documentation</a></li>
<li><a href="{REPO_URL}/tree/main/agents">Agent roster</a></li>
<li><a href="{REPO_URL}/blob/main/CHANGELOG.md">Changelog</a></li>
<li><a href="sitemap.xml">Sitemap</a></li>
</ul>
"""
    site.page("index.html", SITE_NAME, f"{TAGLINE}. {intro}", body, depth=0)

    site.page(
        "404.html",
        "Page not found",
        "That page does not exist.",
        '<h1>Page not found</h1><p><a href="index.html">Back to the catalog</a>.</p>',
        depth=0,
    )

    # ---- sitemap / robots / nojekyll ---------------------------------------
    today = date.today().isoformat()
    urls = []
    for rel in sorted(site.pages):
        loc = f"{site.base}/" if rel == "index.html" else f"{site.base}/{rel}"
        urls.append(f"  <url><loc>{esc(loc)}</loc><lastmod>{today}</lastmod></url>")
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n",
        encoding="utf-8",
    )
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {site.base}/sitemap.xml\n", encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    files = [p for p in out.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    print(
        f"built {len(site.pages)} pages ({skill_page_count} skill, {len(by_domain)} domain, "
        f"{len(doc_sources)} docs) + sitemap/robots in {out}: {len(files)} files, {size / 1e6:.1f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
