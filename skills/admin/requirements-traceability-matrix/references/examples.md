# Examples — Requirements Traceability Matrix

Three RTM samples covering common project shapes. All examples use the canonical column set from SKILL.md.

---

## Example 1: 10-Row Greenfield Sales Cloud Implementation

**Context:** A mid-market manufacturer is implementing Sales Cloud for the first time. The discovery phase produced 10 requirements; the build is one release across three sprints. No regulatory overlay.

**Problem without an RTM:** At UAT, the business sponsor asks "did we implement the territory rule we discussed in week 2?" and nobody can find which story covered it. With an RTM, the answer is `REQ-006 → US-114 → TC-303 → Released in R1.0`.

**Solution (CSV excerpt):**

```csv
req_id,source,description,priority,story_ids,test_case_ids,defect_ids,sprint,release,status
REQ-001,interview,Sales reps see only their accounts on My Accounts list view,must,US-101,TC-201,,Sprint-1,R1.0,Released
REQ-002,interview,Lead conversion creates Opportunity with Stage = Prospecting,must,US-102,TC-202|TC-203,,Sprint-1,R1.0,Released
REQ-003,sow,Opportunity Stage cannot regress without Sales Manager approval,must,US-103|US-104,TC-204|TC-205,DEF-401,Sprint-2,R1.0,Released
REQ-004,interview,Quote PDF is generated from approved Opportunity record,should,US-105,TC-206,,Sprint-2,R1.0,Released
REQ-005,interview,Sales Manager dashboard shows pipeline by stage and territory,must,US-106|US-107,TC-207|TC-208,,Sprint-2,R1.0,Released
REQ-006,sow,Account auto-assigns to territory based on State + Industry,must,US-114,TC-303,,Sprint-3,R1.0,Released
REQ-007,interview,Lost Opportunity requires reason code and competitor name,should,US-108,TC-209,DEF-402,Sprint-3,R1.0,Released
REQ-008,change-request,Mobile users can log call activity from app home screen,could,US-109,TC-210,,Sprint-3,R1.0,Released
REQ-009,interview,Inactive leads auto-archive after 90 days,could,,,,,, Deferred
REQ-010,interview,Integration with marketing automation for lead scoring,should,US-115,,,Sprint-3,,In UAT
```

**Why it works:** Every released row has a story and a test. Row 9 was deferred mid-sprint and kept as evidence (status `Deferred`, blank story/test cells are intentional). Row 10 captures an incomplete requirement at release-gate review — the `release` column is empty, status is `In UAT`, so the gate review immediately flags it.

`scripts/check_rtm.py` on this excerpt returns exit 1 with
`ERROR: row 11 (REQ-010): status 'In UAT' requires at least one test_case_id`. That is the example
working, not the example broken: the gate is supposed to stop here until `REQ-010` has a test or is
moved back to `In Build`.

---

## Example 2: Regulatory Project (HIPAA) with Compliance Source Column

**Context:** A healthcare provider is implementing Health Cloud for case management. Half the requirements come from elicitation interviews, half come from HIPAA Security Rule mappings. The auditor will ask for evidence of every regulatory control.

**Problem without an RTM:** At audit, the team can produce HIPAA controls and screenshots of the org, but cannot link the two. Auditor finding: "no evidence of traceability between regulatory requirements and implemented controls." With an RTM that adds `compliance_control_id` and `evidence_link`, every regulatory row points to a specific test result file or signed approval.

**Solution (CSV excerpt with regulated columns):**

```csv
req_id,source,description,priority,story_ids,test_case_ids,defect_ids,sprint,release,status,compliance_control_id,evidence_link
REQ-001,regulatory,Encrypt PHI fields at rest using Shield Platform Encryption,must,US-201,TC-501,,Sprint-1,R1.0,Released,HIPAA-164.312(a)(2)(iv),evidence/r1-encryption-test.pdf
REQ-002,regulatory,Field Audit Trail enabled on PHI fields with 10-year retention,must,US-202,TC-502,,Sprint-1,R1.0,Released,HIPAA-164.312(b),evidence/r1-fat-config-screenshot.png
REQ-003,regulatory,Login IP ranges restrict org access to corporate network,must,US-203,TC-503,,Sprint-1,R1.0,Released,HIPAA-164.312(a)(1),evidence/r1-ip-restriction-policy.pdf
REQ-004,regulatory,Two-factor authentication required for all users with PHI access,must,US-204,TC-504,DEF-601,Sprint-2,R1.0,Released,HIPAA-164.308(a)(5),evidence/r1-2fa-rollout-signoff.pdf
REQ-005,interview,Care coordinators triage incoming patient cases by SLA,must,US-205|US-206,TC-505|TC-506,,Sprint-2,R1.0,Released,,
REQ-006,interview,Care plan templates surfaced on patient record page,should,US-207,TC-507,,Sprint-3,R1.0,Released,,
REQ-007,regulatory,Audit log exported monthly to long-term archive,must,US-208,TC-508,,Sprint-3,R1.0,Released,HIPAA-164.312(b),evidence/r1-audit-export-runbook.pdf
REQ-008,sow,Patient consent captured before sharing record with external provider,must,US-209,TC-509,,Sprint-3,R1.0,Released,HIPAA-164.508,evidence/r1-consent-flow-uat.pdf
```

