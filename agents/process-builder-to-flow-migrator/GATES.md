# Process Builder → Flow Migrator — Gated Execution Protocol

This migrator rides the same five-gate protocol as `flow-builder`, with a Gate B extension that grounds the **source** Process Builder and a REQUIREMENTS.md that records the parity checklist. Enforced by `scripts/run_builder.py` via `scripts/builder_plugins/pb_to_flow.py`.

---

## Gate A — Input readiness

`inputs.schema.json` is the contract. `source_process_name` + `trigger_sobject` are required on top of the generic flow-builder schema. Two rounds max → `REFUSAL_INPUT_AMBIGUOUS`.

## Gate A.5 — Requirements document

Renders `REQUIREMENTS_TEMPLATE.md` including the parity checklist (entry criteria preserved, all criteria nodes become decisions, immediate actions become same-transaction elements, scheduled actions become scheduled paths, field updates preserved with identical values, process order preserved).

## Gate B — Ground every symbol

Validates `trigger_sobject`, every `referenced_field`, every `subflow`, and **the source Process Builder** as a resource in expected_resources. `flow_developer_name` must NOT already exist. One unresolved symbol ⇒ `REFUSAL_UNGROUNDED_OUTPUT`.

## Gate C — Build and self-test

**Static check** (inherited from FlowBuilderPlugin):
- XML parses; root `<Flow>`; `<processType>`, `<status>`, `<apiVersion>` present
- Record-triggered flows have `<start>` with `<object>` + `<triggerType>`
- Every `<recordCreates|Updates|Deletes|Lookups>` and `<actionCalls>` has a `<faultConnector>`

**Live check:** `sf project deploy validate --target-org <alias>` over emitted `.flow-meta.xml` files.

Confidence tiers: HIGH iff static green + live green; MEDIUM iff static green + live skipped; LOW otherwise.

## Gate D — Envelope seal

Envelope validates against the shared schema. The parity checklist is surfaced in the envelope's `notes[]` so reviewers can cross-check without reopening the source PB.

---

## What this protocol is NOT

- Not a PB executor. Gate C does not RUN the source Process Builder — it validates the emitted Flow will compile.
- Not a metadata retriever. The caller is responsible for pointing `source_process_name` at real metadata in the org.
