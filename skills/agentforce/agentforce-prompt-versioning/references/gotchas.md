# Prompt Versioning — Gotchas

## 1. UI Edits Silently Diverge

A "quick fix" in Prompt Builder bypasses review. After a week, the repo
and org are out of sync. Retrieve immediately or revert.

## 2. Renaming A Prompt Breaks Actions / Topics

Prompt templates are referenced by developer name. Renaming cascades.
Only rename when bumping the version suffix deliberately.

## 3. Variable Rename Is A Breaking Change

Adding a variable is usually backward-compatible (optional default).
Renaming is breaking — callers must update.

## 4. Auto-Update Model Version Without Regression Run

Auto-updates can silently change behaviour. Pin or schedule explicit
re-evaluation.

## 5. A/B Without Telemetry Tag

Cannot attribute metrics without the variant tag emitted at inference.
Add it before enabling A/B.

## 6. Deleted Prompts Break In-Flight Agent Sessions

If an in-flight conversation referenced a prompt you deleted, the
session fails. Retire via 0% traffic first.

## 7. Environment Drift (Sandbox vs Prod)

Prompts deployed to sandbox but forgotten in prod release = inverted
behaviour when comparing. Include prompts in the standard release train.

## 8. Reference Data Inside Prompt

Embedding rules ("current refund policy as of 2026-04") directly in the
prompt binds version to policy update cadence. Prefer parameter
injection so policy lives in data, not prompt.
