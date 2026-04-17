# Designer Mode Contract

Every designer that inherits `designer_base` routes on a `mode` input. Two modes are canonical:

## `design` mode

**Purpose:** greenfield design. The agent accepts business inputs (motion, cycle length, volume, segments) and produces a design doc. Live-org grounding is optional — the designer may cite `describe_org` for edition/API-version context but does not require a connected org.

**Required output sections** (per `shared_output_shape.md`):
- Summary (domain-specific counts + confidence)
- Design (domain-specific artifact — e.g. stage ladder, permission-set matrix, queue topology)
- Process Observations
- Citations

**Must NOT emit:**
- An Audit Findings section (belongs to audit mode).
- Concrete org-level remediations (the design hasn't been validated against the org yet).

**Refusal conditions specific to design mode:**
- Required business inputs missing → `REFUSAL_MISSING_INPUT`.
- Inputs so underspecified that any design would be speculation → `REFUSAL_INPUT_AMBIGUOUS`; ask a clarifying question rather than guess.

## `audit` mode

**Purpose:** assess an existing org configuration in the designer's domain and emit findings + remediations. Live-org grounding is REQUIRED — `target_org_alias` is mandatory.

**Required output sections:**
- Summary (domain-specific counts + findings breakdown + confidence)
- Audit Findings (P0/P1/P2 rows with evidence)
- Process Observations
- Citations

**May also emit:**
- Design section (only when the audit naturally leads to a redesign recommendation and the user asked for one).

**Refusal conditions specific to audit mode:**
- `target_org_alias` missing → `REFUSAL_MISSING_ORG`.
- `target_org_alias` unreachable via `sf` CLI → `REFUSAL_ORG_UNREACHABLE`.
- Domain has no active configuration in the org (nothing to audit) → return "not yet using <feature>" summary; do NOT invent a design. That's the user's next conversation.

## Single-mode exception

Three designers (`object-designer`, `flow-builder`, `duplicate-rule-designer`) ship as `modes: [single]`. Their behavior is shaped like a `design` mode with an embedded audit step — the audit isn't a separate invocation, it's a validation pass inside the design work. Those agents inherit `designer_base` but the mode gate collapses to "single". They are STILL bound by the shared output shape + refusal patterns.

When a future `[single]` designer grows a standalone audit capability, promote it to `[design, audit]` and split the Plan into two mode branches — do not keep audit-only logic hidden inside a single mode.

## Mixed mode (design + audit in one invocation)

Not supported. One mode per invocation. If an admin wants both, run the agent twice. This keeps the output schema unambiguous and makes run history easier to trust.

## Mode selection logic

Designers declare `mode` as a required input when they have multiple modes:

```
| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
```

The agent's Plan selects the branch based on `mode`. Steps that are mode-specific are tagged inline (e.g., "### Step 6 — Audit-mode additions").

## Validator enforcement

When `harness: designer_base` is declared:

1. `modes` must contain `design`, `audit`, or `single` (or some combination). No other values allowed.
2. If `modes` includes both `design` and `audit`, the Inputs table must declare `mode` as a required input.
3. Output contract must include the shared sections from `shared_output_shape.md`.

Violations emit a validator ERROR at PR time.
