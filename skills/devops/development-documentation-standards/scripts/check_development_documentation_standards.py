#!/usr/bin/env python3
"""Checker for Salesforce development documentation standards (ApexDoc + naming).

Scans Apex source (*.cls) for the documentation-convention mistakes described in
references/gotchas.md and references/llm-anti-patterns.md. ApexDoc is a *convention*
the compiler never validates, so these are exactly the errors that ship silently.

Checks performed per public/global class, method, and constructor:
  - Missing ApexDoc block immediately preceding the declaration.
  - A preceding doc block opened with `/*` (one asterisk) instead of `/**`.
  - `@return` present on a `void` method or a constructor (invalid).
  - `@return` missing on a non-`void` method.
  - `@param` count / names not matching the parameter list.
  - JavaDoc-only tags that ApexDoc doesn't define (e.g. `@exception`, `@inheritDoc`).
Plus naming-convention checks:
  - Class name not starting with a capital letter.
  - Method name not starting with a lowercase letter.

Stdlib only — no pip dependencies. Heuristic regex parser: it aims for low false
positives on ordinary Apex, not full-grammar parsing.

Usage:
    python3 check_development_documentation_standards.py [--manifest-dir path] [--require-return]

Exit code 0 = no issues, 1 = issues found (or bad input).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ApexDoc-defined tags (block + inline). Anything else that looks like a tag is suspect.
APEXDOC_BLOCK_TAGS = {
    "@param", "@return", "@throws", "@author", "@deprecated",
    "@example", "@group", "@see", "@since", "@version",
}
APEXDOC_INLINE_TAGS = {"@code", "@link", "@literal", "@hidden"}
# JavaDoc-only tags an LLM commonly bleeds in (see llm-anti-patterns.md #2).
JAVADOC_ONLY_TAGS = {
    "@exception", "@inheritdoc", "@serial", "@serialdata", "@serialfield", "@value",
}

VISIBILITY = r"(?:global|public|protected|private)"
# Class / interface / enum declaration.
TYPE_DECL_RE = re.compile(
    r"^\s*(?:(?P<mods>(?:global|public|protected|private|virtual|abstract|with sharing|"
    r"without sharing|inherited sharing|static|final)\s+)*)"
    r"(?P<kind>class|interface|enum)\s+(?P<name>\w+)",
    re.IGNORECASE,
)
# Method / constructor declaration: <mods> [returnType] name(params) {  or ;
METHOD_DECL_RE = re.compile(
    r"^\s*(?P<mods>(?:global|public|protected|private|virtual|abstract|override|static|"
    r"final|testmethod|with sharing|without sharing)\s+)+"
    r"(?:(?P<rettype>[\w<>,.\[\]\s]+?)\s+)?"
    r"(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*(?:\{|;)",
    re.IGNORECASE,
)
KEYWORDS_NOT_METHODS = {"if", "for", "while", "catch", "switch", "else", "return", "new", "get", "set"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for ApexDoc and naming-convention issues (unenforced by the compiler).",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce source (scanned recursively for *.cls). Default: cwd.",
    )
    parser.add_argument(
        "--require-return",
        action="store_true",
        help="Also flag non-void methods that are missing a @return tag.",
    )
    return parser.parse_args()


def _preceding_doc_block(lines: list[str], decl_idx: int) -> tuple[list[str] | None, bool]:
    """Return (doc_block_lines, opened_with_double_star) for the block that immediately
    precedes the declaration at decl_idx, skipping only annotation lines (@Foo) which are
    allowed to sit between the block and the declaration. (None, False) if no block."""
    i = decl_idx - 1
    # Skip annotation lines directly above the declaration (e.g. @AuraEnabled, @isTest).
    while i >= 0 and lines[i].strip().startswith("@") and "*/" not in lines[i]:
        i -= 1
    if i < 0 or lines[i].strip() != "" and not lines[i].rstrip().endswith("*/"):
        # The line immediately above must be the end of a comment block; a blank line or
        # code means the declaration is undocumented / detached.
        if not lines[i].rstrip().endswith("*/"):
            return None, False
    if not lines[i].rstrip().endswith("*/"):
        return None, False
    end = i
    # Walk up to the block opener.
    start = end
    while start >= 0 and not (lines[start].lstrip().startswith("/*")):
        start -= 1
    if start < 0:
        return None, False
    opener = lines[start].lstrip()
    opened_double = opener.startswith("/**")
    return lines[start:end + 1], opened_double


def _tags_in_block(block: list[str]) -> list[str]:
    tags: list[str] = []
    for ln in block:
        for m in re.finditer(r"@\w+", ln):
            tags.append(m.group(0).lower())
    return tags


def _param_names(param_str: str) -> list[str]:
    param_str = param_str.strip()
    if not param_str:
        return []
    names: list[str] = []
    for chunk in param_str.split(","):
        toks = chunk.strip().split()
        if toks:
            names.append(toks[-1])  # last token is the parameter name
    return names


def _check_declaration(
    path: Path, lines: list[str], idx: int, issues: list[str], require_return: bool,
) -> None:
    line = lines[idx]
    type_m = TYPE_DECL_RE.match(line)
    method_m = None if type_m else METHOD_DECL_RE.match(line)

    if type_m:
        name = type_m.group("name")
        kind = type_m.group("kind").lower()
        block, opened_double = _preceding_doc_block(lines, idx)
        loc = f"{path}:{idx + 1}"
        if kind == "class" and not name[:1].isupper():
            issues.append(f"{loc}: class '{name}' should start with a capital letter (naming convention).")
        if block is None:
            issues.append(f"{loc}: {kind} '{name}' has no ApexDoc block immediately preceding it.")
        elif not opened_double:
            issues.append(
                f"{loc}: {kind} '{name}' doc block opens with '/*' — use '/**' or generators skip it."
            )
        return

    if not method_m:
        return

    name = method_m.group("name")
    if name.lower() in KEYWORDS_NOT_METHODS:
        return
    rettype = (method_m.group("rettype") or "").strip()
    params = method_m.group("params")
    loc = f"{path}:{idx + 1}"

    # Constructor: no return type and name matches an enclosing type is hard to know cheaply;
    # heuristic — a method with no return type token is treated as a constructor.
    is_constructor = rettype == ""
    is_void = rettype.lower() == "void"

    if not name[:1].islower() and not is_constructor:
        issues.append(f"{loc}: method '{name}' should start with a lowercase verb (naming convention).")

    block, opened_double = _preceding_doc_block(lines, idx)
    label = "constructor" if is_constructor else "method"
    if block is None:
        issues.append(f"{loc}: {label} '{name}' has no ApexDoc block immediately preceding it.")
        return
    if not opened_double:
        issues.append(
            f"{loc}: {label} '{name}' doc block opens with '/*' — use '/**' or generators skip it."
        )

    tags = _tags_in_block(block)

    for t in tags:
        if t in JAVADOC_ONLY_TAGS:
            fix = " (use @throws)" if t == "@exception" else ""
            issues.append(f"{loc}: {label} '{name}' uses JavaDoc-only tag '{t}' not defined by ApexDoc{fix}.")

    has_return = "@return" in tags
    if (is_void or is_constructor) and has_return:
        issues.append(f"{loc}: {label} '{name}' has @return but returns void / is a constructor.")
    if require_return and not is_void and not is_constructor and not has_return:
        issues.append(f"{loc}: method '{name}' returns '{rettype}' but has no @return tag.")

    declared_params = _param_names(params)
    param_tag_count = sum(1 for t in tags if t == "@param")
    if param_tag_count != len(declared_params):
        issues.append(
            f"{loc}: {label} '{name}' has {param_tag_count} @param tag(s) for "
            f"{len(declared_params)} parameter(s)."
        )
    else:
        # Check the documented names match the declared names (order-insensitive membership).
        documented = []
        for ln in block:
            m = re.search(r"@param\s+(\w+)", ln)
            if m:
                documented.append(m.group(1))
        for d in documented:
            if d not in declared_params:
                issues.append(
                    f"{loc}: {label} '{name}' @param '{d}' does not match any parameter "
                    f"({', '.join(declared_params) or 'none'})."
                )


def check(manifest_dir: Path, require_return: bool) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    cls_files = sorted(manifest_dir.rglob("*.cls"))
    if not cls_files:
        return [f"No Apex classes (*.cls) found under {manifest_dir} — nothing to check."]

    for path in cls_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"{path}: could not read ({exc})")
            continue
        lines = text.splitlines()
        for idx in range(len(lines)):
            _check_declaration(path, lines, idx, issues, require_return)
    return issues


def main() -> int:
    args = parse_args()
    issues = check(Path(args.manifest_dir), args.require_return)
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
