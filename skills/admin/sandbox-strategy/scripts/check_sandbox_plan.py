#!/usr/bin/env python3
"""Lint sandbox strategy artifacts.

Two independent modes, either or both:

  Plan mode      positional markdown files -- the strategy document itself.
                 Section presence, masking/refresh omissions, and the topology
                 table (every environment row typed, purposed, owned; no second
                 Full sandbox without a justification; production never a build
                 target).

  Manifest mode  --manifest-dir <DX source dir> -- the deployable pieces.
                 A SandboxPostCopy Apex class (interface, no-arg constructor,
                 runApexClass, DML access mode, hard-coded Ids), its test
                 (five-argument testSandboxPostCopyScript overload), and
                 settings/Sandbox.settings.

Stdlib only. Emits JSON on stdout; exit 1 when any finding is raised.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

# Built rather than written literally so this file stays free of the marker it looks for.
PLACEHOLDER_MARKER = "TO" + "DO"

REQUIRED_SECTIONS = [
    "Environment Inventory",
    "Refresh Cadence",
    "Masking and Data Policy",
    "Post-Refresh Tasks",
    "Release Path",
]
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

SANDBOX_TYPES = ["Developer Pro", "Partial Copy", "Full", "Developer"]
JUSTIFICATION_WORDS = ("justif", "because", "rationale", "reason", "parity required")

# 15- or 18-character Salesforce Id, as a whole token.
SF_ID = re.compile(r"(?<![A-Za-z0-9_])([a-zA-Z0-9]{15}|[a-zA-Z0-9]{18})(?![A-Za-z0-9_])")
ID_PREFIX_HINT = re.compile(r"^(00[0-9A-Za-z]|01[0-9A-Za-z]|0[0-9A-Za-z]{2})")

DML_VERBS = ("insert", "update", "upsert", "delete", "undelete", "merge")
BARE_DML = re.compile(
    r"^\s*(" + "|".join(DML_VERBS) + r")\s+(?!as\s+(?:user|system)\b)[A-Za-z_]",
    re.MULTILINE,
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def first_child(element, *tags):
    """Return the first matching child element, or None.

    Never chain ``element.find(a) or element.find(b)``: an Element with no
    children is falsy, so a real-but-empty match would be discarded.
    """
    for tag in tags:
        found = element.find(tag)
        if found is not None:
            return found
    return None


def parse_md_tables(text: str) -> list[dict]:
    """Return every pipe table in the document as {heading, header, rows}."""
    tables: list[dict] = []
    heading = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            i += 1
            continue
        if line.strip().startswith("|") and i + 1 < len(lines):
            separator = lines[i + 1].strip()
            if re.fullmatch(r"\|[\s:|-]+\|", separator or "|"):
                header = [c.strip() for c in line.strip().strip("|").split("|")]
                rows = []
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                    j += 1
                tables.append({"heading": heading, "header": header, "rows": rows})
                i = j
                continue
        i += 1
    return tables


def column_index(header: list[str], *needles: str) -> int:
    for idx, name in enumerate(header):
        low = name.lower()
        for needle in needles:
            if needle in low:
                return idx
    return -1


def resolve_type(cell: str) -> str:
    """Which single sandbox type does this cell commit to? '' when ambiguous."""
    named = [t for t in SANDBOX_TYPES if t.lower() in cell.lower()]
    if "Developer Pro" in named and "Developer" in named:
        named.remove("Developer")
    return named[0] if len(named) == 1 else ""


def is_placeholder(cell: str) -> bool:
    stripped = cell.strip()
    if not stripped or stripped in {"-", "--", "n/a", "N/A"}:
        return True
    return PLACEHOLDER_MARKER in stripped


# --------------------------------------------------------------------------
# plan mode
# --------------------------------------------------------------------------


def audit_plan(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.is_file():
        return [f"HIGH {path}: file not found"]

    text = path.read_text(encoding="utf-8", errors="ignore")
    for section in REQUIRED_SECTIONS:
        pattern = rf"^##+\s+{re.escape(section)}\b"
        if not re.search(pattern, text, re.MULTILINE):
            findings.append(f"HIGH {path}: missing required section `{section}`")

    if PLACEHOLDER_MARKER in text:
        findings.append(f"LOW {path}: unresolved {PLACEHOLDER_MARKER} markers remain")

    lower = text.lower()
    if any(token in lower for token in ("partial copy", "full sandbox", "full copy")) and "mask" not in lower:
        findings.append(f"HIGH {path}: production-like sandbox mentioned without masking policy")

    if "refresh" in lower and "post-refresh" not in lower:
        findings.append(f"MEDIUM {path}: refresh cadence described without post-refresh task section")

    if "developer sandbox" in lower and "source" not in lower and "devops center" not in lower:
        findings.append(f"LOW {path}: developer sandbox strategy does not mention source discipline")

    findings.extend(audit_topology(path, text))
    return findings


def audit_topology(path: Path, text: str) -> list[str]:
    """Check the topology table: typed, purposed, owned; Full count; prod as target."""
    findings: list[str] = []
    tables = parse_md_tables(text)

    inventory = None
    for table in tables:
        if "environment" in table["heading"].lower() and "inventory" in table["heading"].lower():
            inventory = table
            break
    if inventory is None:
        for table in tables:
            if column_index(table["header"], "environment") >= 0 and column_index(table["header"], "type") >= 0:
                inventory = table
                break

    if inventory is None:
        findings.append(f"HIGH {path}: no environment inventory table found (need columns for environment, type, purpose, owner)")
        return findings

    header = inventory["header"]
    idx_env = column_index(header, "environment", "name")
    idx_type = column_index(header, "type")
    idx_purpose = column_index(header, "purpose", "use")
    idx_owner = column_index(header, "owner")

    for label, idx in (("type", idx_type), ("purpose", idx_purpose), ("owner", idx_owner)):
        if idx < 0:
            findings.append(f"HIGH {path}: environment inventory table has no `{label}` column")

    full_rows: list[str] = []
    for row in inventory["rows"]:
        env = row[idx_env] if 0 <= idx_env < len(row) else "<unnamed row>"
        if not env.strip():
            continue
        for label, idx in (("type", idx_type), ("purpose", idx_purpose), ("owner", idx_owner)):
            if idx < 0:
                continue
            cell = row[idx] if idx < len(row) else ""
            if is_placeholder(cell):
                findings.append(f"HIGH {path}: environment `{env}` has no {label}")
        if 0 <= idx_type < len(row) and resolve_type(row[idx_type]) == "Full":
            full_rows.append(env)
        if 0 <= idx_type < len(row) and row[idx_type].strip() and not resolve_type(row[idx_type]):
            findings.append(
                f"MEDIUM {path}: environment `{env}` does not commit to one sandbox type "
                f"(`{row[idx_type].strip()}`)"
            )

    if len(full_rows) > 1 and not any(word in text.lower() for word in JUSTIFICATION_WORDS):
        findings.append(
            f"HIGH {path}: {len(full_rows)} Full sandboxes ({', '.join(full_rows)}) with no written "
            f"justification; a Full licence can provision any lower type"
        )

    # Cadence coverage: every inventory environment should appear in a cadence table.
    cadence_rows: set[str] = set()
    for table in tables:
        if "cadence" in table["heading"].lower() or column_index(table["header"], "cadence") >= 0:
            idx = column_index(table["header"], "environment", "name")
            if idx < 0:
                continue
            for row in table["rows"]:
                if idx < len(row) and row[idx].strip():
                    cadence_rows.add(row[idx].strip().lower())
    if cadence_rows:
        for row in inventory["rows"]:
            if not (0 <= idx_env < len(row)):
                continue
            env = row[idx_env].strip()
            if env and env.lower() not in cadence_rows:
                findings.append(f"MEDIUM {path}: environment `{env}` has no refresh cadence row")

    findings.extend(audit_production_as_target(path, text, inventory, idx_env, idx_type))
    return findings


def audit_production_as_target(path: Path, text: str, inventory, idx_env: int, idx_type: int) -> list[str]:
    findings: list[str] = []
    for row in inventory["rows"]:
        if not (0 <= idx_env < len(row)):
            continue
        env = row[idx_env].strip().lower()
        if re.fullmatch(r"(prod|production|prd)\b.*", env):
            findings.append(
                f"CRITICAL {path}: production is listed as an environment in the sandbox inventory; "
                f"production is a deploy target, never a build or test environment"
            )
    for line in text.splitlines():
        low = line.lower()
        if re.search(r"\b(build|develop|development|integrate|test|uat|training)\b.{0,40}\bin:?\s*(prod|production)\b", low):
            findings.append(
                f"CRITICAL {path}: release path names production as a build or test target -- `{line.strip()[:100]}`"
            )
    return findings


# --------------------------------------------------------------------------
# manifest mode
# --------------------------------------------------------------------------


def audit_manifest_dir(root: Path) -> list[str]:
    findings: list[str] = []
    if not root.is_dir():
        return [f"HIGH {root}: --manifest-dir is not a directory"]

    classes = sorted(root.rglob("*.cls"))
    post_copy = [c for c in classes if re.search(r"implements[^{]*\bSandboxPostCopy\b", c.read_text(encoding="utf-8", errors="ignore"))]

    if not post_copy:
        findings.append(
            f"MEDIUM {root}: no Apex class implements SandboxPostCopy; every environment that "
            f"copies production data needs one"
        )
    for cls in post_copy:
        findings.extend(audit_post_copy_class(cls))

    tests = [c for c in classes if "testSandboxPostCopyScript" in c.read_text(encoding="utf-8", errors="ignore")]
    if post_copy and not tests:
        findings.append(
            f"HIGH {root}: SandboxPostCopy class present with no test calling "
            f"Test.testSandboxPostCopyScript()"
        )
    for test in tests:
        findings.extend(audit_post_copy_test(test))

    for settings in sorted(root.rglob("Sandbox.settings")):
        findings.extend(audit_sandbox_settings(settings))

    return findings


def audit_post_copy_class(path: Path) -> list[str]:
    findings: list[str] = []
    src = path.read_text(encoding="utf-8", errors="ignore")
    name = path.stem

    if not re.search(r"\brunApexClass\s*\(\s*(System\.)?SandboxContext\s+\w+\s*\)", src):
        findings.append(
            f"HIGH {path}: no `runApexClass(SandboxContext context)` method; the copy process "
            f"calls only this signature"
        )

    constructors = re.findall(rf"\b{re.escape(name)}\s*\(([^)]*)\)\s*\{{", src)
    if constructors and not any(arg.strip() == "" for arg in constructors):
        findings.append(
            f"HIGH {path}: constructors are declared but none is no-arg; the sandbox copy process "
            f"uses only the no-arg constructor"
        )

    body = strip_comments(src)
    for match in BARE_DML.finditer(body):
        findings.append(
            f"MEDIUM {path}: `{match.group(1)}` statement runs in the default access mode; post-copy "
            f"code runs as the Automated Process user, so pin it with `as system`"
        )
    if re.search(r"Database\.(insert|update|upsert|delete|undelete|merge)\s*\(", body) and "AccessLevel." not in body:
        findings.append(
            f"MEDIUM {path}: Database DML methods used without an AccessLevel argument; pass "
            f"AccessLevel.SYSTEM_MODE for post-copy work"
        )

    findings.extend(find_hardcoded_ids(path, body))
    return findings


def audit_post_copy_test(path: Path) -> list[str]:
    findings: list[str] = []
    src = strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
    for match in re.finditer(r"testSandboxPostCopyScript\s*\((.*?)\)\s*;", src, re.DOTALL):
        args = split_args(match.group(1))
        if len(args) < 5:
            findings.append(
                f"HIGH {path}: testSandboxPostCopyScript called with {len(args)} arguments; use the "
                f"five-argument overload with RunAsAutoProcUser = true or the test runs with the "
                f"initiator's permissions, not the post-copy user's"
            )
        elif args[4].strip().lower() != "true":
            findings.append(
                f"MEDIUM {path}: testSandboxPostCopyScript passes RunAsAutoProcUser = "
                f"{args[4].strip()}; only `true` reproduces post-copy permissions"
            )
    return findings


def audit_sandbox_settings(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"CRITICAL {path}: Sandbox.settings is not well-formed XML ({exc})"]

    tag = root.tag.replace(MD_NS, "")
    if tag != "SandboxSettings":
        findings.append(f"HIGH {path}: root element is `{tag}`, expected `SandboxSettings`")

    flag = first_child(root, f"{MD_NS}disableSandboxExpirationEmails", "disableSandboxExpirationEmails")
    if flag is None:
        findings.append(f"MEDIUM {path}: `disableSandboxExpirationEmails` not set; state the value deliberately")
    else:
        value = (flag.text or "").strip().lower()
        if value not in {"true", "false"}:
            findings.append(f"HIGH {path}: `disableSandboxExpirationEmails` is `{flag.text}`, expected true or false")
        elif value == "true":
            findings.append(
                f"REVIEW {path}: sandbox expiration emails are disabled; confirm a named owner tracks "
                f"the 180-day inactivity deletion by other means"
            )
    return findings


def find_hardcoded_ids(path: Path, body: str) -> list[str]:
    findings: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"'([^']*)'", body):
        literal = match.group(1)
        id_match = SF_ID.fullmatch(literal)
        if not id_match:
            continue
        if not ID_PREFIX_HINT.match(literal):
            continue
        if literal in seen:
            continue
        seen.add(literal)
        findings.append(
            f"HIGH {path}: hard-coded record Id `{literal}`; Ids differ between production and every "
            f"sandbox, so post-copy code must look values up by name or use Custom Metadata"
        )
    return findings


def strip_comments(src: str) -> str:
    """Remove Apex comments without touching string literals.

    A naive regex eats the `//` inside `'https://...'`, which is exactly the
    literal a post-copy class is most likely to contain. Scan instead, tracking
    whether we are inside a single-quoted Apex string and honouring backslash
    escapes.
    """
    out: list[str] = []
    i = 0
    n = len(src)
    in_string = False
    while i < n:
        ch = src[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if ch == "'":
                in_string = False
            i += 1
            continue
        if ch == "'":
            in_string = True
            out.append(ch)
            i += 1
            continue
        if src.startswith("//", i):
            end = src.find("\n", i)
            i = n if end == -1 else end
            continue
        if src.startswith("/*", i):
            end = src.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def split_args(blob: str) -> list[str]:
    args: list[str] = []
    depth = 0
    current: list[str] = []
    in_string = False
    for ch in blob:
        if ch == "'":
            in_string = not in_string
        if not in_string:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            elif ch == "," and depth == 0:
                args.append("".join(current))
                current = []
                continue
        current.append(ch)
    if "".join(current).strip():
        args.append("".join(current))
    return args


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check sandbox strategy plans (sections, topology table, masking/refresh omissions) "
            "and the deployable pieces in a DX source tree (SandboxPostCopy class and test, "
            "Sandbox.settings)."
        )
    )
    parser.add_argument("plans", nargs="*", help="Markdown strategy files to review")
    parser.add_argument(
        "--manifest-dir",
        metavar="DIR",
        help="DX source directory to scan for a SandboxPostCopy class, its test, and Sandbox.settings",
    )
    args = parser.parse_args()

    if not args.plans and not args.manifest_dir:
        parser.error("provide at least one markdown plan or --manifest-dir")

    findings: list[str] = []
    for value in args.plans:
        findings.extend(audit_plan(Path(value)))
    if args.manifest_dir:
        findings.extend(audit_manifest_dir(Path(args.manifest_dir)))

    scanned = len(args.plans) + (1 if args.manifest_dir else 0)
    summary = f"Scanned {scanned} sandbox strategy input(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
