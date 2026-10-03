#!/usr/bin/env python3
"""Check Omni-Channel reporting queries, Apex, and report types for field and grain mistakes.

Stdlib only. Scans a folder of SOQL files (*.soql, *.sql), Apex (*.cls, *.trigger,
*.apex), and custom report types (*.reportType-meta.xml, *.reportType) for the
mistakes documented in references/gotchas.md. Every rule cites the Object
Reference (Summer '26) entry it encodes.

Rules
  OMNI-FIELD-01  ERROR  WaitTime used on AgentWork. AgentWork has no WaitTime field;
                        use SpeedToAnswer (WaitTime belongs to LiveChatTranscript).
  OMNI-API-01    ERROR  IsTransfer or IsConference in SOQL/Apex against AgentWork. Both are
                        "accessible in Reports, but not via the API".
  OMNI-TRG-01    ERROR  Apex trigger on UserServicePresence. "Apex triggers aren't supported
                        with UserServicePresence."
  OMNI-USP-01    WARN   StatusDuration read from UserServicePresence without a StatusEndDate or
                        IsCurrentState filter. StatusDuration is set only when the status ends.
  OMNI-PSR-01    WARN   PendingServiceRouting queried with a historical date range. The object
                        holds work waiting to be routed, not history.
  OMNI-DEP-01    WARN   OriginalQueueId on AgentWork or QueueId on PendingServiceRouting. Both are
                        "no longer recommended"; use OriginalGroupId / GroupId.
  OMNI-ACT-01    WARN   ActiveTime read from AgentWork with no CapacityModel reference. ActiveTime
                        is tracked only for tab-based capacity.

Usage
  python3 check_omni_channel_reporting_data.py --manifest-dir path/to/folder
  python3 check_omni_channel_reporting_data.py --manifest-dir path --strict   # WARN fails too
  python3 check_omni_channel_reporting_data.py --self-test

Exit codes: 0 clean (or only WARN without --strict); 1 any ERROR, a missing folder,
or WARN under --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCE_SUFFIXES = (".soql", ".sql", ".cls", ".trigger", ".apex")
REPORT_TYPE_SUFFIXES = (".reportType-meta.xml", ".reportType")
OMNI_OBJECTS = ("AgentWork", "UserServicePresence", "PendingServiceRouting")
HISTORICAL_LITERALS = re.compile(
    r"\b(LAST_N_DAYS|LAST_N_WEEKS|LAST_N_MONTHS|LAST_N_QUARTERS|LAST_N_YEARS|LAST_WEEK|"
    r"LAST_MONTH|LAST_QUARTER|LAST_YEAR|LAST_90_DAYS|YESTERDAY|LAST_FISCAL_QUARTER|"
    r"LAST_FISCAL_YEAR)\b",
    re.IGNORECASE,
)


def strip_comments(text: str) -> str:
    """Remove // and /* */ comments outside single-quoted Apex/SOQL string literals."""
    out: list[str] = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
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
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end == -1 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            out.append(" ")
            i = n if end == -1 else end + 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def query_segments(text: str) -> list[tuple[str, str]]:
    """Return (object, query_text) for every SELECT ... FROM <omni object> found."""
    segments: list[tuple[str, str]] = []
    for match in re.finditer(r"\bFROM\s+(\w+)\b", text, flags=re.IGNORECASE):
        obj = match.group(1)
        canonical = next((o for o in OMNI_OBJECTS if o.lower() == obj.lower()), None)
        if canonical is None:
            continue
        start = text.rfind("SELECT", 0, match.start())
        start_lower = text.lower().rfind("select", 0, match.start())
        start = max(start, start_lower)
        if start == -1:
            continue
        end_candidates = [i for i in (text.find("]", match.end()), text.find(";", match.end())) if i != -1]
        end = min(end_candidates) if end_candidates else len(text)
        segments.append((canonical, text[start:end]))
    return segments


def has_token(query: str, token: str) -> bool:
    return re.search(rf"\b{re.escape(token)}\b", query, flags=re.IGNORECASE) is not None


