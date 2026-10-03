# Gotchas — NPSP Household Accounts

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Source key used below. "NPSP source" means the Salesforce.org NPSP repository on GitHub (`SalesforceFoundation/NPSP`, branch `main`), read on 2026-10-03. Class paths are under `force-app/` in that repository.

## Gotcha 1: Native Merges Are Fixed Up Later, and Not at All From Batch or Future Apex

**What happens:** Earlier versions of this skill said the native Account merge bypasses NPSP triggers. The NPSP source shows otherwise. Apex triggers fire on merge, and NPSP registers two handlers for it. `ACCT_AccountMerge_TDTM` runs on Account after delete, finds losing records by `MasterRecordId`, and calls a future method that refreshes household names and member counts, recreates household soft credits, re-runs rollups, and cleans up addresses. `CON_ContactMerge_TDTM` runs on Contact after delete and enqueues a fix-up job. Two real problems remain. The fix-ups are asynchronous, so rollups such as `npo02__TotalOppAmount__c` and the household name are wrong until the job runs. And the Account handler only calls its future method when `!System.isFuture() && !System.isBatch()`, so an Account merge executed from batch or future Apex gets no fix-up at all.

**When it occurs:** Bulk deduplication with a tool that merges in batch Apex, merges done in a future method, or reports and integrations that read rollups seconds after a merge. Also when an admin has deactivated either handler in the Trigger Handler records.

**How to avoid:** Merge household Contacts with the NPSP Contact Merge page (`CON_ContactMerge`) where practical. For bulk tools, find out whether they merge in batch context; if they do, re-run NPSP rollups for the surviving Accounts afterwards. Check Setup > Apex Jobs for the NPSP future and queueable jobs before reporting on merged households. Keep `ACCT_AccountMerge_TDTM` and `CON_ContactMerge_TDTM` active.

**Source:** NPSP source, `main/default/classes/ACCT_AccountMerge_TDTM.cls`, `main/default/classes/CON_ContactMerge_TDTM.cls`, `tdtm/classes/TDTM_DefaultConfig.cls` (both handlers default to active on `AfterDelete`).

---

## Gotcha 2: Manually Overridden Fields Are Listed in a Customization Field That Blocks Auto-Updates

**What happens:** If a user directly edits the Account Name, Formal Greeting, or Informal Greeting on a Household Account, NPSP appends that field to `npo02__SYSTEM_CUSTOM_NAMING__c` (for example `Name;Formal_Greeting__c;`). From then on NPSP does not regenerate that field when Contact names change. The Refresh Household Names batch also skips it, because the naming service checks the list before writing each field.

**When it occurs:** Any edit of the household name or greeting fields on the Account record, including edits made via the UI, API, data import tools, Flow, or Apex.

