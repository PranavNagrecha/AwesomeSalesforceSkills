---
name: omni-channel-custom-routing
description: "Use this skill to implement Apex-driven custom routing logic for Omni-Channel work items using PendingServiceRouting and SkillRequirement objects. Trigger keywords: PendingServiceRouting, SkillRequirement, IsReadyForRouting, skills-based routing, custom routing Apex. NOT for declarative Omni-Channel queue-based routing setup, routing configurations in Setup UI, or Einstein Classification routing rules."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "How do I route a Case to an agent with specific skills using Apex in Omni-Channel"
  - "PendingServiceRouting IsReadyForRouting sequence — what order do I insert records"
  - "Skills-based routing Apex — SkillRequirement records not being matched"
  - "Custom routing logic for Omni-Channel with skill relaxation overflow"
  - "ServiceChannelId hardcoded in Apex breaks after sandbox refresh"
tags:
  - omni-channel
  - routing
  - skills-based-routing
  - PendingServiceRouting
  - SkillRequirement
  - service-cloud
inputs:
  - Service Channel Id (query by DeveloperName, never hardcoded)
  - List of required Skill Ids and minimum skill levels
  - Work item record Id (Case, Lead, or custom SObject)
  - Routing priority and capacity weight
outputs:
  - Inserted PendingServiceRouting record with associated SkillRequirement records
  - IsReadyForRouting flipped to true to activate routing
  - Guidance on skill relaxation overflow configuration
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Omni-Channel Custom Routing (Apex)

This skill activates when a team needs programmatic control over how work items are matched to agents via Omni-Channel's skills-based routing engine — specifically when Apex code must construct `PendingServiceRouting` records, associate `SkillRequirement` records, and trigger routing by flipping the `IsReadyForRouting` flag.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that Omni-Channel and Skills-Based Routing are enabled in the org (Setup > Omni-Channel Settings). The `PendingServiceRouting` and `SkillRequirement` objects are only available when the feature is active.
- Identify the `ServiceChannel` `DeveloperName` values that correspond to the work item type — never hardcode `Id` values, which differ across sandboxes and production.
- Confirm the `Skill` `DeveloperName` values for each skill the routing logic requires. Query them at runtime rather than assuming they are stable.
- Understand whether skill relaxation (overflow) is needed: when no agent with all required skills is available, the platform can drop `IsAdditionalSkill=true` skill requirements after a configured timeout.

---

## Core Concepts

### The Three-DML Sequence

Custom routing via Apex requires exactly three discrete DML operations in the correct order. Collapsing them fails silently or throws DML exceptions:

1. `INSERT` a `PendingServiceRouting` record with `RoutingType = 'SkillsBased'` and `IsReadyForRouting = false`. The record must reference a valid `ServiceChannelId` and the `WorkItemId` of the case, chat, or custom object being routed.
2. `INSERT` one or more `SkillRequirement` records, each linked to the `PendingServiceRouting` via `RelatedRecordId`. Each record specifies a `SkillId`, a `SkillLevel` (1–10), and optionally `IsAdditionalSkill = true` to mark it as relaxable overflow.
3. `UPDATE` the `PendingServiceRouting` record, setting `IsReadyForRouting = true`. This signals to the routing engine that the work item is ready to be dispatched.

Attempting to set `IsReadyForRouting = true` on insert, or inserting `SkillRequirement` records before the parent `PendingServiceRouting` record exists, causes runtime errors.

### SkillRequirement and Skill Relaxation

Each `SkillRequirement` record carries a `SkillId`, a `SkillLevel` (minimum proficiency 1–10), and a boolean `IsAdditionalSkill`. Skills marked `IsAdditionalSkill = false` are required — an agent must possess them at or above the minimum level. Skills marked `IsAdditionalSkill = true` are "nice to have" and are subject to relaxation: after the org-configured timeout elapses with no matching agent found, the routing engine drops all `IsAdditionalSkill = true` requirements and retries with only the required skills. This mechanism is the primary overflow strategy for skills-based routing.

### ServiceChannelId Resolution

`ServiceChannel.Id` is an org-specific value. It changes between sandbox refreshes and between sandbox and production. Code that hardcodes a `ServiceChannelId` breaks silently on deployment — the insert succeeds but the routing engine ignores the record or throws a runtime error. The only safe pattern is to query `ServiceChannel` by `DeveloperName` at runtime. Cache the result in a custom metadata type or platform cache when query volume is a concern, but never embed the raw `Id` in Apex.

### Avoiding SOQL in Loops for Skill Resolution

Each `PendingServiceRouting` record requires one or more `Skill` Ids. If the routing logic processes a batch of work items, querying `Skill` by `DeveloperName` inside the loop issues one SOQL call per record, exhausting governor limits. The correct pattern is to collect all required `DeveloperName` values first, issue a single `SELECT Id, DeveloperName FROM Skill WHERE DeveloperName IN :names` query, then build a `Map<String, Id>` for use within the loop.

---

## Common Patterns

### Pattern: Bulk Skills-Based Routing from a Trigger or Batch Job

**When to use:** A trigger fires on Case insert (or a batch job processes a queue of cases) and each case needs to be routed to an agent with matching skills.

**How it works:**

