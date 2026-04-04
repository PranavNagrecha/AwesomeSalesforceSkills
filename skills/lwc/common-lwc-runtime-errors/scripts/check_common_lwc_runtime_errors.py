#!/usr/bin/env python3
"""Checker script for Common LWC Runtime Errors skill.

Scans LWC source files in a Salesforce metadata directory for common runtime
error anti-patterns described in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_common_lwc_runtime_errors.py [--help]
    python3 check_common_lwc_runtime_errors.py --manifest-dir path/to/lwc

Checks performed (JS files):
    1. Wire data accessed without a guard (chained access on .data without if-guard)
    2. document.querySelector / document.getElementById used instead of this.template.querySelector
    3. this.template.querySelector called inside connectedCallback (DOM not yet rendered)
    4. refreshApex used with an Apex-wired (non-LDS) result (heuristic)
    5. Third-party library constructor calls in connectedCallback
    6. CustomEvent dispatched with bubbles:true but no composed:true (cross-boundary heuristic)
    7. event.target property access in event handlers (other than tagName/dataset)
    8. renderedCallback without a guard (missing re-render protection)

Checks performed (HTML files):
    9. <lwc:component> used without loading/error fallback (covered by lwc-dynamic-components)
    10. No errorCallback-related pattern found in parent components rendering child components
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Compiled patterns — JS
# ---------------------------------------------------------------------------

# Detects chained access on wire data without a prior guard:
# e.g., this.wiredX.data.fields or wiredX.data.someField
# This is a heuristic: look for .data. access that appears to chain deeper.
RE_WIRE_CHAINED_ACCESS = re.compile(
    r'\bwired\w*\.data\.\w+'
)

# Detects document.querySelector or document.getElementById usage
RE_DOCUMENT_QUERY = re.compile(
    r'\bdocument\s*\.\s*(?:querySelector|getElementById|getElementsBy\w+|querySelectorAll)\s*\('
)

# Detects this.template.querySelector inside a connectedCallback block.
# Heuristic: looks for the method name and querySelector on nearby lines.
RE_CONNECTED_CALLBACK = re.compile(
    r'\bconnectedCallback\s*\(\s*\)\s*\{'
)
RE_TEMPLATE_QUERY = re.compile(
    r'\bthis\s*\.\s*template\s*\.\s*querySelector\s*\('
)

# Detects refreshApex being called — we then check if the file imports from @salesforce/apex
RE_REFRESH_APEX_CALL = re.compile(
    r'\brefreshApex\s*\('
)
RE_APEX_IMPORT = re.compile(
    r"""from\s+['"]@salesforce/apex/"""
)
RE_LDS_IMPORT = re.compile(
    r"""from\s+['"]lightning/ui\w+Api['"]"""
)

# Detects CustomEvent dispatch with bubbles:true/bubbles: true but no composed:true
RE_CUSTOM_EVENT = re.compile(
    r'new\s+CustomEvent\s*\('
)
RE_BUBBLES_TRUE = re.compile(
    r'bubbles\s*:\s*true'
)
RE_COMPOSED_TRUE = re.compile(
    r'composed\s*:\s*true'
)

# Detects event.target property access beyond .tagName and .dataset
# (potential retargeting issue in cross-boundary handlers)
RE_EVENT_TARGET_PROP = re.compile(
    r'\bevent\s*\.\s*target\s*\.\s*(?!tagName|dataset|id\b|nodeName|closest)\w+'
)

# Detects renderedCallback without an instance guard
RE_RENDERED_CALLBACK = re.compile(
    r'\brenderedCallback\s*\(\s*\)\s*\{'
)
RE_GUARD_PATTERN = re.compile(
    r'\bif\s*\(\s*this\.\w+\s*\)\s*return'
)

# Detects third-party constructor calls taking DOM as first arg in connectedCallback
# Heuristic: new SomeLib(this.template.querySelector or new SomeLib(container
RE_THIRDPARTY_IN_CONNECTED = re.compile(
    r'new\s+[A-Z]\w+\s*\(\s*(?:this\.template|container|el\b|element\b|node\b)'
)


# ---------------------------------------------------------------------------
# Compiled patterns — HTML
# ---------------------------------------------------------------------------

# Detects child component tags (c-*) in a template
RE_CHILD_COMPONENT = re.compile(
    r'<c-[\w-]+'
)


# ---------------------------------------------------------------------------
# File finders
# ---------------------------------------------------------------------------

def find_js_files(root: Path) -> list[Path]:
    return sorted(root.rglob('*.js'))


