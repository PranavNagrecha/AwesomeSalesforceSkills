# Gotchas — Donor Lifecycle Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: NPSP Is No Longer Available for New Production Orgs

**What happens:** A consultant begins a NPSP moves management and lifecycle design for a new nonprofit client, only to discover during provisioning that NPSP is no longer available for new production orgs as of December 2025. New nonprofits must use Nonprofit Cloud (NPC), which has a different portfolio management paradigm.

**When it occurs:** Any engagement started after December 2025 with a new nonprofit client who has not yet provisioned a Salesforce org.

**How to avoid:** Confirm whether the client is on an existing NPSP org (legacy) or is a new org. New orgs use NPC. Adjust the lifecycle and segmentation design for the correct platform before committing to NPSP-specific features like LYBUNT reports or classic Engagement Plans.

---

## Gotcha 2: ERD Status Transitions to Lapsed Automatically

**What happens:** When an Enhanced Recurring Donation misses a scheduled payment, Salesforce automatically transitions the `Status__c` field from Active to Lapsed. Donors receive the "Lapsed" status without staff action. Donors who call about lapsed status are surprised — often their card expired rather than them canceling intentionally.

**When it occurs:** After any missed scheduled recurring donation — card expiration, insufficient funds, or payment processor decline.

**How to avoid:** Build a triggered workflow or Flow that notifies the donor when ERD status transitions to Lapsed. Design a re-engagement process for lapsed recurring donors (update payment method) separate from lapsed one-time donors (new solicitation). Filter LYBUNT reports to exclude donors whose lapse is ERD-related.

---

## Gotcha 3: NPSP LYBUNT Report Uses Last Opportunity Close Date, Not Payment Date

**What happens:** The NPSP LYBUNT report filters on `npsp__LastOppDate__c` (Close Date of the most recent Closed Won Opportunity). A donor who made a pledge last year being paid in installments this year may appear as "not given this year" because the Close Date is last year.

**When it occurs:** In orgs with pledged gifts where Opportunity Close Date is set to pledge date rather than payment completion date.

**How to avoid:** Clarify the organizational definition of "gave this year" — pledge date or payment date. Consider filtering on `npe01__OppPayment__c.npe01__Payment_Date__c` for "actually paid this year" logic. Document the definition in the report description.

---

## Gotcha 4: NPC Actionable Segmentation Does Not Send Marketing Communications

**What happens:** An NPC org administrator configures Actionable Segmentation expecting it to trigger email campaigns or Marketing Cloud sends. Actionable Segmentation classifies donors into portfolio tiers for fundraiser assignment — it does NOT initiate outreach automatically.

**When it occurs:** When the implementation team interprets "segmentation" as "marketing automation" and expects email sends to begin after segmentation configuration.

**How to avoid:** Communicate clearly at project kickoff: Actionable Segmentation = donor classification for portfolio management. Marketing execution requires a separate campaign management or marketing automation tool configured as a distinct workstream.

---

## Gotcha 5: Pipeline Reports Are Required for Moves Management to Be Useful

**What happens:** Moves Management Opportunity stages are configured but no pipeline reports are built. Gift officers update stages, but development directors still request weekly spreadsheet exports because they cannot find the data in Salesforce.

**When it occurs:** When the moves management configuration is completed without corresponding report and dashboard design.

**How to avoid:** Treat the Pipeline Report (Opportunities grouped by officer and stage) as a required deliverable of moves management — not optional. Build and validate reports before declaring configuration complete.
