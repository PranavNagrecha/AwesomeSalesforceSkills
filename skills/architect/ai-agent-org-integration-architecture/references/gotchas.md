# Gotchas — AI Agent to Salesforce Org Integration Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Per-Org API Limit Covers All Consumers Including Agents

**What happens:** Salesforce enforces a daily API call limit at the org level (not per-user). The limit is calculated based on the number of full-use licenses in the org (typically 1,000 calls per license per 24-hour period for Enterprise Edition). An AI agent making hundreds of calls per hour can consume API budget that blocks human users, other integrations, and scheduled jobs from completing their work.

**When it occurs:** When an AI agent is deployed without estimating its expected call volume and comparing it against the available org limit. High-volume agents (batch classification pipelines, polling-based agents) are the highest risk.

**How to avoid:** Query the current API limit via `GET /services/data/vXX.0/limits/` and check `DailyApiRequests.Remaining` before deploying a high-volume agent. Set up an alert (via the Salesforce Limit REST endpoint or Event Monitoring) to notify admins when the remaining limit drops below a safe threshold. Design agents to batch SOQL queries where possible (a single query returning 200 records uses 1 API call, not 200).

---

## Gotcha 2: CDC Event Retention Is 24 Hours

**What happens:** Change Data Capture events are stored in the event bus for only 24 hours. If an AI pipeline subscriber goes offline for more than 24 hours (maintenance, crash, deployment), it misses events that were published during the outage. There is no built-in replay beyond 24 hours and no dead letter queue.

**When it occurs:** Any time a Platform Events or CDC-based AI pipeline has an outage of more than 24 hours. Also relevant for deployment windows that take longer than expected.

**How to avoid:** Design a "catch-up" mechanism: a scheduled Apex job or batch class that identifies records in the expected processing state but with no AI output, and requeues them for processing. Test the recovery flow explicitly before go-live. Document the maximum acceptable outage window in the architecture decision record.

---

## Gotcha 3: Field History Tracking Does Not Record the Human Requester

**What happens:** When an AI agent updates a Salesforce record via the service account (Client Credentials OAuth), the Field History Tracking log shows the service account user as the record modifier, not the human who interacted with the AI client. In audit-sensitive environments (financial services, healthcare), regulators may require that record changes be attributed to the responsible human, not a system user.

**When it occurs:** Any time a shared service account (Client Credentials flow) is used for AI agent operations on records subject to audit or compliance requirements.

**How to avoid:** For audit-sensitive record types, consider using Web Server OAuth flow (user-delegated tokens) so the AI agent operates with the end user's identity. Alternatively, implement a custom audit object that captures the human's identity, the AI agent's action, and the resulting record change in a separate log. Document the audit strategy as part of the architecture decision.

---

## Gotcha 4: Sharing Rules Apply to the Service Account's Record-Level Access

**What happens:** SOQL queries via the REST API run in the sharing context of the authenticated user (the Connected App's run-as user). If the service account has a restricted role in the org's role hierarchy or is covered by sharing rules that limit its record visibility, SOQL queries will silently return fewer records than expected. The agent reports "no records found" for records that exist and are visible to other users.

**When it occurs:** When the service account is placed in a restrictive role in the role hierarchy, or when manual sharing rules or territory management limits its visibility.

**How to avoid:** Test the service account's SOQL access explicitly in a sandbox before production deployment. Run the same SOQL queries authenticated as the service account and as a System Administrator and compare result counts. If broader access is needed, either adjust the service account's role/sharing settings or use `without sharing` in the Apex endpoint class (document the tradeoff explicitly).

---

## Gotcha 5: Named Credentials Require Explicit External Callout Permissions

**What happens:** If Salesforce Apex code needs to call back to an external AI service (bidirectional integration), Named Credentials must be used for the outbound callout. Without explicit Remote Site Settings or Named Credential configuration, Apex callouts to external URLs fail with "Unauthorized endpoint" errors even if the URL is correct.

**When it occurs:** When a bidirectional architecture is designed (Salesforce triggers → Apex → external AI API → result → Salesforce update) without configuring the outbound callout permissions in advance.

**How to avoid:** Design the outbound callout path during architecture (not implementation). Create Named Credentials for each external AI API endpoint. Ensure the Named Credential's authentication settings match the AI provider's requirements (API key in header, OAuth 2.0, JWT). Test callouts in sandbox before production deployment.