**How to avoid:** To hand a field back to NPSP, blank it on the Account (or set it to NPSP's name replacement text) and save. NPSP removes the field from the list on that save. If a permanent manual name is needed, document it so future admins know not to expect auto-updates on those records. UNVERIFIED (2026-10-03): the literal value of the replacement text comes from the `npo02.NameReplacementText` label in the Households package, which is not in the NPSP repository.

**Source:** NPSP source, `main/domain/HouseholdNamingUserControlledFields.cls` (append on change, remove when blank or replacement text); `main/service/HouseholdNamingService.cls` (`setNameFieldValuesOnHousehold` skips user-controlled fields).

---

## Gotcha 3: NPSP Household Account Model and FSC Household Group Model Are Incompatible

**What happens:** NPSP uses a direct Contact-to-Account lookup (`AccountId` on Contact) for household membership, so a Contact belongs to exactly one Household Account. Financial Services Cloud (FSC) uses an `AccountContactRelationship` (ACR) junction object, so a Contact can be associated with multiple Accounts simultaneously. The two models have different APIs, triggers, rollup mechanisms, and naming automation.

**When it occurs:** Admins or AI assistants that confuse the two models attempt to apply FSC household configuration steps to NPSP orgs, or vice versa. Both show "Household" terminology in the UI.

**How to avoid:** Confirm the org's product before advising household configuration. In an NPSP org look for the `npo02__` and `npsp__` namespaces, the `HH_Account` record type, and the `npo02__Households_Settings__c` custom setting (note the plural; an earlier version of this skill wrote `npo02__Household_Settings__c`, which does not exist). In an FSC org look for the `FinServ__` namespace and ACR records.

**Source:** NPSP source, `main/default/objects/npo02__Households_Settings__c/` and `CAO_Constants.cls` (`HH_ACCOUNT_RT_DEVELOPER_NAME = 'HH_Account'`).

---

## Gotcha 4: Every New Contact Without an Account Gets Its Own Household Account

**What happens:** In the Household Account model, NPSP creates a new Household Account for a Contact inserted without an `AccountId`. High-volume imports with blank `AccountId` produce one single-member household per Contact.

**When it occurs:** Contact imports via Data Loader, API, or integrations that leave `AccountId` null.

**How to avoid:** During Contact imports, set `AccountId` to the correct existing Household or Organization Account, and load household members against one Account. If a Contact represents a business or staff member, reference an Organization Account before inserting the Contact. UNVERIFIED (2026-10-03): earlier versions of this skill said NPSP Settings > Accounts can exclude Contact record types from household creation; the source read for this revision only confirmed an exclusion setting (`npo02__Household_Creation_Excluded_Recordtypes__c`) on the legacy Households settings.

**Source:** NPSP source, `tdtm/triggerHandlers/contact/ACCT_IndividualAccounts_TDTM.cls` (Contact before/after insert handling); `main/default/classes/UTIL_CustomSettingsFacade.cls` (`npe01__Account_Processor__c` defaults to `Household Account`).

---

## Gotcha 5: NPSP Naming Token Syntax Does Not Accept Salesforce Formula Functions

**What happens:** NPSP Household Naming format strings are parsed by `HH_NameSpec`, which replaces `{!FieldName}` tokens with Contact field values. It does not evaluate formula functions. If an admin enters `UPPER({!LastName})` or `IF(...)`, the function text is left in the output with only the token inside it replaced.

**When it occurs:** Admins familiar with formula fields try to add conditional logic or text transformations to format strings.

**How to avoid:** Use only Contact field API names in `{!...}` tokens, plus the nested `{!{!...}}` block for per-person parts. For logic that tokens cannot express, write a custom class that implements the global `HH_INaming` interface and enter its name in Household Naming Settings > Implementing Class (`Implementing_Class__c`, default `HH_NameSpec`). An earlier version of this skill named the interface `HH_NameSpec_IF`, which does not exist.

**Source:** NPSP source, `main/default/classes/HH_NameSpec.cls` (token regex and `strConFspec`), `HH_INaming.cls` (`global Interface HH_INaming`), `objects/Household_Naming_Settings__c/fields/Implementing_Class__c.field-meta.xml`.

---

## Gotcha 6: Nothing Regenerates When Automatic Household Naming Is Off

**What happens:** The naming service only writes names and greetings when `npo02__Advanced_Household_Naming__c` is true. With it off, Contact renames, merges, and the Refresh button change nothing, and the household member count still updates, which makes the setting look broken rather than off.

**When it occurs:** Orgs that turned automatic naming off during a migration and never turned it back on, or sandboxes refreshed from an org with different settings.

**How to avoid:** Check NPSP Settings > Households > Automatic Household Naming before debugging names. Turning it on for the first time runs an activation batch that marks every existing name that does not match `<LastName> Household`, and every existing greeting, as user-controlled. Review those households afterwards and release the ones that should follow the format.

**Source:** NPSP source, `main/service/HouseholdNamingService.cls` (`if (settings.isAdvancedHouseholdNaming())`), `main/domain/HouseholdSettings.cls`, `main/default/classes/HH_HouseholdNaming_BATCH.cls` (`isActivation` branch).

---

## Gotcha 7: Large Households Switch to the Overrun Text After Nine Members

**What happens:** `Contact_Overrun_Count__c` (default 9) caps how many members are named. Beyond it, NPSP stops listing people and appends the Name Overrun text (default from the `npo02.HouseholdNameOverrun` label).

**When it occurs:** Group homes, extended families, or bad imports that put many Contacts on one Household Account.

**How to avoid:** Decide the overrun count and text with the requester. Treat a household that hits the overrun as a data-quality signal and check whether Contacts were attached to the wrong Account.

**Source:** NPSP source, `objects/Household_Naming_Settings__c/fields/Contact_Overrun_Count__c.field-meta.xml`, `Name_Overrun__c.field-meta.xml`; `UTIL_CustomSettingsFacade.configHouseholdNamingSettings` (`Contact_Overrun_Count__c = 9`); `HH_NameSpec.strNameFromNameSpec`.

---

## Gotcha 8: Excluded Members Still Count as Household Members

**What happens:** A Contact can be left out of the household name, formal greeting, or informal greeting with the Exclude from Household Name / Formal Greeting / Informal Greeting checkboxes (kept in sync with `npo02__Naming_Exclusions__c` by `HouseholdNamingExclusionsCheckboxes`). Excluded members are removed from that string only. If every member is excluded, NPSP writes the anonymous household name or greeting instead.

**When it occurs:** Households with children, deceased members, or staff contacts.

**How to avoid:** Set exclusions per field, not one blanket rule, and test a household where all members are excluded so the anonymous text is approved.

**Source:** NPSP source, `objects/Contact/fields/Exclude_from_Household_Name__c.field-meta.xml` and siblings; `HH_NameSpec.cls` (method comments on exclusions, `HouseholdAnonymousName` and `HouseholdAnonymousGreeting` labels when the list is empty).

---

## Gotcha 9: Naming Order Falls Back to Primary Contact, Then CreatedDate

**What happens:** NPSP sorts members by `npo02__Household_Naming_Order__c` ascending with nulls last, then by the `Primary_Contact__c` checkbox formula, then by CreatedDate. When nobody sets the naming order, the primary contact comes first and the rest follow creation order. `Primary_Contact__c` is a read-only formula (`Account.npe01__One2OneContact__c = Id`), not a lookup on Account.

**When it occurs:** Couples where the second person was created first, or imports that create Contacts in an arbitrary order.

**How to avoid:** Set `npo02__Household_Naming_Order__c` explicitly when order matters. To change the primary contact, change `npe01__One2OneContact__c` on the Account.

**Source:** NPSP source, `main/selector/ContactSelector.cls` (`ORDER BY ... npo02__Household_Naming_Order__c ASC NULLS LAST, Primary_Contact__c DESC, CreatedDate`); `objects/Contact/fields/Primary_Contact__c.field-meta.xml`.

---

## Gotcha 10: The NPSP Contact Merge Page Takes Two or Three Contacts

**What happens:** The NPSP Contact Merge page refuses fewer than two or more than three selected Contacts. Large duplicate clusters cannot be merged in one pass.

**When it occurs:** Duplicate sets of four or more records for one person, common after repeated imports.

**How to avoid:** Merge clusters in passes of two or three, starting with the record that holds the most giving history as the winner. For large volumes, use a dedupe tool and follow Gotcha 1.

**Source:** NPSP source, `main/default/classes/CON_ContactMerge_CTRL.cls` (`loadMergeCandidates`: errors when the selection is at most 1 or more than 3).

---

## Gotcha 11: A Custom Naming Class Is Resolved by Name From Inside the Managed Package

**What happens:** NPSP reads `Implementing_Class__c` and calls `Type.forName(className)` from inside the managed package, both when the settings page validates the class and when names are generated. The Apex Reference Guide says this single-argument form returns null when called from an installed managed package for a local type in an org with no namespace, and recommends the two-argument form instead. If the class cannot be resolved, the settings page reports an invalid class, and the naming service has no implementation to call.

**When it occurs:** When an org registers its own class implementing `npsp.HH_INaming`, especially in orgs without a namespace.

**How to avoid:** Register the class in a sandbox first and confirm the settings page accepts it and Refresh Household Names produces the expected output. Keep the class `global` with `global` methods. UNVERIFIED (2026-10-03): whether declaring the class `global` changes the `Type.forName` result for a no-namespace org was not confirmed in any source read for this revision.

**Source:** NPSP source, `main/default/classes/HH_HouseholdNamingSettingValidator.cls` (`Type.forName(className)`), `main/service/HouseholdNamingService.cls` (`householdNamingImpl`); Apex Reference Guide (Spring '26), Type Class, `forName(fullyQualifiedName)` usage notes.
