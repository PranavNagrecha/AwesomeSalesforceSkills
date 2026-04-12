# Gotchas — Fundraising Process Mapping

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: NPSP Is No Longer Provisioned for New Orgs (December 2025)

**What happens:** Salesforce stopped offering NPSP as a pre-configured package for new production orgs in December 2025. Practitioners who apply NPSP-specific guidance (namespace fields, NPSP-specific Setup menus, `npsp__` objects, Engagement Plans) to a post-December 2025 nonprofit org will find the features do not exist. Configuration steps fail, Setup menus are absent, and automation referencing the `npsp__` namespace throws errors.

**When it occurs:** Any engagement with a nonprofit org created after December 2025, or when a nonprofit begins a new Salesforce implementation and the NPSP managed package is not visible in Setup > Installed Packages. Also occurs when a consultant assumes NPSP is "standard for nonprofits" without verifying the installed packages list.

**How to avoid:** Before any NPSP-specific guidance, verify the platform: check Setup > Installed Packages for the `npsp` namespace. If absent, the org is on Nonprofit Cloud (NPC), a Salesforce.org product trial, or a standard Salesforce org. Apply NPC-appropriate guidance instead.

---

## Gotcha 2: NPC Does Not Have NPSP Engagement Plans

**What happens:** The Engagement Plans feature — `npsp__Engagement_Plan_Template__c`, `npsp__Engagement_Plan__c`, and `npsp__Engagement_Plan_Task__c` — is part of the NPSP managed package. It does not exist in Nonprofit Cloud (NPC). Practitioners who recommend Engagement Plan setup for post-close stewardship on NPC orgs will produce guidance that has no implementation path. The objects are not present and cannot be added.

**When it occurs:** When designing stewardship automation for an NPC org, or when a migrating nonprofit asks whether their existing NPSP Engagement Plan templates will carry over to NPC after migration.

**How to avoid:** For NPC orgs, recommend Flow-based stewardship automation, Salesforce Cadences (Sales Engagement), or task generation via Process Automation. Do not reference Engagement Plans in any NPC context. If migrating from NPSP to NPC, document that Engagement Plan templates must be rebuilt as Flow or Cadence logic — they cannot be imported or converted automatically.

---

## Gotcha 3: Renaming a Stage Picklist Value Does Not Update Existing Records

**What happens:** An admin renames an Opportunity stage value in Setup (e.g., changes "Cultivation" to "Cultivating") expecting all Opportunities currently in "Cultivation" to automatically reflect the new name. In Salesforce, picklist value renames update the picklist definition but do NOT mass-update existing records. Existing Opportunities retain the old value — "Cultivation" — which is now a retired or inactive picklist value. Reports, Flows, and validation rules that reference the new value ("Cultivating") will not match existing records.

**When it occurs:** Any time an organization goes through a stage rename exercise after live data is in the system. Extremely common when a new development director joins and wants to rename stages to match their preferred methodology vocabulary.

**How to avoid:** Before renaming any stage value, query Opportunity records that carry the old value and plan a data update job to replace the old value with the new value. Use Dataloader or a Bulk API job. After the data update is complete, deactivate the old picklist value. Automation and reports can then be safely updated to reference the new name. Sequence is: update records first, update automation second, deactivate old value third.

---

## Gotcha 4: Closed Stage Records Are Excluded from Standard Pipeline Forecasts

**What happens:** Opportunities with a stage marked as "Closed Won" or "Closed Lost" (IsWon = true or IsClosed = true respectively) are excluded from standard pipeline and forecast views in Salesforce. If a nonprofit adds a custom post-close stage called "Stewardship" and marks it as a Closed Won stage, Opportunities moved to Stewardship disappear from the active pipeline report. Gift officers lose visibility into which major gifts are still in active stewardship without building a custom report that explicitly includes closed stages.

**When it occurs:** When designing stewardship-phase stages for multi-year pledges or gift agreements where the organization still considers the relationship "active" even after the first payment is received.

**How to avoid:** Before marking any stage as Closed Won, confirm whether the org needs those records to remain visible in pipeline reports. For multi-year pledge tracking, consider keeping the stage as an open stage with high probability rather than marking it closed. Alternatively, create a separate Stewardship dashboard that explicitly includes IsClosed = true records filtered to the Stewardship stage.

---

## Gotcha 5: Sales Process Assignment Is Record-Type-Specific and Cannot Be Shared

**What happens:** A Salesforce org can have multiple Sales Processes defined, but each Opportunity Record Type can be assigned to only one Sales Process. If a nonprofit tries to share a single "Fundraising" sales process across all four NPSP Record Types (Donation, Grant, In-Kind, Major Gift), all four Record Types will show the same stage picklist — defeating the purpose of having separate processes for different program types.

**When it occurs:** When an admin tries to simplify the NPSP configuration by consolidating all stages into one process, or when a migration creates a new Record Type and the admin assigns it to the wrong Sales Process.

**How to avoid:** Maintain separate Sales Processes per major program type. Each NPSP Record Type (Donation, Grant, In-Kind, Major Gift) should have its own Sales Process with stages appropriate to that program's lifecycle. Verify Record Type to Sales Process assignments in Setup > Sales Processes after any Record Type or Sales Process change.
