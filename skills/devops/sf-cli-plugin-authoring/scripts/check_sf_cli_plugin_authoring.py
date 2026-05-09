#!/usr/bin/env python3
"""Checker script for the sf-cli-plugin-authoring skill.

Scans a Salesforce CLI plugin source tree (`package.json` + `src/commands/`) for
the most common authoring mistakes covered in this skill's gotchas:

- topicSeparator left at colon (legacy sfdx style) instead of space (sf v2)
- console.log / console.error / console.warn in command source (corrupts --json)
- process.exit() inside command source (skips the JSON envelope)
- SfCommand<any> or SfCommand<unknown> (untyped public JSON contract)
- Hand-parsing process.argv inside run() (bypasses flag plumbing)
- Use of Flags.<name> for factories that don't exist on @salesforce/sf-plugins-core
  (Flags.email, Flags.url, Flags.password, Flags.json, Flags.regex)
- Missing or empty messages/ directory when commands import Messages
- aliases array present without deprecateAliases set to true (silent legacy spelling)

Stdlib only — no pip dependencies.

Usage:
    python3 check_sf_cli_plugin_authoring.py [--plugin-root path/to/plugin]
    python3 check_sf_cli_plugin_authoring.py --plugin-root . --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Factories actually exported by @salesforce/sf-plugins-core (Spring '25 era).
KNOWN_FLAG_FACTORIES = {
    "string", "boolean", "integer", "directory", "file",
    "salesforceId", "duration", "orgApiVersion",
    "requiredOrg", "optionalOrg", "requiredHub", "optionalHub",
    "custom", "option",
}

# Factories the LLMs invent that don't exist.
INVENTED_FLAG_FACTORIES = {"email", "url", "password", "json", "regex", "phone", "uuid"}

CONSOLE_RE = re.compile(r"\bconsole\.(log|error|warn|info|debug)\s*\(")
PROCESS_EXIT_RE = re.compile(r"\bprocess\.exit\s*\(")
ARGV_RE = re.compile(r"\bprocess\.argv\b")
SF_COMMAND_ANY_RE = re.compile(r"\bSfCommand<\s*(any|unknown)\s*>")
RUN_RETURN_ANY_RE = re.compile(r"\bpublic\s+async\s+run\s*\([^)]*\)\s*:\s*Promise<\s*(any|unknown)\s*>")
FLAG_FACTORY_CALL_RE = re.compile(r"\bFlags\.([A-Za-z][A-Za-z0-9_]*)\s*\(")
ALIASES_RE = re.compile(r"\baliases\s*=\s*\[", re.MULTILINE)
DEPRECATE_RE = re.compile(r"\bdeprecateAliases\s*=\s*true\b", re.MULTILINE)
MESSAGES_LOAD_RE = re.compile(r"Messages\.loadMessages\s*\(")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a sf CLI plugin source tree for common authoring mistakes.",
    )
    parser.add_argument(
        "--plugin-root",
        default=".",
        help="Root directory of the plugin (must contain package.json and src/). Default: current directory.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on any finding (default: exit non-zero only on errors, not warnings).",
    )
    return parser.parse_args()


def find_command_files(src_commands: Path) -> list[Path]:
    if not src_commands.exists():
        return []
    return sorted(p for p in src_commands.rglob("*.ts") if p.is_file())


def check_package_json(plugin_root: Path) -> list[tuple[str, str]]:
    """Return [(severity, message)] from package.json checks."""
    findings: list[tuple[str, str]] = []
    pkg_path = plugin_root / "package.json"
    if not pkg_path.exists():
        findings.append(("ERROR", f"{pkg_path} not found — not a recognizable plugin root."))
        return findings

    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(("ERROR", f"{pkg_path} is not valid JSON: {exc}"))
        return findings

    oclif = pkg.get("oclif")
    if not isinstance(oclif, dict):
        findings.append(("ERROR", f"{pkg_path} has no `oclif` configuration block — required for sf plugins."))
        return findings

    sep = oclif.get("topicSeparator")
    if sep is None:
        findings.append((
            "WARN",
            f"{pkg_path}: `oclif.topicSeparator` not set explicitly. v2 default is space; "
            "set it to ' ' explicitly to avoid surprises with stale @oclif/core versions.",
        ))
    elif sep == ":":
        findings.append((
            "ERROR",
            f"{pkg_path}: `oclif.topicSeparator` is ':' (legacy sfdx style). "
            "Set it to ' ' for v2 sf invocation. Commands won't dispatch correctly otherwise.",
        ))
    elif sep != " ":
        findings.append((
            "WARN",
            f"{pkg_path}: `oclif.topicSeparator` is {sep!r}; expected ' ' for sf v2.",
        ))

    deps = pkg.get("dependencies", {}) or {}
    if "@salesforce/sf-plugins-core" not in deps:
        findings.append((
            "ERROR",
            f"{pkg_path}: missing dependency `@salesforce/sf-plugins-core`. "
            "Authoring directly against @oclif/core breaks the SfCommand JSON wrapper.",
        ))

    bin_block = pkg.get("bin", {}) or {}
    if not bin_block:
        findings.append((
            "WARN",
            f"{pkg_path}: no `bin` entry. Plugin will install but commands cannot be invoked from a linked checkout.",
        ))

    return findings


def check_command_files(plugin_root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    src_commands = plugin_root / "src" / "commands"
    if not src_commands.exists():
        findings.append((
            "ERROR",
            f"{src_commands} does not exist. sf plugins discover commands under src/commands/<topic>/<command>.ts.",
        ))
        return findings

    cmd_files = find_command_files(src_commands)
    if not cmd_files:
        findings.append((
            "WARN",
            f"{src_commands} contains no .ts files — plugin will register zero commands.",
        ))
        return findings

    for path in cmd_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(("WARN", f"{path}: could not read ({exc})."))
            continue
        rel = path.relative_to(plugin_root)

        for match in CONSOLE_RE.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            findings.append((
                "ERROR",
                f"{rel}:{line_no} — console.{match.group(1)}() corrupts --json output. Use this.log/this.warn/this.error.",
            ))

        for match in PROCESS_EXIT_RE.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            findings.append((
                "ERROR",
                f"{rel}:{line_no} — process.exit() bypasses the SfCommand JSON envelope. "
                "Use this.error('msg', { exit: N }) or throw SfError.",
            ))

        for match in ARGV_RE.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            findings.append((
                "WARN",
                f"{rel}:{line_no} — process.argv reference inside a command file. "
                "Hand-parsing argv bypasses Flags factories and breaks --help / --json / --flags-dir.",
            ))

        for match in SF_COMMAND_ANY_RE.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            findings.append((
                "WARN",
                f"{rel}:{line_no} — SfCommand<{match.group(1)}> declared. The result type is the public JSON contract; type it explicitly.",
            ))

        for match in RUN_RETURN_ANY_RE.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            findings.append((
                "WARN",
                f"{rel}:{line_no} — run() returns Promise<{match.group(1)}>. Replace with a typed Result.",
            ))

        for match in FLAG_FACTORY_CALL_RE.finditer(text):
            name = match.group(1)
            if name in INVENTED_FLAG_FACTORIES:
                line_no = text[: match.start()].count("\n") + 1
                findings.append((
                    "ERROR",
                    f"{rel}:{line_no} — Flags.{name}() does not exist on @salesforce/sf-plugins-core. "
                    "Use Flags.string with a custom parse() or Flags.custom<T>({ parse }).",
                ))
            elif name not in KNOWN_FLAG_FACTORIES:
                line_no = text[: match.start()].count("\n") + 1
                findings.append((
                    "WARN",
                    f"{rel}:{line_no} — Flags.{name}() is not a known factory. "
                    f"Known: {', '.join(sorted(KNOWN_FLAG_FACTORIES))}.",
                ))

        if ALIASES_RE.search(text) and not DEPRECATE_RE.search(text):
            findings.append((
                "WARN",
                f"{rel} — `aliases` array set without `deprecateAliases = true`. "
                "Legacy spellings will be accepted silently with no migration warning.",
            ))

        if MESSAGES_LOAD_RE.search(text):
            messages_dir = plugin_root / "messages"
            if not messages_dir.exists():
                findings.append((
                    "ERROR",
                    f"{rel} calls Messages.loadMessages() but {messages_dir} does not exist. "
                    "Create the messages catalog before publishing.",
                ))
            elif not any(messages_dir.iterdir()):
                findings.append((
                    "WARN",
                    f"{messages_dir} is empty but {rel} loads messages — Messages.getMessage() will throw at runtime.",
                ))

    return findings


def main() -> int:
    args = parse_args()
    plugin_root = Path(args.plugin_root).resolve()

    if not plugin_root.exists():
        print(f"ERROR: plugin root not found: {plugin_root}", file=sys.stderr)
        return 2

    findings: list[tuple[str, str]] = []
    findings.extend(check_package_json(plugin_root))
    findings.extend(check_command_files(plugin_root))

    if not findings:
        print(f"No issues found in {plugin_root}.")
        return 0

    errors = [f for f in findings if f[0] == "ERROR"]
    warnings = [f for f in findings if f[0] == "WARN"]

    for sev, msg in findings:
        stream = sys.stderr if sev == "ERROR" else sys.stdout
        print(f"{sev}: {msg}", file=stream)

    print(
        f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s) "
        f"in {plugin_root.name}.",
        file=sys.stderr if errors else sys.stdout,
    )

    if errors:
        return 1
    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
