# Well-Architected Notes — NPSP Household Accounts

## Relevant Pillars

### Operational Excellence

NPSP Household Accounts are a configuration-heavy area where small missteps (e.g., using the wrong merge path or allowing batch name refresh jobs to fail silently) create data quality debt that compounds over time. Operational Excellence applies in three ways:

- **Naming consistency:** Format strings in NPSP Settings are a single configuration point that governs all household names org-wide. Changes take effect on the next trigger fire or batch refresh — poorly tested format strings can corrupt display names across thousands of Accounts before the issue is caught.
- **Batch job monitoring:** The "Refresh Household Names" batch job runs asynchronously. Orgs must monitor Apex Jobs (Setup > Apex Jobs) to confirm completion and catch partial failures in large orgs.
- **Customization flag hygiene:** Manual name overrides set a persistent flag. Without documentation and periodic audits, orgs accumulate an unknown number of "frozen" household names that diverge from Contact data.

### Reliability

- **Merge integrity:** The most significant reliability risk in this domain is using the native Salesforce merge UI instead of the NPSP Merge Duplicate Contacts flow. This is a data corruption vector: rollup totals become inaccurate, relationship records become orphaned, and the errors may not surface until a campaign or financial report reveals incorrect totals.
- **Trigger chain dependencies:** NPSP household naming relies on Apex triggers firing in the correct order. Third-party packages that also fire on Account or Contact update can interfere with NPSP trigger logic. Always test naming refresh after installing any package that touches Account or Contact.

---

## Architectural Tradeoffs

**Standard NPSP naming vs Custom Household Naming Class:** The built-in NPSP naming token format covers the majority of use cases (up to 3-4 Contacts per household, standard name concatenation). For complex scenarios — conditional honorifics, language-specific connectors, or custom business rules for household names — a custom Apex class implementing `HH_NameSpec_IF` provides full programmatic control. The tradeoff is maintainability: a custom naming class requires Apex development and must be updated when NPSP releases breaking changes to the naming interface.

**Direct Contact-Account lookup vs ACR junction (NPSP vs FSC):** NPSP's direct lookup model is simpler — a Contact belongs to one Account — but it cannot represent a Contact who belongs to multiple households simultaneously (e.g., a child living in two homes). FSC's ACR junction solves this but adds complexity for gift processing, rollup maintenance, and naming. Do not attempt to retrofit FSC's ACR model onto an NPSP org.

**Auto-enrollment vs explicit Account assignment:** NPSP's auto-enrollment behavior creates Household Accounts automatically, reducing data entry burden but producing unwanted one-Contact households for imported staff or vendor Contacts. Orgs with mixed Contact populations (individual donors + organizational staff) must configure NPSP Account processor settings carefully to route non-donor Contacts to Organization Accounts.

---

## Anti-Patterns

1. **Using native Salesforce merge for Household Account deduplication** — The native merge UI does not invoke NPSP trigger logic. Rollup totals become stale, relationship records become orphaned, and household names may not regenerate. Always use the NPSP Merge Duplicate Contacts flow from the Contact record.

2. **Treating NPSP household naming format strings as Salesforce formula fields** — NPSP's `{!Field}` tokens are parsed by NPSP Apex, not the formula engine. Entering formula functions like `UPPER()` or `IF()` produces literal text in the household name. Use only documented NPSP token names, or implement a Custom Household Naming Class for complex logic.

3. **Applying FSC household configuration guidance to NPSP orgs** — NPSP and FSC use incompatible household data models. ACR junction settings, FSC Household Group record types, and FSC naming automations have no equivalent in NPSP. Mixing guidance from the two products produces non-functional configurations.

---

## Official Sources Used

- What is the Household Account Model? — https://help.salesforce.com/s/articleView?id=sf.npsp_household_account_model.htm
- Customize Household Names — https://help.salesforce.com/s/articleView?id=sf.npsp_customize_household_name.htm
- Merge or Split Households — https://help.salesforce.com/s/articleView?id=sf.npsp_merge_households.htm
- Configure Household Naming — Trailhead NPSP module (help.salesforce.com/s/articleView?id=sf.npsp_household_naming_configure.htm)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
