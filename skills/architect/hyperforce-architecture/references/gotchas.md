# Gotchas — Hyperforce Architecture

Non-obvious platform behaviors that cause real production problems during and after a Hyperforce migration.

## Gotcha 1: production migrates separately from sandboxes

**What happens:** Production cuts over to Hyperforce on Saturday; the team validates against a sandbox the prior week and sees no issues. Post-cutover, real integrations break in ways the sandbox didn't reveal because the sandbox was still on First-Generation infrastructure.

**When it occurs:** Whenever the migration window for production precedes the sandbox window — the default for Salesforce-initiated migrations.

**How to avoid:** Run integration validation tests against production immediately post-cutover, not against a still-First-Gen sandbox the week before. If pre-cutover validation in a Hyperforce-aligned environment is required, request a Hyperforce sandbox refresh first or coordinate windows.

---

## Gotcha 2: customer firewalls pinned by company name vs by CIDR

**What happens:** A corporate firewall has rules like "allow outbound to Salesforce Inc. owned IP space." After migration, those rules silently no longer match because Hyperforce IP ranges are AWS / Azure / GCP owned, not Salesforce-owned.

**When it occurs:** Any enterprise environment with mature outbound-egress controls and rule annotations rather than pure CIDR.

**How to avoid:** The IP-allowlist inventory must work in CIDR terms. Ask each firewall owner: "what CIDRs does your rule actually match against?" not "is Salesforce traffic allowed?". The answer to the second is "yes" while the first is "no."

---

## Gotcha 3: Hyperforce regions are at-rest residency, not data sovereignty

**What happens:** Compliance team approves a Hyperforce US-East org for EU-customer data on the basis of "encryption + residency." Schrems II raises legal-process concerns: a US-region cloud provider can be compelled to disclose data under US law regardless of where it's encrypted at rest.

**When it occurs:** Any cross-border compliance review where the obligation is sovereignty (legal-process scope), not just residency (storage location).

**How to avoid:** Distinguish residency from sovereignty in the architecture decision record. Hyperforce regions deliver residency; sovereignty obligations require either a region pairing the customer's jurisdiction (EU-Frankfurt for EU data) or, for the strictest regulated workloads, Government Cloud / FedRAMP / Health Cloud-residency programs that are *separate* from commercial Hyperforce regions.

---

## Gotcha 4: My Domain URLs are stable but instance URLs are not

**What happens:** A custom integration hard-codes `https://acme--prod.na32.salesforce.com/services/data/v60.0/` referring to instance `na32`. Post-migration, the org is on a different instance; the URL no longer resolves and the integration breaks.

**When it occurs:** Any integration written before My Domain became universal, or any vendor library that pinned to an instance URL during initial development.

**How to avoid:** Inventory hard-coded `na*.salesforce.com`, `cs*.salesforce.com`, `eu*.salesforce.com`, `ap*.salesforce.com`, `um*.salesforce.com` references in repos, runbooks, and partner documentation. Replace with `*.my.salesforce.com` (production) or `*.sandbox.my.salesforce.com` (sandbox).

---

## Gotcha 5: Salesforce-managed cross-region failover is not customer-controllable

**What happens:** An architect plans a multi-region active-active deployment using Hyperforce on the assumption that the customer controls failover triggers and timing. Hyperforce manages failover at platform level; customer code cannot trigger or observe an in-region degradation in a way that supports active-active orchestration.

**When it occurs:** Architecture reviews that bring AWS / Azure regional-failover patterns to bear on Salesforce.

**How to avoid:** Frame Hyperforce as Salesforce-managed within-platform reliability. For customer-controllable HA across orgs, the answer is multi-org strategy with replication, not Hyperforce region pairing. Document this in the HA/DR architecture explicitly.

---

## Gotcha 6: Hyperforce migration is unrelated to Salesforce Functions decommission, but customers conflate them

**What happens:** A team treats the Functions decommission deadline as a sub-task of the Hyperforce migration. They are unrelated. Functions has its own retirement timeline and replacement options; Hyperforce migration has its own. Conflating them produces a blocked plan when one slips and the other doesn't.

**When it occurs:** Any org that is both on First-Generation infrastructure *and* has Salesforce Functions in production.

**How to avoid:** Surface Functions decommission as a separate workstream tracked in `integration/salesforce-functions-replacement`. Hyperforce migration does not retire Functions; Functions retires on its own schedule regardless of Hyperforce status.

---

## Gotcha 7: TLS / cipher pinning on legacy integrations fails silently

**What happens:** A 2018-era SOAP integration pins to TLS 1.0 / specific ciphers. Hyperforce's TLS posture is stricter; the integration's handshake fails. The customer side logs no error (it just times out), and the failure is attributed to "Salesforce performance issues."

**When it occurs:** Any partner integration written against early-2010s standards that hasn't been updated.

**How to avoid:** Audit SIEM logs and middleware audit trails in the first 72 hours post-migration for TLS handshake failures. Inventory integrations by TLS posture before migration. Salesforce has been TLS 1.2-only for years; if a partner still hasn't updated by Hyperforce day, that's a partner-team escalation, not a platform issue.

---

## Gotcha 8: Marketing Cloud / MCAE / partner-org IP allowlists are out of the customer's direct control

**What happens:** Day-1 post-migration: the partner org's outbound connection to your Salesforce org fails because the partner team hasn't updated their allowlist. The customer can't fix it; only the partner can.

**When it occurs:** Any architecture with org-to-org or org-to-partner-tenant trust relationships using IP-pinned allowlists.

**How to avoid:** Open partner tickets 21 days ahead of migration. The partner's update SLA is rarely under 14 days. Don't assume "they'll handle it" — get a confirmation ticket with a land-by date.

---

## Gotcha 9: data-export schedules and sandbox-refresh windows shift after migration

**What happens:** The org's Data Export schedule was pinned to "every Saturday 02:00" assuming the First-Gen instance maintenance schedule. Post-migration, the schedule still runs but Saturday 02:00 may now overlap a Hyperforce-region maintenance event the team didn't anticipate.

**When it occurs:** Any operational schedule that implicitly avoided the old instance's maintenance window.

**How to avoid:** Re-pin operational schedules after migration based on the new region's published maintenance behavior. Don't assume schedules are infrastructure-neutral.

---

## Gotcha 10: Government Cloud and Hyperforce commercial regions are not interchangeable

**What happens:** A regulated workload (DoD contractor, HIPAA-bound health record set, IRS-bound tax data) is moved to a commercial Hyperforce region under the assumption that "Hyperforce regions cover compliance." They don't — Government Cloud / FedRAMP-authorized programs are separate licensing.

**When it occurs:** Any regulated-workload migration where the compliance program isn't surfaced before region selection.

**How to avoid:** Surface the regulatory program (FedRAMP Moderate / High, IL5, ITAR, etc.) before choosing the region. Government Cloud is a separate product and a separate org type, not a checkbox on a Hyperforce migration plan.
