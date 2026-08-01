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
    - admin/connected-apps-and-auth
    - admin/integration-admin-connected-apps
    - admin/integration-user-management
    - admin/remote-site-settings
    - apex/apex-jwt-bearer-flow
    - architect/integration-framework-design
    - architect/integration-security-architecture
    - integration/api-governance-and-rate-limits
    - integration/api-versioning-strategy
    - integration/change-data-capture-integration
    - integration/connect-rest-api-patterns
    - integration/data-cloud-zero-copy-federation
    - integration/middleware-integration-patterns
    - integration/mutual-tls-callouts
    - integration/named-credentials-setup
    - integration/oauth-flows-and-connected-apps
    - integration/outbound-messages-and-callbacks
    - integration/platform-events-integration
    - integration/private-connect-setup
    - integration/pub-sub-api-patterns
    - integration/rest-api-patterns
    - integration/salesforce-connect-external-objects
    - integration/salesforce-data-pipeline-etl
    - integration/soap-api-patterns
    - integration/streaming-api-and-pushtopic
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

Breadth note (`AGENT_CONTRACT.md` Mandatory Reads rule 4): 27 skill reads, just above the 8–25 design target. The deliverable is an inventory, and an inventory is judged by what it fails to list — an endpoint archetype this agent cannot name is an endpoint it silently omits, and the omission looks identical to a clean org. The classification section therefore carries one read per archetype the platform can egress through (REST, SOAP, Platform Events, CDC, Pub/Sub, streaming, external objects, outbound messages, Connect, and lakehouse ETL) rather than the subset an average org happens to use.

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
3. `AGENT_RULES.md`

### The catalog surface — what is being inventoried
4. `skills/admin/integration-admin-connected-apps` — Connected App inventory: what each row means and which fields carry the posture signal
5. `skills/admin/connected-apps-and-auth` — OAuth scope and policy semantics, so a Connected App is scored rather than just listed
6. `skills/admin/remote-site-settings` — Remote Sites are the legacy half of the catalog and the ones most likely to be stale
7. `skills/integration/named-credentials-setup` — the modern endpoint record — external credential / principal split changes what 'who owns this' means
8. `skills/admin/integration-user-management` — maps each endpoint to the integration user and PSG that actually exercises it
9. `skills/integration/oauth-flows-and-connected-apps` — the flow chosen per endpoint is the single biggest posture score input
10. `skills/apex/apex-jwt-bearer-flow` — JWT bearer flow for server-to-server auth, signed assertions — the flow most often mis-scored as password-grant
11. `skills/security/connected-app-security-policies` — IP relaxation, refresh policy and admin-approval settings that turn a working endpoint into an exposed one
12. `skills/security/certificate-and-key-management` — certificate expiry is the rotation-overdue signal; without it the age score is a guess
13. `skills/integration/mutual-tls-callouts` — mTLS via Named Credentials — a certificate-backed endpoint that expires fails closed and silently
14. `skills/integration/private-connect-setup` — Hyperforce private networking — an endpoint on Private Connect has a different exposure profile from the same URL over the internet

### Classifying what each endpoint does
15. `skills/integration/rest-api-patterns` — the default classification for an outbound endpoint, and the request shape to expect in referencing Apex
16. `skills/integration/soap-api-patterns` — legacy SOAP endpoints carry WSDL-generated stubs the reference scan must recognise
17. `skills/integration/platform-events-integration` — event-based integrations have no Named Credential at all; without this they are missing from the catalog
18. `skills/integration/change-data-capture-integration` — CDC subscriptions are an egress path that no endpoint inventory surfaces on its own
19. `skills/integration/pub-sub-api-patterns` — the gRPC subscriber surface, and how to tell a live subscriber from an abandoned one
20. `skills/integration/streaming-api-and-pushtopic` — PushTopic and generic streaming are the deprecated predecessors most likely to be unused deprecation candidates
21. `skills/integration/salesforce-connect-external-objects` — external data sources are endpoints with their own auth records, easy to miss entirely
22. `skills/integration/outbound-messages-and-callbacks` — outbound messages carry their own endpoint URL and session id — a credential path outside every other inventory
23. `skills/integration/middleware-integration-patterns` — when one Named Credential fronts a whole middleware estate, the catalog must say so rather than record one endpoint
24. `skills/integration/data-cloud-zero-copy-federation` — Lakehouse Federation connectors (Snowflake/Databricks/BigQuery/Redshift) — auth surface, rotation hazards, governance inheritance
25. `skills/integration/connect-rest-api-patterns` — Chatter / CMS / Experience Cloud traffic hits /connect/ resource paths rather than SObject rows, so a reference scan keyed on object names misses these consumers entirely; Connect also respects sharing where the equivalent SObject query would not, which changes the endpoint's posture score
26. `skills/integration/salesforce-data-pipeline-etl` — a lakehouse feed is not one REST endpoint but a Bulk API 2.0 snapshot plus a standing CDC delta subscription; cataloguing only the half that owns the credential under-reports the largest bulk-egress path in the org

### Governance & scoring
27. `skills/integration/api-versioning-strategy` — contract evolution + sunset policy — the age dimension of the score
28. `skills/integration/api-governance-and-rate-limits` — 24h allocation governance; a catalog without consumption context cannot prioritise cleanup
29. `skills/architect/integration-framework-design` — the target-state shape the cleanup list should move the org toward
30. `skills/architect/integration-security-architecture` — the posture rubric the findings are graded against

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
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
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
