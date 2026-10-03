# LLM Anti-Patterns — NPSP Household Accounts

Common mistakes AI coding assistants make when generating or advising on NPSP Household Accounts.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Native Account Merge Without Its Async and Batch-Context Caveats

**What the LLM generates:**
```
"To merge duplicate household accounts, go to the Account record, click 'Merge Accounts',
select the master record, and complete the merge wizard."
```

**Why it happens:** LLMs are trained on general Salesforce documentation where the native Account merge UI is the standard deduplication path. The opposite error is just as common: claiming native merge "bypasses NPSP triggers". The Apex Developer Guide (Triggers and Merge Statements) says a merge fires delete triggers on the losing records and an update trigger on the winner, and NPSP handles both (`ACCT_AccountMerge_TDTM`, `CON_ContactMerge_TDTM`). What merge does not do is fire triggers on reparented children such as Opportunities, which is why NPSP runs its own fix-up afterwards, asynchronously.

**Correct pattern:**
```
To merge duplicate NPSP Household Contacts:
1. Open the NPSP Contact Merge page (Visualforce page CON_ContactMerge).
2. Select two or three Contacts (the page rejects one, or four or more).
3. Choose the winning Contact and field values, then merge.
4. Verify rollup totals on the surviving Household Account.

If a native merge or a dedupe tool is used instead:
- NPSP repairs names and rollups in a future method (Account merge) or a
  queueable (Contact merge), so totals lag until those jobs finish.
- An Account merge run from batch or future Apex gets NO fix-up
  (ACCT_AccountMerge_TDTM checks !System.isFuture() && !System.isBatch()).
  Re-run rollups for those survivors.
```

**Detection hint:** Flag advice that uses "Merge Accounts", `/merge?mergeType=Account`, or `Database.merge(Account...)` for households without mentioning the asynchronous fix-up and the batch-context gap. Also flag any claim that native merge "bypasses NPSP triggers", and any mention of an "NPSP Merge Duplicate Contacts flow"; the NPSP merge UI is a Visualforce page, not a flow.

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
Apex class that implements the global npsp.HH_INaming interface and enter its name in
Household Naming Settings > Implementing Class (Implementing_Class__c, default HH_NameSpec).
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
Household Account adds that field to the npo02__SYSTEM_CUSTOM_NAMING__c list.
Once a field is listed, NPSP will NOT regenerate it on future Contact changes,
and Refresh Household Names skips it too.

To correct a household name without freezing it:
1. Fix the underlying Contact data (name, salutation, naming order, exclusions).
2. If the field was already overridden, blank it on the Account and save;
   NPSP removes it from the list and regenerates it.
3. Use "Refresh Household Names" in NPSP Settings for format changes across all households.
4. Do NOT edit the Account Name directly unless you intend a permanent manual override.

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

**Why it happens:** In standard Salesforce, updating `AccountId` on a Contact is the correct way to change Account association, and it is also correct in NPSP. The mistake runs the other way: LLMs claim API updates "bypass NPSP triggers". Apex triggers fire on DML from any source, including Data Loader and the Bulk API (Apex Developer Guide, Triggers; the guide describes Bulk API requests firing triggers in chunks of 200). NPSP's Contact handlers (`ACCT_IndividualAccounts_TDTM`, `HH_Households_TDTM`) run on those updates.

**Correct pattern:**
```
Updating Contact.AccountId through the UI, Data Loader, or the API fires NPSP's
Contact trigger handlers, so household naming and member counts follow the move.
Check these before a bulk move instead:
- NPSP Trigger Handler records for Contact are active (a load that deactivates
  TDTM handlers to go faster also turns off household maintenance)
- Automatic Household Naming is on, or names will not change
- Opportunities stay on the old Household Account; review whether giving history
  should move, because the move does not reparent Opportunities by itself
- Rollups on both households are verified after the load

Do not call npsp.HouseholdNamingService from subscriber code: the class is declared
public, not global, in the NPSP source, so it is not callable outside the package.
```

**Detection hint:** Flag any claim that Data Loader or API updates bypass NPSP triggers, and any reference to `npsp.HouseholdNamingService` as a public API. UNVERIFIED (2026-10-03): whether moving a Contact reparents its Opportunities was not traced through the NPSP source; confirm in a sandbox before a bulk move.

---

## Anti-Pattern 6: Inventing Household Naming Settings That Do Not Exist

**What the LLM generates:**
```
Household Name Format:       {!LastName}
Name Append Text:            " Household"
Formal Greeting Connector:   " and "
Informal Greeting Connector: " and "
```

**Why it happens:** The settings page reads like a template engine, so LLMs invent per-string connectors and suffix fields that a template engine might have.

**Correct pattern:**
```
Household_Naming_Settings__c fields (NPSP source, objects/Household_Naming_Settings__c):
  Household_Name_Format__c     default "{!LastName} Household"
  Formal_Greeting_Format__c    default "{!{!Salutation} {!FirstName}} {!LastName}"
  Informal_Greeting_Format__c  default "{!{!FirstName}}"
  Name_Connector__c            one connector shared by all three strings
  Name_Overrun__c              text used past the overrun count
  Contact_Overrun_Count__c     default 9
  Implementing_Class__c        default HH_NameSpec
Suffix text such as "Household" goes inside the format string itself.
```

**Detection hint:** Flag "Name Append Text", per-greeting connector fields, or a Household Name Format of `{!LastName}` presented as producing "... Household".
