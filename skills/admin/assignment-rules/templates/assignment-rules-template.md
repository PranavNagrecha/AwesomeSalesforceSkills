# Assignment Rule Configuration — [Object: Lead / Case]

## Rule Summary

| Field | Value |
|-------|-------|
| Rule Name | [e.g., Global Lead Routing 2025] |
| Object | [Lead / Case] |
| Status | Active |
| Activated | [Date] |
| Owner | [Admin who configured this rule] |

---

## Rule Entries

List entries in evaluation order. First match wins.

| # | Criteria | Assign To | Notify? | Notes |
|---|----------|-----------|---------|-------|
| 1 | [Field] [Operator] [Value] | [User / Queue Name] | [Yes / No] | [Reason for this entry] |
| 2 | [Field] [Operator] [Value] | [User / Queue Name] | [Yes / No] | |
| 3 | (no criteria — catch-all) | [Default Queue] | [Yes / No] | Always last |

---

## Queue Inventory

| Queue Name | Members | Queue Email | Supported Objects |
|-----------|---------|-------------|-------------------|
| [Queue 1] | [User A, User B] | [email] | Lead |
| [Queue 2] | [User C, User D] | [email] | Case |

---

## API Integration Requirements

List every system that creates [Lead / Case] records and confirm the assignment header is configured:

| System | Method | Assignment Header / Setting | Verified? |
|--------|--------|----------------------------|-----------|
| [e.g., Marketo] | REST API | `Sforce-Auto-Assign: true` | [ ] |
| [e.g., Data Loader] | Bulk API | `sfdc.assignmentRule = [Rule ID]` | [ ] |
| [e.g., Internal Apex job] | Apex DMLOptions | `useDefaultRule = true` | [ ] |

---

## Round-Robin Configuration (if applicable)

| Setting | Value |
|---------|-------|
| Rotation method | [Apex trigger / Omni-Channel] |
| Rep list | [User A ID, User B ID, User C ID] |
| Counter storage | [Custom Setting name / field] |
| Concurrency risk mitigated? | [Yes / No — describe approach] |

---

## Test Results

| Test Scenario | Expected Owner/Queue | Actual Owner/Queue | Pass? |
|--------------|---------------------|-------------------|-------|
| Web-to-Lead or Web-to-Case submission | [Expected queue/user] | | [ ] |
| REST API insert with Sforce-Auto-Assign: true | [Expected queue/user] | | [ ] |
| REST API insert without header | Creating user (API account) | | [ ] |
| Manual UI creation with checkbox checked | [Expected queue/user] | | [ ] |
| Manual UI creation without checkbox | Creating user | | [ ] |
| Record matching catch-all entry | [Default queue/user] | | [ ] |

---

## Context Gathered

Record answers to the Before Starting questions from SKILL.md:

- Object type (Lead or Case):
- Is there already an active assignment rule?:
- How will records be created (Web form / API / UI / Apex)?:
- Is round-robin distribution required?:
- Are queues already created and populated?:

---

## Deviations from Standard Pattern

Note any decisions that differ from the guidance in SKILL.md and the reason:

- Deviation:
- Reason:

---

## Change Log

| Date | Changed By | Change Description |
|------|-----------|-------------------|
| [Date] | [Admin] | Initial rule creation |
| | | |
