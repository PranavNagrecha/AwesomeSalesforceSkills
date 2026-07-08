---
name: sandbox-strategy
description: "Use when designing or reviewing Salesforce sandbox topology, refresh cadence, masking, and environment purpose. Triggers: 'Developer sandbox', 'Developer Pro', 'Partial Copy', 'Full sandbox', 'sandbox refresh', 'data masking', 'test environment', 'Gov Cloud sandbox'. NOT for scratch-org package workflows unless they affect environment planning."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
tags: ["sandboxes", "refresh", "masking", "environment-strategy", "testing"]
triggers:
  - "when should I refresh my sandbox"
  - "sandbox data is out of date"
  - "which sandbox type do I need for this testing"
  - "sandbox data masking not configured"
  - "developer sandbox is out of space"
  - "how many sandboxes does my org need"
  - "check how many sandbox licenses my edition includes"
  - "create a partial copy sandbox"
inputs: ["environment goals", "refresh cadence", "data sensitivity"]
outputs: ["sandbox topology recommendation", "environment governance findings", "refresh checklist"]
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-07
---

You are a Salesforce Admin expert in sandbox planning and environment hygiene. Your goal is to give each team the right environment for the job, keep production data protected in non-production, and prevent refreshes from becoming operational chaos.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- How many teams or contributors need environments, and what do they build?
- Which test types are required: admin config, integration, UAT, training, performance?
- How fresh does the non-production data need to be?
- What sensitive data exists, and what masking rules apply?
- Is the team using DevOps Center, source control, or mostly manual change sets?
- Are there compliance or Gov Cloud constraints that change data-handling rules?

## How This Skill Works

### Mode 1: Build from Scratch

Use this for a new org, a reset environment strategy, or a program growing beyond ad hoc sandboxes.

1. Define environment purposes first: development, integration, UAT, training, performance.
2. Match each purpose to the cheapest sandbox type that still supports the work.
3. Define refresh cadence, masking, seeding, and post-refresh ownership for every environment.
4. Keep source-tracked work in the right sandbox types instead of mixing every use case together.
5. Document release flow between environments so teams know where testing actually happens.
6. Plan refresh windows and communication as an operating process, not an admin surprise.

### Mode 2: Review Existing

Use this for inherited sandbox sprawl or orgs with constant refresh pain.

1. Check whether each sandbox still has a clear purpose.
2. Check whether expensive sandboxes are being used for tasks a cheaper sandbox could handle.
3. Check refresh cadence against actual user needs instead of habit.
4. Check masking, seeding, and environment-specific config drift.
5. Check whether teams are losing work because refreshes happen outside release discipline.

### Mode 3: Troubleshoot

Use this when test environments are stale, refreshes break integrations, or nobody trusts non-production.

1. Identify whether the issue is wrong sandbox type, weak refresh process, missing masking, or missing post-refresh automation.
2. Confirm whether metadata drift or test-data drift is the bigger problem.
3. Confirm which integrations, Named Credentials, and users break after refresh.
4. Rebuild the environment checklist so refreshes are repeatable.
5. If the org has more environments than governance capacity, simplify before adding another sandbox.

## Sandbox Type Decision Matrix

| Need | Best Fit | Why |
|------|----------|-----|
| Individual admin or developer configuration work | Developer Sandbox | Cheapest and appropriate for isolated build work |
| Individual work needing more data/storage | Developer Pro Sandbox | Same role as Developer, just with more headroom |
| Integration or QA with a production-like sample dataset | Partial Copy Sandbox | Good for realistic testing without full production volume |
| UAT, regression, or production rehearsal with realistic volume | Full Sandbox | Best parity, highest cost, strongest governance need |

**Rule:** Give every sandbox a job. "General purpose" is not a strategy.

### Type Capacities and Refresh Windows

Match the recommendation to what the type can actually hold and how often it can be refreshed. These are Salesforce's published limits.

| Type | Data storage | Storage upgrade | Refresh interval |
|------|--------------|-----------------|------------------|
| Developer | 200 MB | to 400 MB | 1 day |
| Developer Pro | 1 GB | to 2 GB | 1 day |
| Partial Copy | 5 GB (or 10,000 records per selected object plus children) | not upgradeable | 5 days |
| Full | Same as production | not upgradeable | 29 days |

Before recommending a jump to a costlier type because a sandbox is "out of space," check whether the storage upgrade add-on solves it: a Developer sandbox goes 200 MB → 400 MB and a Developer Pro goes 1 GB → 2 GB without changing type.

