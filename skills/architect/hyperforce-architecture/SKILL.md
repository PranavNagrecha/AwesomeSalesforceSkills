---
name: hyperforce-architecture
description: "Use when an architect must plan a Hyperforce migration, choose a Hyperforce region, validate Hyperforce-only feature dependencies, or assess data-residency and IP-allowlisting impact. Triggers: 'hyperforce migration', 'hyperforce region selection', 'first-generation infrastructure to hyperforce', 'hyperforce ip allowlisting', 'data residency on hyperforce', 'hyperforce features not on first gen'. NOT for general HA/DR strategy (use architect/ha-dr-architecture), NOT for Salesforce Functions decommission (use integration/salesforce-functions-replacement), NOT for vertical-specific data residency (use architect/health-cloud-data-residency or architect/government-cloud-compliance)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "we got a notification that our org is being migrated to hyperforce"
  - "salesforce hyperforce migration runbook checklist customer obligations"
  - "do we need to update IP allowlists when our org moves to hyperforce"
  - "hyperforce region selection data residency compliance"
  - "what features require hyperforce that are not on first generation infrastructure"
  - "hyperforce maintenance window post migration validation tests"
tags:
  - hyperforce
  - migration
  - data-residency
  - ip-allowlisting
  - region-selection
  - infrastructure
inputs:
  - "current org infrastructure (First-Generation, Hyperforce, mixed sandbox parity)"
  - "regulatory and contractual data-residency obligations"
  - "current IP-allowlist scope and downstream firewall rules"
  - "feature backlog dependent on Hyperforce-only capabilities"
outputs:
  - "Hyperforce migration readiness checklist tied to the announced migration window"
  - "region selection rationale linked to data-residency obligations"
  - "IP allowlist update plan covering customer-side firewalls and middleware"
  - "post-migration validation test plan and rollback escalation path"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Hyperforce Architecture

Activate when an architect or technical lead must reason about Hyperforce as an *infrastructure choice* — planning a migration off First-Generation infrastructure, selecting a region for a new org, validating data-residency posture, assessing whether a Hyperforce-only feature is on the roadmap. The skill produces a migration readiness checklist, a region-selection rationale, an IP-allowlist plan, and a post-migration validation test plan. It is the architect-domain counterpart to the operational mechanics of a specific migration; it does **not** answer "should we do HA/DR" (that's `architect/ha-dr-architecture`) and it does **not** decommission Salesforce Functions (that's `integration/salesforce-functions-replacement`). For health-vertical residency the answer lives in `architect/health-cloud-data-residency`; for govcloud, `architect/government-cloud-compliance`.

---

## Before Starting

