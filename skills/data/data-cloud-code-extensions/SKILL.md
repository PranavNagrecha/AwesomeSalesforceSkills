---
name: data-cloud-code-extensions
description: "Use when native Data 360 (formerly Data Cloud) transforms and pipelines can't express your logic and you need to deploy custom Python into the platform — a Code Extension — either as a batch data transform script or as a search-index chunking function, built with the Salesforce CLI Code Extension plugin + Data Custom Code Python SDK and promoted with a DevOps Data Kit. NOT for querying Data Cloud from outside the platform (use integration/data-cloud-query-api), NOT for stream/ingestion setup (use data/data-cloud-data-streams), and NOT for Apex — Code Extension is Python-only today and unavailable in BYOK orgs."
category: data
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "write custom Python transform logic in Data Cloud because the native batch transforms can't do what I need"
  - "deploy a Python script to Data 360 as a scheduled batch data transform"
  - "customize how documents are chunked when building a Data Cloud search index for RAG"
  - "set up the Salesforce CLI code extension plugin and Python SDK for Data 360 custom code"
  - "move a code extension and its batch data transform from sandbox to production"
tags:
  - data-cloud
  - data-360
  - code-extension
  - python
  - batch-data-transform
  - search-index-chunking
inputs:
  - "The transform or chunking requirement that native Data 360 features can't express"
  - "Source and target objects (DLOs or DMOs) for a script, or the search index data source for a function"
  - "Org context: edition, Feature Manager enablement, BYOK status, Data Cloud Architect permission set"
  - "Local toolchain state: Python 3.11, JDK 17, Docker Desktop, Salesforce CLI version"
outputs:
  - "A code extension project: Dockerfile, requirements.txt, payload/config.json, payload/entrypoint.py"
  - "A deployed custom script wired to a batch data transform, or a custom function wired to a search-index chunking strategy"
  - "A DevOps Data Kit promotion plan with the correct dependency order (DLOs/DMOs → code extensions → batch transforms)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-06
---

# Data Cloud Code Extensions

This skill activates when a practitioner needs to run custom Python **inside** Data 360 (formerly Data Cloud) because the native features don't meet the requirement. The mechanism is a **Code Extension** — packaged Python that runs on isolated containers on the platform — with exactly two supported surfaces today: **custom scripts** that execute as batch data transforms, and **custom functions** that control chunking in the search-index pipeline.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the org can use the feature at all.** Code Extension is available in Developer, Enterprise, Performance, and Unlimited editions, must be enabled in **Feature Manager**, and is **not currently supported in orgs with Bring Your Own Key (BYOK) enabled**. A BYOK org is a hard stop — there is no workaround in the bundle.
- **Confirm who runs it.** Developers author the code, but users need the **Data Cloud Architect** permission set to run, monitor, and migrate code extensions.
- **Pick the right surface.** A *script* is a batch data transform job (on demand or scheduled) that reads and writes DLOs/DMOs. A *function* is a narrow chunking extension inside the search-index pipeline — it is not a general data job and cannot read DLOs/DMOs at runtime.
- **Check the toolchain floor.** Local development requires **Python 3.11** specifically (pyenv on macOS/Linux; Python.org, Microsoft Store, or pyenv-win on Windows), **Azul Zulu OpenJDK 17.x**, and **Docker Desktop** (WSL 2 backend on Windows), plus Salesforce CLI **2.130.9+**, the Code Extension plugin **0.1.5+**, and the `salesforce-data-customcode` Python SDK.
- **Know the maturity caveats.** The Code Extension developer guide attaches no GA/Beta/Pilot label — do not assert one. Python is the only supported language today; Salesforce states more languages and more Data 360 capabilities are planned, not shipped.

---

## Core Concepts

### Two surfaces: scripts vs. functions

Code Extension deploys custom Python to exactly two Data 360 features:

- **Custom scripts** run as a **batch data transform** — a job you run on demand or on a schedule. Use them for complex, multi-step data engineering that native transforms can't express: string manipulation, custom computations, data cleansing.
- **Custom functions** run as part of the **search-index pipeline** and control how content is chunked for search and AI retrieval. Data 360 parses source content into `SearchIndexChunkingV1DocElement` objects, passes them to your function in a `SearchIndexChunkingV1Request` payload, and your function returns chunks in a `SearchIndexChunkingV1Response` payload, which Data 360 then vectorizes and indexes. During search-index creation with Advanced Setup, you select the deployed function as the chunking strategy.

