# Answer key for the clarification gate (G1)

Use these when the clarifier asks; anything not listed here, accept the clarifier's proposed
default and note it under assumptions. Source: skills/admin/case-management-setup/references/worked-example-case-intake.md § 1.

| Topic | Answer |
|---|---|
| Mailbox ownership | IT owns the forwarding rules for support@ and billing@. |
| Unmatched cases | Go to the Tier 1 General queue. |
| Queue notifications | Tier 1 uses Omni-Channel push, so no queue email; Billing wants the queue address emailed. |
| Other writers of OwnerId | None today; Omni-Channel will, by design. |
| Acknowledgement | Yes, from support@acme.example, for both channels, including the case number. |
| Region at creation | From the account's Region__c; unknown accounts default to US. US is the default calendar. |
| Reply identity | Tier 1 replies from support@; billing@ replies from billing@. |
| Proof before go-live | Sandbox test with real inbound email, a clock test, and a loop test. |
| Queue membership | By role and public group, no named users (monthly churn; usernames do not deploy). |
