#!/usr/bin/env python3
"""Deterministic Confluence space -> headings file for `onboard_source.py url`.

`onboard_source.py`'s url mode expects a caller-distilled headings file because
fetching is out of scope for it. For a one-off web article you can distil by
hand; for a wiki with hundreds of pages you cannot, and hand-distillation is
exactly the kind of step that lets fabricated topics into the pipeline. This
script closes that gap for Confluence Cloud: it reads a space through the
public REST v2 API and emits topic names only.

    python3 scripts/confluence_to_headings.py \
        --base-url https://example.atlassian.net \
        --space-key SF \
        --out /tmp/space-topics.md \
        --manifest /tmp/space-manifest.json

    python3 scripts/onboard_source.py url /tmp/space-topics.md \
        --source-url https://example.atlassian.net/wiki/spaces/SF --update-backlog

Clean-room safety
-----------------
The output file contains ONLY page titles and H2/H3 heading text. Body prose
never leaves this script — it is read to measure the page (length, external
link count) and to locate headings, then discarded. Downstream agents see topic
names, never source expression. Do not add a flag that emits page bodies.

Filtering
---------
A wiki accumulates bookmarks, vendor notes, and event links alongside real
documentation. Emitting all of it floods BACKLOG.yaml and burns the expensive
verification stages on junk, so pages are dropped when they are:

    * thinner than --min-chars of visible text (stubs)
    * link-dumps (short body carrying an external href, or many hrefs and
      little text) — a bookmark, not documentation
    * verbatim third-party clippings, detected by a trailing publisher
      attribution in the title ("... - Salesforce Ben", "... - Arkus, Inc.")

Surviving pages contribute their title plus each H2/H3 heading as candidate
topics. `onboard_source.py` dedupes by slug and drops the first H1, so the
first line here is a deliberately sacrificial title.

Authentication
--------------
Anonymous by default (many spaces permit it). For a private space, export
CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN and they are sent as Basic auth.

stdlib-only.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

PAGE_LIMIT = 100
DEFAULT_MIN_CHARS = 800

# "Title - Publisher" / "Title — Publisher, Inc." — a clipped third-party article.
CLIPPING_RE = re.compile(r"\s[-–—]\s[A-Z][\w .,'&/]{2,40}$")
HEADING_RE = re.compile(r"<h([23])\b[^>]*>(.*?)</h\1>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
EXT_LINK_RE = re.compile(r'href="https?://', re.I)

# Titles that name a product, a person, or an event rather than a capability.
# Keep these lists observational — every entry earned its place from a real run.
#
# Substrings, only for phrases that cannot appear inside a real capability name.
NOISE_TITLE_PHRASES = (
    "chrome extension", "appexchange", "podcast", "webinar", "dreamforce",
    "user group", "résumé", "bookmark",
)
# Whole-title matches. These words DO appear inside real capability names
# ("Resume a Paused Flow", "Deep Links"), so substring matching would silently
# eat good pages on the next wiki this script meets.
NOISE_TITLE_EXACT = frozenset({
    "resources", "links", "resume", "notes", "help", "tips", "index", "home",
})


def _fetch(url: str) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    email = os.environ.get("CONFLUENCE_EMAIL")
    token = os.environ.get("CONFLUENCE_API_TOKEN")
    if email and token:
        credential = base64.b64encode(f"{email}:{token}".encode()).decode()
        request.add_header("Authorization", f"Basic {credential}")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = "set CONFLUENCE_EMAIL + CONFLUENCE_API_TOKEN" if exc.code in (401, 403) else exc.reason
        raise SystemExit(f"Confluence API {exc.code} for {url} — {detail}")


def resolve_space_id(base_url: str, space_key: str) -> str:
    query = urllib.parse.urlencode({"keys": space_key})
    payload = _fetch(f"{base_url}/wiki/api/v2/spaces?{query}")
    results = payload.get("results") or []
    if not results:
        raise SystemExit(f"No space with key {space_key!r} at {base_url}")
    return results[0]["id"]


def iter_pages(base_url: str, space_id: str):
    query = urllib.parse.urlencode({"limit": PAGE_LIMIT, "body-format": "storage"})
    url = f"{base_url}/wiki/api/v2/spaces/{space_id}/pages?{query}"
    while url:
        payload = _fetch(url)
        yield from payload.get("results", [])
        following = (payload.get("_links") or {}).get("next")
        url = f"{base_url}{following}" if following else None


def visible_text(storage: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", storage))).strip()


def headings(storage: str) -> list[str]:
    found = []
    for _, inner in HEADING_RE.findall(storage):
        text = html.unescape(TAG_RE.sub("", inner)).strip()
        text = re.sub(r"\s+", " ", text).strip(" :!?")
        if len(text) >= 4:
            found.append(text)
    return found


def is_link_dump(text_length: int, external_links: int) -> bool:
    """A bookmark: little of its own text, pointing somewhere else."""
    if text_length < 400 and external_links >= 1:
        return True
    return external_links >= 8 and text_length < 2000


def is_noise_title(title: str) -> bool:
    lowered = title.lower().strip()
    if lowered in NOISE_TITLE_EXACT:
        return True
    return any(phrase in lowered for phrase in NOISE_TITLE_PHRASES)


def classify_page(page: dict, min_chars: int) -> tuple[bool, str, int]:
    """Return (keep, reason-when-dropped, visible-text-length)."""
    title = page["title"]
    storage = ((page.get("body") or {}).get("storage") or {}).get("value") or ""
    text_length = len(visible_text(storage))
    external_links = len(EXT_LINK_RE.findall(storage))
    if CLIPPING_RE.search(title):
        return False, "third-party clipping (publisher attribution in title)", text_length
    if is_noise_title(title):
        return False, "noise title (product/person/event, not a capability)", text_length
    if is_link_dump(text_length, external_links):
        return False, f"link-dump ({text_length} chars, {external_links} external links)", text_length
    if text_length < min_chars:
        return False, f"below --min-chars ({text_length} < {min_chars})", text_length
    return True, "", text_length


def harvest(base_url: str, space_key: str, min_chars: int) -> dict:
    space_id = resolve_space_id(base_url, space_key)
    kept, dropped, topics, provenance = [], [], [], {}
    for page in iter_pages(base_url, space_id):
        keep, reason, chars = classify_page(page, min_chars)
        record = {
            "id": page["id"],
            "title": page["title"],
            "version": page["version"]["number"],
            "updated": page["version"].get("createdAt", "")[:10],
            # A caller ordering waves needs a priority signal that is not a
            # model's opinion: how much the page actually had to say.
            "chars": chars,
        }
        if not keep:
            dropped.append({**record, "reason": reason})
            continue
        kept.append(record)
        storage = page["body"]["storage"]["value"]
        for topic in [page["title"], *headings(storage)]:
            if topic not in provenance:
                provenance[topic] = page["id"]
                topics.append(topic)
    return {
        "base_url": base_url,
        "space_key": space_key,
        "space_id": space_id,
        "space_url": f"{base_url}/wiki/spaces/{space_key}",
        "pages_seen": len(kept) + len(dropped),
        "pages_kept": len(kept),
        "pages_dropped": len(dropped),
        "topics": topics,
        "topic_page_ids": provenance,
        "kept": kept,
        "dropped": dropped,
    }


def render_headings(result: dict) -> str:
    """First line is a sacrificial H1 — onboard_source.py drops the doc title."""
    lines = [f"# {result['space_key']} space topic radar", ""]
    lines += [f"## {topic}" for topic in result["topics"]]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base-url", required=True, help="https://<site>.atlassian.net")
    parser.add_argument("--space-key", required=True)
    parser.add_argument("--min-chars", type=int, default=DEFAULT_MIN_CHARS,
                        help=f"minimum visible text per page (default {DEFAULT_MIN_CHARS})")
    parser.add_argument("--out", required=True, help="headings file to write")
    parser.add_argument("--manifest", help="page-id/version lockfile for delta runs")
    args = parser.parse_args(argv)

    result = harvest(args.base_url.rstrip("/"), args.space_key, args.min_chars)

    with open(args.out, "w") as handle:
        handle.write(render_headings(result))
    if args.manifest:
        with open(args.manifest, "w") as handle:
            json.dump({
                "space_url": result["space_url"],
                "space_id": result["space_id"],
                "pages": {p["id"]: p["version"] for p in result["kept"]},
                "page_chars": {p["id"]: p["chars"] for p in result["kept"]},
                "page_updated": {p["id"]: p["updated"] for p in result["kept"]},
                "topic_page_ids": result["topic_page_ids"],
            }, handle, indent=1)
            handle.write("\n")

    print(f"{result['space_url']}: {result['pages_seen']} pages seen, "
          f"{result['pages_kept']} kept, {result['pages_dropped']} dropped")
    reasons: dict[str, int] = {}
    for page in result["dropped"]:
        key = page["reason"].split(" (")[0]
        reasons[key] = reasons.get(key, 0) + 1
    for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  drop: {count:4d}  {reason}")
    print(f"{len(result['topics'])} topics -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
