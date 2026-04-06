# LLM Anti-Patterns — Quotes and Quote Templates

Common mistakes AI coding assistants make when generating or advising on Salesforce Quotes and Quote Templates. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Multiple Quotes Can Be Synced Simultaneously

**What the LLM generates:** Advice such as "sync all your quote variants to the opportunity so products stay current" or code that iterates over quotes and calls sync on each one expecting all to remain synced simultaneously.

**Why it happens:** LLMs generalize from CRM concepts where multiple child records can all be "linked" to a parent. The platform constraint that only one quote can hold `IsSyncing = true` per opportunity is not intuitive from the data model alone.

**Correct pattern:**

```text
Only ONE quote per opportunity can be synced at a time.
Opportunity.SyncedQuoteId holds the ID of the single synced quote.
Starting sync on a second quote automatically stops sync on the first.
Draft quotes that are not synced do not update opportunity products.
```

**Detection hint:** Any instruction or code that iterates over multiple quotes and calls "Start Sync" or sets `IsSyncing = true` without first stopping sync on existing quotes.

---

## Anti-Pattern 2: Recommending Standard Quote Templates for CPQ Quote Lines

**What the LLM generates:** Instructions to create a standard Quote Template in Setup and configure it to display CPQ (SBQQ) quote lines in the PDF body table.

**Why it happens:** LLMs conflate "Salesforce Quotes" and "Salesforce CPQ Quotes" because both are marketed as quoting tools on the Salesforce platform. The distinction between `QuoteLineItem` (standard) and `SBQQ__QuoteLine__c` (CPQ) is often missing from training data context.

**Correct pattern:**

```text
Standard quote template body: renders QuoteLineItem records only.
CPQ quote lines: stored in SBQQ__QuoteLine__c — NOT rendered by standard templates.
For CPQ quotes: use CPQ SBQQ Document Templates
  (Setup > Installed Packages > Salesforce CPQ > Document Templates).
Do NOT advise using standard quote templates for CPQ quotes.
```

**Detection hint:** Any recommendation to use Setup > Quote Templates for a quote in an org with CPQ installed, without checking which quote line object is in use.

---

## Anti-Pattern 3: Claiming Custom Opportunity Fields Auto-Map to Quote Fields

**What the LLM generates:** Advice like "your custom Opportunity fields will automatically appear on the related Quote when the quote is created" or "Salesforce maps opportunity custom fields to quote fields the same way it maps lead fields during conversion."

**Why it happens:** Lead Conversion has a well-known field mapping mechanism. LLMs incorrectly generalize this behavior to the Opportunity-to-Quote relationship, which has no equivalent declarative mapping.

**Correct pattern:**

```text
There is NO platform-native field mapping from Opportunity/OpportunityLineItem
to Quote/QuoteLineItem.
Custom fields must be:
  1. Manually created on the Quote/QuoteLineItem object.
  2. Populated via Record-Triggered Flow on Quote creation/update, OR via custom Apex.
Lead Conversion field mapping (Setup > Lead Conversion Mapping) does NOT apply to Quotes.
```

**Detection hint:** Any claim that opportunity custom fields "appear on" or "are copied to" the quote without a Flow or Apex implementation step.

---

## Anti-Pattern 4: Advising System Administrator Users to Test Approval Processes

**What the LLM generates:** Test instructions like "log in as an admin and submit a quote with a 20% discount to verify the approval fires correctly."

**Why it happens:** LLMs default to SysAdmin credentials in testing instructions because it is the most permissive and commonly referenced role. The approval bypass behavior for SysAdmins is an edge case not always represented in training data.

**Correct pattern:**

```text
System Administrators with "Modify All Data" bypass approval process entry criteria.
ALWAYS test approval processes with a user profile that matches the actual submitter role
(e.g., Sales Representative profile without admin permissions).
Create a dedicated test user in the sandbox for this purpose.
If tested only as SysAdmin, the approval may NEVER fire for real users in production.
```

**Detection hint:** Test instructions that reference logging in as a System Administrator or using the SysAdmin profile to validate approval process behavior.

---

## Anti-Pattern 5: Treating Quote PDF as a Saved Snapshot Immune to Template Changes

**What the LLM generates:** Statements like "once you generate the PDF, it is saved on the quote record and will not change" or "the PDF attached to the quote is the final version that will be emailed."

**Why it happens:** LLMs assume that the "Generate PDF" action creates a static file. While Salesforce saves the PDF as a file on the record when the user clicks "Save PDF," the "Email Quote" button re-generates the PDF at send time from the current template state — it does not use the previously saved file.

**Correct pattern:**

```text
"Save PDF" button: creates a static PDF file attached to the quote record.
"Email Quote" button: re-generates a new PDF from the current template at send time.
  Does NOT use the previously saved PDF file.
If the template changes between "Save PDF" and "Email Quote," the customer receives
  the new version, not the reviewed version.
To guarantee the customer receives the exact reviewed PDF:
  1. Save the PDF as a Salesforce File on the quote.
  2. Email it as a manual attachment, NOT via the "Email Quote" button.
```

**Detection hint:** Any statement that the quote PDF "is saved" and will be the version emailed to the customer without qualifying that "Email Quote" re-generates from the current template.

---

## Anti-Pattern 6: Referencing Opportunity or Account Fields Directly in Quote Template Merge Fields

**What the LLM generates:** Template configuration instructions that include merge fields like `{!Opportunity.Name}`, `{!Account.BillingCity}`, or `{!Opportunity.Custom_Field__c}` directly in the quote template header or footer.

**Why it happens:** Salesforce merge fields work across object relationships in many contexts (email templates, formula fields). LLMs extrapolate this to quote templates without checking the specific field picker constraints.

**Correct pattern:**

```text
Quote template field picker only surfaces:
  - Quote object fields
  - QuoteLineItem fields (in the body table)
Opportunity and Account fields are NOT directly available as merge fields in quote templates.
Workaround: create mirror fields on Quote, populate via Flow, then use those Quote fields
  in the template field picker.
```

**Detection hint:** Any merge field in a quote template configuration that references a parent object (Opportunity, Account, Contact) rather than a Quote or QuoteLineItem field.