def check_source(path: Path, raw: str) -> list[tuple[str, str, str]]:
    findings: list[tuple[str, str, str]] = []
    text = strip_comments(raw)
    if re.search(r"\btrigger\s+\w+\s+on\s+UserServicePresence\b", text, flags=re.IGNORECASE):
        findings.append(("ERROR", "OMNI-TRG-01",
                         f"{path}: Apex trigger on UserServicePresence; triggers aren't supported on this object."))
    for obj, query in query_segments(text):
        if obj == "AgentWork":
            if has_token(query, "WaitTime"):
                findings.append(("ERROR", "OMNI-FIELD-01",
                                 f"{path}: AgentWork has no WaitTime field; use SpeedToAnswer for request-to-accept."))
            for hidden in ("IsTransfer", "IsConference"):
                if has_token(query, hidden):
                    findings.append(("ERROR", "OMNI-API-01",
                                     f"{path}: AgentWork.{hidden} is readable in reports but not via the API; "
                                     "count distinct WorkItemId or use an AgentWork report type."))
            if has_token(query, "OriginalQueueId"):
                findings.append(("WARN", "OMNI-DEP-01",
                                 f"{path}: OriginalQueueId is no longer recommended; use OriginalGroupId."))
            if has_token(query, "ActiveTime") and not has_token(query, "CapacityModel"):
                findings.append(("WARN", "OMNI-ACT-01",
                                 f"{path}: ActiveTime is tracked only for tab-based capacity; "
                                 "filter or group by CapacityModel."))
        elif obj == "UserServicePresence":
            if has_token(query, "StatusDuration") and not (
                has_token(query, "StatusEndDate") or has_token(query, "IsCurrentState")
            ):
                findings.append(("WARN", "OMNI-USP-01",
                                 f"{path}: StatusDuration is null until a status ends; "
                                 "filter StatusEndDate != null or handle IsCurrentState rows."))
        elif obj == "PendingServiceRouting":
            if HISTORICAL_LITERALS.search(query) or re.search(r"CreatedDate\s*<", query, flags=re.IGNORECASE):
                findings.append(("WARN", "OMNI-PSR-01",
                                 f"{path}: PendingServiceRouting holds work waiting to be routed; "
                                 "use AgentWork for historical ranges."))
            if has_token(query, "QueueId"):
                findings.append(("WARN", "OMNI-DEP-01",
                                 f"{path}: PendingServiceRouting.QueueId is no longer recommended; use GroupId."))
    return findings


def _local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def check_report_type(path: Path) -> list[tuple[str, str, str]]:
    findings: list[tuple[str, str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", "OMNI-XML-01", f"{path}: report type XML does not parse ({exc}).")]
    base = next((el.text or "" for el in root if _local(el.tag) == "baseObject"), "")
    if base.strip() != "AgentWork":
        return findings
    for col in root.iter():
        if _local(col.tag) != "columns":
            continue
        field = next((c.text or "" for c in col if _local(c.tag) == "field"), "").strip()
        table = next((c.text or "" for c in col if _local(c.tag) == "table"), "").strip()
        if table != "AgentWork":
            continue
        if field == "WaitTime":
            findings.append(("ERROR", "OMNI-FIELD-01",
                             f"{path}: report type column AgentWork.WaitTime does not exist; use SpeedToAnswer."))
        if field == "OriginalQueueId" or field.startswith("OriginalQueue."):
            findings.append(("WARN", "OMNI-DEP-01",
                             f"{path}: report type column {field} is no longer recommended; use OriginalGroup."))
    return findings


def scan(root: Path) -> tuple[int, list[tuple[str, str, str]]]:
    files = [p for p in root.rglob("*") if p.is_file()
             and (p.name.endswith(SOURCE_SUFFIXES) or p.name.endswith(REPORT_TYPE_SUFFIXES))]
    findings: list[tuple[str, str, str]] = []
    for path in sorted(files):
        if path.name.endswith(REPORT_TYPE_SUFFIXES):
            findings.extend(check_report_type(path))
        else:
            findings.extend(check_source(path, path.read_text(encoding="utf-8", errors="replace")))
    return len(files), findings


def _fenced(md: Path, lang: str) -> list[str]:
    text = md.read_text(encoding="utf-8")
    return re.findall(rf"```{lang}\n(.*?)```", text, flags=re.DOTALL)


def self_test() -> int:
    here = Path(__file__).resolve().parent
    fixtures = here / "fixtures"
    _, good = scan(fixtures / "good")
    _, bad = scan(fixtures / "bad")
    expected = {"OMNI-FIELD-01", "OMNI-API-01", "OMNI-TRG-01", "OMNI-USP-01",
                "OMNI-PSR-01", "OMNI-DEP-01", "OMNI-ACT-01"}
    seen = {rule for _, rule, _ in bad}
    # The skill's own worked examples must pass with no ERROR.
    refs = here.parent / "references"
    own: list[tuple[str, str, str]] = []
    for i, sql in enumerate(_fenced(refs / "examples.md", "sql")):
        own.extend(check_source(Path(f"examples.md#sql{i + 1}"), sql))
    import tempfile
    for i, xml in enumerate(_fenced(refs / "metadata-examples.md", "xml")):
        if "<ReportType" not in xml:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / f"example{i + 1}.reportType-meta.xml"
            target.write_text(xml, encoding="utf-8")
            own.extend(check_report_type(target))
    own_errors = [f for f in own if f[0] == "ERROR"]
    ok = not good and expected <= seen and not own_errors
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print("   ", *f)
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    print(f"skill examples: {len(own_errors)} ERROR(s) (expected 0)")
    for f in own:
        print("   ", *f)
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Omni-Channel reporting SOQL, Apex and report types.")
    ap.add_argument("--manifest-dir", default=".", help="Folder to scan recursively (default: current directory).")
    ap.add_argument("--strict", action="store_true", help="Treat WARN findings as failures.")
    ap.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    count, findings = scan(root)
    if count == 0:
        print(f"WARN: no SOQL, Apex, or report type files found under {root}; nothing checked.")
        return 0
    for severity, rule, message in findings:
        print(f"{severity} {rule}: {message}")
    errors = [f for f in findings if f[0] == "ERROR"]
    warns = [f for f in findings if f[0] == "WARN"]
    print(f"Checked {count} file(s): {len(errors)} error(s), {len(warns)} warning(s).")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
