# ApexGuru Gotchas

## Connected-org analysis is not automatically runtime telemetry

The engine uses a connected org service. Unless the output explicitly includes an analysis mode and runtime metrics, label findings as source analysis.

## VS Code and CLI scopes differ

The VS Code ApexGuru command scans one selected file at a time. The CLI supports bounded workspace targets. Do not claim a folder was scanned because one editor command completed.

## File coverage is narrower than Code Analyzer as a whole

Other engines scan JavaScript, TypeScript, Flow, XML, Visualforce, or dependencies. ApexGuru itself scans `.cls` and `.trigger` only.

## Severity is not measured impact

Severity guides triage. It is not proof of CPU time, query count, row cardinality, execution frequency, or production blast radius.

## Remote polling has a hard overall timeout

Increasing retry intervals does not override `api_timeout_ms`. Excessive backoff can leave too few polls inside the total budget.

## Default orgs make CI evidence ambiguous

If `target_org` is omitted and multiple environments are authenticated, a developer default can change. Prefer explicit target identity and record the org ID/environment class.

## A rescan can move line numbers

Normalize by rule, file, message, and code context; do not treat a changed line number alone as a new or resolved defect.

## Suppression can hide future regressions

Scope suppressions narrowly and include rationale, owner, and review trigger. Never disable ApexGuru globally because one recommendation is disputed.