**Why it works:** Every regulatory row pairs a HIPAA control ID with a concrete evidence artifact. The auditor can sample any control and walk to the test result that proves it. Non-regulatory rows leave the compliance columns blank — the schema is consistent, the data is sparse only where applicable.

---

## Example 3: Post-Release Defect Column Populated (Hypercare Snapshot)

**Context:** A Service Cloud rollout went live three weeks ago. Hypercare is in progress. The BA is preparing the Steerco rollup that shows which requirements are stable and which are still seeing defects.

**Problem without an RTM:** Defects are tracked in Jira, but Steerco wants "which requirements are flaky?" not "which stories have open defects?" Without backward linkage from defect → story → requirement, the answer takes a day to compile. With the RTM, the `defect_ids` column tells the story directly.

**Solution (CSV excerpt with defect linkage):**

```csv
req_id,source,description,priority,story_ids,test_case_ids,defect_ids,sprint,release,status
REQ-001,interview,Cases auto-assign to support queue based on product,must,US-301,TC-401,,Sprint-1,R1.0,Released
REQ-002,interview,SLA timer pauses when case is in Awaiting Customer status,must,US-302,TC-402,DEF-701|DEF-702|DEF-705,Sprint-1,R1.0,Released
REQ-003,sow,Knowledge article suggestions surface on case record page,should,US-303,TC-403,DEF-703,Sprint-2,R1.0,Released
REQ-004,interview,Escalation rule fires after 24h of no agent response,must,US-304|US-305,TC-404|TC-405,,Sprint-2,R1.0,Released
REQ-005,interview,Customer satisfaction survey emailed on case close,should,US-306,TC-406,DEF-704,Sprint-3,R1.0,Released
REQ-006,change-request,Agent scripting widget surfaces on case page,could,US-307,TC-407,,Sprint-3,R1.0,Released
REQ-007,interview,Case merging preserves all comments and attachments,must,US-308,TC-408,,Sprint-3,R1.0,Released
REQ-008,interview,Mobile agents can update cases offline and sync later,could,,,,,, Deferred
```

**Steerco rollup derived from this RTM:**

- `REQ-002` (SLA timer): 3 defects raised in hypercare. Owner: Service Cloud lead. Action: investigate timer-pause logic. **Flaky — escalate.**
- `REQ-003` (Knowledge suggestions): 1 defect, low severity. Owner: knowledge admin. **Stable, monitoring.**
- `REQ-005` (CSAT survey): 1 defect, fixed in hotfix. **Stable, closed.**
- All other released requirements: **stable, no defects.**
- `REQ-008`: deferred to R1.1 backlog. **Tracked, not in scope for hypercare.**

**Why it works:** The defect column makes the "which requirements are flaky?" question a one-line filter (`defect_ids != empty`), and the count of defect IDs per row gives the severity proxy. Steerco gets the rollup in five minutes, not a day.

---

## Anti-Pattern: RTM as Title Index Instead of ID Matrix

**What practitioners do:** Build the RTM with a `requirement_title` column and no `req_id`. They reason "the title is descriptive enough, why add an opaque ID?"

**What goes wrong:**
- Two requirements with similar titles (e.g., "Case auto-assignment" and "Case auto-assignment by region") collide in joins.
- A requirement title gets edited mid-flight (e.g., scope refinement) and the row no longer matches the original requirement doc.
- Defects, stories, and tests cannot reliably link to a stable key.

**Correct approach:** Always assign a stable, immutable `req_id` (e.g., `REQ-001`) at elicitation time. The title is a description column for human readability; the ID is the join key.

The collision, made concrete — the same two requirements written both ways:

```csv
# WRONG — title is the key. These two rows collide on every join, and editing either
# title mid-sprint silently detaches the row from the requirements document.
requirement_title,story_ids,test_case_ids,status
Case auto-assignment,US-301,TC-401,Released
Case auto-assignment by region,US-311,TC-411,In UAT

# RIGHT — the id is the key, the title is a column. Both prefixes are legal keys
# (see SKILL.md "REQ-XXX <-> FG-XXX"), so a fit-gap-led project keys on FG- instead.
req_id,source,description,priority,story_ids,test_case_ids,defect_ids,sprint,release,status
REQ-021,interview,Case auto-assignment,must,US-301,TC-401,,Sprint-1,R1.0,Released
FG-034,sow,Case auto-assignment by region,should,US-311,TC-411,,Sprint-3,,In UAT
```

Run `python3 scripts/check_rtm.py --file rtm.csv` on the first block and it stops at check 1:
`missing required columns for the audit schema: req_id, source, description, priority, defect_ids,
sprint, release`. A title-keyed matrix is not a lightweight RTM — it is a different document.

---

## `--file` on a path that is not there is a failure

```bash
python3 scripts/check_rtm.py --file build/traceability.md   # exit 1 when the file is absent
python3 scripts/check_rtm.py --manifest-dir build/          # exit 0 when no matrix exists yet
```

Naming a file that was never written is a broken invocation, so it exits 1 with
an ERROR — a build step whose `traceability.md` was never produced must not pass
its own acceptance test. Discovery through `--manifest-dir` stays lenient,
because "this project has no RTM yet" is a real state and not an error.