The two surfaces share the toolchain and packaging but have very different runtime contracts — a function is a targeted chunking extension, not a full data processing job, and it does not read DLOs or DMOs directly during runtime.

### The toolchain and the package

Three pieces work together locally: **Salesforce CLI** (2.130.9+), the **Code Extension CLI plugin** (0.1.5+), and the **Data Custom Code Python SDK** (`salesforce-data-customcode`). The scaffolded project is a containerized package:

```
my-code-extension/
├── Dockerfile              # used for containerized builds/deployments — don't modify
├── requirements.txt        # pip packages your script needs for deployment
├── requirements-dev.txt    # packages for local development and testing only
├── payload/
│   ├── config.json         # Data 360 deployment configuration
│   └── entrypoint.py       # the Python file implementing your transform logic
├── examples/               # sample code and data shipped with the scaffold
└── .devcontainer/          # VS Code Dev Container configuration
```

You write and validate locally against a sandbox org, deploy to the sandbox, test, then promote to production with a data kit.

### Object-type parity for scripts

A custom script must preserve object-type parity end to end: **DLOs read → DLOs written, DMOs read → DMOs written**. Crossing types is not supported. Additionally, a DMO-to-DMO transform can **only write to a transform-type DMO**. Design the target objects before writing any Python — this constraint shapes the whole pipeline.

### Isolated, ephemeral compute and the Logs DLO

At execution, the code runs on isolated Data 360 compute resources that are **ephemeral** — Salesforce's architecture blog describes them as spinning up to execute the task and tearing down immediately after, "leaving no residual footprint or persistent backdoor access." Design every run (and every chunking invocation) to be self-contained; Data 360 can invoke a function multiple times depending on batching, so each request must be processed independently.

All execution logs land in a dedicated system Data Lake Object, `DataCustomCodeLogs__dll`. **Any user with access to the Logs DLO can view its contents** — never write PII, credentials, or other sensitive data to standard output.

---

## Common Patterns

### Custom batch data transform script

**When to use:** a transform needs logic native Data 360 transforms can't express — multi-step cleansing, custom computations, nontrivial string manipulation.

**How it works:** scaffold the project with the Code Extension plugin; implement the logic in `payload/entrypoint.py`; declare pip dependencies in `requirements.txt`; validate locally against a sandbox org; deploy to the sandbox; create a batch data transform that uses the code extension and run it on demand or on a schedule; monitor via the Logs DLO.

**Why not the alternative:** hand-rolling the logic outside the platform (external ETL calling the Ingestion API) adds an integration to secure and operate; if the data is already in Data 360, a code extension keeps compute, governance, and observability on-platform.

### Custom search-index chunking function

**When to use:** default chunking splits your content badly for retrieval — e.g. related product attributes scatter across chunks and RAG answers degrade.

**How it works:** implement a function that accepts `SearchIndexChunkingV1Request` (parsed `SearchIndexChunkingV1DocElement` objects) and returns `SearchIndexChunkingV1Response`; deploy it; in the search index's Advanced Setup, select the function as the chunking strategy. Keep it stateless — each invocation must stand alone.

**Why not the alternative:** pre-chunking content upstream bakes retrieval decisions into ingestion; a chunking function keeps the source content intact and the chunk boundaries adjustable.

### DevOps Data Kit promotion

**When to use:** always, when moving from sandbox to production. The **DevOps Data Kit** is the documented promotion mechanism for code extensions and their transforms.

**How it works:** add the batch data transform to a DevOps Data Kit — the referenced code extension is **auto-included**, but referenced DLOs/DMOs must be **added manually**. Deployment follows a fixed dependency order: DLOs/DMOs first, code extensions second, batch data transforms last. If any component fails, deployment stops and subsequent components aren't deployed.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Native transform/formula can express the logic | Use the native Data 360 feature | Custom code adds a toolchain, container lifecycle, and promotion process to maintain |
| Complex batch cleansing/computation on DLOs or DMOs | Code extension custom script | The documented surface for batch logic beyond native transforms |
| Retrieval quality suffers from default chunking | Code extension custom function | The documented chunking extension point in the search-index pipeline |
| Chunking logic needs to look up other DLO/DMO data at runtime | Redesign — enrich upstream via a script or ingestion | Functions can't read DLOs/DMOs during invocation |
| Script reads DLOs but the target is a DMO (or vice versa) | Split the pipeline so each script preserves object-type parity | DLO→DLO and DMO→DMO only; DMO targets must be transform-type DMOs |
| Org has BYOK enabled | Don't propose Code Extension | Explicitly not supported with BYOK |
| Logic must run in a language other than Python | Wait or solve outside the platform | Python is the only supported language today; more are planned, not shipped |
| Promoting to production | DevOps Data Kit, fixed order | The data kit is the documented promotion mechanism for code extensions |

