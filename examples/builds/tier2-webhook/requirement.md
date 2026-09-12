# Requirement — Tier 2 escalation webhook and event

When a Case is escalated to the Tier 2 Engineering queue, Salesforce must notify our on-call tool (PagerDuty-style,
HTTPS REST endpoint, API-key authentication) within a minute, with the case number, severity, subject and a link back
to the case. The same escalation must also publish an event that our internal ops dashboard (a separate system already
subscribed to Salesforce platform events) can consume. Retries and a visible failure record are required: if the
webhook call fails, an admin must be able to see it and re-send. No customer-facing change. The on-call tool's API key
must never be stored in code or in a custom setting.

Asked by: Support Engineering lead (Pranav), 2026-09-12. Existing org has the case-intake build (queues, escalation
rule) but this build is designed standalone; it may assume a queue named Tier_2_Engineering exists.
