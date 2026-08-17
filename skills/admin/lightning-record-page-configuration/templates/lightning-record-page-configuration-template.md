# Lightning Record Page Assignment Matrix — [REPLACE: object API name]

The platform never renders this matrix in one place. This document is where it exists.

**Object:** `[REPLACE: e.g. Opportunity]`
**Page type:** `[REPLACE: RecordPage | AppPage | HomePage]`
**Author / owner:** [REPLACE: name]
**Date:** [REPLACE: YYYY-MM-DD]
**Org:** [REPLACE: production | sandbox name]

---

## 1. Page Inventory

Every Lightning page that exists for this object today. Populate from Setup > Lightning App Builder, or:

```soql
SELECT Id, DeveloperName, MasterLabel, Type, EntityDefinitionId, NamespacePrefix
FROM FlexiPage
WHERE Type = 'RecordPage' AND EntityDefinitionId = '[REPLACE: object name or EntityDefinition Id]'
```

| Page developer name | Label | Keep / retire | Why it exists |
|---|---|---|---|
| `[REPLACE: Opportunity_Record_Page]` | [REPLACE: Opportunity Record Page] | Keep | [REPLACE: the default for everyone] |
| `[REPLACE: Opportunity_Console_Page]` | [REPLACE: Opportunity Console] | Keep | [REPLACE: denser layout for inside sales in the console] |
| `[REPLACE: Opportunity_Old_2019]` | [REPLACE: Opportunity (old)] | Retire | [REPLACE: no owner found; superseded] |

---

## 2. Assignment Matrix

One row per override that will exist after this change. Rung 1 beats Rung 2 beats Rung 3.

| Rung | App | Record type | Profile | Form factor | Page | Metadata home |
|---|---|---|---|---|---|---|
| 3 — Org Default | (all) | (all) | (all) | `Large` | `[REPLACE: Opportunity_Record_Page]` | `objects/[REPLACE: Opportunity]/…object-meta.xml` |
| 2 — App Default | `[REPLACE: Sales_Console]` | (all) | (all) | `Large` | `[REPLACE: Opportunity_Console_Page]` | `applications/[REPLACE: Sales_Console].app-meta.xml` |
| 1 — App + RT + Profile | `[REPLACE: app]` | `[REPLACE: Object.RecordTypeName]` | `[REPLACE: Profile_Api_Name]` | `Large` | `[REPLACE: page]` | `applications/[REPLACE: app].app-meta.xml` |

**Form factor coverage.** `Large` is Lightning Experience desktop; `Small` is the Salesforce mobile app; an absent form factor on a `CustomObject` override means Salesforce Classic. State the decision explicitly:

- Mobile (Salesforce mobile app) in scope? [REPLACE: yes / no]
- If yes, which rows above are duplicated at `Small`? [REPLACE: list them, or "none — mobile keeps the platform default"]

**Overrides being deleted.** List every existing override this change removes, and who confirmed it is safe:

| App | Profile | Record type | Page it pointed at | Confirmed by |
|---|---|---|---|---|
| `[REPLACE: app]` | `[REPLACE: profile]` | `[REPLACE: record type]` | `[REPLACE: page]` | [REPLACE: name / date] |

---

## 3. Component Visibility Register

Every rule on the page, and the business reason for it. Operators are limited to `EQUAL`, `NE`, `CONTAINS`, `GT`, `GE`, `LT`, `LE`. Expressions may span no more than five fields.

| Component / field | `leftValue` | `operator` | `rightValue` | `booleanFilter` | Reason |
|---|---|---|---|---|---|
| `[REPLACE: Record.Invoice_Number__c]` | `{!Record.RecordType.DeveloperName}` | `EQUAL` | `[REPLACE: Billing]` | — | [REPLACE: billing cases only] |
| `[REPLACE: riskPanel LWC]` | `{!$Permission.CustomPermission.[REPLACE: name]}` | `EQUAL` | `true` | — | [REPLACE: risk team only; permission-set assignable] |
| `[REPLACE: mobileSummary]` | `{!$Client.FormFactor}` | `EQUAL` | `Small` | — | [REPLACE: phone-only summary card] |

**Security check.** For each rule above, state whether the hidden data also needs field-level security. A visibility rule hides the field on screen only; the field stays readable via API, reports, list views, and Apex.

- [ ] No rule in this register is standing in for field-level security
- [ ] Any rule that *is* about confidentiality has a matching FLS change recorded here: [REPLACE: permission set names and fields, or "none"]

---

## 4. Deployment Manifest

The page and its assignment are three metadata types. A manifest naming only `FlexiPage` ships an inert page.

```xml
<!-- manifest/package.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>[REPLACE: Opportunity_Record_Page]</members>
        <name>FlexiPage</name>
    </types>
    <types>
        <members>[REPLACE: Opportunity]</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>[REPLACE: Sales_Console]</members>
        <name>CustomApplication</name>
    </types>
    <version>[REPLACE: 64.0]</version>
</Package>
```

```bash
sf project deploy start --manifest manifest/package.xml \
  --target-org [REPLACE: target] --dry-run
```

**Pre-deploy confirmations:**

- [ ] Every profile named in a Rung 1 row already exists in the target org
- [ ] Every record type named in a Rung 1 row already exists in the target org
- [ ] No production admin has hand-edited these assignments since the last deploy

---

## 5. Validation

Run the checker against the local metadata before deploying:

```bash
python3 skills/admin/lightning-record-page-configuration/scripts/check_lightning_record_page_configuration.py \
  --manifest-dir [REPLACE: force-app/main/default]
```

Then verify against reality, not against the Activation dialog — the dialog shows what you set, not what resolves.

| # | Check | Result |
|---|---|---|
| 1 | Checker exits 0 (no unassigned pages, no over-capacity regions, no missing identifiers, no invalid operators, no pre-API-49 shape) | [REPLACE: pass / fail] |
| 2 | Logged in as a user on each profile in the matrix; each landed on the expected page | [REPLACE: pass / fail — list the users tested] |
| 3 | Opened the same record from each app in the matrix; precedence resolved as designed | [REPLACE: pass / fail] |
| 4 | Checked the Salesforce mobile app if `Small` is in scope | [REPLACE: pass / fail / not in scope] |
| 5 | Each record type opened at least once; record-type visibility rules fired correctly | [REPLACE: pass / fail] |
| 6 | No region exceeds 100 components | [REPLACE: pass / fail — record the largest count] |
| 7 | Retired pages have no remaining override pointing at them | [REPLACE: pass / fail] |

**Sign-off:** [REPLACE: name, date]

---

## 6. Notes and Deviations

[REPLACE: record anything done differently from the patterns in SKILL.md and why — e.g. "kept a second page for Field Service because the tab structure genuinely differs, not just the fields".]
