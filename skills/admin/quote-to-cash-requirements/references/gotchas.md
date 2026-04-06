# Gotchas — Quote-to-Cash Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Syncing a New Quote Destroys All Opportunity Products

**What happens:** When a second Quote is synced to an Opportunity, Salesforce replaces all existing Opportunity Products (OpportunityLineItem records) with the line items from the newly synced Quote. Any products added manually to the Opportunity — or from a previously synced Quote — are permanently removed. There is no merge; it is a full replace.

**When it occurs:** Any time a rep creates a second quote version and clicks "Start Sync" on it, or when a Flow or automation syncs a new Quote. This is especially destructive when reps maintain a working Quote outside of Salesforce sync and periodically sync an alternate version.

**How to avoid:** Communicate clearly in user training and business process documentation that only one Quote should ever be synced per Opportunity, and that syncing a new Quote is destructive. If versioning is needed, use a custom status field (e.g., "Draft", "Active", "Superseded") to control which Quote is considered canonical rather than relying on sync state. Consider validation rules or Flow entry conditions to prevent inadvertent re-syncing.

---

## Gotcha 2: Quote PDF Line Item Limit Is Silent — No Warning to the User

**What happens:** Quote Templates support a maximum of 100 line items in the rendered PDF. If a Quote has more than 100 line items, Salesforce generates the PDF without error, but silently truncates the line item list at 100. The rep sees a complete-looking PDF that is missing products. The customer may receive an incomplete quote document without anyone noticing.

**When it occurs:** On any quote where the product catalog per deal exceeds 100 SKUs. Common in manufacturing, distribution, and IT reseller scenarios with complex bills of materials.

**How to avoid:** Add a validation rule on Quote or a warning banner via Flow/in-app guidance when `QuoteLineItemCount > 90` (giving a buffer before the hard limit). Explicitly call out this limit in requirements gathering. For high-volume line item scenarios, evaluate CPQ/Revenue Cloud, which does not have this PDF line item restriction.

---

## Gotcha 3: Quote Currency Is Locked at Creation and Cannot Be Changed

**What happens:** The currency on a Quote record is set when the Quote is created and cannot be updated afterward. If the Opportunity currency changes (e.g., a deal moves from USD to EUR mid-process), or if the wrong currency was selected at creation, the Quote must be deleted and recreated. Editing the currency field is not possible via UI or API after creation.

**When it occurs:** Multi-currency orgs where deal currency is uncertain at quote creation, or where Opportunities are cloned and their currency updated after the fact.

**How to avoid:** Enforce currency confirmation as part of the opportunity qualification checklist before a Quote is created. If the org regularly handles multi-currency deals, include currency in the Quote creation quick action form (making it required and visible) so reps are forced to confirm it upfront.

---

## Gotcha 4: Approval Process Final Actions Cannot Create Records — Order Creation Must Be in a Flow

**What happens:** Approval Process Final Approval and Final Rejection actions support field updates, email alerts, tasks, and outbound messages only. They cannot create Order records, Contract records, or any other related object. Teams that attempt to wire Order creation into a Final Approval action discover this limitation only at build time.

**When it occurs:** Any time the business requirement is "auto-create an Order when the Quote is approved." The natural assumption is that the Approval Process handles it — but it cannot.

**How to avoid:** Design Order creation as a Record-Triggered Flow on Quote, fired when `Status` changes to "Accepted". The Final Approval action sets the Quote Status field, and the Flow reacts to that field change.

---

## Gotcha 5: The Start Sync Button Does Not Appear Until Quotes Are Enabled in Setup

**What happens:** The Quote sync feature — including the "Start Sync" button on the Quote record and the "Synced Quote" indicator on the Opportunity — only appears if Quotes are explicitly enabled in Setup > Quotes Settings > Enable Quotes. In orgs that have Quote objects but never enabled the sync feature, the button is absent and sync is impossible.

**When it occurs:** During requirements reviews when Quote objects are visible (because they were created via import or API) but the sync feature is not enabled. Also occurs after org migrations where settings are not fully replicated.

**How to avoid:** Confirm Quotes Settings in Setup as the first step of any quote-to-cash engagement. Verify "Enable Quotes" is checked and that the Quotes related list is present on the Opportunity page layout for the relevant record types.
