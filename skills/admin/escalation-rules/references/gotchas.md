# Gotchas — Escalation Rules

Non-obvious Salesforce platform behaviors that cause real production problems.

## Gotcha 1: The Time-Based Engine Is Not Real-Time

**What happens:** An escalation set to fire after 4 hours does not fire at exactly the 4-hour mark. The Salesforce time-based workflow engine processes escalation actions in batches, approximately once per hour. A case that crosses the 4-hour threshold at 10:35 AM may not escalate until 11:00–11:30 AM when the engine's next pass runs.

**When it occurs:** Every time an escalation action fires. There is no way to guarantee sub-one-hour precision. This is inherent to the declarative time-based engine.

**How to avoid:** Do not commit to customers or SLAs that require minute-level escalation precision. If real-time enforcement is required, use Apex Schedulable with a short interval or Platform Events to build a near-real-time escalation path. Document this platform behavior in your SLA agreements with stakeholders.

---

## Gotcha 2: Only One Active Escalation Rule Per Org — Silently Deactivates Previous

**What happens:** When you activate a second escalation rule, Salesforce automatically deactivates the previously active rule without any warning or error message. All escalation entries and actions from the deactivated rule stop firing. Cases that were in flight against the old rule are no longer evaluated.

**When it occurs:** Whenever an admin clicks the "Active" checkbox on a new escalation rule and saves, or when importing configuration via Change Set or Metadata API with the new rule marked Active.

**How to avoid:** Always audit Setup > Escalation Rules before creating a new rule. Check which rule is currently Active. If a rule exists, add entries to it rather than creating a parallel rule. If you need to replace the rule entirely, export the old entries first, replicate them in the new rule, validate, then activate.

---

## Gotcha 3: Default Business Hours Are 24/7 — "Use Business Hours" Without Configuration Has No Effect

**What happens:** Every org has a default business hours record that runs 24 hours a day, 7 days a week. If you check "Use Business Hours" in an escalation rule entry without explicitly configuring restricted business hours, the clock still runs on weekends and overnight. Escalations fire at 3 AM Saturday as expected — because "business hours" technically include that time.

**When it occurs:** When a team configures escalation entries with "Use Business Hours" enabled but never visits Setup > Business Hours to restrict the working window.

**How to avoid:** After enabling "Use Business Hours" on a rule entry, immediately navigate to Setup > Business Hours and verify that the active business hours record has the correct days and times configured. The name "Default" does not mean Mon–Fri 9–5 — it means 24/7 unless changed.

---

## Gotcha 4: Reopened Cases May Escalate Immediately

**What happens:** When a case is closed, escalation stops. When it is reopened, the escalation clock does not restart — it resumes from where it left off based on the case's original creation date (if that is the age-over setting). A case that was open for 6 hours, closed, and reopened 2 weeks later may immediately fire escalation actions if the rule threshold is 4 hours.

**When it occurs:** Any time cases are closed and reopened. Common in support orgs that close cases optimistically and reopen when customers reply.

**How to avoid:** If your support process regularly reopens cases and you want to give agents a fresh escalation window after reopening, configure the rule entry to use "Last Modified Date" as the age-over basis instead of creation date. This resets the clock each time the case is updated — including on reopen. Be aware that this also means any agent activity on a case resets the escalation clock.

---

## Gotcha 5: Entry Criteria Must Match Exact Field Values Used in Production

**What happens:** An escalation entry with criteria `Priority equals High` never fires because the org's picklist has values `High`, `Medium`, `Low` but cases are being created with `1-High`, `2-Medium`, `3-Low` from a legacy import. The criteria never match — cases are silently never evaluated.

**When it occurs:** After data migrations, picklist value changes, or when building rules in a sandbox that has slightly different picklist values than production.

**How to avoid:** Before finalizing rule entry criteria, inspect the actual field values in production using a report or SOQL: `SELECT Priority, COUNT(Id) FROM Case GROUP BY Priority`. Ensure the criteria values match exactly.
