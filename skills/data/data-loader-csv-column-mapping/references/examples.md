# Examples — Data Loader CSV Column Mapping

Three worked examples covering External ID upsert, polymorphic Task.WhoId, and the picklist label-vs-API-name trap.

---

## Example 1: Contact upsert binding to Account by External ID

**Context:** nightly sync from a CRM-of-record into Salesforce. Source system holds an `External_Account_Id__c` value on every account; Contacts must bind to the right Account without the loader pre-resolving Salesforce IDs.

**Problem:** the naive approach is to issue a SOQL query per row to look up the Account Id, then write it into a `AccountId` column. This burns API calls (1 per row) and races against concurrent inserts.

**Solution — Data Loader CLI with `.sdl`:**

CSV header (exact field API name casing for cross-tool safety):

```
External_Contact_Id__c,FirstName,LastName,Email,Account.External_Account_Id__c
EXT-C-001,Alice,Nguyen,alice@example.com,EXT-A-001
EXT-C-002,Bob,Schmidt,bob@example.com,EXT-A-001
EXT-C-003,Carla,Diaz,carla@example.com,EXT-A-002
```

Data Loader `.sdl`:

```
External_Contact_Id__c=External_Contact_Id__c
FirstName=FirstName
LastName=LastName
Email=Email
Account\.External_Account_Id__c=Account.External_Account_Id__c
```

(The dot in the relationship column needs escaping in `.sdl` only on the left-hand side parsing — the right-hand side is the literal API path.)

Operation: **Upsert** with `External ID = External_Contact_Id__c`.

**Why it works:** Bulk API V2 resolves `Account.External_Account_Id__c` to the matching `Account.Id` server-side, in the same transaction as the Contact upsert. Zero pre-load SOQL, deterministic match because `External_Account_Id__c` is `External ID = true, Unique = true`.

---

## Example 2: Task.WhoId polymorphic upsert

**Context:** a marketing automation platform exports Activities targeting both Leads and Contacts. The `WhoId` is polymorphic, and the source CSV has one row per Activity with the target's email and a `Type` discriminator.

**Problem:** a single `WhoId` column with bare emails fails — the API has no way to choose between Lead.Email and Contact.Email. A single `Who.Email` column is also ambiguous in the same way.

**Solution — explicit type-prefixed columns:**

```
Subject,Status,ActivityDate,Who.Lead.Email,Who.Contact.Email,What.Account.External_Account_Id__c
"Follow up demo","Completed",2026-04-28,,alice@example.com,EXT-A-001
"Trial signup","In Progress",2026-04-28,bob.lead@example.com,,
"Pricing question","Open",2026-04-28,,carla@example.com,EXT-A-002
```

Each row populates exactly one of the two `Who.<Type>.Email` columns. The unused side is left blank — the API resolves whichever side has a value.

**Why it works:** Bulk API V2's relationship-name path supports the form `Who.<Type>.<ExternalIdField>` precisely to disambiguate polymorphic lookups. Lead/Contact emails are inherently unique-per-record by org convention, so they serve as External IDs without a custom field.

**Watch out for:** if both `Who.Lead.Email` and `Who.Contact.Email` are populated on the same row, the row errors. Source-side validation must guarantee mutual exclusion before export.

---

## Example 3: Picklist label vs API name silent corruption

**Context:** an org translated to French. The `Industry` picklist has API name `Technology` and French label `Technologie`. A business analyst exports a CSV from a French-rendered report (which shows labels) and loads it back via Data Loader.

**Problem:** Data Loader accepts the CSV. The job reports green. Records load with `Industry = "Technologie"` written as a free-text value because the picklist's "Restrict to defined values" is off (a common default for legacy orgs). Reports filtering on `Industry = 'Technology'` exclude the loaded records. Reports filtering on `Industry = 'Technologie'` include them — but the analyst is looking for `Technology` and concludes the load lost data.

**Solution — translate labels to API names pre-load:**

Step 1: pull the picklist API names from describe:

```bash
sf sobject describe -s Account --json \
  | jq '.result.fields[] | select(.name=="Industry") | .picklistValues[].value'
```

Output:

```
"Agriculture"
"Apparel"
"Banking"
"Technology"
"Telecommunications"
```

Step 2: build a translation table (label → API name) for every picklist column.

Step 3: pre-process the CSV:

```python
import csv

LABEL_TO_API = {
    "Technologie": "Technology",
    "Banque": "Banking",
    "Agriculture": "Agriculture",
    # ...full set...
}

with open("src.csv") as fin, open("loadable.csv", "w", newline="") as fout:
    r = csv.DictReader(fin)
    w = csv.DictWriter(fout, fieldnames=r.fieldnames)
    w.writeheader()
    for row in r:
        if row["Industry"] in LABEL_TO_API:
            row["Industry"] = LABEL_TO_API[row["Industry"]]
        w.writerow(row)
```

Step 4: load `loadable.csv`. Spot-check post-load with `SELECT Industry, COUNT(Id) FROM Account GROUP BY Industry` — every value should be an API name from the describe.

**Why it works:** the load API stores the literal text submitted. With "Restrict to defined values" off, anything is accepted. By forcing the input to API names, the loaded values match what every SOQL filter, formula field, and Flow condition expects.

---

## Anti-Pattern: blind column-name → field-name match without verifying types

**What practitioners do:** open the CSV, see headers like `Date`, `Amount`, `Phone`, and assume Data Loader will figure it out — match `Date` to whatever the first date-shaped field is.

**What goes wrong:**

- `Date` could match `CloseDate` (Date) or `LastModifiedDate` (DateTime, not writeable) or a custom `Date__c` (Date) — Data Loader's UI suggests the alphabetically first match. The CLI errors on ambiguity in some versions, silently picks one in others.
- `Amount` mapped to a `Currency(18,2)` field accepts a string `"1,234.56"` in en-US locale but errors in fr-FR locale where the decimal separator is `,`.
- `Phone` mapped to a `Phone` field gets auto-formatted in some Salesforce editions, leaving the loaded value different from the CSV value.

**Correct approach:**

1. Author the CSV header as the **exact field API name** — `CloseDate`, `Amount`, `Phone`. No ambiguity to resolve.
2. Run the type-compatibility check: `scripts/check_data_loader_csv_column_mapping.py --csv-header header.csv --describe-json describe.json` flags type mismatches before the load.
3. For currency and dates, normalise the CSV to API formats (`1234.56`, `yyyy-MM-dd`) at export time, not at load time.
