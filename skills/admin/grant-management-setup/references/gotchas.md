# Gotchas — Grant Management Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: NPSP Outbound Funds Module and Nonprofit Cloud for Grantmaking Are Architecturally Incompatible

**What happens:** Guidance, automation, and data models designed for one platform silently fail or produce incorrect results when applied to the other. Specifically: OFM API names (e.g., `outfunds__Funding_Request__c`, `outfunds__Disbursement__c`) do not exist in NC Grantmaking orgs, and NC Grantmaking objects (`FundingAward`, `FundingDisbursement`, `FundingAwardRequirement`) do not exist in NPSP + OFM orgs. A Flow or SOQL query referencing OFM objects deployed to a NC Grantmaking org will fail at runtime with an "object not found" error.

**When it occurs:** Any time guidance is mixed between platforms — most commonly when a practitioner finds Trailhead or documentation for one platform and applies it to an org on the other. Also occurs during migrations when teams assume the data model "maps over" without transformation.

**How to avoid:** Always confirm the installed platform before writing any query, Flow, or Apex that references grant objects. For NPSP orgs: verify `outfunds` namespace is present. For NPC orgs: verify the Grantmaking license is active and FundingAward is accessible. Never use OFM object names in NC Grantmaking orgs, and never use NC object names in NPSP orgs.

---

## Gotcha 2: Nonprofit Cloud for Grantmaking Requires a Separate License Beyond Base NPC

**What happens:** An org may be fully provisioned on Nonprofit Cloud (NPC) but still receive "Insufficient Permissions" or "Object Not Found" errors when attempting to access FundingAward, FundingDisbursement, or FundingAwardRequirement. This is not a permissions configuration issue — it is a licensing issue. These objects are gated behind the Grantmaking product license, which is sold separately from the base NPC license.

**When it occurs:** Orgs that purchased NPC for fundraising or program management without explicitly purchasing the Grantmaking add-on. Also occurs when a sandbox is refreshed from a production org that has the license — the sandbox may not have the license provisioned even if production does.

**How to avoid:** Verify the Grantmaking license in Setup → Company Information → Permission Set Licenses before any grantmaking implementation work. If the license is absent, the correct path is either (a) purchase the Grantmaking license, or (b) implement OFM on NPSP or NPC as a substitute. Do not attempt to recreate FundingAward as a custom object — this produces a non-standard data model that breaks all future Salesforce Grantmaking product updates.

---

## Gotcha 3: FundingAwardRequirement Status Is a Fixed Lifecycle — Extensions Require Careful Documentation

**What happens:** The FundingAwardRequirement Status picklist (Open → Submitted → Approved) is the standard platform-intended lifecycle. Adding custom values (e.g., "Rejected," "Needs Revision," "On Hold") is technically possible via Setup, but doing so breaks compatibility with standard Flow templates, Trailhead guidance, and any future Salesforce Grantmaking product updates that assume the three-value lifecycle. Specifically: if a Rejected requirement is never transitioned back to Open and resubmitted, it may remain in a terminal non-Approved state that triggers disbursement-gating automation indefinitely.

**When it occurs:** When grants managers request a "Rejected" or "Returned" status to communicate feedback to grantees, leading admins to add custom picklist values without considering automation side effects.

**How to avoid:** Before adding custom status values, design the full status transition map including: (a) what happens to disbursement gating when a requirement enters the new status, (b) how grantees are notified, and (c) how the requirement returns to a reviewable state. The simplest approach is to use the Description or Comments field on FundingAwardRequirement to capture rejection feedback and revert Status to Open for resubmission — preserving the standard lifecycle while enabling feedback.

---

## Gotcha 4: FundingDisbursement Is a Tranche Object, Not a Payment Confirmation

**What happens:** Practitioners sometimes treat FundingDisbursement as a record of an actual payment made (like a cash disbursement in accounting) rather than as a scheduled tranche in the grant payment plan. This leads to disbursement records being created only after payment is sent, losing the forward-looking pipeline view that FundingDisbursement is designed to provide.

**When it occurs:** When grants staff who are familiar with accounting systems map "disbursement = payment posted" to the Salesforce data model. The FundingDisbursement record should be created at award setup time with a scheduled date, then updated to "Paid" when the payment is sent — not created after the fact.

**How to avoid:** Create all FundingDisbursement records at the time of award setup, with Status = Draft or Scheduled and a ScheduledDate in the future. The Status field tracks the lifecycle from planning to execution. Treating it as a retroactive ledger entry eliminates the scheduling and pipeline reporting value of the object.
