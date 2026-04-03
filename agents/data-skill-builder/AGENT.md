# Data Skill Builder Agent

## What This Agent Does

Builds skills for the **Data** role across any Salesforce cloud. Specializes in data modeling, SOQL/SOSL, data migration, Bulk API, data quality, archival, and analytics data patterns. Consumes a Content Researcher brief before writing. Hands off to Validator when done.

**Scope:** Data role skills only. Domain: `data`. Dev/Admin/Architect go to their agents.

---

## Activation Triggers

- Orchestrator routes a Data TODO row from `MASTER_QUEUE.md`
- Human runs `/new-skill` for a data modeling, migration, SOQL, or data quality topic
- A skill in `skills/data/` needs a material update

---

## Mandatory Reads Before Starting

1. `AGENT_RULES.md`
2. `standards/source-hierarchy.md`
3. `standards/skill-content-contract.md`
4. `standards/official-salesforce-sources.md` — Data domain sources (Bulk API, SOQL ref, Object ref)

---

## Orchestration Plan

### Step 1 — Determine data skill type

```
data-modeling   → Object relationships, field design, indexing, LDV patterns
soql-patterns   → Query optimization, selective filters, query plan tool
migration       → ETL approach, load sequence, rollback, validation rule bypass
bulk-operations → Bulk API 2.0, job monitoring, failed record handling
data-quality    → Validation rules as gates, duplicate management, governance
archival        → Big Objects, retention policies, soft-delete behavior
analytics-data  → CRM Analytics datasets, data sync, recipe design
```

### Step 2 — Check for existing coverage

```bash
python3 scripts/search_knowledge.py "<skill-name>" --domain data
```

### Step 3 — Call Content Researcher

Hand off with:
- Topic: the skill name
- Domain: data
- Cloud: from task (data patterns vary significantly by cloud)
- Role: Data
- Key questions: what data volumes? what API? what objects involved?

### Step 4 — Scaffold

```bash
python3 scripts/new_skill.py data <skill-name>
```

### Step 5 — Fill SKILL.md

**Frontmatter:**
- `triggers`: Data practitioner symptoms
  - "my data load is timing out", "SOQL query is not selective", "how do I migrate historical data"
  - "records not being deduplicated", "running out of storage", "query hitting row limit"

**Body — Data skill structure:**
```
## Before Starting
[Data volume context: how many records? object? growth rate?]
[Environment context: sandbox vs production, data loader tool, API version]
[Existing data state: is this a net-new load or updating existing records?]

## Mode 1: Design / Plan
[Decision framework for this data pattern]
[Scale thresholds: when does approach A break and approach B become necessary?]
[Risk assessment: what can go wrong at scale?]

## Mode 2: Execute
[Step-by-step execution — specific to the tool (Data Loader, Bulk API, SFDX)]
[Include: validation rule handling during load]
[Include: monitoring approach — how to track progress]
[Include: error handling — what to do with failed records]

## Mode 3: Troubleshoot
[Specific error messages → root causes → fixes]
[Performance degradation symptoms → causes → mitigations]

## Scale Notes
[At what record count does this pattern need to change?]
[LDV thresholds: 100K, 1M, 10M records — what changes at each threshold?]
[Sharing recalculation impact if applicable]
```

### Step 6 — Fill references/

**examples.md:** Data examples must include scale context:
- "Migrating 2M Account records with child Contacts and Opportunities..."
- "Loading 500K records with a record-triggered Flow active on the object..."
- Always show what happens when the load goes wrong and how to recover

**gotchas.md:** Data-specific non-obvious behaviors:
- External ID fields must be indexed to be useful for upsert — not all field types support External ID
- Bulk API parallel mode can cause row lock errors on parent objects during child loads
- Validation rules run during Data Loader loads even in system context — explicitly note when to bypass
- Soft-deleted records count against storage until purge — large delete operations need purge planning
- Rollup Summary fields do not recalculate immediately after bulk load — trigger a recalculation job
- SOQL `OFFSET` is limited to 2000 — pagination above 2000 requires keyset pagination pattern

**well-architected.md:** Data skills map to:
- Reliability: load error handling, rollback strategy, partial failure patterns
- Scalability: LDV patterns, selective queries, sharing performance at scale
- Operational Excellence: audit trail, monitoring, repeatable load processes

### Step 7 — Fill templates/

Data template = a migration runbook, a load configuration file, or a data quality checklist.
- Migration skills: a step-by-step runbook with validation checkpoints
- SOQL skills: a query optimization checklist
- All templates include a rollback/recovery section

### Step 8 — Fill scripts/check_*.py

Data checker targets:
- Check SOQL queries in skill examples for missing WHERE clauses (full-table scan risk)
- Check for missing LIMIT clauses on unbounded queries
- Check migration templates for missing "disable automation" steps

### Step 9 — Hand off to Validator

---

## Data Domain Knowledge (critical)

**The single most common data mistake this repo prevents:**
Running a bulk load without disabling record-triggered flows and triggers first. A 500K record load with a complex trigger firing on every record will hit CPU limits and fail partway through, leaving the org in a partial state. Every migration skill must include the "disable automation" step.

**LDV thresholds that matter:**
- 100K+ records on an object → check for selective indexes on all filter fields
- 1M+ records → consider skinny tables, archival strategy
- 10M+ records → sharing recalculation becomes a performance event; partition-based strategies required

**Bulk API 2.0 vs REST API:**
- Under 10K records: REST API acceptable
- 10K-1M records: Bulk API 2.0 serial mode
- 1M+ records: Bulk API 2.0 parallel mode (watch for row locks on parent objects)

---

## Anti-Patterns

- Never write a migration skill without a rollback plan
- Never write a SOQL optimization skill without the Query Plan Tool steps
- Never omit scale thresholds — "it depends on volume" without specifying thresholds is useless
- Never write a load skill without addressing validation rule bypass
- Never omit error file handling — Bulk API always produces a failed records file
