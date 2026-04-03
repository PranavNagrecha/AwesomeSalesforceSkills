# Examples — Custom Field Creation

## Example 1: Sales Team Needs a Region Field on Opportunity

**Context:** A sales operations manager wants to capture the sales region on every Opportunity so that regional dashboards and assignment rules can use the data. The valid regions are fixed: North America, EMEA, APAC, LATAM.

**Problem:** The admin creates a Text field named "Region" and sets its length to 255. Users start entering inconsistent values ("NA", "N. America", "North America") that break dashboard filters. The admin has no way to enforce consistent values with a Text field without a validation rule and a hard-coded list.

**Solution:**

Create a Picklist field instead:

1. Object Manager → Opportunity → Fields & Relationships → New.
2. Select **Picklist** as the field type.
3. Label: `Sales Region`, API Name: `Sales_Region__c`.
4. Add values: `North America`, `EMEA`, `APAC`, `LATAM`. Leave "Sort values alphabetically" unchecked so values appear in the business-preferred order.
5. Set FLS: Read + Edit for Sales Rep profile, Sales Manager profile. Read-only for reporting profiles.
6. Add to Opportunity page layouts for Sales Rep and Sales Manager.
7. Mark field as Required if every opportunity must have a region before it can be moved to any closed stage.

**Why it works:** Picklist enforces a controlled vocabulary. Users cannot enter free-form text. Reports and dashboards filter on exact picklist API values, which are stable even if the label changes. FLS restricts edit access to prevent unauthorized value changes.

---

## Example 2: Support Team Needs to Track Customer Contract Expiry Date

**Context:** A service team tracks customer support contracts. They need to capture the contract expiry date on the Account object so that automated flows can trigger renewal outreach 30 days before expiry.

**Problem:** The admin creates a Text field and asks users to type the date as "MM/DD/YYYY". Dates entered inconsistently ("Jan 1 2026", "2026-01-01", "1/1/26") cannot be used in date functions in flows, reports, or formula fields without complex parsing logic.

**Solution:**

Create a Date field:

1. Object Manager → Account → Fields & Relationships → New.
2. Select **Date** as the field type. (Not Date/Time — no time component is needed.)
3. Label: `Contract Expiry Date`, API Name: `Contract_Expiry_Date__c`.
4. Help Text: "Enter the date the customer's support contract expires."
5. FLS: Read + Edit for Account Manager profile and Contract Admin profile. Read for Sales Rep profile.
6. Add to the Account page layout in the "Contract Information" section.
7. Verify in a sandbox: create a test account, enter the expiry date, confirm the date formula in a flow evaluates correctly (TODAY() vs Contract_Expiry_Date__c gives a numeric day difference).

**Why it works:** Date fields store values as ISO date strings internally. All Salesforce formulas, flows, reports, and Apex DML use this consistent storage format. The UI renders dates in the user's locale automatically, so international teams see correct regional date formats with no additional configuration.

---

## Example 3: Master-Detail vs Lookup — Order Line Items

**Context:** A team is building a custom object `Order_Line_Item__c` that belongs to a parent `Order__c` custom object. They need to display the total order value on the Order record by summing all line item amounts.

**Problem:** The admin creates a Lookup Relationship from `Order_Line_Item__c` to `Order__c`. When they try to create a Roll-Up Summary field on `Order__c` to sum the line item amounts, the option is greyed out. Roll-Up Summary requires a Master-Detail relationship.

**Solution:**

Use Master-Detail Relationship:

1. On `Order_Line_Item__c`, create a **Master-Detail Relationship** to `Order__c` (not a Lookup).
2. This makes `Order__c` the master object and `Order_Line_Item__c` the detail object.
3. On `Order__c`, create a **Roll-Up Summary** field:
   - Summary Type: **SUM**
   - Summarized Field: `Amount__c` on `Order_Line_Item__c`
   - Filter criteria: none (sum all line items)
4. The total order value is now always current and maintained by the platform without any Apex or Flow.

**Why it works:** Master-Detail is the only relationship type that enables Roll-Up Summary fields. The platform maintains the roll-up automatically whenever a child record is created, updated, or deleted. Using a Lookup would require a trigger or Flow to maintain the parent total, adding complexity and potential for stale data.

---

## Anti-Pattern: Creating a Text Field When a Picklist Is Needed

**What practitioners do:** They create a Text field because it feels more flexible — users can type anything. They plan to handle validation through instructions or training.

**What goes wrong:** Users enter inconsistent values. Reports show dozens of variations for the same logical value ("Enterprise", "Ent.", "enterprise", "ENT"). Dashboard filters break. Workflow criteria that compare the text value to a fixed string miss records with unexpected capitalization or spacing. The admin must build a complex validation rule to enforce the allowed values, which is exactly what a Picklist does by default.

**Correct approach:** When the field represents one of a known set of discrete values, use a Picklist. The platform enforces the allowed values by construction. If the values may expand over time, use a Global Value Set Picklist so the same values are shared and managed centrally across multiple objects.
