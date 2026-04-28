# LLM Anti-Patterns — Data Loader CSV Column Mapping

Common mistakes AI coding assistants make when generating CSV mappings, `.sdl` files, or Bulk API V2 ingest configs.

---

## Anti-Pattern 1: Recommending UPSERT with `externalIdFieldName` without verifying the External ID is unique and indexed

**What the LLM generates:**

```bash
sf data upsert -s Contact -f contacts.csv -i Email
```

…with no check that `Email` is `External ID = true, Unique = true`. The model assumes "Email looks unique, that's fine."

**Why it happens:** training data conflates "Email is usually unique in production data" with "Email is configured as a Salesforce External ID." The platform does not enforce uniqueness on `Email` by default, and `Email` is only an External ID on `Lead`/`Contact` if the org explicitly set it.

**Correct pattern:**

```bash
# 1. Verify the External ID configuration first
sf sobject describe -s Contact --json \
  | jq '.result.fields[] | select(.name=="Email") | {externalId, unique}'
# Expect: {"externalId": true, "unique": true}

# 2. Only then run the upsert
sf data upsert -s Contact -f contacts.csv -i Email
```

If `externalId` or `unique` is false, either pick a different External ID field or configure one before the load.

**Detection hint:** any `upsert` command or Bulk V2 `externalIdFieldName` config without a preceding describe-based verification.

---

## Anti-Pattern 2: Authoring `.sdl` with lower-case headers because "Data Loader is case-insensitive"

**What the LLM generates:**

```
externalid=External_Account_Id__c
accountname=Name
industry=Industry
```

**Why it happens:** the model knows Data Loader matches case-insensitively and optimises for typing convenience. It ignores that the same `.sdl` is often used in cross-tool pipelines where Bulk API V2 is strict.

**Correct pattern:**

```
External_Id=External_Account_Id__c
Account_Name=Name
Industry=Industry
```

Left-hand side matches the CSV header in the casing the CSV actually uses (so the producer of the CSV knows what to write), and the CSV header itself uses exact field API name casing where possible.

**Detection hint:** lower-case API name fragments on the right-hand side of `.sdl` lines (`accountname`, `myfield__c`); CSV headers in lower case in worked examples.

---

## Anti-Pattern 3: Recommending a single `WhoId` column for polymorphic Task loads with raw IDs

**What the LLM generates:**

```
Subject,WhoId,Status
"Follow up",003ABC...,"Open"
"Follow up",00QXYZ...,"Open"
```

**Why it happens:** Salesforce Id prefixes (`003` = Contact, `00Q` = Lead) do encode the type, so the model "knows" this works. It misses that the entire point of this skill is to avoid pre-resolving IDs — the producer of the CSV usually does not have Salesforce IDs.

**Correct pattern:**

```
Subject,Status,Who.Lead.Email,Who.Contact.Email
"Follow up","Open",,alice@example.com
"Follow up","Open",bob.lead@example.com,
```

Type-explicit External ID columns let the bulk job resolve at load time, so the CSV producer never needs Salesforce Ids.

**Detection hint:** any `WhoId` or `WhatId` column in a CSV example for an upsert workflow.

---

## Anti-Pattern 4: Suggesting "leave the column blank to use the field default"

**What the LLM generates:**

> If you want the `Status__c` field to use its default value of `'New'`, just leave the column blank in the CSV.

**Why it happens:** general-purpose intuition about defaults — "blank means default" — bleeds into Salesforce-specific advice. The model has not internalised that Salesforce defaults fire only when the field is **absent from the request**, not when it is present-and-empty.

**Correct pattern:**

> To let the `Status__c` default of `'New'` apply, **omit the `Status__c` column from the CSV entirely**. A blank cell will store null on Bulk API V2 (or leave the field unchanged on update) — the default will not fire.

**Detection hint:** any prose containing "leave blank" or "leave empty" in the same sentence as "default."

---

## Anti-Pattern 5: Submitting picklist labels instead of API names without warning the user

**What the LLM generates:**

```python
# CSV authored from a UI export
df["Industry"] = df["Industry"].fillna("Technologie")  # French label
df.to_csv("accounts.csv", index=False)
# ... loaded directly via Data Loader
```

**Why it happens:** the model treats picklist labels and API names as interchangeable because most English orgs have label == API name. It misses that translated orgs and global value sets diverge, and that the load API stores the literal text submitted.

**Correct pattern:**

```python
LABEL_TO_API = {"Technologie": "Technology", "Banque": "Banking", ...}
df["Industry"] = df["Industry"].map(LABEL_TO_API).fillna(df["Industry"])
# Validate every value matches a known API name
unknown = set(df["Industry"]) - set(LABEL_TO_API.values())
assert not unknown, f"Unmapped picklist values: {unknown}"
df.to_csv("accounts.csv", index=False)
```

Always translate labels to API names pre-load, and assert no unmapped values remain.

**Detection hint:** any picklist-column transformation in CSV prep code that does not consult a label-to-API-name mapping.

---

## Anti-Pattern 6: Claiming "the load succeeded" without recommending a post-load diff

**What the LLM generates:**

> The Bulk API V2 job returned `state: JobComplete` with `numberRecordsProcessed: 50000` and `numberRecordsFailed: 0`. The load was successful.

**Why it happens:** the model trusts the API's success signal as proof of correctness. It does not account for FLS-hidden fields, case-mismatched headers silently dropped, polymorphic ambiguity warnings logged but not surfaced, or picklist-label-as-free-text writes.

**Correct pattern:**

> Bulk API V2 reports `JobComplete` with no row errors. Run a post-load diff to confirm the data wrote as intended:
>
> ```sql
> SELECT Id, Name, External_Account_Id__c, Industry, AnnualRevenue
> FROM Account
> WHERE Id IN :loadedIds
> ```
>
> Spot-check 20 random rows against the source CSV. Any column that loaded null when the CSV had a value indicates FLS, case mismatch, or a silent drop — investigate before declaring the load complete.

**Detection hint:** any "load successful" or "load complete" claim in a runbook or post-mortem that ends without a diff query.

---

## Anti-Pattern 7: Using `#N/A` as a null sentinel in Bulk API V2 CSVs

**What the LLM generates:**

```
Id,Description__c
001ABC,#N/A
001DEF,#N/A
```

…with a comment "the `#N/A` will null out the field."

**Why it happens:** the model trained on Bulk API V1 examples and Data Loader UI documentation, where `#N/A` is the explicit null sentinel. Bulk API V2 dropped that convention — `#N/A` is now stored as the literal string `"#N/A"`.

**Correct pattern (Bulk V2):**

```
Id,Description__c
001ABC,
001DEF,
```

Blank cell on update means null. There is no sentinel.

**Detection hint:** the literal string `#N/A` in any CSV example aimed at Bulk API V2 (`/jobs/ingest`).