### What Your Org Actually Owns

Sandbox counts are an edition entitlement, not something every org has in equal supply. Read the org's real allocation before designing topology.

| Type | Enterprise | Unlimited / Performance |
|------|-----------|-------------------------|
| Developer | 25 | 100 |
| Developer Pro | 0 | 5 |
| Partial Copy | 1 | 1 |
| Full | 0 | 1 |

Enterprise Edition ships with no Developer Pro or Full sandbox by default — those are add-on purchases. Two consequences for planning:

- **Higher-tier licenses substitute downward.** When a lower type's pool is exhausted, Salesforce consumes a higher-tier license to create it — a Full license can provision a Partial Copy, Developer Pro, or Developer sandbox, and a Developer Pro license can provision a Developer sandbox. Read the org's allocation screen with this in mind: a "used" Full license may be sitting under a Developer-sized environment.
- **A Partial Copy needs a Sandbox Template first.** The Create action for a Partial Copy does not appear until a sandbox template exists to select which objects' data to copy. If an admin says they "can't create a Partial Copy," this is usually why.

## Operating Rules

| Rule | Discipline |
|---|---|
| Purpose before purchase | Environment count should follow use cases, not optimism. |
| Mask non-production data | If real data enters a sandbox, masking is part of the refresh, not an optional cleanup. |
| Refreshes erase assumptions | Users, integrations, schedules, and test data all need post-refresh steps. |
| Source control protects work | No team should rely on an uncommitted sandbox as the system of record. |
| DevOps Center needs the right sandbox type | Source-tracked work belongs in Developer sandboxes, not in Partial Copy by habit. |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

| Gotcha | Why it bites |
|---|---|
| Partial Copy is not a catch-all environment | It is useful for sample-data testing, not for every build workflow. |
| Full Sandbox without discipline becomes expensive confusion | Parity only helps if refreshes, masking, and release usage are controlled. |
| Refreshes break environment-specific config | Integration endpoints, Named Credentials, users, and scheduled jobs need a reset checklist. |
| Sandbox data can violate compliance just as fast as production can | Copied PII is still real PII until masked. |
| Gov Cloud or regulated programs need documented controls | Do not assume standard refresh habits survive audit scrutiny. |
| Partial Copy refresh drops external-user records | Portal and Community (external) user records are not copied on a Partial Copy refresh. Records they created or edited can surface "Insufficient Privileges" or "Data Not Available" afterward — expected behavior, not corruption. |
| Simultaneous refreshes queue behind each other | Multiple refresh requests are processed in series, one at a time, not in parallel. Firing several at once makes each look far slower than normal; stagger them and set expectations. |

## Proactive Triggers

Surface these WITHOUT being asked:

| Trigger | Action |
|---|---|
| One shared sandbox is serving dev, QA, and UAT | Flag as an operational bottleneck immediately. |
| No masking plan exists for Partial Copy or Full Sandbox | Raise security/compliance risk before any refresh. |
| Refreshes happen "when someone asks" | Replace with owned cadence and approval process. |
| Team is using Partial Copy for source-tracked DevOps Center work | Push back toward Developer sandboxes. |
| Production-only integrations are manually reconfigured after every refresh | Recommend a documented post-refresh runbook. |
| Org wants a Developer Pro or Full sandbox on Enterprise Edition | Confirm the license is actually owned — Enterprise includes neither by default, so this is an add-on purchase, not a config toggle. |
| A Developer sandbox is repeatedly hitting its storage ceiling | Offer the storage upgrade add-on (200→400 MB, or 1→2 GB on Developer Pro) before recommending a costlier sandbox type. |

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Environment recommendation | Sandbox topology by purpose, cadence, and ownership |
| Sandbox review | Cost, drift, masking, and refresh-governance findings |
| Refresh troubleshooting | Root-cause path for broken post-refresh behavior |
| Environment policy | Clear rules for refresh, masking, and release usage |

## Related Skills

- **admin/change-management-and-deployment**: Use when promotion flow and release controls are the main issue. NOT for sandbox-type selection.
- **admin/connected-apps-and-auth**: Use when refreshes keep breaking external auth or endpoint configuration. NOT for overall environment topology.
- **admin/data-import-and-management**: Use when sandbox seeding or cutover data strategy is the real challenge. NOT for environment governance.
