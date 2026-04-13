# Gotchas — Industries Communications Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Account RecordType Segmentation — Billing, Service, and Consumer Are NOT Separate Objects

**What happens:** Developers and admins expect the Communications Cloud data model to have distinct Billing Account, Service Account, and Consumer Account objects (analogous to how Insurance Cloud has an InsurancePolicy object). Instead, all three are RecordTypes on the standard Account object. Any code or configuration that queries, triggers on, or processes Account records without filtering by RecordType will mix all three subtypes, producing incorrect data processing, workflow misfires, and corrupted relationships.

**When it occurs:** Any time an Apex trigger, Flow, Process Builder rule, or SOQL query references the Account object without a `RecordType.DeveloperName` filter. Most commonly encountered when standard CRM code is reused or adapted for a Communications Cloud org.

**How to avoid:** Enforce a code review rule that every Account query in a Communications Cloud org must include `WHERE RecordType.DeveloperName IN ('Billing_Account', 'Service_Account', 'Consumer_Account')` or a specific single-type filter. Use `RecordType.DeveloperName` (not `RecordType.Name`, which is locale-sensitive) in all SOQL and Apex. Add this check to the org's standard code review checklist.

---

## Gotcha 2: Industries Order Management Is Not Salesforce Order Management (B2C/B2B Commerce)

**What happens:** Practitioners searching for "order management" documentation or APIs in a Communications Cloud context land on Salesforce Order Management documentation (part of the Commerce platform). They attempt to use `OrderSummary`, `FulfillmentOrder`, `OrderDeliveryGroup`, and Commerce REST APIs for Communications Cloud order processing. None of these objects or APIs exist or function in the Communications Cloud order model. The result is missing field errors, "Object not found" API responses, and completely absent fulfillment records.

**When it occurs:** During initial setup when a developer is unfamiliar with Industries products, or during a migration from a Commerce-based solution to Communications Cloud. Also occurs when asking a generic Salesforce AI assistant for order management help without specifying the platform.

**How to avoid:** In Communications Cloud, all order management references must point to the Industries Order Management documentation and the `vlocity_cmt` namespace. Key objects are different: commercial orders use the standard Order object with Industries extensions, and technical orders use vlocity_cmt decomposed order objects. Always prefix documentation searches with "Communications Cloud" or "Industries Order Management" to avoid Commerce order management results.

---

## Gotcha 3: EPC Order Decomposition Requires Child Items — Direct Product2 Configuration Breaks Fulfillment

**What happens:** An admin creates product records directly in Product2 (standard Salesforce products) without creating corresponding EPC Product Offerings and ProductChildItem records. Orders placed against these products create commercial order records successfully but generate no technical order records. The Industries Order Management decomposition engine silently skips products that have no EPC child item structure, producing no error message and no fulfillment output.

**When it occurs:** When administrators with a standard Salesforce CRM or CPQ background configure products the way they would for a standard org. Also occurs during data migrations when legacy product data is loaded directly into Product2 without going through EPC import tooling.

**How to avoid:** Always configure products through the EPC app (Product Specification → Product Offering → Catalog Assignment). For data migrations, use the EPC bulk import tooling provided with the Communications Cloud package rather than direct Product2 data loads. After any product configuration, run a test order and verify that technical order records are generated before moving to production.

---

## Gotcha 4: Permission Sets Must Be Assigned Before Any EPC Configuration

**What happens:** An admin attempts to access the EPC app or configure catalog records before assigning Communications Cloud permission sets. The EPC app either does not appear in App Launcher, or appears but shows no records and provides no error message. Catalog configuration appears to save successfully but records are not visible to other users or downstream processes.

**When it occurs:** During initial org setup, before the implementing admin has assigned themselves the Communications Cloud Admin permission set. This is counterintuitive because standard Salesforce System Admins have full access to most configuration screens, but Communications Cloud EPC visibility is controlled at the permission set level on top of the System Admin profile.

**How to avoid:** Make permission set assignment step 1 of any Communications Cloud org setup. Assign `Vlocity_Communications_Admin` (or the equivalent Communications Cloud Admin permission set for the installed package version) to the implementing admin before opening the EPC app. Verify by confirming that EPC objects appear in Object Manager and that catalog records are visible after creation.

---

## Gotcha 5: TM Forum Order Decomposition Requires Commercial-to-Technical Mapping — Skipping This Step Breaks Provisioning

**What happens:** An implementing team configures EPC, creates test orders, and sees commercial order records created correctly. They mark order management as complete. When the technical team attempts to trigger network provisioning, no technical order records exist. The decomposition step between commercial and technical order was never configured.

**When it occurs:** When teams are unfamiliar with TM Forum SID order decomposition concepts and treat the commercial order as the final order artifact. The Communications Cloud decomposition engine does not auto-decompose without explicit decomposition rule configuration pointing commercial order items to their EPC child item counterparts.

**How to avoid:** After EPC catalog configuration, explicitly configure and test the order decomposition rules in Industries Order Management. Decomposition rules map commercial order line items to technical fulfillment actions based on EPC child item definitions. Test by placing a commercial order and verifying that corresponding technical order records are created in the vlocity_cmt decomposed order objects before declaring order management setup complete.
