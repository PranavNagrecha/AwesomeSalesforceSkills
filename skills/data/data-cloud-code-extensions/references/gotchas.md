# Gotchas — Data Cloud Code Extensions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: BYOK orgs can't use the feature at all

**What happens:** the team builds and tests a code extension locally, then discovers it
can't be enabled in the target org. There is no bundle-level workaround.

**When it occurs:** the org has Bring Your Own Key (BYOK) enabled — the docs state code
extension "isn't currently supported in orgs that have Bring Your Own Key (BYOK) enabled."

**How to avoid:** check the org's encryption posture during scoping, before anyone installs
the toolchain. If BYOK is on, solve the requirement with native transforms or an external
pipeline instead.

---

## Gotcha 2: Everything you print lands in a broadly readable DLO

**What happens:** a debug `print()` of a record payload becomes a data-exposure incident.

**When it occurs:** all code execution logs are written to a dedicated Logs DLO
(`DataCustomCodeLogs__dll`), and any user with access to that DLO can view its contents —
including PII or credentials your script echoed to standard output.

**How to avoid:** treat stdout as shared output. Log run metadata (counts, durations, error
codes), never field values; strip debug prints before deploying, and review the Logs DLO
after the first sandbox run to confirm nothing sensitive appears.

---

## Gotcha 3: Object-type parity is a hard wall, not a guideline

**What happens:** a script that reads a DLO and writes a DMO (or vice versa) doesn't fit the
batch-transform contract, and the pipeline design has to be reworked late.

**When it occurs:** scripts must read from and write to the same object type — DLOs to DLOs
and DMOs to DMOs — and a DMO-to-DMO transform can only write to a **transform-type** DMO.

**How to avoid:** lock the source/target object types (and create the transform-type DMO
target if needed) before writing any Python; if you must cross types, split the flow —
code extension within one type, standard mapping between types.

---

## Gotcha 4: Data kits auto-include the code, not its objects

**What happens:** a production deployment fails or ships incomplete because referenced
DLOs/DMOs never made it into the data kit.

**When it occurs:** adding a batch data transform to a DevOps Data Kit automatically
includes the associated code extension, but referenced DLOs/DMOs must be added manually.
Deployment runs in a fixed order (DLOs/DMOs → code extensions → batch transforms), and if a
component fails, the process stops and subsequent components aren't deployed.

**How to avoid:** enumerate every DLO/DMO the extension touches and add them to the kit
explicitly; after deploying, verify all components landed rather than assuming partial
success is success.

---

## Gotcha 5: Chunking functions are stateless and can't reach the data layer

**What happens:** a chunking function that tries to look up DLO/DMO data at runtime, or that
accumulates state across calls, produces wrong or inconsistent chunks.

**When it occurs:** the function receives only content already ingested and readable by the
search-index pipeline; it does not read DLOs or DMOs directly during runtime, and Data 360
can invoke it multiple times depending on batching.

**How to avoid:** design each request to be processed independently; push any enrichment
upstream (into the content itself) before indexing; validate chunk output against the
`SearchIndexChunkingV1Response` contract in the sandbox before wiring it into a production
search index.

---

## Gotcha 6: Governance tags on script outputs are your job

**What happens:** a code extension creates or updates a target DLO/DMO and the new object
carries no data-governance classification, silently escaping consent/privacy controls.

**When it occurs:** the docs require you to manually assign and audit appropriate governance
tags on target DLOs or DMOs that your code extension scripts create or update — the platform
doesn't infer them.

**How to avoid:** make governance tagging a standing step in the deployment checklist, and
re-audit tags whenever the script's output schema changes.
