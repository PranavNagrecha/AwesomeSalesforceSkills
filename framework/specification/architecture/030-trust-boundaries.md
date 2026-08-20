# Trust boundaries and authority model

## Principle

The model is not the security boundary. Product safety comes from minimizing authority, validating every boundary crossing, and making host limitations visible.

## Boundaries

### User-to-command boundary

User text can request a job but cannot grant itself Salesforce authority, approve a different org, override hard context/evidence rules, or convert scratch setup into a product tool. Inputs are validated before execution.

### Host-to-framework boundary

Hosts differ in subagent isolation, MCP inheritance, hooks, cloud behavior, compaction events, and approvals. Every run records a host capability object. Missing enforcement causes restriction or partial status—not documentation pretending the control exists.

### Model boundary

All model outputs are untrusted proposals. Structured output is schema-validated. Material claims are evidence-linted. Recommendations are policy-reviewed. Confidence is recomputed from evidence rather than accepted from model language.

### Knowledge boundary

Skills and references may be stale, conditional, or inapplicable. They are versioned advisory inputs. Release-sensitive knowledge carries source records and review dates.

### Tool/evidence boundary

Salesforce data, logs, error messages, metadata, files, and vendor exports can contain prompt injection or secrets. The broker treats them as data, redacts before model/persistence, and never executes instructions embedded in evidence.

### Salesforce org boundary

Authorized orgs are not interchangeable. Product runs prefer explicit aliases/usernames and record resolved org identity. Cached job association must match the requested org. `ALLOW_ALL_ORGS`, silent default resolution, and implicit most-recent jobs are disallowed in consequential product mode.

### Local project boundary

SfSkills is a library, not the target DX project. Project inspection uses an explicit path first, then one unambiguous workspace/bounded root. Canonical path checks, symlink/path-escape defenses, and digests are required. No project produces standalone mode; multiple projects produce ambiguity.

### Product/QA authority boundary

Product authority is read-only. Scratch QA setup can mutate only a disposable, marked, allowlisted scratch org through versioned non-model scripts. Setup credentials, commands, and teardown are unavailable to product agents.

### Review artifact boundary

A report is not proof. Cursor must return the actual Git bundle, exact source, test logs with exit codes, host evidence, run bundles, QA results, safety scans, traceability, and checksums. The offline verifier rejects missing or contradictory evidence.

## Deny-by-default behavior

Unknown product tools, unknown shell forms, unresolved targets, unsupported authority, and malformed policy input default to deny/refuse. Allowlisting uses parsed commands and explicit tool IDs, not substring matching.

## Threats the product explicitly tests

- prompt injection in logs, metadata descriptions, source comments, and record fields;
- compound/nested shell bypasses and renamed mutating tools;
- wrong-org cached jobs;
- symlink/path traversal;
- secret-shaped errors;
- evidence truncation that hides contradictions;
- compaction that drops target or policy state;
- malicious or persuasive unsupported drafts;
- scenario-label drift and benchmark gaming;
- review ZIPs that claim files/tests they omit.
