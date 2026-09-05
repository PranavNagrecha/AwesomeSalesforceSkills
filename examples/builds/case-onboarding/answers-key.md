# Answer key for the clarification gate (G1)

Use these when the clarifier asks; anything not listed here, accept the clarifier's proposed
default and note it under assumptions. Source: skills/admin/case-management-setup/references/worked-example-case-intake.md § 1.

| Topic | Answer |
|---|---|
| Mailbox ownership | IT owns the forwarding rules for support@ and billing@. |
| Unmatched cases | Go to the Tier 1 General queue. |
| Queue notifications | Tier 1 uses Omni-Channel push, so no queue email; Billing wants the queue address emailed. |
| Other writers of OwnerId | None today. By design after go-live: Omni-Channel (Tier 1 push) and the 8-business-hour escalation rule (reassigns to Tier 2). |
| Acknowledgement | Yes, from support@acme.example (an org-wide email address, never the Email-to-Case routing address itself), for both channels, including the case number. Loop risk is covered by the sandbox loop test. |
| Region at creation | From the account's Region__c; unknown accounts default to US. US is the default calendar. |
| Reply identity | Tier 1 replies from support@; billing@ replies from billing@. |
| Proof before go-live | Sandbox test with real inbound email, a clock test, and a loop test. |
| Queue membership | By role and public group, no named users (monthly churn; usernames do not deploy). |

## Dry-run log

- 2026-09-05: G1 answered by the dry-run operator on the owner's behalf — 9 from this key, 18 from requirement.md, 45 proposed defaults accepted, 25 deferred (no default, no source). Finance case visibility (routing only vs sharing restriction) is one of the deferred items; the planner must record it as an assumption.
