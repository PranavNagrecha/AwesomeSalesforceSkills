# Gotchas — Lead Scoring Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Formula Fields Cannot Be Referenced in Flow Entry Criteria or Assignment Rule Conditions

**What happens:** A practitioner stores the composite lead score as a Formula field (e.g., `Composite_Score__c = Fit_Score__c + Engagement_Score__c`) and then tries to use it as a Flow entry criterion (`{!Lead.Composite_Score__c} >= 50`). The Flow either errors on save with "The formula or expression is invalid" or silently never triggers because formula field values are computed at read time, not stored, and Flow entry criteria evaluate stored field values at the point of the triggering DML event.

**When it occurs:** Any time a record-triggered Flow's entry criterion or Assignment Rule's criteria references a formula field for routing decisions. Also affects list view filters and some report filters depending on formula complexity.

**How to avoid:** Store the composite score in a real Number field (`Composite_Score__c` as a Number, not Formula). Maintain it via a record-triggered Flow that fires whenever either dimension score changes. The formula approach is only safe for display purposes on the page layout where it is rendered on demand.

---

## Gotcha 2: Account Engagement Sync Overwrites CRM-Side Edits to Synced Score Fields

**What happens:** When Account Engagement (Pardot) is integrated, the prospect Score and Grade fields sync from AE to Salesforce Lead/Contact. If a Salesforce admin or Flow writes a different value to the synced score field, the next AE sync cycle (typically every few minutes) overwrites it with AE's value. Any CRM-side automation that depends on a modified score value silently loses its data.

**When it occurs:** When a team tries to augment or override the AE-synced score within Salesforce (e.g., adding CRM-side fit points to the AE score in the same field). It also occurs when a data migration loads historical score values into the AE-synced field.

**How to avoid:** Treat AE-synced fields as read-only in Salesforce. If you need a composite score that blends AE score with CRM-side fit data, create a separate `Composite_Score__c` Number field in Salesforce and write the blended value there. Never write to `Pardot_Score__c` or the standard `Score` field from CRM-side automation.

---

## Gotcha 3: Record-Triggered Flows Fire on Every Lead Save — Including Bulk Data Loads

**What happens:** A record-triggered Flow that recalculates all scoring dimensions on every Lead create/edit fires for every record in a bulk import or list upload. An import of 5,000 leads triggers 5,000 Flow interviews simultaneously, consuming Apex CPU time and DML rows. In orgs with multiple record-triggered Flows on the Lead object, this can cause governor limit errors, partial import failures, or org-wide slowdowns during the load window.

**When it occurs:** During list imports via Data Import Wizard, Data Loader, or external system API writes that update Lead records in bulk. Also occurs during any mass-update operation (e.g., field update from a batch report action).

**How to avoid:** For orgs with high lead volume (>200 leads/day), move score recalculation out of the record-triggered Flow and into a Scheduled Flow that runs nightly or twice daily. The record-triggered Flow should only stamp the `MQL_Date__c` and set `Is_MQL__c` if the score is already populated — not recompute the score from scratch. For real-time scoring needs, use a before-save Flow that calculates the score in a single pass on create only.

---

## Gotcha 4: Lead Stage Picklist Values Must Be Agreed Upon Before Build — They Drive Reporting

**What happens:** Teams skip defining an explicit Lead Stage picklist (or use the standard `Status` field with ad-hoc values) and instead rely on `Is_MQL__c` checkbox and `Is_SQL__c` checkbox as stage proxies. When they try to build funnel reports showing Raw → Nurture → MQL → Accepted → SQL → Converted → Recycled, there is no single field to group on. Reports require multiple filters and become unmaintainable. Recycle history is lost when a lead is recycled back to Nurture and `Is_MQL__c` is unchecked.

**When it occurs:** In the first reporting cycle after go-live, when marketing asks for a stage-by-stage funnel report and the data model does not support it.

**How to avoid:** Define a `Lead_Stage__c` custom picklist (not the standard `Status` field, which is tied to conversion logic) with all lifecycle stages before build. Use a Flow to maintain it: a Lead enters MQL stage when `Is_MQL__c` flips to true; it enters Accepted when the rep stamps `SQL_Date__c`; it enters Recycled when `Recycle_Count__c` is incremented. Keep the standard `Status` field for its intended purpose (New, Working, Converted, Unqualified).

---

## Gotcha 5: Back-Scoring Historical Leads Triggers All Record-Triggered Flows

**What happens:** After the scoring model is built, a team wants to retroactively score all 50,000 existing Lead records by running a data update via Data Loader to populate `Fit_Score__c`. The update fires all record-triggered Flows on the Lead object for every record — including any MQL-notification Flows — causing 50,000 rep notification emails to be sent and 50,000 `MQL_Date__c` timestamps to be set for leads that scored above threshold years ago.

**When it occurs:** During initial go-live when populating dimension score fields for existing lead records for the first time.

**How to avoid:** Add a `Scoring_Model_Active__c` checkbox field (or a Custom Setting flag) that gates all scoring-related Flow actions. Set it to false before the initial back-score data load, run the load, verify the scores are correct, then flip the flag to true to enable MQL automation going forward. Alternatively, add a date condition to the MQL Flow: only set `MQL_Date__c` if the Lead was created within the last 90 days (or whatever the active pipeline window is).
