# LLM Anti-Patterns

Use this list when reviewing an ApexGuru analysis. It protects the distinction between a remote source-analysis finding, measured runtime evidence, and an approved code change.

## 1. Runtime-telemetry claim

**Mistake:** Call every authenticated-org ApexGuru scan “production insights” or a measured hotspot report.

**Why it happens:** The engine is remote and org-authenticated, which sounds equivalent to observing production transactions.

**Correct form:** Preserve the report's explicit analysis mode and metrics. When no mode or runtime metrics are present, label the result `Source analysis`. Link debug logs, Event Monitoring, APM, or transaction traces as separate evidence.

## 2. Coverage inflation

**Mistake:** Say ApexGuru scanned the org, Flow, LWC, objects, metadata, or every Apex file when only bounded `.cls`/`.trigger` targets were supplied.

**Why it happens:** “Scan succeeded” is generalized to complete coverage.

**Correct form:** Record workspace, target globs/files, exclusions, source revision, and unsupported file types. Completion claims cannot exceed the manifest actually submitted.

## 3. Severity-as-impact

**Mistake:** Convert engine severity directly into CPU milliseconds, query count, incident probability, or business impact.

**Why it happens:** Severity appears quantitative and invites prioritization without context.

**Correct form:** Treat severity as engine prioritization. Validate reachable path, data volume, cardinality, transaction frequency, limits, and user impact before estimating runtime or business risk.

## 4. Blind autofix

**Mistake:** Apply a generated recommendation without checking behavior, sharing, CRUD/FLS, locking, order, bulk semantics, and error handling.

**Why it happens:** Performance findings often suggest recognizable refactors.

**Correct form:** Inspect all locations and call paths, design the smallest safe change, run positive/negative/bulk/failure tests, collect scale evidence, and rescan the same target. Never let the engine approve its own fix.

## 5. Default-org ambiguity

**Mistake:** Run a remote engine against whichever org the CLI currently treats as default and omit identity from the report.

**Why it happens:** Local commands succeed without an explicit alias.

**Correct form:** Resolve and record the exact alias/username/org ID and environment class. Pass `--target-org` in reproducible automation, especially when multiple authentications exist.

## 6. Unbounded workspace

**Mistake:** Scan a monorepo, home directory, or broad package tree and present timeouts or partial output as complete.

**Why it happens:** Broad globs seem safer than missing a file.

**Correct form:** Select the affected package/bundle and explicit Apex targets, record exclusions, and split large scopes into reproducible batches. A partial run must remain `partial`.

## 7. CSV flattening

**Mistake:** Use CSV as the canonical evidence and discard secondary locations or path information for multi-location findings.

**Why it happens:** CSV is convenient for spreadsheets and simple gates.

**Correct form:** Preserve raw JSON or SARIF as the canonical report; derive CSV only for review. Retain `primaryLocationIndex`, every location, resources, suggestions, and the raw hash.

## 8. Engine conflation

**Mistake:** Attribute PMD, SFGE, ESLint, RetireJS, Flow, or CPD findings to ApexGuru in a combined Code Analyzer run.

**Why it happens:** All violations share one output schema.

**Correct form:** Preserve the `engine` field and normalize only ApexGuru entries for this workflow. Route other findings to the appropriate Code Analyzer or domain skill.

## 9. Zero-findings certification

**Mistake:** Declare code performant, scalable, secure, or defect-free because ApexGuru returned no violations.

**Why it happens:** Empty output resembles a passing test suite.

**Correct form:** State only that no ApexGuru findings were returned for the recorded engine version, source revision, and targets. Keep runtime tests, query plans, logs, load tests, and other analyzers as independent evidence.

## 10. Suppression by engine disablement

**Mistake:** Turn off ApexGuru or exclude a broad directory to silence one disputed finding.

**Why it happens:** It makes a gate pass without resolving triage.

**Correct form:** Use a scope-limited suppression or `not-applicable` disposition with reproducible evidence, owner, expiry/review trigger, and residual risk. Keep the rest of the engine active.

## 11. Before/after drift

**Mistake:** Compare scans from different commits, target lists, configs, engine versions, orgs, or evidence modes and claim a finding was fixed.

**Why it happens:** Teams reuse whatever reports are available.

**Correct form:** Pin revision, workspace, targets, target org, command/config, tool/engine version, timestamp, and raw hash. Re-run the same experiment, then separately disclose any unavoidable change in conditions.

## 12. Secret in configuration

**Mistake:** Put usernames, passwords, tokens, refresh tokens, or auth URLs in `code-analyzer.yml`, scripts, fixtures, or normalized output.

**Why it happens:** Remote-engine prerequisites are mistaken for application configuration.

**Correct form:** Reuse Salesforce CLI authentication and pass only an alias. Redact credentials from logs/reports, scan artifacts for secrets, and never commit auth material.
