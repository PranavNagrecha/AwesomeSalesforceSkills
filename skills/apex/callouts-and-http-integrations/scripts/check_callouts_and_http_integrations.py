#!/usr/bin/env python3
"""Audit Apex HTTP callout code for the failure modes documented in this skill.

Static, regex-and-brace-scanning only. This script never compiles or executes Apex, and it
cannot resolve call graphs across files -- every cross-method inference is marked REVIEW
rather than asserted.

Checks (each grounded in references/gotchas.md):

  1. CRITICAL  DML before a callout in the same method body.
               "You have uncommitted work pending. Please commit or rollback before calling
               out." (Apex Developer Guide v67.0 L8769-8770). The blocking set also includes
               System.enqueueJob / Database.executeBatch / @future calls (L35379-35380).
  2. CRITICAL  Http().send() reachable inside a .trigger file, or inside a method a trigger
               handler names -- "Callouts must be made asynchronously from a trigger"
               (guide L14900-14903).
  3. HIGH      Literal http:// or https:// endpoint instead of a Named Credential
               `callout:` URL (guide L34293-34299, L34332-34335).
  4. HIGH      Callout inside a for/while/do loop -- 100 callouts per transaction and 120 s
               cumulative (guide L35844, L35856-35857).
  5. HIGH      Queueable/Batchable that calls out without Database.AllowsCallouts
               (guide L16164-16166), or @future without callout=true (guide L5134-5135).
  6. HIGH      Test class that exercises callout code with no Test.setMock (guide
               L35384-35385), or Test.setMock placed before Test.startTest (L35677-35681).
  7. HIGH      catch (CalloutException ...) whose body neither logs, rethrows, nor records.
  8. MEDIUM    No explicit setTimeout, or a value outside 1..120,000 ms
               (Apex Reference Guide v67.0 L216720).
  9. MEDIUM    setBody/setBodyAsBlob on a request whose method is GET -- silently performs a
               POST (guide L35377-35378).
 10. REVIEW    An active Database.setSavepoint() with no releaseSavepoint before the callout
               (guide L8747-8748).

Usage:
    python3 check_callouts_and_http_integrations.py --manifest-dir force-app
    python3 check_callouts_and_http_integrations.py --manifest-dir force-app --fail-on HIGH
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".cls", ".trigger"}

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}
SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "REVIEW"]

# --- detection patterns -------------------------------------------------------------

HTTP_USE_RE = re.compile(r"\bnew\s+Http\s*\(\s*\)|\bHttpRequest\b|\bHttpResponse\b", re.IGNORECASE)
SEND_RE = re.compile(r"\.\s*send\s*\(", re.IGNORECASE)
ENDPOINT_RE = re.compile(r"setEndpoint\s*\(\s*(['\"])(.*?)\1", re.IGNORECASE | re.DOTALL)
ENDPOINT_ANY_RE = re.compile(r"setEndpoint\s*\(", re.IGNORECASE)
TIMEOUT_LITERAL_RE = re.compile(r"setTimeout\s*\(\s*(\d+)\s*\)", re.IGNORECASE)
TIMEOUT_ANY_RE = re.compile(r"setTimeout\s*\(", re.IGNORECASE)
SET_METHOD_RE = re.compile(r"setMethod\s*\(\s*(['\"])(\w+)\1", re.IGNORECASE)
SET_BODY_RE = re.compile(r"\.\s*setBody(?:AsBlob)?\s*\(", re.IGNORECASE)

QUEUEABLE_RE = re.compile(r"\bimplements\b[^{;]*\bQueueable\b", re.IGNORECASE)
BATCHABLE_RE = re.compile(r"\bimplements\b[^{;]*\bDatabase\.Batchable\b", re.IGNORECASE)
ALLOWS_CALLOUTS_RE = re.compile(r"\bDatabase\.AllowsCallouts\b", re.IGNORECASE)
FUTURE_RE = re.compile(r"@\s*future\b([^\n)]*\))?", re.IGNORECASE)
FUTURE_CALLOUT_RE = re.compile(r"@\s*future\s*\(\s*callout\s*=\s*true\s*\)", re.IGNORECASE)

SETMOCK_RE = re.compile(r"Test\.setMock\s*\(", re.IGNORECASE)
STARTTEST_RE = re.compile(r"Test\.startTest\s*\(", re.IGNORECASE)
ISTEST_RE = re.compile(r"@\s*isTest\b|\btestMethod\b", re.IGNORECASE)

DML_RE = re.compile(
    r"(^|[^\w.])(insert|update|upsert|delete|undelete|merge)\s+(?!\s*\()"
    r"|\bDatabase\.(insert|update|upsert|delete|undelete|merge|executeBatch)\s*\("
    r"|\bSystem\.enqueueJob\s*\(",
    re.IGNORECASE | re.MULTILINE,
)
SAVEPOINT_SET_RE = re.compile(r"Database\.setSavepoint\s*\(", re.IGNORECASE)
SAVEPOINT_RELEASE_RE = re.compile(r"Database\.releaseSavepoint\s*\(", re.IGNORECASE)

LOOP_RE = re.compile(r"(^|[^\w.])(for|while|do)\s*[({]", re.MULTILINE)
CATCH_CALLOUT_RE = re.compile(
    r"catch\s*\(\s*(?:System\.)?(?:Callout|Http)?\w*Exception\s+(\w+)\s*\)\s*\{", re.IGNORECASE
)
LOGGING_RE = re.compile(
    r"System\.debug|ApplicationLogger|Logger\.|insert\s|Database\.insert|throw\s|"
    r"addError|EventBus\.publish|\.add\s*\(",
    re.IGNORECASE,
)

TRIGGER_HANDLER_HINT_RE = re.compile(
    r"\bextends\s+TriggerHandler\b|\bimplements\s+TriggerHandler\b|"
    r"\bTrigger\.(new|old|newMap|oldMap|isBefore|isAfter|isInsert|isUpdate)\b",
    re.IGNORECASE,
)

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_RE = re.compile(r"'(?:\\.|[^'\\])*'")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex callout code for endpoint, transaction, limit and testability defects."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes and triggers (e.g. force-app).",
    )
    parser.add_argument(
        "--fail-on",
        default="LOW",
        choices=SEVERITY_ORDER,
        help="Lowest severity that makes this script exit non-zero. Default LOW (REVIEW never fails).",
    )
    return parser.parse_args()


# --- source helpers -----------------------------------------------------------------


def strip_noise(text: str) -> str:
    """Blank out comments and string literals, preserving offsets and line breaks."""

    def blank(match: re.Match) -> str:
        return "".join("\n" if ch == "\n" else " " for ch in match.group(0))

    text = BLOCK_COMMENT_RE.sub(blank, text)
    text = LINE_COMMENT_RE.sub(blank, text)
    return STRING_RE.sub(blank, text)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def iter_apex_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_SUFFIXES
        and "__tests__" not in path.parts
    )


def method_bodies(clean: str) -> list[tuple[int, int]]:
    """Return (start, end) offsets of each brace block that looks like a method body.

    Brace matching only -- good enough to keep 'DML then callout' inside one method,
    which is the point. Nested blocks are included as their own entries, so a caller
    that wants the outermost body should take the widest span containing an offset.
    """
    spans: list[tuple[int, int]] = []
    stack: list[int] = []
    for i, ch in enumerate(clean):
        if ch == "{":
            stack.append(i)
        elif ch == "}" and stack:
            start = stack.pop()
            spans.append((start, i))
    return spans


def enclosing_blocks(spans: list[tuple[int, int]], index: int) -> list[tuple[int, int]]:
    return [(a, b) for a, b in spans if a < index < b]


# --- checks -------------------------------------------------------------------------


def audit_file(path: Path, raw: str) -> list[dict]:
    findings: list[dict] = []
    clean = strip_noise(raw)

    def add(severity: str, index: int, message: str) -> None:
        findings.append(
            {
                "severity": severity,
                "location": f"{path}:{line_of(clean, index)}",
                "message": message,
            }
        )

    uses_http = bool(HTTP_USE_RE.search(clean))
    send_hits = [m.start() for m in SEND_RE.finditer(clean) if uses_http]
    endpoint_hits = [m.start() for m in ENDPOINT_ANY_RE.finditer(clean)]
    callout_points = sorted(set(send_hits + endpoint_hits))

    if not uses_http and not endpoint_hits:
        return findings

    is_test = bool(ISTEST_RE.search(clean))
    spans = method_bodies(clean)

    # --- 3. literal endpoints (runs on the raw text: the URL is inside a string literal) ---
    for match in ENDPOINT_RE.finditer(raw):
        endpoint = match.group(2).strip()
        idx = match.start()
        if endpoint.lower().startswith(("http://", "https://")):
            add(
                "HIGH",
                idx,
                f"literal endpoint `{endpoint[:80]}` -- use a Named Credential "
                f"`callout:My_Credential/path`; a literal URL also needs a Remote Site Setting "
                f"(guide L34293-34299)",
            )
        elif endpoint and not endpoint.lower().startswith("callout:") and "'" not in endpoint:
            add(
                "REVIEW",
                idx,
                f"endpoint `{endpoint[:80]}` is neither a literal URL nor `callout:` syntax -- "
                f"confirm it resolves to a Named Credential at run time",
            )

    # --- 2. trigger context ---
    if path.suffix.lower() == ".trigger" and callout_points:
        add(
            "CRITICAL",
            callout_points[0],
            "HTTP callout code in a .trigger file -- \"Callouts must be made asynchronously "
            "from a trigger\" (guide L14900-14903); enqueue a Queueable instead",
        )
    elif (
        send_hits
        and not is_test
        and TRIGGER_HANDLER_HINT_RE.search(clean)
        and not QUEUEABLE_RE.search(clean)
        and not FUTURE_RE.search(clean)
    ):
        add(
            "CRITICAL",
            send_hits[0],
            "class references Trigger context and calls Http.send() with no Queueable or "
            "@future boundary -- move the callout off the trigger transaction "
            "(guide L14900-14903)",
        )

    # --- 5. async markers ---
    if send_hits and not is_test:
        if QUEUEABLE_RE.search(clean) and not ALLOWS_CALLOUTS_RE.search(clean):
            add(
                "HIGH",
                send_hits[0],
                "Queueable performs a callout without `Database.AllowsCallouts` "
                "(guide L16164-16166)",
            )
        if BATCHABLE_RE.search(clean) and not ALLOWS_CALLOUTS_RE.search(clean):
            add(
                "HIGH",
                send_hits[0],
                "Database.Batchable performs a callout without `Database.AllowsCallouts` "
                "(guide L17508-17510)",
            )
    for match in FUTURE_RE.finditer(clean):
        if FUTURE_CALLOUT_RE.match(clean, match.start()):
            continue
        method_start = clean.find("{", match.end())
        if method_start == -1:
            continue
        body = next(
            (clean[a : b + 1] for a, b in spans if a == method_start),
            "",
        )
        if SEND_RE.search(body) and HTTP_USE_RE.search(body):
            add(
                "HIGH",
                match.start(),
                "@future method performs a callout without `callout=true`; the default is "
                "`callout=false`, which prevents a method from making callouts (guide L5134-5135)",
            )

    # --- 1. DML before callout, 4. loops, 10. savepoints, per method body ---
    outermost: dict[tuple[int, int], list[int]] = {}
    for point in callout_points:
        blocks = enclosing_blocks(spans, point)
        if not blocks:
            continue
        widest = max(blocks, key=lambda b: b[1] - b[0])
        outermost.setdefault(widest, []).append(point)

    for (start, end), points in sorted(outermost.items()):
        body = clean[start:end]
        first_callout = min(points)

        if not is_test:
            for dml in DML_RE.finditer(body):
                dml_abs = start + dml.start()
                if dml_abs < first_callout:
                    add(
                        "CRITICAL",
                        dml_abs,
                        "DML / enqueue / executeBatch appears before a callout in the same method "
                        "-- \"You have uncommitted work pending. Please commit or rollback before "
                        "calling out.\" (guide L8769-8770). Call out first, or move the callout to "
                        "a separate transaction",
                    )
                    break

        sp = SAVEPOINT_SET_RE.search(body)
        if sp and not SAVEPOINT_RELEASE_RE.search(body[: first_callout - start]):
            add(
                "REVIEW",
                start + sp.start(),
                "Database.setSavepoint() with no releaseSavepoint before the callout -- "
                "\"All active Savepoints must be released before making callouts.\" "
                "(guide L8747-8748)",
            )

        # loops: a callout inside a nested loop block within this method
        for loop in LOOP_RE.finditer(body):
            loop_brace = body.find("{", loop.end() - 1)
            if loop_brace == -1:
                continue
            loop_abs = start + loop_brace
            loop_span = next((s for s in spans if s[0] == loop_abs), None)
            if not loop_span:
                continue
            inside = [p for p in points if loop_span[0] < p < loop_span[1]]
            if inside:
                add(
                    "HIGH",
                    inside[0],
                    "callout inside a loop -- a transaction allows 100 callouts and 120 s "
                    "cumulative timeout (guide L35844, L35856-35857). Bound the record count "
                    "per job and check Limits.getCallouts()",
                )
                break

        # 9. body on a GET
        # setMethod's argument is a string literal, which strip_noise blanks -- read raw.
        # strip_noise preserves length, so offsets are interchangeable.
        methods = {m.group(2).upper() for m in SET_METHOD_RE.finditer(raw[start:end])}
        body_hit = SET_BODY_RE.search(clean[start:end])
        if body_hit and methods == {"GET"}:
            add(
                "MEDIUM",
                start + body_hit.start(),
                "setBody on a request whose only setMethod is 'GET' -- \"If you set a request "
                "body and the request method is GET, a POST request is performed\" "
                "(guide L35377-35378). Put parameters on the endpoint query string",
            )

    # --- 8. timeouts ---
    if callout_points and not TIMEOUT_ANY_RE.search(clean) and not is_test:
        add(
            "MEDIUM",
            callout_points[0],
            "no explicit setTimeout() -- the default is 10 seconds and every callout draws on "
            "the same 120 s per-transaction budget (guide L35854-35857)",
        )
    for match in TIMEOUT_LITERAL_RE.finditer(clean):
        value = int(match.group(1))
        if value < 1 or value > 120000:
            add(
                "MEDIUM",
                match.start(),
                f"setTimeout({value}) is outside the valid range -- \"a timeout for the request "
                f"between 1 and 120,000 milliseconds\" (Apex Reference Guide L216720)",
            )

    # --- 6. tests ---
    if is_test:
        if callout_points and not SETMOCK_RE.search(clean):
            add(
                "HIGH",
                callout_points[0],
                "test class exercises HTTP callout code with no Test.setMock -- \"By default, "
                "test methods don't support HTTP callouts, so tests that perform callouts fail\" "
                "(guide L35384-35385)",
            )
        for mock in SETMOCK_RE.finditer(clean):
            preceding = STARTTEST_RE.search(clean[:  mock.start()])
            following = STARTTEST_RE.search(clean, mock.end())
            if preceding is None and following is not None:
                add(
                    "HIGH",
                    mock.start(),
                    "Test.setMock appears before Test.startTest -- \"The Test.startTest statement "
                    "must appear before the Test.setMock statement\" (guide L35677-35681)",
                )
                break

    # --- 7. swallowed CalloutException ---
    for match in CATCH_CALLOUT_RE.finditer(clean):
        if "callout" not in clean[match.start() : match.end()].lower():
            continue
        brace = match.end() - 1
        span = next((s for s in spans if s[0] == brace), None)
        if not span:
            continue
        handler = clean[span[0] + 1 : span[1]]
        if not handler.strip() or not LOGGING_RE.search(handler):
            add(
                "HIGH",
                match.start(),
                "catch block for a CalloutException neither logs, records, nor rethrows -- the "
                "failure becomes invisible to operations",
            )

    return findings


# --- reporting ----------------------------------------------------------------------


def emit_result(findings: list[dict], summary: str, fail_on: str) -> int:
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in findings))
    print(json.dumps({"score": score, "findings": findings, "summary": summary}, indent=2))
    if findings:
        print(f"WARN: {len(findings)} finding(s) detected", file=sys.stderr)
    threshold = SEVERITY_ORDER.index(fail_on)
    blocking = [f for f in findings if SEVERITY_ORDER.index(f["severity"]) <= threshold]
    return 1 if blocking else 0


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result(
            [{"severity": "HIGH", "location": str(root), "message": "manifest directory not found"}],
            "Scanned 0 Apex files; manifest directory was missing.",
            args.fail_on,
        )

    files = iter_apex_files(root)
    if not files:
        return emit_result(
            [{"severity": "HIGH", "location": str(root), "message": "no .cls or .trigger files found"}],
            "Scanned 0 Apex files.",
            args.fail_on,
        )

    findings: list[dict] = []
    for path in files:
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as err:
            findings.append({"severity": "LOW", "location": str(path), "message": f"unreadable: {err}"})
            continue
        findings.extend(audit_file(path, raw))

    findings.sort(key=lambda f: (SEVERITY_ORDER.index(f["severity"]), f["location"]))
    summary = (
        f"Scanned {len(files)} Apex file(s); {len(findings)} callout finding(s). "
        f"Static analysis only -- this script does not compile Apex or resolve call graphs."
    )
    return emit_result(findings, summary, args.fail_on)


if __name__ == "__main__":
    sys.exit(main())
