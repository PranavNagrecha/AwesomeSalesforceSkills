# Examples — Data Model Documentation

## Example 1: Field Inventory for a Service Cloud Onboarding

**Context:** A new admin joins an org that has been running Service Cloud for three years. No data dictionary exists. The team needs to document the Case and custom `Service_Contract__c` objects before a planned integration project begins.

**Problem:** The admin opens Object Manager and sees 85 fields on Case and 42 on `Service_Contract__c`. Most custom fields have blank Descriptions. Without documentation, the integration team cannot safely map fields without risking misuse (e.g., treating a legacy picklist as a current status field).

**Solution:**
1. Run an SFDX retrieve targeting both objects:
   ```bash
   sf project retrieve start --metadata "CustomObject:Case,CustomObject:Service_Contract__c"
   ```
2. In the retrieved `objects/Case/fields/` folder, scan each `.field-meta.xml` file for `<description>` tags. Fields with empty or absent tags are undocumented.
3. Build a spreadsheet from the XML: extract `<fullName>`, `<label>`, `<type>`, `<required>`, `<externalId>`, `<description>`, and `<referenceTo>` for lookup fields.
4. Share the spreadsheet with the business team and ask them to fill in blank Descriptions. This becomes the source-of-truth data dictionary.
5. After descriptions are populated, update the field metadata in the repo and deploy.

**Why it works:** The Metadata API returns every custom field property in a machine-readable format. Version-controlling the updated metadata means description changes are tracked over time, and future drift can be detected with a git diff.

---

## Example 2: ER Diagram for a Sales Process Workshop

**Context:** A BA is facilitating a sales process redesign workshop. Stakeholders need to understand how Lead, Contact, Account, Opportunity, and `Quote__c` relate to each other before the team can map their new process to the system.

**Problem:** Non-technical stakeholders do not understand Salesforce's data model. Without a clear diagram, discussions spiral into confusion about where data lives and who owns it.

**Solution:**
1. Open Setup → Object Manager → Schema Builder.
2. Clear all objects. Add: Lead, Contact, Account, Opportunity, Quote__c, OpportunityLineItem, Product2, Pricebook2.
3. Rearrange objects so the flow reads left to right: Lead → (converted to) → Contact/Account → Opportunity → OpportunityLineItem → Product2.
4. Toggle "Show Elements → Field Names" on for the relationship fields only (WhoId, AccountId, etc.).
5. Export via screenshot. Annotate in a drawing tool: label each arrow with "Lookup" or "Master-Detail", note that Lead conversion creates Contact + Account + Opportunity.
6. Present the diagram in the workshop. Note that the Lead-to-Opportunity conversion is a Salesforce process, not a direct relationship field.

**Why it works:** Schema Builder visualizes the physical Salesforce relationship model without requiring any custom tooling. Annotating conversion processes (which are not relationship fields) separately prevents the diagram from being misleading about how data moves.

---

## Anti-Pattern: Documenting Only Custom Objects

**What practitioners do:** When asked to "document the data model," admins sometimes produce documentation only for custom objects, skipping standard objects like Account, Contact, and Case because "everyone knows what those are."

**What goes wrong:** Integration projects and data migration plans break when custom fields on standard objects are undocumented. A custom field `Account.ERP_Customer_ID__c` used as the external ID for sync is functionally critical, but it lives on a standard object and gets skipped. New team members and integration partners have no idea the field exists or what it contains.

**Correct approach:** Include all custom fields on standard objects in the field inventory. Standard objects are not self-documenting — their custom fields need exactly the same treatment as fields on custom objects. Use the Metadata API retrieve for `CustomObject:Account`, `CustomObject:Contact`, etc. to extract just the custom additions without pulling in standard field definitions that are already in the Object Reference.
