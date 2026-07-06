# Data Cloud Code Extensions — Work Template

Use this template when scoping, building, or promoting a Data 360 (Data Cloud) Code
Extension — a custom Python script (batch data transform) or function (search-index
chunking).

## Scope

**Skill:** `data-cloud-code-extensions`

**Request summary:** (fill in what the user asked for)

**Why native features don't suffice:** (name the native transform/feature considered and
the specific gap — if a native feature can do it, stop here)

## Eligibility Gate (hard stops)

- [ ] Edition is Developer / Enterprise / Performance / Unlimited
- [ ] Code Extension enabled in Feature Manager (sandbox AND production)
- [ ] Org does NOT have BYOK enabled (BYOK = feature unavailable, no workaround)
- [ ] Data Cloud Architect permission set assigned to run/monitor/migrate users
- [ ] Requirement is expressible in Python (only supported language today)

## Context Gathered

- Surface: custom **script** (batch data transform) | custom **function** (chunking)
- For a script — source objects: (DLOs or DMOs) → target objects: (same type only;
  DMO targets must be transform-type DMOs)
- For a function — search index + data source: (function receives
  `SearchIndexChunkingV1Request`, returns `SearchIndexChunkingV1Response`; no DLO/DMO
  access at runtime; must handle repeated invocations independently)
- Schedule / trigger: on demand | scheduled | per index build
- Sensitive fields in play (must never reach stdout / Logs DLO):

## Local Toolchain

- [ ] Python 3.11 (`python3.11 --version`)
- [ ] Azul Zulu OpenJDK 17.x (`java -version`)
- [ ] Docker Desktop running (WSL 2 backend on Windows)
- [ ] Salesforce CLI 2.130.9+ (`sf version`)
- [ ] Code Extension plugin 0.1.5+
- [ ] `salesforce-data-customcode` SDK (`python3.11 -m pip show salesforce-data-customcode`)
- [ ] Authenticated to sandbox (`sf org login web` with environment-specific flags, `sf org display --target-org <alias>`)

## Package Plan

```
<project>/
├── Dockerfile              # DON'T MODIFY
├── requirements.txt        # deployment pip deps only
├── requirements-dev.txt    # local dev/test deps only
└── payload/
    ├── config.json         # deployment configuration
    └── entrypoint.py       # transform / chunking logic
```

- Runtime pip dependencies to add:
- Pattern from SKILL.md applied and why:

## Promotion Plan (DevOps Data Kit)

1. Add the batch data transform to the data kit (code extension auto-includes)
2. Manually add every referenced DLO/DMO: (list them)
3. Deploy in fixed order: DLOs/DMOs → code extensions → batch transforms
4. On any component failure the deployment stops — verify all components landed

## Checklist

- [ ] Object-type parity holds (DLO→DLO / DMO→DMO; transform-type DMO targets)
- [ ] Function is stateless and reads no DLO/DMO at runtime (if applicable)
- [ ] No PII / credentials / sensitive values printed to stdout
- [ ] Governance tags manually assigned + audited on created/updated DLOs/DMOs
- [ ] Sandbox run validated via the Logs DLO (`DataCustomCodeLogs__dll`)
- [ ] No GA/Beta maturity claim in any deliverable (docs state none)

## Validation

Run the skill checker against the project scaffold:

```bash
python3 scripts/check_data_cloud_code_extensions.py --project-dir <project>
```

## Notes

(Record any deviations from the standard pattern and why.)