1. Collect all `ServiceChannel` and `Skill` `DeveloperName` values needed by the batch.
2. Issue one `SELECT` for `ServiceChannel` and one for `Skill` — build lookup maps.
3. For each work item, construct and insert a `PendingServiceRouting` record with `IsReadyForRouting = false`.
4. Build a list of `SkillRequirement` records linked by `RelatedRecordId`.
5. `INSERT` all `SkillRequirement` records in one DML statement.
6. Set `IsReadyForRouting = true` on each `PendingServiceRouting` and `UPDATE` the list.

**Why not the alternative:** A single-record approach (insert PSR, insert SR, flip flag, one at a time) works in low-volume scenarios but hits DML governor limits in batch contexts. Bulkifying all three DML steps avoids this.

### Pattern: Skill Relaxation for Overflow

**When to use:** The org requires a best-effort agent match — if no agent has all skills, route to any agent with the core skill after a timeout.

**How it works:** Mark secondary or specialist skills with `IsAdditionalSkill = true` on the `SkillRequirement` record. The timeout is configured in the routing configuration's overflow settings. The routing engine automatically drops the `IsAdditionalSkill = true` requirements after the timeout and re-evaluates.

**Why not the alternative:** Manually creating a second `PendingServiceRouting` record after a timeout requires a scheduled job or platform event listener — more moving parts and harder to debug than the built-in relaxation mechanism.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Work items always need all skills matched | `IsAdditionalSkill = false` on all `SkillRequirement` records | No relaxation; agent must meet full requirement |
| Need overflow routing after timeout | Add secondary skills with `IsAdditionalSkill = true` | Platform handles relaxation without custom timer logic |
| Routing multiple work items in one transaction | Bulkify all three DML steps | Prevents DML governor limit breaches |
| ServiceChannel lookup needed | Query by `DeveloperName` at runtime | `Id` is org-specific and changes on sandbox refresh |
| Skill Ids needed for multiple records | Single bulk SOQL + `Map<String, Id>` | Avoids SOQL-in-loop governor limit |
| Want to cancel routing | Delete the `PendingServiceRouting` record | Deletion removes the work item from the routing queue |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify feature enablement** — Confirm Omni-Channel and Skills-Based Routing are active in Setup. Confirm the `ServiceChannel` and `Skill` records exist with known `DeveloperName` values.
2. **Gather Ids safely** — Query `ServiceChannel` and `Skill` by `DeveloperName` at the top of the transaction. Store results in maps. Do not issue these queries inside loops.
3. **Insert PendingServiceRouting records (IsReadyForRouting = false)** — Construct and insert all `PendingServiceRouting` records in one DML operation. Set `RoutingType = 'SkillsBased'`, `IsReadyForRouting = false`, and provide `WorkItemId`, `ServiceChannelId`, `RoutingPriority`, and `CapacityWeight`.
4. **Insert SkillRequirement records** — For each `PendingServiceRouting` record, construct `SkillRequirement` records linked via `RelatedRecordId`. Set `IsAdditionalSkill` appropriately for required vs. overflow skills. Insert all in one DML statement.
5. **Flip IsReadyForRouting = true** — Update all `PendingServiceRouting` records to set `IsReadyForRouting = true` in a single DML update. This activates routing.
6. **Handle errors and rollback** — Wrap the sequence in a try/catch. On failure, delete any inserted `PendingServiceRouting` records to avoid orphaned routing entries that hold work items in a pending state indefinitely.
7. **Validate in a sandbox with real agent availability** — Routing only works when at least one agent with matching skills and capacity is present in the Omni-Channel utility. Test with a live agent before deploying to production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `ServiceChannelId` is resolved by querying `DeveloperName` — no hardcoded Id in Apex
- [ ] `Skill` Ids are resolved by a single bulk SOQL query, not queried per record
- [ ] Three-DML sequence is preserved: insert PSR (flag=false) → insert SkillRequirements → update PSR (flag=true)
- [ ] `IsReadyForRouting = false` is set on insert, `true` is set only after `SkillRequirement` records exist
- [ ] Overflow skills are marked `IsAdditionalSkill = true` if relaxation is intended
- [ ] Error handling deletes `PendingServiceRouting` records on failure to prevent orphans
- [ ] Tested in a sandbox with a real agent who has matching skills assigned

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **IsReadyForRouting on insert causes immediate but incomplete routing** — Setting `IsReadyForRouting = true` during the initial insert, before `SkillRequirement` records exist, causes the routing engine to evaluate the work item with zero skill requirements. This may silently route to the wrong agent or cause a DML exception, depending on org configuration.
2. **ServiceChannelId hardcoding breaks on sandbox refresh** — Salesforce reassigns record Ids when a sandbox is refreshed from production. Hardcoded `ServiceChannelId` values in Apex produce silent routing failures — the insert succeeds but the routing engine cannot find the channel.
3. **Orphaned PendingServiceRouting blocks re-routing** — A work item can only have one active `PendingServiceRouting` record at a time. If an exception leaves an orphaned record (inserted but never deleted), subsequent routing attempts fail with a DUPLICATE_VALUE error. Clean up on failure.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `PendingServiceRouting` record | The routing ticket created by Apex; links the work item to a service channel and holds routing parameters |
| `SkillRequirement` records | Per-skill requirements associated with the `PendingServiceRouting` record; define which agent skills and levels are needed |
| Routing outcome | Work item assigned to a qualified agent's Omni-Channel queue when a match is found |

---

## Related Skills

- `architect/omni-channel-capacity-model` — use alongside this skill when tuning agent capacity weights and channel throughput
- `admin/sales-engagement-cadences` — if routing work items generated by cadence steps, coordinate channel setup with this skill
