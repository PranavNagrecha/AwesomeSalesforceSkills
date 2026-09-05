# Metadata Examples — Quotes and Quote Templates

Deployable metadata for standard Salesforce Quotes. Everything here is shaped from the
Metadata API Developer Guide and Object Reference sample definitions and field tables
(Summer '26 / v66 PDFs), then extended to a realistic discount-governance example.

CPQ (`SBQQ__*`) is out of scope — see `admin/cpq-quote-templates` and
`architect/cpq-vs-standard-products-decision`.

---

## 0. The negative result you must design around: there is no `QuoteTemplate` metadata type

The Metadata API Developer Guide (Summer '26 / v66) contains the token `QuoteTemplate`
**exactly once**, and it is not a metadata type — it is a value of the `SummaryLayoutStyle`
enumeration on `Layout.SummaryLayout` (`api_meta.txt` L83165–83167, alongside
`DefaultQuoteTemplate`, `CaseInteraction`, `QuickActionLayoutLeftRight`,
`QuickActionLayoutTopDown`). There is no file suffix, no directory location, no field table
and no sample definition for a quote-template component anywhere in the guide.

Consequences for an agent building this:

| You might expect | Reality |
|---|---|
| `force-app/main/default/quoteTemplates/*.quoteTemplate-meta.xml` | Does not exist. A glob for it matches nothing, in every org. |
| `<name>QuoteTemplate</name>` in `package.xml` | Not a deployable type in the Metadata API guide. |
| Sandbox → production template promotion via `sf project deploy` | Not available. Rebuild the template in each org through Setup. |
| Git diff of a template change | Not available. Use the checklist artifact in §7 instead. |

The only *record-level* trace of a template is `QuoteDocument.DocumentTemplate` — "The ID
of the template used to generate the document", type `string`, properties
`Create, Filter, Group, Nillable, Sort` (`object_reference.txt` L240440–240448). That field
is what lets you audit, after the fact, which template produced a given PDF (§8).

So: the quote **template** is a Setup-only artefact with a reviewable checklist (§7); the
quote **behaviour around** the template — settings, statuses, fields, validation, layout —
is fully deployable (§1–§6).

---

## 1. `QuoteSettings` — turn Quotes on

`QuoteSettings` values live in a single file named `Quote.settings` in the `settings`
directory; the type is available in API version 28.0 and later
(`api_meta.txt` L124895–124904).

**`force-app/main/default/settings/Quote.settings-meta.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QuoteSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableQuote>true</enableQuote>
    <enableQuotesWithoutOppEnabled>false</enableQuotesWithoutOppEnabled>
</QuoteSettings>
```

**How to read it**

- `enableQuote` (boolean) — "When set to true, users can access Quotes."
  (`api_meta.txt` L124911). Nothing else in this file matters until this is `true`.
- `enableQuotesWithoutOppEnabled` (boolean, API 47.0+) — when `true`, users can create
  quotes independently of an opportunity; default is `false`, in which case quotes can only
  be created from an Opportunity (`api_meta.txt` L124913–124919).
- The guide carries an explicit one-way door on that flag: **"Before setting to false,
  delete any quotes that do not have opportunities."** (`api_meta.txt` L124918). Turning the
  setting off is not a safe rollback if standalone quotes already exist.
- Leaving it `false` also means `Quote.QuoteAccountId` stays unusable — that field
  (API 58.0+) is only available "when the Create Quotes Without a Related Opportunity
  setting on the Quotes Settings page is enabled" (`object_reference.txt` L239729–239736).
  With the setting off, the account comes from the parent opportunity via the read-only
  `Quote.AccountId` (properties `Filter, Group, Nillable, Sort` — no `Create`, no `Update`).
- The wildcard `*` in `package.xml` does not apply to feature settings; it applies only when
  retrieving all settings, not an individual one (`api_meta.txt` L124940–124942).

---

## 2. `StandardValueSet: QuoteStatus` — the statuses, and which ones may email a PDF

`Quote.Status` is backed by the standard value set named `QuoteStatus`
(`api_meta.txt` L142923). Components have the suffix `.standardValueSet` and live in the
`standardValueSets` folder; available in API version 38.0 and later
(`api_meta.txt` L130748–130755).

The standard options for `Quote.Status` are `—None—`, `Draft`, `Needs Review`, `In Review`,
`Approved`, `Rejected`, `Presented`, `Accepted`, `Denied`
(`object_reference.txt` L239996–240005).

The lever most admins miss lives on each value: `StandardValue.allowEmail` (boolean, API
18.0+) — **"Indicates whether this value lets users email a quote PDF (true), or not
(false). This field is only relevant for the Status field in quotes."**
(`api_meta.txt` L47538–47541). That is a platform-native gate on the Email Quote action,
per status. It is not a validation rule and it is not a permission.

**`force-app/main/default/standardValueSets/QuoteStatus.standardValueSet-meta.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Draft</fullName>
        <default>true</default>
        <isActive>true</isActive>
        <label>Draft</label>
        <allowEmail>false</allowEmail>
    </standardValue>
    <standardValue>
        <fullName>Needs Review</fullName>
        <default>false</default>
        <isActive>true</isActive>
        <label>Needs Review</label>
        <allowEmail>false</allowEmail>
    </standardValue>
    <standardValue>
        <fullName>In Review</fullName>
        <default>false</default>
        <isActive>true</isActive>
        <label>In Review</label>
        <allowEmail>false</allowEmail>
    </standardValue>
    <standardValue>
        <fullName>Approved</fullName>
        <default>false</default>
        <isActive>true</isActive>
        <label>Approved</label>
        <allowEmail>true</allowEmail>
    </standardValue>
    <standardValue>
        <fullName>Rejected</fullName>
        <default>false</default>
        <isActive>true</isActive>
        <label>Rejected</label>
        <allowEmail>false</allowEmail>
    </standardValue>
    <standardValue>
        <fullName>Presented</fullName>
        <default>false</default>
        <isActive>true</isActive>
        <label>Presented</label>
        <allowEmail>true</allowEmail>
    </standardValue>
    <standardValue>
        <fullName>Accepted</fullName>
        <default>false</default>
        <isActive>true</isActive>
        <label>Accepted</label>
        <allowEmail>true</allowEmail>
    </standardValue>
    <standardValue>
        <fullName>Denied</fullName>
        <default>false</default>
        <isActive>true</isActive>
        <label>Denied</label>
        <allowEmail>false</allowEmail>
    </standardValue>
</StandardValueSet>
```

**How to read it**

- `sorted` (boolean) is **Required** — "Indicates whether a global value set is sorted in
  alphabetical order. By default, this value is false." (`api_meta.txt` L130766–130768).
  Leave it `false` unless you genuinely want alphabetical order, because the pipeline order
  Draft → Review → Approved → Presented → Accepted is not alphabetical.
- `standardValue` is a `StandardValue[]`, and "When you deploy a StandardValueSet, this array
  must contain at least one picklist value. Otherwise, you receive an error."
  (`api_meta.txt` L130770–130774).
- `StandardValue` extends `CustomValue` and inherits `color`, `default`, `description`,
  `isActive`, `label` (`api_meta.txt` L47474–47535). Base-type elements come before the
  `StandardValue`-specific ones, which is why `allowEmail` is written last.
- **The dangerous line:** "If picklist values are missing from a component definition, they
  get deactivated when deployed. Deactivation occurs for picklist values of both standard and
  custom fields." (`api_meta.txt` L47481–47483). Deploying a *partial* `QuoteStatus` file
  silently deactivates every status you left out, breaking existing quotes and any Flow or
  validation rule that references them. Always retrieve first, edit, deploy the whole set.
- `StandardValueSet` "doesn't support the wildcard character `*` in the package.xml manifest
  file" (`api_meta.txt` L130830–130832) — name `QuoteStatus` explicitly (§5).
- `—None—` is the empty selection, not a deployable member; do not add it as a
  `standardValue`.

---

## 3. A custom field on `Quote`

`Quote` is a standard object, so a custom field on it is `Quote.<Name>__c` — the guide's own
example of that form is `Account.MyAcctCustomField__c` (`api_meta.txt` L43222–43223).

**`force-app/main/default/objects/Quote/fields/Contract_Term_Months__c.field-meta.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Contract_Term_Months__c</fullName>
    <label>Contract Term (Months)</label>
    <type>Number</type>
    <precision>4</precision>
    <scale>0</scale>
    <required>false</required>
    <trackHistory>true</trackHistory>
    <inlineHelpText>Mirrored from the parent Opportunity by the Quote_Populate_Mirror_Fields flow. Do not edit directly.</inlineHelpText>
    <description>Mirror field. Quote templates can only merge Quote and QuoteLineItem fields, so Opportunity values must be copied onto Quote to appear on the PDF.</description>
</CustomField>
```

**How to read it**

- Element names are from the `CustomField` field table: `label`, `type`, `precision`
  ("the number of digits"), `scale` ("the number of digits to the right of the decimal
  point"), `required`, `trackHistory`, `inlineHelpText`, `description`
  (`api_meta.txt` L43347–43696 field table).
- `trackHistory` is worth setting here specifically: `QuoteHistory` is available from API
  version 57.0 (`object_reference.txt` L240145–240147), so field history on Quote is a real
  audit surface for mirrored commercial values.
- **Why a mirror field at all:** the quote template's field picker resolves `Quote` and
  `QuoteLineItem` fields. Opportunity and Account values must be copied onto `Quote` first.
  UNVERIFIED (2026-09-05): the field-picker restriction is a Setup-UI behaviour of the quote
  template editor; it is not described in the Metadata API guide or the Object Reference, and
  help.salesforce.com cannot be fetched. It is retained because it is the premise of this
  skill's existing Pattern "Multi-Section Quote Template with Custom Header Fields".
- Do **not** try to solve this with a formula field that rolls up the quote total: the Object
  Reference states that `Quote.GrandTotal` "is a system-calculated summary field and is not
  directly referenceable or usable in custom formula fields on the Quote object. Attempts to
  do so result in an error message. For example, 'Error: Field GrandTotal does not exist.
  Check spelling.'" (`object_reference.txt` L239630–239637).

---

## 4. A `ValidationRule` on `Quote`

`ValidationRule` is available in API version 12.0 and later; `errorConditionFormula` and
`errorMessage` are both Required, and the error message "must be 255 characters or less"
(`api_meta.txt` L45376–45400).

**`force-app/main/default/objects/Quote/validationRules/Accepted_Requires_Line_Items.validationRule-meta.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Accepted_Requires_Line_Items</fullName>
    <active>true</active>
    <description>A quote cannot reach Accepted with no products on it. LineItemCount is the platform roll-up of QuoteLineItem records.</description>
    <errorConditionFormula>AND(
  ISPICKVAL(Status, &quot;Accepted&quot;),
  OR(ISBLANK(LineItemCount), LineItemCount = 0)
)</errorConditionFormula>
    <errorDisplayField>Status</errorDisplayField>
    <errorMessage>Add at least one quote line item before setting this quote to Accepted.</errorMessage>
</ValidationRule>
```

**How to read it**

- `LineItemCount` is a real standard field: type `int`, properties `Filter, Nillable`,
  "The number of line items on the quote." (`object_reference.txt` L239686–239691). It is
  nillable, which is why the formula tests `ISBLANK` as well as `= 0`.
- `errorDisplayField` is "the fully specified name of a field in the application... If you do
  not specify a value or the field isn't visible on the page layout, the value changes
  automatically to Top of Page" (`api_meta.txt` L45389–45394). If §6 does not put `Status` on
  the layout, this silently degrades to a page-top error.
- `active` is Required (`api_meta.txt` L45379–45381).
- `ValidationRule` "doesn't support the wildcard character `*` in the package.xml manifest
  file" (`api_meta.txt` L45437–45439).
- **Naming discrepancy to be aware of:** the guide's own sample definition for a validation
  rule writes the message element as `<validationMessage>` (`api_meta.txt` L45432), while its
  field table says the Required element is `errorMessage` (`api_meta.txt` L45376–45378). Use
  `errorMessage` — that is the documented field name and what a retrieve returns.
- **Do not write a rejection field update against `Quote.Discount`.** `Quote.Discount` is
  type `percent` with properties `Filter, Nillable, Sort` — no `Create`, no `Update` — and is
  defined as "The difference between the QuoteLineItem record's subtotal and its discounted
  total, divided by the QuoteLineItem's subtotal. Expressed as a percentage."
  (`object_reference.txt` L239578–239592). It is derived, not entered. The editable discount
  is `QuoteLineItem.Discount` (`percent`, `Create, Filter, Nillable, Sort, Update`, "Editable
  number from 0 to 100" — `object_reference.txt` L240758–240767), or the fixed-amount
  `QuoteLineItem.DiscountAmount` (API 59.0+, same properties). Read `Quote.Discount` in entry
  criteria; write `QuoteLineItem.Discount`.

---

## 5. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Quote</members>
        <name>Settings</name>
    </types>
    <types>
        <members>QuoteStatus</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Quote.Contract_Term_Months__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Quote.Accepted_Requires_Line_Items</members>
        <name>ValidationRule</name>
    </types>
    <types>
        <members>Quote-Quote Layout</members>
        <name>Layout</name>
    </types>
    <version>66.0</version>
</Package>
```

**How to read it**

- The `Settings` entry is exactly the guide's own package sample for `QuoteSettings` — member
  `Quote`, name `Settings` (`api_meta.txt` L124924–124931). "In the package manifest, all
  organization settings metadata types are accessed using the Settings name."
  (`api_meta.txt` L124886–124887).
- Every type in this manifest refuses the `*` wildcard, so all five are named explicitly:
  Settings (`api_meta.txt` L124940), StandardValueSet (`api_meta.txt` L130830),
  ValidationRule (`api_meta.txt` L45437). CustomField and Layout are named here because the
  target is a *standard* object — a wildcard would drag in the whole org.
- Layout member names embed a literal space (`Quote-Quote Layout`), matching the org's layout
  name. Quote it in shell arguments.

### Deploy order

Order matters because each step is a hard precondition for the next.

| # | Component | Why it must come first |
|---|---|---|
| 1 | `Settings: Quote` (`enableQuote`) | Until Quotes are on, `Quote` metadata has nothing to attach to. |
| 2 | `StandardValueSet: QuoteStatus` | §4's `ISPICKVAL(Status, "Accepted")` fails to compile if `Accepted` is inactive. Deploy the **complete** set (§2) or you deactivate what you omit. |
| 3 | `CustomField: Quote.Contract_Term_Months__c` | Formulas, layouts and flows that reference it cannot deploy before it exists. |
| 4 | `ValidationRule` | Depends on both the status values (2) and any custom field it references (3). |
| 5 | `Layout` | Depends on (3) for `layoutItems`, and gives `errorDisplayField` (§4) a field to point at. |
| 6 | Permission set FLS for the new field | Deploy after the field; without FLS the field is invisible on the record even though the PDF may still merge it. |

### Commands

```bash
# Retrieve the current state first — never author QuoteStatus from scratch (§2).
sf project retrieve start \
  --metadata "Settings:Quote" "StandardValueSet:QuoteStatus" "CustomObject:Quote" \
  --target-org my-sandbox

# Validate without committing (no components are saved).
sf project deploy start --manifest manifest/package.xml \
  --dry-run --target-org my-sandbox

# Deploy.
sf project deploy start --manifest manifest/package.xml \
  --target-org my-sandbox

# Production: validate-only first, then quick-deploy the validated run.
sf project deploy validate --manifest manifest/package.xml \
  --test-level RunLocalTests --target-org production
sf project deploy quick --use-most-recent --target-org production
```

---

## 6. `Layout` snippet — surfacing the field

`Layout.layoutSections` / `layoutColumns` / `layoutItems` with `behavior` and `field` follow
the guide's own layout sample (`api_meta.txt` L83300–83330); `relatedLists` takes
`RelatedListItem[]`, "the related lists for the layout, listed in the order they appear"
(`api_meta.txt` L82375).

**`force-app/main/default/layouts/Quote-Quote Layout.layout-meta.xml`** (excerpt)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Layout xmlns="http://soap.sforce.com/2006/04/metadata">
    <layoutSections>
        <editHeading>true</editHeading>
        <label>Commercial Terms</label>
        <layoutColumns>
            <layoutItems>
                <behavior>Required</behavior>
                <field>Status</field>
            </layoutItems>
            <layoutItems>
                <behavior>Edit</behavior>
                <field>ExpirationDate</field>
            </layoutItems>
            <layoutItems>
                <behavior>Edit</behavior>
                <field>Contract_Term_Months__c</field>
            </layoutItems>
        </layoutColumns>
        <layoutColumns>
            <layoutItems>
                <behavior>Readonly</behavior>
                <field>Discount</field>
            </layoutItems>
            <layoutItems>
                <behavior>Readonly</behavior>
                <field>Subtotal</field>
            </layoutItems>
            <layoutItems>
                <behavior>Readonly</behavior>
                <field>GrandTotal</field>
            </layoutItems>
        </layoutColumns>
    </layoutSections>
</Layout>
```

**How to read it**

- `Discount`, `Subtotal` and `GrandTotal` are `Readonly` because the platform says they are.
  `Subtotal` is `Filter, Nillable` — "The sum of sales price multiplied by quantity for line
  items, not including the discount"; `TotalPrice` is `Filter, Nillable` — "The total of the
  quote line items after discounts and before taxes and shipping"; `GrandTotal` is
  `Filter, Nillable` — "The total price of the quote plus shipping and taxes"
  (`object_reference.txt` L239609–240010). `Tax` and `ShippingHandling`, by contrast, *are*
  `Create ... Update` and can be edited.
- `Status` is `Create, Defaulted on create, Filter, Nillable, Update`
  (`object_reference.txt` L239990–239995) — safe to mark `Required` on the layout.
- This excerpt deliberately does **not** invent related-list names. The Quote Line Items
  related list has an org-specific `relatedList` value that you should take from an actual
  `sf project retrieve start --metadata "Layout:Quote-Quote Layout"` rather than guess; a
  wrong `relatedList` name fails the deploy.

---

## 7. The quote-template checklist (§0's replacement for XML)

Because there is no deployable template component, the reviewable artefact is a checklist
file that travels with the repo and is linted by
`scripts/check_quotes_and_quote_templates.py`. A starter lives at
`templates/quote-template-checklist.json`.

```json
{
  "template_name": "Standard Sales Quote 2026",
  "org": "production",
  "owner": "sales-ops@example.com",
  "last_reviewed": "2026-09-05",
  "sections": {
    "header": {
      "quote_fields": ["QuoteNumber", "ExpirationDate", "Contract_Term_Months__c"],
      "notes": "Only Quote fields merge here. Opportunity/Account values must be mirrored onto Quote first."
    },
    "line_items": {
      "columns": ["Product2Id", "Quantity", "UnitPrice", "Discount", "TotalPrice"],
      "sort_field": "SortOrder",
      "notes": "QuoteLineItem.SortOrder determines the order lines appear in the Quote PDF."
    },
    "footer": {
      "text_blocks": ["terms-and-conditions", "signature-block"],
      "notes": "Split long legal text across multiple blocks rather than one oversized block."
    }
  },
  "verified_in_org": {
    "pdf_generated": true,
    "line_items_rendered": true,
    "email_quote_tested": true,
    "statuses_allowing_email": ["Approved", "Presented", "Accepted"]
  }
}
```

**How to read it**

- `line_items.sort_field` is not decoration. `QuoteLineItem.SortOrder` (`int`,
  `Create, Filter, Group, Nillable, Sort, Update`, API 21.0+) — "The SortOrder value
  determines the order in which a quote line item appears in the Quote Line Items related
  list **and the Quote PDF**" (`object_reference.txt` L241417–241425). If line order on the
  customer-facing PDF matters, `SortOrder` is the only lever, and it is writable.
- `verified_in_org.statuses_allowing_email` must match the `allowEmail` values actually
  deployed in §2. The checker cross-references the two.
- The checker requires `template_name`, `org`, `last_reviewed`, `sections.header`,
  `sections.line_items`, `sections.footer` and `verified_in_org`.

---

## 8. Verification

### 8a. Setup check

Setup → Quotes Settings shows Quotes enabled and, separately, whether quotes may be created
without an opportunity — the two booleans from §1. Setup → Quote Templates lists the
templates; confirm the intended one is marked as the default before any customer-facing send.

### 8b. Reconciliation SOQL: synced quote vs. opportunity products

The whole point of sync is that the synced quote and the opportunity's products agree. This
query finds where they do not.

```sql
SELECT Id, Name, StageName, Amount, SyncedQuoteId,
       SyncedQuote.QuoteNumber, SyncedQuote.Status, SyncedQuote.IsSyncing,
       SyncedQuote.LineItemCount, SyncedQuote.Subtotal, SyncedQuote.TotalPrice,
       SyncedQuote.GrandTotal,
       (SELECT Id, PricebookEntryId, Product2Id, Quantity, UnitPrice, TotalPrice
        FROM OpportunityLineItems)
FROM Opportunity
WHERE SyncedQuoteId != NULL
  AND IsClosed = FALSE
ORDER BY LastModifiedDate DESC
```

Then, from the quote side, find lines that never bound to an opportunity product:

```sql
SELECT Id, QuoteNumber, Status, IsSyncing, LineItemCount, Subtotal, TotalPrice, GrandTotal,
       (SELECT Id, Product2Id, PricebookEntryId, Quantity, UnitPrice, ListPrice,
               Discount, TotalPrice, SortOrder, OpportunityLineItemId,
               HasQuantitySchedule, HasRevenueSchedule
        FROM QuoteLineItems)
FROM Quote
WHERE IsSyncing = TRUE
```

And the state that most often surprises people — more than one quote per opportunity
claiming to sync, or a quote flagged syncing whose opportunity points elsewhere:

```sql
SELECT Id, QuoteNumber, Status, IsSyncing, OpportunityId, Opportunity.SyncedQuoteId
FROM Quote
WHERE IsSyncing = TRUE
  AND OpportunityId != NULL
ORDER BY OpportunityId
```

**How to read the results**

- `Quote.IsSyncing` is `boolean`, `Defaulted on create, Filter` — read-only, "Indicates
  whether the quote is syncing with an opportunity" (`object_reference.txt` L239641–239648).
  You cannot write it; sync is driven from `Opportunity.SyncedQuoteID`
  (`Create, Filter, Nillable, Update` — `object_reference.txt` L192906–192912). Row three
  above should return at most one row per `OpportunityId`.
- `QuoteLineItem.OpportunityLineItemId` — "ID of the related opportunity line item. This
  field is populated by the API during creation of the quote line item. Not editable.
  Available in API version 40.0 and later." (`object_reference.txt` L240990–240998). A null
  here on a syncing quote is the reconciliation exception worth chasing.
- `HasQuantitySchedule` / `HasRevenueSchedule` are read-only booleans indicating whether the
  *opportunity line item the quote line is synced with* has a schedule
  (`object_reference.txt` L240848–240870). Any `true` here means writes to `Quantity`,
  `TotalPrice` or `GrandTotal` on that line will be ignored without an error — see
  `references/gotchas.md` Gotcha 8.
- UNVERIFIED (2026-09-05): the child relationship names `QuoteLineItems` and
  `OpportunityLineItems`, and the `SyncedQuote` parent relationship name on Opportunity, are
  not spelled out in the extracted Object Reference text (the `OpportunityLineItems` form
  does appear in prose at `object_reference.txt` L227785). Confirm with
  `sf sobject describe --sobject Quote --target-org <alias>` before shipping a query that
  depends on them.

### 8c. Which template produced which PDF

```sql
SELECT Id, Name, QuoteId, Quote.QuoteNumber, DocumentTemplate, Status,
       Discount, GrandTotal, CreatedDate, CreatedById
FROM QuoteDocument
WHERE CreatedDate = LAST_N_DAYS:30
ORDER BY CreatedDate DESC
```

`QuoteDocument` "Represents a quote in document format", available in API version 18.0 and
later (`object_reference.txt` L240388–240390). Its `Status` picklist is `Completed`,
`Failed`, `Generating`, `In Progress`, `None`, `Queued`, defaulting to `None`
(`object_reference.txt` L240478–240492) — `Failed` rows are generation failures nobody
noticed. `Discount` and `GrandTotal` on this object are the *snapshot* values at generation
time, which is how you prove what the customer actually received versus what the quote says
today.

---

## Sources

- Metadata API Developer Guide — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
