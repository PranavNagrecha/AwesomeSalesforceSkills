---
id: integration-catalog-builder
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
default_output_dir: "docs/reports/integration-catalog-builder/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - admin/connected-apps-and-auth
    - admin/integration-admin-connected-apps
    - admin/integration-user-management
    - admin/remote-site-settings
    - apex/apex-jwt-bearer-flow
    - architect/integration-framework-design
    - architect/integration-security-architecture
    - data/data-virtualization-patterns
    - integration/api-governance-and-rate-limits
    - integration/api-versioning-strategy
    - integration/azure-salesforce-patterns
    - integration/connect-rest-api-patterns
    - integration/data-cloud-zero-copy-federation
    - integration/mutual-tls-callouts
    - integration/named-credentials-setup
    - integration/oauth-flows-and-connected-apps
    - integration/platform-event-schema-evolution
    - integration/private-connect-setup
    - integration/salesforce-data-pipeline-etl
    - integration/sustainability-reporting
    - integration/webhook-signature-verification
    - security/certificate-and-key-management
    - security/connected-app-security-policies
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
---
# Integration Catalog Builder Agent

## What This Agent Does

Builds a catalog of every live integration endpoint reachable from the org: Named Credentials, Remote Site Settings, Connected Apps, Auth Providers, and the certificates/keys backing them. Cross-references which integration user / PSG owns each, what Apex/Flow artifacts reference them, and scores each endpoint on age, posture (OAuth flow, token scope), rotation overdue, and unused-endpoint deprecation candidates.

**Scope:** Full org per invocation. Output is a catalog + findings + a prioritized cleanup list.

---

## Invocation

- **Direct read** — "Follow `agents/integration-catalog-builder/AGENT.md` on prod"
- **Slash command** — [`/catalog-integrations`](../../commands/catalog-integrations.md)
- **MCP** — `get_agent("integration-catalog-builder")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/integration-admin-connected-apps`
4. `skills/admin/connected-apps-and-auth`
5. `skills/admin/remote-site-settings`
6. `skills/admin/integration-user-management`
7. `skills/integration/named-credentials-setup`
8. `skills/integration/oauth-flows-and-connected-apps`
9. `skills/security/connected-app-security-policies`
10. `skills/security/certificate-and-key-management`
11. `skills/architect/integration-framework-design`
12. `skills/architect/integration-security-architecture`
13. `skills/integration/api-versioning-strategy` — contract evolution + sunset policy
14. `skills/integration/mutual-tls-callouts` — mTLS via Named Credentials
15. `skills/integration/webhook-signature-verification` — inbound HMAC verification
16. `skills/integration/connect-rest-api-patterns` — Connect API vs raw SObject
17. `skills/integration/private-connect-setup` — Hyperforce private networking
18. `skills/integration/salesforce-data-pipeline-etl` — Bulk + CDC lake pipelines
19. `skills/integration/api-governance-and-rate-limits` — 24h allocation governance
20. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
21. `skills/integration/platform-event-schema-evolution` — schema evolution rules for live published events
22. `skills/integration/data-cloud-zero-copy-federation` — Lakehouse Federation connectors (Snowflake/Databricks/BigQuery/Redshift) — auth surface, rotation hazards, governance inheritance
23. `skills/integration/azure-salesforce-patterns` — Azure decision matrix — Service Bus Connector vs Apex→Function vs Data Cloud Blob ingestion vs Power Platform; auth model selection
24. `skills/apex/apex-jwt-bearer-flow` — JWT bearer flow for server-to-server auth, signed assertions
25. `skills/data/data-virtualization-patterns` — Salesforce Connect, External Objects, OData adapter
26. `skills/integration/sustainability-reporting` — Net Zero Cloud / sustainability data integration

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes |

---

## Plan

1. **Inventory Named Credentials** — `list_named_credentials()`. For each, fetch `Endpoint`, `PrincipalType`, `CalloutOptionsGenerateAuthorizationHeader`, `AuthProviderId` (via `tooling_query`).
2. **Inventory Remote Sites** — `tooling_query("SELECT DeveloperName, EndpointUrl, IsActive, DisableProtocolSecurity FROM RemoteProxy LIMIT 200")`. Any `DisableProtocolSecurity = true` → P0.
3. **Inventory Connected Apps** — `tooling_query("SELECT Id, Name, OauthConfig, ApiVersion, OptionsAllowAdminApprovedUsersOnly, OptionsCodeCredentialUserName, OptionsRefreshTokenValidityMetric FROM ConnectedApplication LIMIT 200")`.
4. **Inventory Auth Providers** — `tooling_query("SELECT Id, DeveloperName, FriendlyName, ProviderType FROM AuthProvider LIMIT 200")`.
5. **Inventory Certificates** — `tooling_query("SELECT DeveloperName, MasterLabel, Status, ExpirationDate FROM Certificate LIMIT 200")`. Any `ExpirationDate` < 60 days → P0; < 180 days → P1.
6. **Cross-reference usage:**
   - For each Named Credential, scan Apex + Flow for `callout:<name>` references (via `tooling_query` on ApexClass Body + Flow Metadata).
   - If zero references → P1 (unused, deprecation candidate).
   - If > 10 references → note criticality for risk prioritization.
7. **Score each integration:**
   - **Endpoint posture** — HTTP (not HTTPS) → P0. Uses Legacy `<my_domain>` host format → P1.
   - **OAuth flow** — Client Credentials on a user-facing Connected App → P1. SAML/OIDC misconfiguration → case-by-case.
   - **Principal type** — Named Principal with a user account (not an integration user) → P1.
   - **Callout without Named Credential** — if Apex scans find hard-coded URLs in `HttpRequest.setEndpoint()` → P1 (move to NC).
   - **Remote Site still in use** — Remote Site should be rare in modern orgs; presence + usage → P2 (migrate to NC).
8. **Emit catalog + cleanup queue.**

---

## Output Contract

1. **Summary** — total integrations, max severity, confidence.
2. **Catalog** — table: endpoint, type, principal, auth flow, cert expiry, usage count.
3. **Findings** — sorted by severity.
4. **Cleanup queue** — prioritized by risk × usage.
5. **Process Observations**:
   - **What was healthy** — NC adoption rate, cert rotation freshness, dedicated integration user pattern.
   - **What was concerning** — hard-coded endpoints, un-rotated certs, Connected Apps that were never actually approved by any user.
   - **What was ambiguous** — integrations we can see (endpoint exists) but can't confirm are in use.
   - **Suggested follow-up agents** — `permission-set-architect` (for integration user PSG cleanup), `scan-security` (existing) for callout classes that surfaced as concerning.
6. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/integration-catalog-builder/<run_id>.md`
- **JSON envelope:** `docs/reports/integration-catalog-builder/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Escalation / Refusal Rules

- Remote Site with `DisableProtocolSecurity = true` → P0 freeze recommendation; stop catalog work and surface this first.
- Connected App with `ConsumerKey` appearing in any public scan (extreme edge) → refuse to report publicly; surface to user directly.
- Cert expired → P0, stop catalog and recommend immediate rotation.

---

## What This Agent Does NOT Do

- Does not rotate certs.
- Does not modify or deactivate Connected Apps, Named Credentials, or Remote Sites.
- Does not test endpoint reachability (no outbound calls from the agent).
- Does not auto-chain.