- **Confirm current infrastructure.** Setup → Company Information → Instance shows the instance name; the [Salesforce Trust](https://status.salesforce.com) site discloses each instance's underlying infrastructure (First-Generation Salesforce-owned data center vs Hyperforce on AWS / Azure / GCP). Many teams misunderstand which infrastructure they're on, especially when production and sandboxes split.
- **Surface the migration trigger.** Customer-elected migrations follow a different cadence and shape than Salesforce-initiated migrations. Salesforce-initiated migrations come with a notification, a "Migration Assistance" engagement, and a fixed window. Customer-elected migrations (e.g., to land in a specific region for a new geography) require a contract change and Salesforce concierge engagement.
- **Confirm data-residency obligations.** Hyperforce regions provide *data-at-rest residency*; they do not by default provide *data-sovereignty* in the legal-process sense. Distinguish "data lives in region X" from "no party in jurisdiction Y can compel access" — they're different controls.
- **Inventory IP allowlists.** Customer-side firewalls, middleware allowlists, partner-system allowlists, and Salesforce Connect external systems all may have hard-coded First-Generation IP ranges. The Hyperforce IP ranges are different and announced via Salesforce-managed channels.

---

## Core Concepts

### What Hyperforce is (and what it is not)

Hyperforce is Salesforce's next-generation infrastructure built on major public cloud providers — AWS, Azure, and GCP. It is not a different product; the same Salesforce metadata, APIs, and configuration run on it. Three things change underneath: where the workload runs (cloud-provider region), how the platform scales (containerized services), and how trust and residency are scoped (region selection).

What Hyperforce does **not** change: the customer's metadata, configuration, integrations, customizations, custom Apex, LWC, Flows, profiles, permission sets, or sharing model. A migration is an infrastructure swap, not a re-implementation.

### Region selection and what it gives you

Hyperforce regions are scoped to the major public-cloud regions Salesforce has activated (currently a growing list: US-East, US-West, EU-Frankfurt, EU-Paris, EU-London, India, Japan, Australia, Canada, etc.). Choosing a region is choosing several things at once:

| Lever | What it determines |
|---|---|
| Data residency at rest | The cloud region where record bodies, files, and metadata persist |
| Latency profile | Round-trip time from users and integrations bounded by network distance |
| Pairing with a failover region | Salesforce-managed cross-region failover follows fixed pairing rules; pair choice determines disaster-event behavior |
| Compliance posture input | One input to GDPR Schrems II, India DPDPA, Australia Privacy Act — but not by itself sufficient |

What region selection does **not** give you: customer-controllable cross-region failover, multi-region active-active, in-region read replicas under customer control. Hyperforce manages those at platform level.

### Hyperforce-only features

A growing set of capabilities require Hyperforce and are unavailable or limited on First-Generation infrastructure:

| Capability | Hyperforce dependency |
|---|---|
| Private Connect (peering with customer AWS VPC / Azure VNet so callouts and inbound traffic never traverse the public internet) | Hyperforce only |
| Some Data Cloud regions and capabilities | Region availability follows Hyperforce |
| Certain regional editions (e.g., new EU regions) | Hyperforce only by definition |
| Newer Einstein / Agentforce model regions | Region-paired with Hyperforce activation |

When the backlog includes a feature on this list, "we're on First-Gen" is a hard blocker. The migration is not optional.

### IP allowlisting changes

Hyperforce uses different IP ranges than First-Generation. Salesforce publishes the Hyperforce IP ranges (generally CIDR blocks owned by AWS / Azure / GCP) via Knowledge articles and the IP Range Viewer in Setup. The customer side must update each of the following:

| Allowlist owner | Scope |
|---|---|
| Customer firewall outbound | Any system calling Salesforce APIs from inside the customer network |
| Salesforce IP allowlists in Setup | Any restricted profile pinned to specific IP ranges (Login IP Ranges) |
| Middleware partner-system allowlists | MuleSoft, Boomi, AWS partners, identity providers (Okta, Azure AD), SSO destinations with IP-based controls |
| Marketing-platform / partner allowlists | Marketing Cloud, Pardot / MCAE, partner orgs |

The "we missed an allowlist" failure mode is the most common day-1 migration incident — APIs return 403, integrations begin to time out, scheduled jobs fail silently. The remediation is straightforward; the prevention is an inventory done before migration day.

### Maintenance windows and validation

Hyperforce migrations are scheduled during a published maintenance window. The org is read-only during cutover (typically 1–4 hours for production, shorter for sandboxes). After cutover, the customer must run a validation test plan covering: API connectivity, SSO, integrations, scheduled jobs, Bulk API loads, Pardot/Marketing Cloud sync, partner-org connections, and any IP-pinned restricted profile.

Salesforce-initiated migrations come with a "Migration Assistance" engagement that helps coordinate the window; the validation test plan remains the customer's responsibility.

---

## Common Patterns

### Pattern: Salesforce-initiated migration (the default for most customers)

**When to use:** Salesforce sends a migration notification with a proposed window for an org currently on First-Generation infrastructure.

**How it works:**

1. **Confirm the proposed window** with the technical owner and integration partners; if the window conflicts with a critical release or business event, request reschedule via the Salesforce engagement.
2. **Build the IP allowlist update plan** — inventory every customer-side firewall, partner middleware, and Setup allowlist that pins to First-Gen ranges. Schedule the changes to land *before* the migration window so day-1 traffic flows.
3. **Build the validation test plan** — concrete tests for APIs, SSO, integrations, scheduled jobs, partner orgs, IP-pinned profiles. Owners and pass/fail criteria documented.
4. **Execute the migration window** — the org is read-only during cutover; communicate to users and downstream consumers.
5. **Post-migration validation** — run the test plan within 4 hours of cutover; escalate failures via the Migration Assistance channel.
6. **Document the new region, IP ranges, and infrastructure profile** in the architecture decision record so future readers don't re-discover them.

**Why not the alternative:** declining a Salesforce-initiated migration is contractually constrained and creates progressive feature-availability gaps as Hyperforce-only capabilities ship.

### Pattern: customer-elected new-region landing for a new geography

**When to use:** the customer is launching a business unit in a new region (e.g., expanding into India, EU expansion post-Schrems II) and wants the new org seated in that region from day one.

**How it works:** request a Hyperforce-region-pinned org via the Salesforce engagement; choose region by mapping data-residency obligations to available regions; confirm pairing for DR; design integrations with region-aware latency in mind. Multi-region orgs are not a single-tenant capability — the right answer is multiple orgs (multi-org strategy) rather than expecting one org to serve two regions.

**Why not the alternative:** placing a global business in a single non-region-appropriate Hyperforce region creates compliance debt that grows as the business scales.

### Pattern: pre-migration discovery for a feature blocked on First-Gen

**When to use:** the backlog includes Private Connect, a Data Cloud capability, or another Hyperforce-only feature, and the org is on First-Gen.

**How it works:** treat the migration as a *prerequisite*, not a side project. Open the migration engagement immediately; sequence the feature work after the migration completes and validates. Do not promise the dependent feature's go-live before the migration is confirmed scheduled.

**Why not the alternative:** scoping the feature without the migration produces a project blocked indefinitely on platform-level work the team does not control.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Salesforce-initiated migration notification received | Confirm window, build allowlist + validation plans, execute | Decline isn't operationally available long-term |
| New geography launch | Request a Hyperforce-region-appropriate new org | Single-tenant orgs are single-region |
| Hyperforce-only feature in backlog while on First-Gen | Migrate first, then build the feature | Feature is gated on infra |
| Strict data-sovereignty obligation (legal-process scope) | Region + Government Cloud / FedRAMP / Health Cloud-residency review | Region alone is at-rest residency, not sovereignty |
| IP allowlist inventory is incomplete two weeks before window | Pause non-allowlist work; complete inventory | Day-1 incidents are 90% allowlist gaps |
| Need customer-controlled cross-region failover | Architect via multi-org + integration sync | Hyperforce manages failover; not a customer control |
| Sandbox refresh after production migration | Refresh from production after migration; validate sandbox parity | Sandboxes inherit production's infrastructure |

For "should we adopt Private Connect once on Hyperforce?" — read `integration/private-connect-setup` after the migration succeeds. For HA/DR strategy that wraps around the platform's failover behavior — `architect/ha-dr-architecture`.

---

## Recommended Workflow

1. Confirm current infrastructure (First-Gen vs Hyperforce) and surface the migration trigger (Salesforce-initiated, customer-elected, feature-blocked).
2. Map data-residency obligations to candidate regions; pick one and document the rationale and the pairing implications.
3. Inventory every IP allowlist (customer firewalls, middleware, Setup-side, partner orgs, identity providers); produce the update plan landing before the migration window.
4. Build the validation test plan with owners and pass/fail criteria. Cover APIs, SSO, integrations, scheduled jobs, partner orgs, IP-pinned profiles, Bulk API, and Marketing Cloud / MCAE sync.
5. Coordinate the maintenance window with downstream consumers and business stakeholders. Communicate the read-only cutover window 14–30 days ahead.
6. Execute the migration; immediately after cutover run the validation test plan; escalate failures via Migration Assistance.
7. Document the new region, IP ranges, and infrastructure baseline in an architecture decision record. Update related architecture artifacts (HA/DR, integration catalog, network diagrams).
8. Post-migration: revisit the backlog for newly-unblocked Hyperforce-only features (Private Connect, Data Cloud capabilities, regional Einstein). Sequence those next.

---

## Review Checklist

- [ ] Current infrastructure confirmed via Setup and Trust site
- [ ] Migration trigger and window documented (Salesforce-initiated / customer-elected / feature-blocked)
- [ ] Region selection rationale tied to a specific data-residency obligation
- [ ] IP allowlist inventory complete: customer firewalls, middleware, Setup, partner orgs, identity provider
- [ ] Validation test plan with named owners, pass/fail criteria, and post-migration runtime
- [ ] Cutover communication sent to users and downstream consumers ≥ 14 days ahead
- [ ] Post-migration architecture decision record drafted and reviewed
- [ ] Sandbox refresh / parity strategy after production migration documented
- [ ] HA/DR architecture updated to reflect Hyperforce platform-level failover behavior
- [ ] Backlog reviewed for now-unblocked Hyperforce-only features

---

## Salesforce-Specific Gotchas

1. **Sandboxes don't always migrate at the same time as production** — production may go first; sandboxes follow on a separate window. Integration testing in a sandbox before production migrates won't catch all post-migration-on-prod issues.
2. **IP ranges are AWS / Azure / GCP CIDRs, not Salesforce-owned** — customer firewalls that are configured to allow only "Salesforce IP space" by company name (rather than CIDR) will block traffic. The inventory must use CIDRs.
3. **"My Domain" URL does not change on migration** — but underlying instance names may. Hard-coded references to instance-specific URLs (e.g., `naX.salesforce.com`) will break; use `*.my.salesforce.com` everywhere.
4. **Data export / sandbox refresh windows shift** — operational schedules pinned to instance maintenance windows must be re-pinned after migration.
5. **Salesforce Connect external object endpoints sometimes need re-authentication** — OAuth flows that pinned to specific issuer URLs may need refresh after instance changes.
6. **Hyperforce regions are not a substitute for Government Cloud or Health-Cloud-residency programs** — those are separate licensing/compliance programs. A regulated workload that requires GovCloud/FedRAMP cannot be served by a commercial Hyperforce region.
7. **Migration Assistance is not 24×7 active management** — it's a scheduled engagement window. Day-3 issues escalate via standard support unless explicitly negotiated.
8. **Some legacy integrations use packet-level features (TLS-version pinning, cipher pinning, IP-pinned client certs) that fail silently after migration** — discover them via SIEM logs in the first 72 hours, not via integration health checks.
9. **Salesforce Functions is decommissioned regardless of Hyperforce migration** — they are unrelated programs but customers conflate them. Functions decommission has its own runbook (`integration/salesforce-functions-replacement`).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Migration readiness checklist | Pre-window inventory and decisions tied to the announced cutover date |
| Region selection rationale | Mapping data-residency obligations to chosen region and its pairing |
| IP allowlist update plan | Customer firewalls, middleware, Setup, partner orgs, identity provider — owners and dates |
| Validation test plan | Concrete post-cutover tests with owners and pass/fail criteria |
| Architecture decision record | Documented infrastructure baseline post-migration |
| Hyperforce-only feature backlog | Now-unblocked capabilities sequenced for after the migration validates |

---

## Related Skills

- `architect/ha-dr-architecture` — for HA/DR strategy that wraps around Hyperforce platform-level failover behavior
- `integration/private-connect-setup` — for the most common Hyperforce-only feature unlock
- `integration/salesforce-functions-replacement` — for the unrelated-but-often-conflated Functions decommission
- `architect/health-cloud-data-residency` — for vertical-specific health-data residency that layers on top of region selection
- `architect/government-cloud-compliance` — for FedRAMP / GovCloud workloads where Hyperforce commercial regions don't qualify
- `architect/multi-org-strategy` — for the answer to "we have multiple regions"
- `security/network-security-and-trusted-ips` — for the IP allowlisting and network-segmentation parts of the plan
