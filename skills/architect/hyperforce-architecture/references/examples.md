# Examples — Hyperforce Architecture

## Example 1: Salesforce-initiated migration with a 60-day window

**Context:** A 1,200-user org running on `na32.salesforce.com` (First-Generation Salesforce data center, US-West region) receives a Salesforce-initiated migration notification. Proposed cutover: 8-week window starting in 60 days; 3-hour read-only maintenance window on the cutover Saturday.

**Problem:** The architect inherits the migration with no prior context, no inventory of IP allowlists, and a pending Q-end Marketing Cloud campaign that conflicts with the proposed Saturday window.

**Solution:**

1. **Confirm and reschedule the window** — escalate via the Salesforce Migration Assistance engagement to move the cutover to a Saturday outside Q-end. Salesforce-managed windows are negotiable within the 60-day band when there's a documented business reason.

2. **Inventory IP allowlists** — produce a spreadsheet (or terraform-doc artifact) listing every customer-side firewall rule, middleware allowlist, and Setup → Network Access entry that pins to First-Gen IP CIDRs. Cross-reference against the published Hyperforce IP ranges for the chosen region.

   | Owner | System | Current pinning | Hyperforce update plan | Land-by date |
   |---|---|---|---|---|
   | Network ops | corporate firewall outbound | `*.salesforce.com` + IP whitelist | Add Hyperforce US-West CIDRs (AWS-owned) | T-14 |
   | Integration | MuleSoft connector | named credentials, no IP | none required | — |
   | Identity | Okta SSO ACS allowlist | First-Gen IPs | Add Hyperforce US-West CIDRs | T-14 |
   | Setup | Network Access (Login IP Ranges) | First-Gen IPs | Update via Setup → Network Access | T-7 |
   | Partner | Marketing Cloud sync | First-Gen IPs | Open partner ticket | T-21 |

3. **Build the validation test plan** — concrete tests with named owners and pass criteria:

   | Test | Owner | Pass criteria | Run time |
   |---|---|---|---|
   | OAuth web-server flow from Okta | identity team | `200 OK` token issued | 0:00–0:30 post-cutover |
   | Bulk API 2.0 from MuleSoft | integration | sample job ingests 100 records | 0:30–1:00 |
   | Scheduled Apex jobs run on schedule | platform | next scheduled run completes | 1:00–4:00 |
   | LWC custom record page loads in Lightning | UX | page renders < 2s | 0:00–0:30 |
   | IP-pinned restricted profile login | security | login succeeds for whitelisted user | 0:30–1:00 |
   | Marketing Cloud → Sales Cloud sync | marketing | sample lead syncs successfully | 1:00–4:00 |

4. **Communicate** — 30-day, 14-day, 7-day, 1-day cutover comms to users (in-app banner + email) and downstream consumers (integration partners, marketing ops, identity team).

5. **Execute and validate** — run the test plan in the first 4 hours post-cutover. Two failures emerge: the corporate firewall missed one CIDR block (resolved within 30 minutes), and a legacy SOAP integration pinned to TLS 1.0 (escalated; partner team upgrades the next business day).

6. **Document the new infrastructure baseline** — architecture decision record names the new Hyperforce region (US-West-2 on AWS), pairing region (US-East-2), and Hyperforce-only features now unblocked (Private Connect, regional Data Cloud).

**Why it works:** treating the migration as a project with named owners, pre-cutover inventory, and post-cutover validation flips the failure mode from "we didn't know what would break" to "we know exactly what to test and who runs it."

---

## Example 2: customer-elected new-region landing for EU expansion

**Context:** A North American CRM org wants to launch in the EU. Compliance has issued a directive: EU customer data must be stored on EU infrastructure post-Schrems II. The team initially proposes adding EU customer records to the existing US org with a shielded-encryption strategy.

**Problem:** Shield encrypts at rest but does not change *where* the data is stored. The compliance directive is about residency, not encryption. The proposal does not satisfy the obligation.

**Solution:**

1. **Restate the obligation** — EU records must reside on EU infrastructure. This is a residency control, not an encryption control.
2. **Choose architecture** — multi-org strategy (North American org + new EU org), not single-org. Hyperforce orgs are single-region; placing EU records in a US-region org cannot satisfy residency regardless of encryption.
3. **Select region** — EU-Frankfurt or EU-Paris based on user-population latency and pairing for failover. Frankfurt selected for AWS pairing with EU-Ireland.
4. **Engage Salesforce** — request a new Hyperforce-region-pinned org via the contract / engagement path. Customer-elected new orgs are a contractual line, not a Setup toggle.
5. **Plan integration** — design the cross-org sync (CRM Analytics, Data Cloud, or middleware) that respects residency: aggregations and anonymized rollups can flow to a global tenant, but raw EU records do not leave the EU org without an explicit transfer mechanism (SCC, BCR).
6. **Document residency posture** — architecture decision record explicitly names what data lives where, what crosses the border, and under which legal mechanism.

**Why it works:** the multi-org answer matches the platform reality (Hyperforce orgs are single-region) and the legal reality (residency is about location, not encryption). The single-org Shield proposal would have produced a compliance gap that grew with EU customer count.

---

## Example 3: feature-blocked migration sequencing

**Context:** A retail customer wants to adopt Private Connect (no public-internet path between Salesforce and a regulated AWS-hosted analytics warehouse). Their org is on First-Generation infrastructure.

**Problem:** Private Connect is Hyperforce-only. The proposal frames "adopt Private Connect" as a 6-week project; the underlying infrastructure migration has not been scheduled.

**Solution:**

1. **Reframe** the project: migration is a *prerequisite*, not a side concern. Private Connect work cannot start until the org is on Hyperforce.
2. **Open the migration engagement** with Salesforce immediately. Customer-elected migrations on First-Gen orgs run 90–180 days end-to-end depending on org complexity.
3. **Sequence the backlog**: migration → 30-day stabilization → Private Connect engagement → analytics integration. The 6-week framing for Private Connect alone was correct; the dependency chain takes 5–8 months.
4. **Communicate the dependency** to stakeholders: the warehouse-integration go-live moves accordingly.

**Why it works:** Private Connect's Hyperforce dependency is non-negotiable. Recognizing the dependency early sets honest expectations; missing it produces a project that stalls 80% in.

---

## Anti-Pattern: skipping the IP allowlist inventory

**What practitioners do:** Trust the migration assistance engagement to "handle networking." Skip the customer-side allowlist inventory.

**What goes wrong:** Day-1 post-migration: 30% of integrations fail with 403. Salesforce APIs return correctly; the customer's *outbound* firewall is blocking responses. Marketing Cloud's outbound IP-pinned connection drops. Okta ACS allowlist still references First-Gen ranges. The team spends the first 8 hours after cutover firefighting a problem that could have been prevented in 4 hours of pre-migration inventory work.

**Correct approach:** the IP allowlist inventory is the customer's responsibility, not the migration assistance's. Build it 30 days out, validate the update plan with each owner, land the changes 7–14 days before cutover so any rollback can land before the read-only window opens.