---

## Recommended Workflow

1. **Verify eligibility** — edition (Developer/Enterprise/Performance/Unlimited), Code Extension enabled in Feature Manager, no BYOK, Data Cloud Architect permission set assigned to whoever will run/monitor/migrate.
2. **Choose the surface** — batch data transform script vs. search-index chunking function; confirm the runtime contract fits (parity rules for scripts, no-DLO/DMO-access and stateless batching for functions).
3. **Set up the toolchain** — Python 3.11, Azul Zulu OpenJDK 17.x, Docker Desktop; Salesforce CLI 2.130.9+; Code Extension plugin 0.1.5+; `salesforce-data-customcode` SDK; authenticate with `sf org login web` (add the environment-specific flags from the setup guide) against the sandbox.
4. **Scaffold and implement** — build on the generated project; put logic in `payload/entrypoint.py`, deployment pip dependencies in `requirements.txt` (dev-only ones in `requirements-dev.txt`); do not modify the `Dockerfile`; log nothing sensitive to stdout.
5. **Validate locally, then in the sandbox** — run against the sandbox, deploy, wire it to a batch data transform (script) or select it as the chunking strategy in the search index's Advanced Setup (function), and review the `DataCustomCodeLogs__dll` output.
6. **Govern and promote** — manually assign and audit governance tags on any target DLOs/DMOs the script creates or updates; then build a DevOps Data Kit (manually add referenced DLOs/DMOs; the code extension auto-includes with the transform) and deploy in dependency order to production.
7. **Monitor in production** — watch the Logs DLO after the first scheduled runs; confirm no sensitive data appears in log output.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Org eligibility verified: edition, Feature Manager enablement, no BYOK, Data Cloud Architect permission set
- [ ] Surface choice justified: script (batch transform) vs. function (chunking) matches the runtime contract
- [ ] Script preserves object-type parity (DLO→DLO / DMO→DMO) and DMO targets are transform-type DMOs
- [ ] Function processes each request independently and never tries to read DLOs/DMOs at runtime
- [ ] No PII, credentials, or sensitive data written to stdout / the Logs DLO
- [ ] `Dockerfile` unmodified; deployment deps in `requirements.txt`, dev-only deps in `requirements-dev.txt`
- [ ] Governance tags manually assigned and audited on DLOs/DMOs the script creates or updates
- [ ] Promotion plan uses a DevOps Data Kit with DLOs/DMOs added manually and the fixed deploy order respected
- [ ] No GA/Beta claim, no non-Python language, no unsupported surface asserted anywhere in the deliverable

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **BYOK silently rules the feature out** — Code Extension isn't currently supported in orgs with Bring Your Own Key enabled. Teams discover this after building locally; check encryption posture *first*.
2. **The Logs DLO is broadly readable** — every execution logs to `DataCustomCodeLogs__dll`, and any user with access to that DLO can view its contents. A debug `print()` of a customer record is a data exposure, not a log line.
3. **Data kits auto-include the code extension but not its objects** — adding a batch transform pulls in the referenced code extension automatically, yet referenced DLOs/DMOs must be added by hand, and a single component failure stops the rest of the deployment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Code extension project | `Dockerfile` (don't modify), `requirements.txt`, `requirements-dev.txt`, `payload/config.json`, `payload/entrypoint.py` |
| Deployed custom script + batch data transform | On-demand or scheduled transform running the Python on isolated, ephemeral Data 360 compute |
| Deployed custom function + search-index wiring | Chunking strategy selected in the search index's Advanced Setup |
| DevOps Data Kit | Promotion bundle: DLOs/DMOs (manual) → code extension (auto) → batch transform, deployed in that order |
| `templates/data-cloud-code-extensions-template.md` | Work template for scoping, parity checks, and the promotion plan |

---

## Related Skills

- `data/data-cloud-data-model-objects` — design the DMOs (including transform-type targets) your script reads and writes.
- `data/data-cloud-data-streams` — get the source data into DLOs before a code extension transforms it.
- `agentforce/data-cloud-vector-search-dev` — the search-index/RAG side that a custom chunking function plugs into.
- `integration/data-cloud-query-api` — query Data 360 data from *outside* the platform; not a substitute for in-platform transforms.
