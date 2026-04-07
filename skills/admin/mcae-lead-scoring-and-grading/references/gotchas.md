# Gotchas — MCAE Lead Scoring and Grading

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Manual Score or Grade Override Silently Blocks Automatic Updates

**What happens:** When an MCAE admin edits a prospect's score or grade directly in the MCAE UI (via the prospect record), MCAE marks that record as "manually overridden." From that point forward, automated scoring activities — form fills, email clicks, page views — no longer increment or decrement the score. Decay rules also stop applying. The score is frozen at the manually set value indefinitely.

**When it occurs:** Any time an admin directly edits the Score or Grade field on a prospect record in the MCAE UI. This is often done as a quick fix to push a borderline prospect over the MQL threshold or to zero out a stale record.

**How to avoid:** Establish a formal policy that manual overrides are documented with a reason and reviewed quarterly. Use MCAE's override indicator (visible on the prospect record under Scoring) to audit overridden records. To re-enable automatic scoring for an overridden prospect, the admin must explicitly clear the manual override in the prospect record UI. Do not use manual overrides as a routine operational tool — if a threshold needs adjusting, change the automation rule, not individual prospect scores.

---

## Gotcha 2: Activating an Automation Rule Retroactively Floods the Queue

**What happens:** When you activate an MCAE Automation Rule, the rule immediately evaluates all existing prospects in the database — not just prospects who meet the criteria after the activation date. If the rule assigns prospects to a Salesforce queue, activating it on a database of tens of thousands of prospects can instantly push thousands of records to the Sales queue, overwhelming SDRs and potentially creating duplicate tasks or CRM records.

**When it occurs:** Most dangerous when activating a new MQL routing rule on a mature MCAE database. Also occurs when re-activating a previously paused rule after a long inactive period.

**How to avoid:** Before activating any automation rule that triggers an assignment or notification action, add a temporary date filter: "Prospect created date is after [today - 90 days]" or "Prospect added to list [recently active list]." Run the rule in narrow scope first, verify the output, then broaden the criteria. Alternatively, export the prospects who would match the rule before activation and review the list with Sales before going live.

---

## Gotcha 3: Score Decay Does Not Trigger Automation Rules or Completion Actions

**What happens:** Score decay silently reduces a prospect's score on a scheduled basis. When decay drops a prospect's score below the MQL threshold (e.g., from 105 to 95), no automation rule fires to remove the prospect from the MQL list, notify Sales, or update any field. The CRM record continues to show the decayed score after the next sync, but there is no active alert or workflow triggered by the decay event itself.

**When it occurs:** Any time a decay rule fires and a prospect's score crosses a threshold (upward or downward) as a result. This is the expected platform behavior — decay is intentionally silent to avoid triggering a cascade of actions for thousands of records simultaneously.

**How to avoid:** Build a separate "MQL Recycle" automation rule that fires when: Prospect Score < [MQL threshold] AND Prospect is a member of [MQL Salesforce Campaign]. This rule removes the prospect from the MQL campaign, reassigns them to a nurture queue, and optionally notifies Sales of the recycle. Run this rule on a "repeat" setting to catch all decayed MQLs. Document this recycle rule as a required companion to the MQL promotion rule.

---

## Gotcha 4: Grade Does Not Update in Real-Time When Profile Criteria Fields Change

**What happens:** MCAE evaluates profile criteria and recalculates grade when a prospect's field values are synced. If the relevant fields (e.g., Job Title, Industry, Number of Employees) are updated directly in Salesforce CRM and synced to MCAE, the grade will update during the next sync cycle. However, grade is not instantly recalculated on every keystroke or field change — it depends on the sync schedule. During the window between the field update and the next sync, the prospect's grade in MCAE may be stale.

**When it occurs:** Most visible during prospecting events where Sales enriches Contact or Lead records in bulk (e.g., after a trade show import), then expects MCAE grade to reflect the enriched data immediately.

**How to avoid:** Set sync expectations clearly with Sales. The MCAE CRM connector sync runs on a roughly 5-minute cycle for prospect-level changes, but batch imports or bulk updates may take longer to process. Do not design workflows that depend on near-instant grade recalculation after CRM field updates.

---

## Gotcha 5: A Prospect Can Only Match One Profile, But Profile Selection Is Automatic and Non-Obvious

**What happens:** MCAE assigns each prospect to the profile whose criteria it best matches (most criteria satisfied). If two profiles have overlapping criteria, the assignment can be unpredictable — MCAE does not expose which profile a prospect was matched to in a prominent way, and there is no conflict resolution rule admins can configure. The default profile is used only when no other profile has any matching criteria.

**When it occurs:** Orgs that create multiple profiles without carefully isolating their criteria will see prospects graded by the "wrong" profile. A mid-market prospect who happens to be in Technology might match an Enterprise profile's industry criterion alone and get graded against Enterprise ICP standards — resulting in an artificially low grade.

**How to avoid:** Design profiles with mutually exclusive primary criteria (e.g., use employee count ranges that don't overlap between SMB and Enterprise profiles). Review a sample of prospect-to-profile assignments after configuring new profiles by checking individual prospect records. Use the profile's most discriminating criterion (usually employee count or account tier) as the first and most heavily weighted criterion to ensure correct matching.

---

## Gotcha 6: Score Sync to Salesforce Requires Explicit Field Mapping in the Connector

**What happens:** MCAE prospect score and grade exist as internal MCAE fields. They do not automatically appear on Salesforce Lead or Contact records unless the MCAE CRM connector field mapping explicitly maps them. A common setup oversight is to configure scoring correctly in MCAE but never add Score and Grade to the connector field mapping, leaving Salesforce with blank or stale score-related fields and making CRM-side reporting on MQLs impossible.

**When it occurs:** During initial MCAE setup or when adding scoring to an org that previously used MCAE only for email sends. Also occurs when the Salesforce org is re-provisioned or the connector is reset.

**How to avoid:** As part of the scoring configuration checklist, always verify the field mapping in Admin > Connectors > Salesforce Connector > [Edit Field Mapping]. Confirm that Score maps to a Lead/Contact integer field and that Grade maps to a Lead/Contact text or picklist field. Run a test prospect through the full flow and check that the CRM record reflects the correct values after sync.
