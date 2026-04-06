# Gotchas — SLA Design and Escalation Matrix

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Business Hours Must Be Configured on Both the Entitlement Process AND Each Escalation Rule Entry — They Are Independent

**What happens:** An admin correctly sets Business Hours on the entitlement process, which makes the milestone clock respect working hours. However, the escalation rule entries do not have Business Hours populated. The escalation rule's time-based evaluation runs on calendar hours 24/7. A case that hits the 4-calendar-hour mark at 2 AM Saturday triggers a manager escalation email in the middle of the night, even though the milestone clock has not moved because business hours are paused.

**When it occurs:** Any implementation where both entitlement process milestones and escalation rules are in use for the same cases. This is the most common SLA configuration defect in Service Cloud implementations. It is invisible in sandbox testing unless tests are run outside business hours.

**How to avoid:** Use the Business Hours Mapping Table artifact (from this skill) as a configuration checklist. The table must have a row for every entitlement process AND a row for every escalation rule entry. Both rows must reference the same Business Hours record for the same tier. Review both locations in Setup before marking SLA configuration complete.

---

## Gotcha 2: The "Default" Business Hours Record Is 24/7 Until Manually Changed

**What happens:** Every Salesforce org ships with a Business Hours record named "Default" that is configured as 24/7, Monday through Sunday, midnight to midnight. An admin who selects "Default" as the Business Hours for an entitlement process or escalation rule entry while intending to restrict tracking to Mon–Fri 9–5 gets 24/7 behavior. The milestone clock never pauses overnight or on weekends. Agents return on Monday morning to cases that have been in breach since Saturday.

**When it occurs:** When an admin uses the "Default" record without verifying its configuration. This is especially common after an org is newly provisioned — no one has changed the Default record, so it silently runs 24/7.

**How to avoid:** In the design artifact, never reference "Default" by name — always specify the Business Hours record name explicitly (e.g., "US Support M-F 9am-5pm PST"). Create named records with descriptive names and verify their day and time settings in Setup > Business Hours before referencing them in the design. During design review, verify the actual configuration of any Business Hours record referenced by name.

---

## Gotcha 3: Milestone Entry Criteria Use AND Logic Only — OR Conditions Require Separate Milestones

**What happens:** A practitioner designs a milestone that should apply to "Priority equals High OR Priority equals Critical." In Salesforce milestone entry criteria, the condition logic is AND-only. Adding two criteria for Priority creates an AND condition (Priority = High AND Priority = Critical), which can never be true simultaneously. The milestone never starts for any case. No error is displayed — cases simply process without the milestone tracking, and SLA compliance appears perfect in reports because no milestones are entered.

**When it occurs:** When a tier design assumes one milestone can cover multiple priority values using OR logic. This is a natural design assumption that does not match the platform's declarative behavior.

**How to avoid:** Design one milestone per priority level (or per distinct entry condition set). In the milestone configuration plan artifact, document the exact entry criteria for each milestone using AND-only language. If a tier has four priority levels, design four milestones with individual entry criteria per priority. The 10-milestone-per-process limit accommodates this (4 priorities x 2 milestones for First Response and Resolution = 8 milestones, within the 10 limit).

---

## Gotcha 4: Milestone Actions Fire in Batch — Sub-One-Hour Precision Is Not Achievable Declaratively

**What happens:** A milestone is configured to send a warning email at 90% of a 1-hour first-response target. Stakeholders expect this warning to arrive at 54 minutes. In practice, Salesforce's time-based workflow engine processes milestone actions in batch cycles (approximately every 15–60 minutes depending on queue load). The warning may arrive at 50 minutes or at 75 minutes. For a P1 case with a 30-minute target, the entire first-response window may pass before the engine processes the 50% or 75% action.

**When it occurs:** Any time SLA targets are short (under 1 hour) or when precise notification timing is required. The impact is worst for high-urgency tiers with short SLA windows.

**How to avoid:** Document in the escalation matrix that milestone action timing has a platform-inherent variance of up to 60 minutes. For tiers with sub-30-minute SLA targets (e.g., a Platinum tier with a 15-minute first response), recommend custom Apex Schedulable classes or Platform Events as the notification mechanism. Declarative milestones are appropriate for SLAs of 2 hours or more.

---

## Gotcha 5: Multiple Active Entitlements on the Same Account Breaks Auto-Assignment

**What happens:** An Account has two active entitlements — one for "Product A Support: Enterprise" and one for "Product B Support: Enterprise." When a case is created on this Account, Salesforce entitlement auto-assignment picks one entitlement arbitrarily (or fails silently if ambiguity resolution is not configured). The wrong entitlement is assigned, the wrong milestone targets apply, and the case is tracked against the wrong SLA tier. This goes unnoticed until a case escalation threshold fires unexpectedly early or late.

**When it occurs:** In multi-product implementations where customers have purchased support for multiple products at different SLA levels, or when entitlement records are not expired or closed after renewal.

**How to avoid:** Design the entitlement model so each Account has at most one active entitlement per product line. If multi-product SLAs are required, use entitlement auto-assignment validation logic (a Flow on case creation) that selects the correct entitlement based on the case's product or record type field. Include an explicit deactivation/expiration policy in the SLA design: old entitlements must be set to inactive when renewed or superseded, to prevent duplicate active entitlements on the same account.

---

## Gotcha 6: Changing a Milestone's Time Target Does Not Update In-Flight Cases

**What happens:** The support operations team changes a milestone time target from 4 hours to 2 hours (SLA tightening after a contract renegotiation). Cases that were already created and have already entered the milestone continue tracking against the original 4-hour target. Only new cases created after the entitlement process is re-activated pick up the 2-hour target. The team believes all cases are now on 2-hour SLAs but in-flight cases are still on 4-hour targets.

**When it occurs:** Any time a milestone target is changed mid-implementation or after go-live, which is common during contract renewals or SLA revisions.

**How to avoid:** Document in the SLA design that milestone target changes take effect only for new cases. When changing SLA targets, design a communication plan for the support team: existing open cases remain on the old SLA, new cases pick up the new SLA. If immediate migration of in-flight cases is required, close and re-open them, or use a bulk data update to the Case Milestone record's TargetDate field (Apex or Data Loader).
