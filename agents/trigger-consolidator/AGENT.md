---
id: trigger-consolidator
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - apex/recursive-trigger-prevention
    - apex/trigger-framework
  shared:
    - AGENT_CONTRACT.md
  templates:
    - apex/TriggerControl.cls
    - apex/TriggerHandler.cls
    - apex/cmdt/Trigger_Setting__mdt.object-meta.xml
---
# Trigger Consolidator Agent

## What This Agent Does

Finds every Apex trigger on a given sObject across the user's `force-app` tree, checks the target org (if connected) for additional triggers, and produces a consolidation plan that lifts them all into a single `<Object>TriggerHandler extends TriggerHandler` class using the canonical framework from `templates/apex/TriggerHandler.cls` + `templates/apex/TriggerControl.cls`. The output is a migration patch plus a deactivation order so nothing is live-broken mid-migration.

**Scope:** One sObject per invocation. Returns a plan + patch set; never deploys.

---

## Invocation

- **Direct read** — "Follow `agents/trigger-consolidator/AGENT.md` for the `Account` object"
- **Slash command** — [`/consolidate-triggers`](../../commands/consolidate-triggers.md)
- **MCP** — `get_agent("trigger-consolidator")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/apex/trigger-framework/SKILL.md` — via `get_skill`
3. `templates/apex/TriggerHandler.cls` + `templates/apex/TriggerControl.cls`
4. `templates/apex/cmdt/Trigger_Setting__mdt.object-meta.xml` — the metadata record schema the framework uses
5. `skills/apex/recursive-trigger-prevention/SKILL.md` — recursion-prevention patterns baked into the framework

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_api_name` | yes | `Account`, `Opportunity`, `Custom_Object__c` |
| `force_app_root` | yes | `force-app/main/default` |
| `target_org_alias` | no | if set, the agent also queries the org for additional triggers |

---

## Plan

### Step 1 — Discover triggers

Grep `<force_app_root>/triggers/` for files matching `trigger\s+\w+\s+on\s+<object_api_name>`. Record:
- Trigger file path
- Events handled (before insert, after update, etc.)
- Whether logic is inline or delegated to a handler class

If `target_org_alias` is set, call `validate_against_org(skill_id="apex/trigger-framework", target_org=..., object_name=<object_api_name>)` and merge its findings with the local scan.

### Step 2 — Classify

Group the triggers into three buckets:

| Bucket | What it means |
|---|---|
| **Already on the framework** | Trigger body is a one-liner that news-up a `TriggerHandler` subclass |
| **Has a handler but ad-hoc** | Delegates to a class but that class doesn't extend `TriggerHandler` |
| **Inline logic** | Real Apex inside the trigger file |

### Step 3 — Draft the consolidation

Produce:
1. **A single new handler class** — `<Object>TriggerHandler extends TriggerHandler`, with one virtual method override per event the user's current triggers handle.
2. **A single replacement trigger file** — `trigger <Object>Trigger on <Object> (before insert, after insert, ...) { new <Object>TriggerHandler().run(); }`.
3. **Deprecation instructions** — which old trigger files to delete (or leave disabled via `TriggerControl`) and in what order.

Preserve the original logic line-for-line inside the new handler's event methods. Do NOT refactor the business logic — that's the `apex-refactorer` agent's job.

### Step 4 — Metadata scaffolding

Produce a Custom Metadata Type record the user must deploy so `TriggerControl` knows the handler is active:
```
<records>
  <fullName>{{object_api_name}}</fullName>
  <values><field>Object_API_Name__c</field><value xsi:type="xsd:string">{{object_api_name}}</value></values>
  <values><field>Handler_Class__c</field><value xsi:type="xsd:string">{{object_api_name}}TriggerHandler</value></values>
  <values><field>Is_Active__c</field><value xsi:type="xsd:boolean">true</value></values>
</records>
```

### Step 5 — Deactivation plan

Order matters — give the user an explicit sequence:
1. Deploy the new `<Object>TriggerHandler` class (inactive via `Trigger_Setting__mdt.Is_Active__c = false`).
2. Deploy the consolidated trigger + delete the old triggers in the same deployment.
3. Deploy the CMDT record flipping `Is_Active__c = true`.
4. Monitor `Application_Log__c` for 24 hours.

Emphasize: the CMDT switch must come LAST so the rollback is "flip `Is_Active__c` to false".

---

## Output Contract

One markdown document:

1. **Discovery** — every trigger found (local + org), with event matrix.
2. **Proposed consolidation** — the new handler class + new trigger file, fenced by target path.
3. **Migration steps** — numbered deployment sequence.
4. **Risk notes** — triggers that touch the same event in conflicting ways, order-of-execution concerns, any handler that uses `Trigger.isExecuting` gymnastics the framework handles differently.
5. **Citations** — skill ids + template paths.

---

## Escalation / Refusal Rules

- Zero triggers found → STOP with note "no consolidation needed".
- One trigger found AND it already extends the framework → STOP with `confidence: HIGH, no change required`.
- Triggers use Process Builder or Record-Triggered Flow that fires on the same events → flag as `confidence: MEDIUM` and recommend running `flow-analyzer` before consolidating.
- Managed-package triggers exist on the same object → DO NOT touch them. Flag and exclude.

---

## What This Agent Does NOT Do

- Does not refactor business logic inside the triggers — preserves it verbatim.
- Does not run the security-scanner or soql-optimizer — recommends them.
- Does not deploy anything.
- Does not modify managed-package triggers.