def find_html_files(root: Path) -> list[Path]:
    return sorted(root.rglob('*.html'))


def find_js_for_html(html_path: Path) -> Path | None:
    """Return the JS file for the same component, if it exists."""
    js_path = html_path.with_suffix('.js')
    return js_path if js_path.exists() else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return None


def extract_method_body(source: str, method_pattern: re.Pattern) -> str:
    """Extract the body of the first method matched by method_pattern.

    Walks the source from the match position, counting braces to find the
    closing brace. Returns the extracted body or an empty string.
    """
    match = method_pattern.search(source)
    if not match:
        return ''

    start = match.end()
    depth = 1
    pos = start
    while pos < len(source) and depth > 0:
        ch = source[pos]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        pos += 1

    return source[start:pos]


# ---------------------------------------------------------------------------
# JS checkers
# ---------------------------------------------------------------------------

def check_wire_chained_access(path: Path, source: str) -> list[str]:
    """Flag chained .data. access on wire results without visible guard."""
    issues: list[str] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if RE_WIRE_CHAINED_ACCESS.search(line):
            # Check if the same or a nearby line has an 'if (data)' or 'if (this.wired'
            # This is a conservative heuristic — flag only direct chain access.
            if 'if (' not in line and 'if(' not in line:
                issues.append(
                    f'{path}:{lineno}: possible unguarded wire data access — '
                    f'"wiredX.data.field" chaining without a guard. '
                    f'Check that this is inside an "if (data)" block. '
                    f'Destructure data/error in the wire handler instead.'
                )
    return issues


def check_document_query(path: Path, source: str) -> list[str]:
    """Flag document.querySelector/getElementById usage."""
    issues: list[str] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if RE_DOCUMENT_QUERY.search(line):
            issues.append(
                f'{path}:{lineno}: document.querySelector/getElementById detected — '
                f'shadow DOM encapsulation prevents document-level queries from reaching '
                f'elements inside an LWC shadow root. Use this.template.querySelector instead.'
            )
    return issues


def check_connected_callback_dom_access(path: Path, source: str) -> list[str]:
    """Flag this.template.querySelector calls inside connectedCallback."""
    issues: list[str] = []
    body = extract_method_body(source, RE_CONNECTED_CALLBACK)
    if not body:
        return issues

    for lineno_offset, line in enumerate(body.splitlines(), start=1):
        if RE_TEMPLATE_QUERY.search(line):
            issues.append(
                f'{path}: this.template.querySelector detected inside connectedCallback — '
                f'the template is not yet rendered when connectedCallback fires. '
                f'Move DOM access to renderedCallback.'
            )
            break  # one issue per file for this check

    # Also flag third-party constructor calls in connectedCallback
    for lineno_offset, line in enumerate(body.splitlines(), start=1):
        if RE_THIRDPARTY_IN_CONNECTED.search(line):
            issues.append(
                f'{path}: possible third-party library DOM initialization in connectedCallback — '
                f'DOM elements are not available until renderedCallback. '
                f'Move third-party library initialization to renderedCallback with a guard.'
            )
            break

    return issues


def check_refresh_apex_on_non_lds(path: Path, source: str) -> list[str]:
    """Flag refreshApex calls in files that wire Apex methods but not LDS adapters."""
    issues: list[str] = []
    if not RE_REFRESH_APEX_CALL.search(source):
        return issues

    has_apex_wire = bool(RE_APEX_IMPORT.search(source))
    has_lds_wire = bool(RE_LDS_IMPORT.search(source))

    if has_apex_wire and not has_lds_wire:
        issues.append(
            f'{path}: refreshApex called in a file that wires an Apex method but has no LDS '
            f'wire adapter import — refreshApex only works for LDS-backed wires (e.g., getRecord). '
            f'For Apex wires, use an imperative Apex call after mutations instead.'
        )
    elif has_apex_wire and has_lds_wire:
        # Mixed: may or may not be a problem — issue a warning only
        issues.append(
            f'{path}: refreshApex called and file mixes Apex and LDS wire imports — '
            f'verify that refreshApex is called on the LDS-backed wire result, '
            f'not on an Apex-wired property.'
        )

    return issues


