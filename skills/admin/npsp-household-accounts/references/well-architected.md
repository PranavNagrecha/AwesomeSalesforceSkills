# Well-Architected Notes — NPSP Household Accounts

## Relevant Pillars

### Operational Excellence

NPSP Household Accounts are a configuration-heavy area where small missteps (e.g., using the wrong merge path or allowing batch name refresh jobs to fail silently) create data quality debt that compounds over time. Operational Excellence applies in three ways:

- **Naming consistency:** Format strings in NPSP Settings are a single configuration point that governs all household names org-wide. Changes take effect on the next trigger fire or batch refresh — poorly tested format strings can corrupt display names across thousands of Accounts before the issue is caught.
- **Batch job monitoring:** The "Refresh Household Names" batch job runs asynchronously. Orgs must monitor Apex Jobs (Setup > Apex Jobs) to confirm completion and catch partial failures in large orgs.
- **Customization flag hygiene:** Manual name overrides set a persistent flag. Without documentation and periodic audits, orgs accumulate an unknown number of "frozen" household names that diverge from Contact data.

### Reliability

- **Merge integrity:** The most significant reliability risk in this domain is reading household totals before NPSP's asynchronous merge fix-ups finish, or merging from batch Apex where the Account fix-up is skipped (`ACCT_AccountMerge_TDTM`). Rollup totals stay inaccurate until rollups are re-run, and the errors may not surface until a campaign or financial report reveals incorrect totals.
- **Trigger chain dependencies:** NPSP household naming relies on Apex triggers firing in the correct order. Third-party packages that also fire on Account or Contact update can interfere with NPSP trigger logic. Always test naming refresh after installing any package that touches Account or Contact.

---

## Architectural Tradeoffs

**Standard NPSP naming vs Custom Household Naming Class:** The built-in NPSP naming token format covers the majority of use cases (standard name concatenation up to the Contact Overrun Count, default 9). For complex scenarios (conditional honorifics, language-specific connectors, or custom business rules for household names), a custom Apex class implementing the global `HH_INaming` interface provides full programmatic control. The tradeoff is maintainability: a custom naming class requires Apex development and must be updated when NPSP releases breaking changes to the naming interface.

**Direct Contact-Account lookup vs ACR junction (NPSP vs FSC):** NPSP's direct lookup model is simpler — a Contact belongs to one Account — but it cannot represent a Contact who belongs to multiple households simultaneously (e.g., a child living in two homes). FSC's ACR junction solves this but adds complexity for gift processing, rollup maintenance, and naming. Do not attempt to retrofit FSC's ACR model onto an NPSP org.

**Auto-enrollment vs explicit Account assignment:** NPSP's auto-enrollment behavior creates Household Accounts automatically, reducing data entry burden but producing unwanted one-Contact households for imported staff or vendor Contacts. Orgs with mixed Contact populations (individual donors + organizational staff) must configure NPSP Account processor settings carefully to route non-donor Contacts to Organization Accounts.

---

## Anti-Patterns

1. **Using native or batch merges for Household Account deduplication without a follow-up check**: Merges fire NPSP's merge handlers, but their fix-ups run asynchronously and the Account fix-up is skipped in batch or future contexts. Prefer the NPSP Contact Merge page, and verify rollups after any other merge path.

2. **Treating NPSP household naming format strings as Salesforce formula fields** — NPSP's `{!Field}` tokens are parsed by NPSP Apex, not the formula engine. Entering formula functions like `UPPER()` or `IF()` produces literal text in the household name. Use only documented NPSP token names, or implement a Custom Household Naming Class for complex logic.

3. **Applying FSC household configuration guidance to NPSP orgs** — NPSP and FSC use incompatible household data models. ACR junction settings, FSC Household Group record types, and FSC naming automations have no equivalent in NPSP. Mixing guidance from the two products produces non-functional configurations.

---

## Official Sources Used

Read for the 2026-10-03 revision:

- NPSP source, naming implementation `HH_NameSpec.cls` and interface `HH_INaming.cls`: https://github.com/SalesforceFoundation/NPSP/tree/main/force-app/main/default/classes. Supports token parsing, last-name grouping, overrun handling, and the global interface name.
- NPSP source, `HouseholdNamingService.cls`, `HouseholdNamingUserControlledFields.cls`, `HouseholdSettings.cls`: https://github.com/SalesforceFoundation/NPSP/tree/main/force-app/main. Supports the user-controlled field list, the Automatic Household Naming gate, and implementing-class lookup.
- NPSP source, `HH_HouseholdNaming_BATCH.cls`, `HH_HouseholdNamingSettingValidator.cls`, `UTIL_CustomSettingsFacade.cls`: https://github.com/SalesforceFoundation/NPSP/tree/main/force-app/main/default/classes. Supports activation behavior, `Type.forName` validation, and the default settings values.
- NPSP source, `ContactSelector.cls`: https://github.com/SalesforceFoundation/NPSP/blob/main/force-app/main/selector/ContactSelector.cls. Supports the member sort order.
- NPSP source, merge handlers `ACCT_AccountMerge_TDTM.cls`, `CON_ContactMerge_TDTM.cls`, `CON_ContactMerge_CTRL.cls`, and `TDTM_DefaultConfig.cls`: https://github.com/SalesforceFoundation/NPSP/tree/main/force-app. Supports the asynchronous fix-ups, the batch/future gap, the two-to-three Contact limit, and default handler registration.
- NPSP source, object definitions (`Household_Naming_Settings__c`, `npo02__Households_Settings__c`, Contact fields `Primary_Contact__c` and `Exclude_from_Household_*`): https://github.com/SalesforceFoundation/NPSP/tree/main/force-app/main/default/objects
- Apex Developer Guide (Spring '26), Triggers and Merge Statements, and the Bulk API trigger chunking note: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Reference Guide (Spring '26), Type Class `forName`: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_reference_guide.pdf

Carried from earlier revisions (not re-read on 2026-10-03; help.salesforce.com does not render to a fetcher):

- What is the Household Account Model? — https://help.salesforce.com/s/articleView?id=sf.npsp_household_account_model.htm
- Customize Household Names — https://help.salesforce.com/s/articleView?id=sf.npsp_customize_household_name.htm
- Merge or Split Households — https://help.salesforce.com/s/articleView?id=sf.npsp_merge_households.htm
- Configure Household Naming — Trailhead NPSP module (help.salesforce.com/s/articleView?id=sf.npsp_household_naming_configure.htm)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
