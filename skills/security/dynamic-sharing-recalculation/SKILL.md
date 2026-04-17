---
name: dynamic-sharing-recalculation
description: "Force or orchestrate sharing recalculation after bulk data loads, rule changes, or user/role reorgs so row access catches up with policy. NOT for designing new sharing rules — use sharing-selection tree."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "after data load users cant see records"
  - "added sharing rule recalculation is still running"
  - "role hierarchy change access not updated"
  - "recalculate sharing apex"
tags:
  - sharing
  - recalculation
  - bulk
inputs:
  - "Which driving event triggered the drift"
  - "estimated record volume"
outputs:
  - "Recalc orchestration plan (defer rules, enable in batches, verify)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Dynamic Sharing Recalculation

Sharing recalculation is a platform-managed process that rebuilds __Share rows after rule or hierarchy changes. For orgs above 1M records it can take hours; bulk loads can temporarily leave users without access. This skill prescribes a deferred-sharing pattern (Defer Sharing Calculations permission) and a verification checklist.

## When to Use

Before a data migration of >100k records into a Private OWD object, a sharing-rule edit on a multi-million-row object, or a role-hierarchy reorg. Not for small day-to-day edits.

Typical trigger phrases that should route to this skill: `after data load users cant see records`, `added sharing rule recalculation is still running`, `role hierarchy change access not updated`, `recalculate sharing apex`.

## Recommended Workflow

1. Request the 'Defer Sharing Calculations' permission from Salesforce Support 2–3 weeks in advance.
2. Before the load, enable 'Defer Sharing Rule Calculations' on the affected object.
3. Run the data load; verify counts; spot-check owner and criteria fields.
4. Re-enable sharing calculations — monitor Setup → Sharing Recalculation until queue is empty.
5. Run a verification script (SOQL as a representative user) to confirm expected record visibility.

## Key Considerations

- Defer Sharing is global per object; plan change freezes around it.
- Role hierarchy changes trigger background recalc on ALL objects that share via hierarchy.
- Group maintenance jobs run asynchronously — public group changes can take minutes to propagate even without explicit recalc.
- Big Object sharing recalc is not supported.

## Worked Examples (see `references/examples.md`)

- *Migrating 10M Opportunity records into a Private org* — ETL inserts nightly for a week.
- *Role reorg 1200 users* — New regional structure.

## Common Gotchas (see `references/gotchas.md`)

- **Defer never requested** — Support takes weeks to enable; deadline missed.
- **Re-enable forgotten** — Sharing stays deferred, new records have no access.
- **Apex Managed Sharing inserts still happen** — Defer flag does not block your __Share DML; inconsistency.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Enabling Defer Sharing without a runbook to re-enable
- Loading 10M records on a Monday without defer permissions
- Asking users to verify access 'eventually' — provide a specific verification script

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
