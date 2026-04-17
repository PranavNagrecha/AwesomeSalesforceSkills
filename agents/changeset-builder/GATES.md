# Changeset Builder — Gated Execution Protocol

Five-gate protocol enforced by `scripts/run_builder.py` via `scripts/builder_plugins/changeset.py`.

---

## Gate A — Input readiness

`package_name`, `feature_summary` (≥10 words), `items[]` with at least one `{type,member}`, and `api_version` are required. Every item's `type` must appear in the plugin's `KNOWN_METADATA_TYPES` set — an unknown type is a Gate A refusal.

## Gate A.5 — Requirements document

Renders `REQUIREMENTS_TEMPLATE.md` with the full `items[]` inventory and the target_org_alias (or "library-only mode").

## Gate B — Ground every symbol

Every item is surfaced as a grounding symbol. The grounding gate does NOT attempt to describe each metadata piece via the org stub — the live oracle in Gate C does that for free via `sf project retrieve preview`. Gate B's role is to confirm nothing in `items[]` is structurally malformed.

## Gate C — Build and self-test

**Static check:** XML parses, root `<Package>`, each `<types>` has a known `<name>` + ≥1 `<members>`, `<version>` matches `\d{2}\.0`.

**Live check:** `sf project retrieve preview --target-org <alias> --manifest <package.xml> --json`. The CLI is idempotent and does not write anything. A nonzero top-level status is surfaced as an oracle failure.

Confidence: HIGH iff static green + live green; MEDIUM iff static green + live skipped; LOW otherwise.

## Gate D — Envelope seal

Envelope validates against the shared schema; deliverable kind is `xml`.

---

## What this protocol is NOT

- Not a deployer. Gate C is preview-only — no mutations to the target org.
- Not a diff tool. Generating the list of items is the user's job; this agent validates the manifest shape + org reachability.