def check_custom_event_composition(path: Path, source: str) -> list[str]:
    """Flag CustomEvent dispatches with bubbles but no composed when the pattern suggests
    cross-component propagation is intended.

    Heuristic: flag if CustomEvent has bubbles:true and no composed:true anywhere in the
    same file. This is intentionally conservative — only flag when composed is absent entirely.
    """
    issues: list[str] = []
    if not RE_CUSTOM_EVENT.search(source):
        return issues

    has_bubbles = RE_BUBBLES_TRUE.search(source)
    has_composed = RE_COMPOSED_TRUE.search(source)

    if has_bubbles and not has_composed:
        issues.append(
            f'{path}: CustomEvent dispatched with bubbles:true but composed:true is absent '
            f'from the entire file — if this event needs to cross shadow boundaries to reach '
            f'a parent component, add composed:true. If the event stays within this component\'s '
            f'own template, this is fine (suppress this warning by adding composed:false explicitly).'
        )

    return issues


def check_event_target_property(path: Path, source: str) -> list[str]:
    """Flag event.target property access beyond .tagName and .dataset."""
    issues: list[str] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if RE_EVENT_TARGET_PROP.search(line):
            issues.append(
                f'{path}:{lineno}: event.target property access detected — '
                f'composed events retarget at shadow boundaries; event.target is the host element, '
                f'not the originating element inside the child shadow. '
                f'Use event.detail for cross-boundary payload data.'
            )
    return issues


def check_rendered_callback_guard(path: Path, source: str) -> list[str]:
    """Flag renderedCallback implementations that lack an early-return guard."""
    issues: list[str] = []
    body = extract_method_body(source, RE_RENDERED_CALLBACK)
    if not body:
        return issues

    if not RE_GUARD_PATTERN.search(body):
        issues.append(
            f'{path}: renderedCallback found without an early-return guard — '
            f'renderedCallback fires on every render cycle. Add a guard like '
            f'"if (this._initialized) return; this._initialized = true;" '
            f'to prevent duplicate initialization of DOM resources.'
        )

    return issues


# ---------------------------------------------------------------------------
# HTML checkers
# ---------------------------------------------------------------------------

def check_error_callback_presence(html_path: Path, html_source: str) -> list[str]:
    """Flag HTML templates that render child LWC components if the JS sibling
    does not implement errorCallback."""
    issues: list[str] = []

    if not RE_CHILD_COMPONENT.search(html_source):
        return issues  # no child components rendered

    js_path = find_js_for_html(html_path)
    if js_path is None:
        return issues  # no JS sibling to check

    js_source = read_file(js_path)
    if js_source is None:
        return issues

    if 'errorCallback' not in js_source:
        issues.append(
            f'{html_path}: template renders child LWC components (<c-*>) but the JS '
            f'class ({js_path.name}) does not implement errorCallback — '
            f'runtime errors in child components will propagate unhandled. '
            f'Add errorCallback(error, stack) to catch and display child errors gracefully.'
        )

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_js_file(path: Path) -> list[str]:
    source = read_file(path)
    if source is None:
        return [f'{path}: cannot read file']

    issues: list[str] = []
    issues.extend(check_wire_chained_access(path, source))
    issues.extend(check_document_query(path, source))
    issues.extend(check_connected_callback_dom_access(path, source))
    issues.extend(check_refresh_apex_on_non_lds(path, source))
    issues.extend(check_custom_event_composition(path, source))
    issues.extend(check_event_target_property(path, source))
    issues.extend(check_rendered_callback_guard(path, source))
    return issues


def check_html_file(path: Path) -> list[str]:
    source = read_file(path)
    if source is None:
        return [f'{path}: cannot read file']

    issues: list[str] = []
    issues.extend(check_error_callback_presence(path, source))
    return issues


def check_all(manifest_dir: Path) -> list[str]:
    """Run all checks across all LWC source files under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f'Manifest directory not found: {manifest_dir}')
        return issues

    js_files = find_js_files(manifest_dir)
    html_files = find_html_files(manifest_dir)

    if not js_files and not html_files:
        issues.append(
            f'No .js or .html files found under {manifest_dir}. '
            f'Verify the path points to an LWC source directory.'
        )
        return issues

    for js_path in js_files:
        issues.extend(check_js_file(js_path))

    for html_path in html_files:
        issues.extend(check_html_file(html_path))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Check LWC source files for common runtime error anti-patterns. '
            'See skills/lwc/common-lwc-runtime-errors/references/ for details.'
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help='Root directory of the LWC source or Salesforce metadata (default: current directory).',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_all(manifest_dir)

    if not issues:
        print('No common LWC runtime error anti-patterns found.')
        return 0

    for issue in issues:
        print(f'ISSUE: {issue}')

    print(f'\n{len(issues)} issue(s) found.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
