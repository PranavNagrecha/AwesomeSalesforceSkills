# Examples: Email Templates and Alerts

---

## Example: Case SLA Breach Email Alert

**Requirement:** Notify the case owner and support manager when a high-priority case is about to breach SLA.

**Pattern:**
- Trigger: Record-Triggered Flow with strict entry criteria
- Mechanism: Email Alert
- Sender: Org-Wide Email Address `support@example.org`
- Template: `Case_SLA_Breach_Warning`

**Subject example:**
```text
SLA warning: Case {!Case.CaseNumber} is nearing breach
```

**Why this works:** One operational event, one transactional email, clear sender identity.

---

## Example: Approval Reminder Template

**Requirement:** Send approvers a reminder with the essential record context, not the full novel.

**Body structure:**
- what needs review,
- why it needs approval,
- key values,
- link to record,
- clear next action.

```text
Opportunity {!Opportunity.Name} requires discount approval.
Discount requested: {!Opportunity.Discount_Percent__c}
Amount: {!Opportunity.Amount}
Open record: {!Opportunity.Link_To_Record__c}
```

**Rule:** Approval reminders should reduce friction, not restate the entire record page.

---

## Example: Internal Status Change Alert With Duplicate-Email Protection

**Requirement:** Notify account managers when onboarding status changes to `Ready for Handoff`.

**Trigger rule:**
```text
Only send when Status changes TO Ready for Handoff
and Prior Status was not Ready for Handoff
```

**Why this matters:** Without the prior-value check, later edits on the same record keep sending the same email.

---

## Running the template checker on these files

```bash
python3 skills/admin/email-templates-and-alerts/scripts/check_email_templates.py --manifest-dir force-app/main/default
```

`--manifest-dir` is an alias of the positional path, so `check_email_templates.py force-app/main/default/email` is equivalent. Only `*.email`, `*.email-meta.xml`, and body files under an `email/` directory are linted — a `sender-identity-note.md` or deploy-order note beside the templates is documentation, not a template, and is skipped. REVIEW findings print and exit 0; `--strict` makes them exit 1. Exit 1 without `--strict` means an ERROR: the paths matched no template artefact, or a `.email-meta.xml` will not parse.
