#!/usr/bin/env python3
"""Audit inbound Apex REST resources for contract, security, and mapping defects.

Static text analysis only — this script never compiles Apex and never contacts an
org. Every rule below traces to a documented platform behaviour:

  * `@RestResource` class must be `global`                     apexdev L6352
  * verb methods must be `global static`                       apexdev L6388 (per verb)
  * one method per HTTP verb per class                         apexdev L18446-18448
  * `@HttpGet` / `@HttpDelete` take no parameters              apexdev L18442-18443
  * urlMapping: leading '/', <= 255 chars, wildcard preceded
    by '/' and followed by '/' unless it is the last char      apexdev L6356-6361
  * overlapping mappings resolve by save order, not specificity apexdev L18589-18591
  * mapping is case-sensitive                                  apexdev L6350-6351
  * sharing default inverted at apiVersion 67.0                apexdev L18738-18739
  * statusCode outside the documented table becomes a 500      apexrefguide L228768-228820
  * a catch block that sets no statusCode leaves the default   apexrefguide L228728-228734

Usage:
    python3 check_apex_rest_services.py --manifest-dir force-app
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REST_RE = re.compile(r"@RestResource\b", re.IGNORECASE)
URLMAP_RE = re.compile(
    r"@RestResource\s*\(\s*urlMapping\s*=\s*['\"](?P<mapping>[^'\"]*)['\"]\s*\)",
    re.IGNORECASE,
)
CLASS_DECL_RE = re.compile(
    r"@RestResource\s*\([^)]*\)(?P<mods>[^{]*?)\bclass\s+(?P<name>\w+)",
    re.IGNORECASE | re.DOTALL,
)
VERB_METHOD_RE = re.compile(
    r"@Http(?P<verb>Get|Post|Patch|Put|Delete)\b(?P<sig>[^{;]*?)\((?P<params>[^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)
SHARING_RE = re.compile(r"\b(with|without|inherited)\s+sharing\b", re.IGNORECASE)
STATUS_ASSIGN_RE = re.compile(r"statusCode\s*=\s*(\d+)")
STATUS_ANY_RE = re.compile(r"statusCode\s*=", re.IGNORECASE)
RESTCONTEXT_RE = re.compile(r"RestContext\.(request|response)", re.IGNORECASE)
RESTCONTEXT_SET_RE = re.compile(r"RestContext\.(request|response)\s*=")
ISTEST_RE = re.compile(r"@IsTest\b", re.IGNORECASE)
CATCH_RE = re.compile(r"\bcatch\s*\(([^)]*)\)\s*\{")
API_VERSION_RE = re.compile(r"<apiVersion>\s*([0-9.]+)\s*</apiVersion>")

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

# apexrefguide L228772-228820 — the complete set of codes RestResponse.statusCode accepts.
# Anything else returns 500 "Invalid status code for HTTP response: nnn" (L228767-228769).
VALID_STATUS_CODES = {
    200, 201, 202, 204, 206,
    300, 301, 302, 304,
    400, 401, 403, 404, 405, 406, 409, 410, 412, 413, 414, 415, 417,
    500, 503,
}

# apexdev L6357 — "The path can be up to 255 characters long."
MAX_MAPPING_LENGTH = 255

# A class with no sharing keyword runs `with sharing` from API 67.0 (Summer '26);
# below that it runs without sharing. See agents/_shared/AGENT_CONTRACT.md,
# "Apex security idiom by API version", and apexdev L18738-18739.
DEFAULT_WITH_SHARING_IN = 67.0


# --------------------------------------------------------------------------- utils


def line_of(text: str, index: int) -> int:
    """1-based line number of a character offset."""
    return text.count("\n", 0, index) + 1


def scan(text: str) -> tuple[str, str]:
    """One pass that classifies each character as code, comment, or string literal.

    Returns (code_only, no_comments), both the same length as `text` so that
    `line_of` still reports real line numbers:

      * code_only   — comments AND string literals blanked. Used for structure
                      (class declaration, method signatures, catch bodies), so a
                      `/*` inside a string literal such as urlMapping='/v1/cases/*'
                      cannot be mistaken for the start of a block comment.
      * no_comments — comments blanked, string literals intact. Used for the
                      urlMapping value, which only exists inside a literal.
    """
    code = list(text)
    nocom = list(text)
    i, n = 0, len(text)
    while i < n:
        two = text[i : i + 2]
        if two == "//":
            j = text.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                code[k] = " "
                nocom[k] = " "
            i = j
        elif two == "/*":
            j = text.find("*/", i + 2)
            j = n if j == -1 else j + 2
            for k in range(i, j):
                if text[k] != "\n":
                    code[k] = " "
                    nocom[k] = " "
            i = j
        elif text[i] == "'":
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == "'":
                    j += 1
                    break
                j += 1
            for k in range(i, min(j, n)):
                if text[k] != "\n":
                    code[k] = " "
            i = min(j, n)
        else:
            i += 1
    return "".join(code), "".join(nocom)


def block_after(text: str, open_brace_index: int) -> str:
    """Return the source between a `{` and its matching `}`."""
    depth = 0
    for i in range(open_brace_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1 : i]
    return text[open_brace_index + 1 :]


def class_api_version(path: Path) -> float | None:
    """apiVersion from the sibling `<Class>.cls-meta.xml`, or None.

    The missing sharing keyword is undecidable from the .cls alone — the class's
    own version pin decides it, not the org's release — but the meta XML sits
    right next to it, so it is decidable here.
    """
    meta = path.with_name(path.name + "-meta.xml")
    if not meta.is_file():
        return None
    match = API_VERSION_RE.search(meta.read_text(encoding="utf-8", errors="ignore"))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check inbound Apex REST resource classes for contract, mapping, and security defects."
    )
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for Apex classes.")
    return parser.parse_args()


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.cls") if path.is_file())


# --------------------------------------------------------------------------- rules


def check_mapping(path: Path, mapping: str, line: int) -> list[str]:
    """apexdev L6356-6361 — URL path mapping rules."""
    findings: list[str] = []
    where = f"{path}:{line}"
    if not mapping.startswith("/"):
        findings.append(
            f"CRITICAL {where}: urlMapping '{mapping}' does not begin with a forward slash; "
            f"'The path must begin with a forward slash (/)' (apexdev L6357)"
        )
    if len(mapping) > MAX_MAPPING_LENGTH:
        findings.append(
            f"HIGH {where}: urlMapping is {len(mapping)} characters; the documented cap is "
            f"{MAX_MAPPING_LENGTH} (apexdev L6358)"
        )
    for i, char in enumerate(mapping):
        if char != "*":
            continue
        if i == 0 or mapping[i - 1] != "/":
            findings.append(
                f"HIGH {where}: urlMapping '{mapping}' has a wildcard that is not preceded by '/'; "
                f"'A wildcard (*) that appears in a path must be preceded by a forward slash (/)' (apexdev L6359)"
            )
        if i != len(mapping) - 1 and mapping[i + 1] != "/":
            findings.append(
                f"HIGH {where}: urlMapping '{mapping}' has a non-terminal wildcard that is not followed by '/'; "
                f"'unless the wildcard is the last character in the path, it must be followed by a forward slash (/)' "
                f"(apexdev L6360-6361)"
            )
    if mapping != mapping.lower():
        findings.append(
            f"LOW {where}: urlMapping '{mapping}' mixes case and the mapping is case-sensitive "
            f"(apexdev L6350-6351); a client that normalises casing gets a 404"
        )
    return findings


def check_verb_methods(path: Path, text: str, source: str) -> list[str]:
    """One method per verb; global static; no parameters on GET/DELETE."""
    findings: list[str] = []
    seen: dict[str, int] = {}
    for match in VERB_METHOD_RE.finditer(source):
        verb = match.group("verb").capitalize()
        sig = match.group("sig")
        params = match.group("params").strip()
        line = line_of(text, match.start())
        where = f"{path}:{line}"

        if verb in seen:
            findings.append(
                f"CRITICAL {where}: a second @Http{verb} method in the same class (first at line {seen[verb]}); "
                f"'A single Apex class annotated with @RestResource can't have multiple methods annotated with "
                f"the same HTTP request method' (apexdev L18446-18448)"
            )
        else:
            seen[verb] = line

        lowered = sig.lower()
        if "global" not in lowered or "static" not in lowered:
            findings.append(
                f"CRITICAL {where}: @Http{verb} method is not declared `global static`; "
                f"'To use this annotation, your Apex method must be defined as global static' (apexdev L6388)"
            )
        if verb in ("Get", "Delete") and params:
            findings.append(
                f"CRITICAL {where}: @Http{verb} declares parameters ({params!r}); "
                f"'Methods annotated with @HttpGet or @HttpDelete must have no parameters' (apexdev L18442-18443)"
            )
        if verb in ("Post", "Patch", "Put") and params and "requestBody" in source:
            findings.append(
                f"MEDIUM {where}: @Http{verb} declares parameters AND the class reads requestBody; "
                f"'If the method has parameters... the data won't be deserialized into the "
                f"RestRequest.requestBody property' (apexdev L18459-18461) — one of the two reads nothing"
            )
        if params and "returntype" not in lowered and re.search(r"\bvoid\b", lowered) is None:
            # informational: a non-void verb method hands serialization to the platform
            pass
    return findings


def check_return_types(path: Path, text: str, source: str) -> list[str]:
    """A non-void verb method lets the platform own the body and the status code."""
    findings: list[str] = []
    for match in VERB_METHOD_RE.finditer(source):
        sig = match.group("sig")
        if re.search(r"\bvoid\b", sig, re.IGNORECASE):
            continue
        line = line_of(text, match.start())
        findings.append(
            f"MEDIUM {path}:{line}: @Http{match.group('verb').capitalize()} has a non-void return type; "
            f"the platform serializes the return value, drops null fields (apexdev L18463-18465), and on a "
            f"large collection can exhaust heap after the 200 header is sent (apexdev L18474-18477). "
            f"'To gain control of the statusCode and the responseBody, use a RestResponse instead of directly "
            f"returning sObjects' (apexdev L18477-18478)"
        )
    return findings


def check_status_codes(path: Path, text: str, source: str) -> list[str]:
    """apexrefguide L228768-228820 — codes outside the table are converted to 500."""
    findings: list[str] = []
    for match in STATUS_ASSIGN_RE.finditer(source):
        code = int(match.group(1))
        if code in VALID_STATUS_CODES:
            continue
        line = line_of(text, match.start())
        findings.append(
            f"CRITICAL {path}:{line}: statusCode = {code} is not in the documented RestResponse.statusCode "
            f"table, so the platform returns 500 'Invalid status code for HTTP response: {code}' "
            f"(apexrefguide L228768-228770). Use 400 for validation and 409 for a conflict, and carry the "
            f"specific reason in the error envelope"
        )
    return findings


def method_bodies(source: str) -> list[tuple[str, int, str]]:
    """(name, offset_of_open_brace, body) for every `name(...) {` in the source."""
    out: list[tuple[str, int, str]] = []
    for match in re.finditer(r"\b([A-Za-z_]\w*)\s*\([^()]*\)\s*\{", source):
        brace = source.index("{", match.end() - 1)
        out.append((match.group(1), brace, block_after(source, brace)))
    return out


def check_catch_blocks(path: Path, text: str, source: str) -> list[str]:
    """A catch inside a verb method that neither sets a status code nor rethrows
    leaves the response at its default, so the caller reads a success.

    Helper delegation counts: a catch that calls a same-class method whose own body
    assigns statusCode (the `fail(res, 400, ...)` idiom) is not a finding. Catches in
    private helpers that return a sentinel are not exit paths and are not checked.
    """
    findings: list[str] = []
    status_setters = {
        name for name, _, body in method_bodies(source) if STATUS_ANY_RE.search(body)
    }
    setter_call = (
        re.compile(r"\b(?:" + "|".join(re.escape(n) for n in status_setters) + r")\s*\(")
        if status_setters
        else None
    )

    # Only the bodies of @Http*-annotated methods are exit paths.
    for verb_match in VERB_METHOD_RE.finditer(source):
        brace = source.find("{", verb_match.end() - 1)
        if brace == -1:
            continue
        body_start = brace + 1
        body = block_after(source, brace)
        for catch in CATCH_RE.finditer(body):
            inner_brace = body.find("{", catch.end() - 1)
            if inner_brace == -1:
                continue
            handler = block_after(body, inner_brace)
            if STATUS_ANY_RE.search(handler) or re.search(r"\bthrow\b", handler):
                continue
            if setter_call is not None and setter_call.search(handler):
                continue
            line = line_of(text, body_start + catch.start())
            findings.append(
                f"HIGH {path}:{line}: catch ({catch.group(1).strip()}) in the @Http"
                f"{verb_match.group('verb').capitalize()} method sets no statusCode, calls no status-setting "
                f"helper, and does not rethrow; the response keeps its default and the caller reads a success. "
                f"Set an explicit code and write the error envelope on every exit path"
            )
    return findings


def check_sharing(path: Path, text: str, source: str, mods: str) -> list[str]:
    findings: list[str] = []
    if SHARING_RE.search(mods) or SHARING_RE.search(source.split("{", 1)[0]):
        return findings
    api = class_api_version(path)
    if api is not None and api >= DEFAULT_WITH_SHARING_IN:
        findings.append(
            f"LOW {path}: Apex REST class has no explicit sharing declaration; at apiVersion "
            f"{api:.1f} it runs `with sharing` (apexdev L18738-18739), so declare it rather than leave the "
            f"posture to the version pin"
        )
    elif api is None:
        findings.append(
            f"HIGH {path}: Apex REST class has no explicit sharing declaration and has no sibling "
            f".cls-meta.xml to read; graded as pre-{DEFAULT_WITH_SHARING_IN:.1f} (runs without sharing)"
        )
    else:
        findings.append(
            f"HIGH {path}: Apex REST class has no explicit sharing declaration; at apiVersion "
            f"{api:.1f} it runs without sharing (apexdev L18738-18739) and exposes records the caller "
            f"cannot otherwise see"
        )
    return findings


def audit_file(path: Path) -> tuple[list[str], list[tuple[str, str]], str | None]:
    """Return (findings, [(mapping, class_name)], class_name_if_rest_resource)."""
    findings: list[str] = []
    mappings: list[tuple[str, str]] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not REST_RE.search(text):
        return findings, mappings, None

    source, no_comments = scan(text)
    decl = CLASS_DECL_RE.search(source)
    class_name = decl.group("name") if decl else path.stem
    mods = decl.group("mods") if decl else ""

    if decl and "global" not in mods.lower():
        findings.append(
            f"CRITICAL {path}:{line_of(text, decl.start())}: class {class_name} carries @RestResource but is "
            f"not declared `global`; 'To use this annotation, your Apex class must be defined as global' "
            f"(apexdev L6352)"
        )

    mapping_match = URLMAP_RE.search(no_comments)
    if not mapping_match:
        findings.append(
            f"HIGH {path}: @RestResource has no readable urlMapping literal; the annotation form is "
            f"@RestResource(urlMapping='/yourUrl') (apexdev L6333)"
        )
    else:
        mapping = mapping_match.group("mapping")
        mappings.append((mapping, class_name))
        findings.extend(check_mapping(path, mapping, line_of(text, mapping_match.start())))

    if not VERB_METHOD_RE.search(source):
        findings.append(f"HIGH {path}: `@RestResource` class has no HTTP method annotations")

    findings.extend(check_verb_methods(path, text, source))
    findings.extend(check_return_types(path, text, source))
    findings.extend(check_status_codes(path, text, source))
    findings.extend(check_catch_blocks(path, text, source))
    findings.extend(check_sharing(path, text, source, mods))

    if not STATUS_ANY_RE.search(source):
        findings.append(
            f"REVIEW {path}: REST resource sets no response status code anywhere; every non-2xx path is "
            f"reporting success to the caller"
        )
    if "requestBody" in source and "JSON.deserialize" not in source and "JSON.deserializeUntyped" not in source \
            and "JSON.deserializeStrict" not in source:
        findings.append(f"MEDIUM {path}: request body access found without obvious JSON parsing")
    if not RESTCONTEXT_RE.search(source):
        findings.append(
            f"REVIEW {path}: REST resource does not reference `RestContext`; verify response handling is explicit"
        )
    return findings, mappings, class_name


def check_cross_file(
    mappings: list[tuple[str, str, Path]],
    rest_classes: list[tuple[str, Path]],
    test_targets: set[str],
    any_test_sets_restcontext: bool,
) -> list[str]:
    findings: list[str] = []

    by_mapping: dict[str, list[tuple[str, Path]]] = {}
    for mapping, class_name, path in mappings:
        by_mapping.setdefault(mapping, []).append((class_name, path))
    for mapping, owners in sorted(by_mapping.items()):
        if len(owners) > 1:
            names = ", ".join(f"{n} ({p})" for n, p in owners)
            findings.append(
                f"CRITICAL {owners[0][1]}: urlMapping '{mapping}' is claimed by {len(owners)} classes — {names}. "
                f"The request resolves to the class that was saved first, not the more specific one "
                f"(apexdev L18589-18591)"
            )

    # /x versus /x/* — the guide's named collision case.
    plain = {m.rstrip("/"): (n, p) for m, n, p in mappings if not m.endswith("*")}
    for mapping, class_name, path in mappings:
        if not mapping.endswith("/*"):
            continue
        stem = mapping[:-2]
        if stem in plain and plain[stem][0] != class_name:
            findings.append(
                f"CRITICAL {path}: urlMapping '{mapping}' and '{stem}' (class {plain[stem][0]}) match the same "
                f"URL; 'a REST request for this URL pattern resolves to the class that was saved first' "
                f"(apexdev L18589-18591)"
            )

    for class_name, path in rest_classes:
        if class_name not in test_targets:
            findings.append(
                f"HIGH {path}: no @IsTest class in the scanned tree names {class_name} while assigning "
                f"RestContext.request/response; an Apex REST class cannot be exercised without building "
                f"RestRequest/RestResponse and assigning them (apexrefguide L228308-228340)"
            )
    if rest_classes and not any_test_sets_restcontext:
        findings.append(
            f"CRITICAL {rest_classes[0][1]}: the scanned tree contains @RestResource classes but no test "
            f"assigns RestContext.request or RestContext.response; RestContext is null outside a real REST "
            f"invocation, so those tests exercise a different code path than production"
        )
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned 0 Apex classes; manifest directory was missing.",
        )
    files = iter_files(root)
    if not files:
        return emit_result(
            [f"HIGH {root}: no Apex classes found"],
            "Scanned 0 Apex classes; no .cls files were found.",
        )

    findings: list[str] = []
    mappings: list[tuple[str, str, Path]] = []
    rest_classes: list[tuple[str, Path]] = []
    test_targets: set[str] = set()
    any_test_sets_restcontext = False

    for path in files:
        file_findings, file_mappings, class_name = audit_file(path)
        findings.extend(file_findings)
        for mapping, owner in file_mappings:
            mappings.append((mapping, owner, path))
        if class_name:
            rest_classes.append((class_name, path))

        raw = path.read_text(encoding="utf-8", errors="ignore")
        if ISTEST_RE.search(raw) and RESTCONTEXT_SET_RE.search(raw):
            any_test_sets_restcontext = True
            test_targets.update(re.findall(r"\b([A-Za-z_]\w*)\s*\.\s*do[A-Z]\w*\s*\(", raw))
            test_targets.update(re.findall(r"\b([A-Za-z_]\w*)\s*\.\s*\w+\s*\(\s*\)\s*;", raw))

    if rest_classes:
        findings.extend(
            check_cross_file(mappings, rest_classes, test_targets, any_test_sets_restcontext)
        )

    summary = (
        f"Scanned {len(files)} Apex class file(s), {len(rest_classes)} carrying @RestResource; "
        f"{len(findings)} Apex-REST finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
