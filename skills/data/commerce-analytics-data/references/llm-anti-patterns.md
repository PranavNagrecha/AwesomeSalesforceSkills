# LLM Anti-Patterns — Commerce Analytics Data

Common mistakes AI coding assistants make when generating or advising on Commerce Analytics Data.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Applying SOQL or Standard Reports to B2C Commerce Data

**What the LLM generates:** A SOQL query against `Order`, `OrderItem`, or custom objects expecting to find B2C Commerce storefront data; or instructions to build a standard Salesforce report for conversion rate or cart abandonment on a B2C Commerce storefront.

**Why it happens:** LLMs associate "Salesforce Commerce" with the Salesforce CRM platform and generate CRM-native tooling. B2C Commerce (SFCC) runs on a separate SaaS infrastructure with no native CRM objects. This distinction is not well-represented in general training data.

**Correct pattern:**

```
For B2C Commerce analytics:
→ Log into Business Manager (https://<instance>.demandware.net)
→ Navigate to Reports & Dashboards
→ Use the Conversion, Revenue, or Products dashboard

SOQL and standard Salesforce Reports do NOT apply to B2C Commerce data
unless an explicit integration has synced records into the CRM.
```

**Detection hint:** Any response that mentions `SELECT ... FROM Order WHERE ...` or "create a Salesforce Report" in the context of B2C Commerce storefront metrics is almost certainly wrong.

---

## Anti-Pattern 2: Not Distinguishing Between B2C Commerce and B2B Commerce Analytics

**What the LLM generates:** A single, unified analytics approach that treats "Salesforce Commerce" as one product — e.g., "go to the Commerce Analytics dashboard" without specifying which platform, or a SOQL query that the response claims works for both B2C and B2B Commerce.

**Why it happens:** "Salesforce Commerce" is often treated as a monolith in training data. B2C Commerce (SFCC) and B2B Commerce on Core are architecturally different products with completely different data stores and analytics surfaces. A B2C Commerce instance has no WebCart object; a B2B Commerce on Core instance has no Business Manager.

**Correct pattern:**

```
B2C Commerce (SFCC):
→ Analytics live in Business Manager Reports & Dashboards
→ No SOQL; no standard Salesforce Reports
→ Export capped at 1,000 rows; use SFTP feed for volume

B2B Commerce on Core:
→ No built-in analytics dashboard
→ Analytics via SOQL on WebCart, CartItem, OrderSummary
→ CRM Analytics B2B Commerce template if licensed
```

**Detection hint:** Any response that does not explicitly identify which Commerce platform it is addressing should be treated as ambiguous and clarified before proceeding.

---

## Anti-Pattern 3: Treating CRM Analytics as the Only or Default Option for Commerce Analytics

**What the LLM generates:** An instruction to "set up CRM Analytics" or "use Einstein Analytics" as the primary recommendation for any commerce analytics request, regardless of whether the org has a CRM Analytics license or whether a simpler native option exists.

**Why it happens:** CRM Analytics is prominent in Salesforce documentation and is a valid solution for B2B Commerce analytics. LLMs over-index on it as the "Salesforce analytics answer" and skip checking (a) whether the user is on B2C Commerce (where Business Manager already handles this natively), (b) whether CRM Analytics is licensed, and (c) whether SOQL is sufficient.

**Correct pattern:**

```
Decision order:
1. B2C Commerce? → Business Manager Reports & Dashboards (no additional license)
2. B2B Commerce + CRM Analytics licensed? → bi_template_b2bcommerce template
3. B2B Commerce, no CRM Analytics? → SOQL on WebCart/CartItem (free, always available)

Do not recommend CRM Analytics setup unless it is confirmed licensed.
```

**Detection hint:** Any response that starts with "install CRM Analytics" without first confirming the Commerce platform and license stack should be flagged.

---

## Anti-Pattern 4: Referencing the Retired Legacy Business Manager Analytics Module

**What the LLM generates:** Navigation instructions that reference "Business Manager > Analytics" as a standalone menu item, or describe a UI with chart-heavy "Analytics" screens that no longer match the current Business Manager interface.

**Why it happens:** The legacy Business Manager Analytics module was deprecated and retired on January 1, 2021. Training data from before that date (or undated content) describes the old module. The current surface is "Reports & Dashboards" with a different navigation path and feature set.

**Correct pattern:**

```
Current navigation (post-January 2021):
Business Manager → Merchant Tools → Reports & Dashboards
  or
Business Manager → Left navigation panel → Reports & Dashboards

Any reference to a standalone "Analytics" module in Business Manager
is outdated (retired 2021). Verify navigation against the current UI.
```

**Detection hint:** Navigation instructions that say "Business Manager > Analytics" without mentioning "Reports & Dashboards" are likely based on pre-2021 documentation.

---

## Anti-Pattern 5: Ignoring the 1,000-Row CSV Export Cap

**What the LLM generates:** An instruction to "export the product performance report to CSV" for analysis in Excel or a BI tool, without mentioning the 1,000-row limit or offering the SFTP feed alternative.

**Why it happens:** LLMs default to the simplest export mechanism (UI CSV download) and do not model platform-specific row-cap constraints. A practitioner following this advice on a large catalog will silently receive truncated data.

**Correct pattern:**

```
For exports ≤ 1,000 rows:
→ Business Manager dashboard > Export to CSV (acceptable)

For exports > 1,000 rows (large catalogs, row-level session data):
→ Use the SFTP Data Feed:
   Administration > Site Development > SFTP Data Feed
→ Configure endpoint, schedule, and data feed type
→ No row cap on SFTP feed delivery
```

**Detection hint:** Any export recommendation that does not mention the 1,000-row cap and the SFTP feed alternative is incomplete for B2C Commerce product or session-level analytics.

---

## Anti-Pattern 6: Using Incorrect WebCart Status Values for Abandonment

**What the LLM generates:** A SOQL query for cart abandonment that uses `Status != 'Closed'` or `Status = 'Open'` — neither of which matches the actual WebCart Status picklist values (`Active`, `Closed`, `PendingDelete`).

**Why it happens:** LLMs generalize from generic e-commerce data models where "open" or "pending" are common status values. The actual B2B Commerce on Core WebCart object uses specific Salesforce-defined picklist values that differ from common assumptions.

**Correct pattern:**

```soql
-- Correct: use Status = 'Active' for unordered carts
SELECT Id, AccountId, TotalAmount, CreatedDate
FROM WebCart
WHERE Status = 'Active'
  AND CreatedDate < LAST_N_DAYS:7

-- Wrong: 'Open' is not a valid WebCart Status value
-- Wrong: Status != 'Closed' catches PendingDelete carts unexpectedly
```

**Detection hint:** Any WebCart SOQL query that uses `Status = 'Open'`, `Status = 'Pending'`, or `Status != 'Closed'` without explicit intent to include PendingDelete carts is incorrect.
