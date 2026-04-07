# LLM Anti-Patterns — NPSP Household Accounts

Common mistakes AI coding assistants make when generating or advising on NPSP Household Accounts.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Native Account Merge UI for NPSP Household Deduplication

**What the LLM generates:**
```
"To merge duplicate household accounts, go to the Account record, click 'Merge Accounts',
select the master record, and complete the merge wizard."
```

**Why it happens:** LLMs are trained on general Salesforce documentation where the native Account merge UI is the standard deduplication path. The NPSP-specific merge requirement is a managed-package override that is underrepresented in general Salesforce training data.

**Correct pattern:**
```
To merge duplicate NPSP Household Contacts:
1. Navigate to the duplicate Contact record (not the Account).
2. Click "Find Duplicates" or use the NPSP Merge Duplicate Contacts quick action.
3. Complete the NPSP Merge Duplicate Contacts flow, selecting the master Contact.
4. Verify rollup totals on the surviving Household Account after the flow completes.

Do NOT use the native Salesforce Account merge UI — it bypasses NPSP Apex triggers
and leaves rollup fields stale and Relationship records orphaned.
```

**Detection hint:** Any advice referencing "Merge Accounts" button, `/merge?mergeType=Account` URL, or `Database.merge(Account...)` in Apex for Household Account types should be flagged as incorrect for NPSP orgs.

---

## Anti-Pattern 2: Confusing NPSP Household Account Model with FSC AccountContactRelationship Model

**What the LLM generates:**
```
"To add a Contact to a Household in Salesforce, create an AccountContactRelationship (ACR)
record linking the Contact to the Household Account, and set Primary_Group_Member__c = true."
```

**Why it happens:** Both NPSP and FSC use "Household" terminology, and the ACR junction model is heavily documented in FSC developer guides. LLMs conflate the two because the surface language is similar, even though the underlying data models are incompatible.

**Correct pattern:**
```
In NPSP, a Contact belongs to a Household Account via a direct lookup (Contact.AccountId).
There is no AccountContactRelationship junction object for household membership in NPSP.

To add a Contact to a Household Account:
1. Set the Contact's AccountId field to the Household Account ID.
2. NPSP triggers will update the Household Account's naming and rollups automatically.

AccountContactRelationship and Primary_Group_Member__c are FSC-specific fields.
Do not use them in NPSP orgs.
```

**Detection hint:** Any mention of `AccountContactRelationship`, `FinServ__` namespace fields, `Primary_Group_Member__c`, or "Household Group record type" in the context of NPSP should be treated as a model confusion error.

---

## Anti-Pattern 3: Using Salesforce Formula Functions Inside NPSP Household Naming Format Strings

**What the LLM generates:**
```
"Set the Household Name Format to: UPPER({!LastName}) & ' Household'
This will capitalize the last name in the household display name."
```

**Why it happens:** LLMs associate the `{!FieldName}` syntax with Salesforce formula fields and assume standard formula functions like `UPPER()`, `IF()`, `TEXT()`, and `&` concatenation work in the same context. NPSP's naming format parser is a custom Apex implementation that only supports token substitution, not formula evaluation.

**Correct pattern:**
```
NPSP Household Naming format strings only support field token substitution using {!FieldName} syntax.
Salesforce formula functions do NOT work in these strings.

Valid format string:  {!LastName}
Invalid format string: UPPER({!LastName})

For complex naming logic (conditional honorifics, special connectors), implement a custom
Apex class that implements the HH_NameSpec_IF interface and register it in
NPSP Settings > Household Naming > Custom Household Naming Class.
```

**Detection hint:** Any NPSP naming format string containing parentheses, formula operators (`&`, `+`), or standard formula function names (`UPPER`, `LOWER`, `IF`, `CASE`, `TEXT`) is applying incorrect formula field syntax.

---

## Anti-Pattern 4: Expecting NPSP Household Name to Auto-Update After Direct Account Field Edit

**What the LLM generates:**
```
"If the household name is wrong, just edit the Account Name field directly.
It will continue to auto-update when Contact names change in the future."
```

**Why it happens:** LLMs assume that editing a generated field is safe because the generation logic will simply overwrite it next time. NPSP's design is the opposite — it treats a manual edit as a deliberate customization and sets a flag to stop auto-overwriting.

**Correct pattern:**
```
In NPSP, directly editing the Account Name, Formal Greeting, or Informal Greeting on a
Household Account sets the npo02__SYSTEM_CUSTOM_NAMING__c customization flag.
Once this flag is set, NPSP will NOT regenerate that field on future Contact changes.

To correct a household name without freezing it:
1. Fix the underlying Contact data (name, salutation, naming order).
2. Use "Refresh Household Names" in NPSP Settings to re-trigger generation.
3. Do NOT edit the Account Name directly unless you intend a permanent manual override.

If a permanent manual name is required (e.g., a family trust name), editing directly is
acceptable — but document this decision so future admins know the field will not auto-update.
```

**Detection hint:** Any instruction to "edit the Account Name" or "update the Formal Greeting field directly" without mentioning the customization flag consequence should be flagged for NPSP household contexts.

---

## Anti-Pattern 5: Advising Direct AccountId Reassignment Without Considering NPSP Household Cleanup

**What the LLM generates:**
```
"To move a Contact to a different household, just update the Contact's AccountId field
to the new Household Account ID using a Data Loader update."
```

**Why it happens:** In standard Salesforce, updating `AccountId` on a Contact is the correct way to change Account association. LLMs apply this general rule without knowing that NPSP attaches additional logic — rollup recalculation, relationship management, and potentially household deletion — to Contact account changes.

**Correct pattern:**
```
In NPSP, moving a Contact to a different Household Account requires using the NPSP
"Change Account" functionality or the "Remove from Household" button on the Household Account,
not a direct AccountId field update via Data Loader.

Direct AccountId updates via Data Loader or API bypass NPSP triggers, which means:
- The original Household Account rollups are NOT recalculated (the departed Contact's giving
  history remains in the old household totals)
- The new Household Account rollups are NOT recalculated (the moved Contact's history is
  not added to the new household)
- The original Household Account may not be deleted even if it is now empty

Use the NPSP-provided UI actions or the npsp.HouseholdNamingService API for programmatic moves.
```

**Detection hint:** Any advice to update `Contact.AccountId` via Data Loader, API, or bulk tools for NPSP household transfers — without mentioning rollup recalculation or NPSP-specific move functions — is applying incorrect generic Salesforce logic.
