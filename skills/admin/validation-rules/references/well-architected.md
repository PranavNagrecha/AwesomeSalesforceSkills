# Well-Architected Mapping: Validation Rules

---

## Pillars Addressed

### Reliability

**Principle: Data Integrity at the Point of Entry**
Validation rules are the declarative enforcement layer for data quality. A record that enters the org wrong will cause problems downstream — in reports, integrations, automations, and analytics. Catching bad data at the source is cheaper than cleaning it later.

- WAF check: Are critical business rules enforced declaratively (can't be bypassed by accident)?
- WAF check: Do validation rules have bypass mechanisms so they don't block legitimate system operations?
- WAF check: Is the error message actionable — does it tell the user how to fix the problem?

**How this skill addresses it:**
- Mode 1 produces rules with correct formula structure and error messages
- Mode 2 surfaces rules that could silently block integrations
- Bypass patterns ensure rules don't become operational blockers

**Risk of not following this:** Data quality degrades. Reports built on the data produce incorrect outputs. Integrations fail silently. Support tickets spike every data migration.

### Operational Excellence

**Principle: Rules Are Maintainable and Documented**
A validation rule with no documentation, no bypass, and a one-word error message is a future support ticket. Rules need to be understandable to an admin who didn't write them.

- WAF check: Is each rule documented with its business justification?
- WAF check: Is there a bypass mechanism that doesn't require deactivating the rule in production?
- WAF check: Is the rule scoped to the right Record Types and contexts?

**How this skill addresses it:**
- The template in `templates/` captures business justification and ownership
- Naming conventions make rule purpose visible in the Setup menu
- Bypass pattern documentation prevents "deactivate in prod" anti-pattern

**Risk of not following this:** Admin turnover creates orphaned rules no one understands. Data migrations require disabling rules. Rules accumulate with no owner and no review cadence.

---

## Pillars Not Addressed

- **Security** — Validation rules don't enforce security (FLS/CRUD does). A validation rule can reference a field the user can't see, but that's a formula evaluation issue, not a security control.
- **Performance** — Cross-object validation rules add query overhead. Worth noting but rarely a primary concern unless on very high-volume objects (millions of records per day).
- **Scalability** — Validation rules scale declaratively with Salesforce's platform; no action required.
- **User Experience** — Partially addressed (error message quality), but UX design of the rule placement is out of scope.

---

## Governance Recommendations

**Who should own validation rules?**
- Business owner: defines the requirement ("Close Date required on Closed Opportunities")
- Salesforce Admin: translates to formula + tests + deploys
- Data/Integration team: reviews for impact on integrations before deployment

**Review cadence:**
- Audit active rules annually — check for inactive rules, rules with no bypass, rules tied to deprecated processes
- Review rules before any data migration
- Review rules when integrations are added or changed

**Change management:**
- Any new validation rule should be tested in sandbox with the integration user before production deployment
- Communicate to integration teams before deploying rules that affect objects they write to

## Official Sources Used

- Metadata API Developer Guide, **ValidationRule** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (element table used verbatim in `references/metadata-examples.md`: `active`, `description`, `errorConditionFormula`, `errorDisplayField`, `errorMessage`, `fullName`; the 255-character `errorMessage` cap; the errorDisplayField "changes automatically to Top of Page" behaviour; availability in API 12.0+; no compound fields as of API 20.0; custom metadata types as of API 40.0; no `*` wildcard in package.xml)
- Metadata API Developer Guide, **CustomObject** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (ValidationRule listed under "Declarative Metadata Additional Components"; the `.object` file suffix and `objects` folder location that `references/metadata-examples.md` Example 1 uses; the note that retrieving a CustomObject makes it appear in Profile and PermissionSet components retrieved in the same package)
- Metadata API Developer Guide, **CustomObjectTranslation / ValidationRuleTranslation** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (translated error messages are a separate `name` + `errorMessage` component, and packaged translations can override existing ones — the "Translated Error Messages Live in a Separate Metadata Type" gotcha)
- Metadata API Developer Guide, **Sample package.xml Manifest Files** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the `objectName.componentName` `<members>` syntax for CustomObject sub-components, shown for CustomField and ListView, that the ValidationRule manifest in `references/metadata-examples.md` follows)
- Apex Developer Guide, **Triggers and Order of Execution** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (before-save flows at step 3 and custom validation rules at step 5, which is why a before-save flow can repair data ahead of the rule; and step 11b, where a workflow field update re-saves without re-running custom validation rules — the Reliability claim that a validation rule alone is not a database invariant)
- Apex Developer Guide, **Trigger and Order of Execution Considerations** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (validation rules do not fire for an Opportunity when an opportunity product or product schedule changes it — the line-item gotcha)
- Apex Developer Guide, **Testing Apex** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (the `System.runAs` negative-test pattern and the `FIELD_CUSTOM_VALIDATION_EXCEPTION` status code asserted in the guide's own validation-rule test; and the API 28.0 change where `VLOOKUP` no longer reads org data from a running test)
- Apex Reference Guide, **Database.Error** — Summer '26 / v62 PDF, `Database.Error Methods` (`getStatusCode()`, `getMessage()`, `getFields()` used by both Apex tests in `references/metadata-examples.md`, and the note that the full status-code list lives in the org WSDL rather than the reference)
- Apex Developer Guide, **Debug Log Categories** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (the `Validation` log category records the rule name and whether it evaluated true or false — the troubleshooting step in `SKILL.md` Mode 3)
- Object Reference for the Salesforce Platform, **Opportunity** — local copy at `knowledge/imports/salesforce-channel-revenue-management.md:3903-3930` (the `HasOpportunityLineItem` field entry: type `boolean`, properties `Defaulted on create, Filter, Group, Sort`, and the "Read-only field that indicates whether the opportunity has associated line items" description behind Gotcha 15 and the products-before-Propose example) and `:4293-4302` (the Opportunity → Usage note that validation rules *do* fire when a child opportunity product update causes an update to the parent — recorded in Gotcha 15 as a direct conflict with the Apex Developer Guide claim cited above, unresolved)
- Object Reference for the Salesforce Platform, **OpportunityLineItem → Usage** — local copy at `knowledge/imports/salesforce-channel-revenue-management.md:4696` ("The Opportunity `HasOpportunityLineItem` field is set to true when an `OpportunityLineItem` is inserted for that Opportunity" — when the platform sets the field, and the basis for the derived claim that it is false during the Opportunity's own insert)
- `templates/admin/validation-rule-patterns.md` (repo canon) — the Custom Permission plus `Integration_Bypass__c` hierarchy Custom Setting bypass contract, the six valid uses of a validation rule, and the Bypass → Relevance gate → Business rule formula shape referenced throughout this skill
