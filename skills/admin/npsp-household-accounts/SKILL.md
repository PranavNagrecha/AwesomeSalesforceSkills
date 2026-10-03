---
name: npsp-household-accounts
description: "Use this skill to configure and manage NPSP Household Accounts: household naming rules, formal/informal greeting formats, primary contact designation, household merges, and household splits. Trigger keywords: NPSP household naming, household account not updating, merge duplicate households NPSP, household greeting customization, primary affiliation NPSP. NOT for FSC (Financial Services Cloud) households — use admin/household-model-configuration. NOT for bulk-loading constituents and households into NPSP — use data/constituent-data-migration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "configure NPSP household naming rules for households with different last names"
  - "merge duplicate household accounts in NPSP without corrupting rollup totals"
  - "household account name not updating after contact name change in NPSP"
  - "set up formal and informal greeting formats for NPSP households"
  - "primary contact designation for NPSP household account"
  - "change the household name format so couples with different last names both appear"
  - "fix NPSP household names after merging duplicate contacts"
tags:
  - npsp
  - nonprofit
  - household-accounts
  - naming
inputs:
  - NPSP package installed and Household Account model enabled (not Individual/Bucket model)
  - List of Contact names and household membership requirements
  - Desired household naming format (e.g., hyphenated last names, formal titles)
  - Whether any household names have been manually customized
outputs:
  - Configured Household Naming Settings with correct Name Format, Formal Greeting, and Informal Greeting strings
  - Primary Contact assigned per household
  - Duplicate households merged using NPSP-safe flow (not native Account merge)
  - Review checklist confirming naming regeneration and rollup integrity
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# NPSP Household Accounts

Use this skill when configuring the Nonprofit Success Pack (NPSP) Household Account model — including household naming formats, greeting strings, primary contact designation, and the correct procedure for merging or splitting duplicate households. This skill does NOT apply to Financial Services Cloud (FSC) Household Groups, which use a fundamentally different AccountContactRelationship junction model.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm NPSP is installed and the org uses the **Household Account** model, not the legacy Individual/Bucket Account model. Navigate to NPSP Settings > Households to verify.
- Identify which Contacts already have manually customized household names. The `npo02__SYSTEM_CUSTOM_NAMING__c` field on the Account holds a semicolon list of the fields the user controls (`Name;`, `Formal_Greeting__c;`, `Informal_Greeting__c;`). A value of `;` alone means nothing is user-controlled. Fields in that list will NOT auto-update on Contact changes.
- Know the Salesforce edition and NPSP package version — Household Naming format tokens (e.g., `{!{!FirstName}} {!LastName}`) are template strings evaluated by NPSP Apex (`HH_NameSpec`); they are not standard Salesforce formula syntax.
- Confirm Automatic Household Naming is on (`npo02__Advanced_Household_Naming__c` in Households Settings). When it is off, NPSP never regenerates names or greetings.
- Confirm whether any deduplication work is in scope. If so, plan to use the NPSP Contact Merge page (`CON_ContactMerge`) for Contacts, and know that native merges are cleaned up afterwards by NPSP's merge trigger handlers, asynchronously and not in batch or future contexts.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Is Automatic Household Naming turned on, and should it stay on? | Every naming feature depends on `npo02__Advanced_Household_Naming__c`; turning it on for the first time also marks existing non-default names as user-controlled (`HH_HouseholdNaming_BATCH`). | A yes/no plus a list of households whose current names must survive. | Existing hand-written household names are kept on purpose, not by accident. |
| How should couples with different last names, and households of ten or more people, read? | The default format already joins different last names with the Name Connector; past the Contact Overrun Count (default 9) NPSP writes the Name Overrun text instead of more names. | Sample households with the exact name, formal greeting, and informal greeting expected. | Format strings are tested against real edge cases before a refresh rewrites every household. |
| Which household members should be left out of the name or greetings? | Members can be excluded per field with the Exclude from Household Name / Formal Greeting / Informal Greeting checkboxes. | The rule (for example: children, deceased members, staff contacts). | Greetings on printed mail stop naming people who should not be named. |
| Who should appear first in names and greetings? | NPSP orders members by `npo02__Household_Naming_Order__c` (nulls last), then the Primary Contact formula, then CreatedDate. | A naming-order value per member, or acceptance of the primary-then-oldest default. | The order is deliberate and stable instead of depending on which Contact was created first. |
| How will duplicates be merged: NPSP Contact Merge page, native merge, or a batch dedupe tool? | NPSP fixes up native Account merges in a future method and native Contact merges in a queueable; Account merge fix-ups are skipped when the merge itself runs in a future or batch context (`ACCT_AccountMerge_TDTM`). | The tool and the context it runs in. | Rollups and names on surviving households are correct after a bulk dedupe, not stale. |
| Does any naming rule need logic the token syntax cannot express? | Format strings support field tokens only; conditional logic needs a custom class that implements the global `HH_INaming` interface. | A decision to stay with tokens or to build and register a custom class. | Complex rules live in tested Apex instead of half-working format strings. |

---

## Core Concepts

### 1. Auto-Enrollment and the Household Account Record Type

When a new Contact is created in an NPSP org using the Household Account model, NPSP automatically creates (or assigns) a Household Account with the record type `HH_Account`. The default naming pattern is `[Last Name] Household`. The Account holds three generated fields:

- **Name** (`Name`) — the public household name (e.g., "Smith Household" or "Smith and Jones Household")
- **Formal Greeting** (`npo02__Formal_Greeting__c`) — used on printed correspondence (e.g., "Mr. John Smith and Ms. Jane Jones")
- **Informal Greeting** (`npo02__Informal_Greeting__c`) — used in casual outreach (e.g., "John and Jane")

These three fields are regenerated by NPSP Apex triggers whenever a Contact's name fields change, according to the format strings configured in NPSP Settings > Households > Household Naming.

### 2. The "Customized" Flag and Manual Overrides

If a user edits the Household Account Name, Formal Greeting, or Informal Greeting fields directly, NPSP adds that field to the customization list in `npo02__SYSTEM_CUSTOM_NAMING__c` on the Account. Once a field is in the list, NPSP stops auto-updating that field and the manual value is preserved indefinitely. This is intentional behavior for households whose naming cannot follow a formula (e.g., donors who prefer a non-standard name). To resume auto-generation for a field, blank the field on the Account (or set it to NPSP's replacement text) and save; NPSP removes the field from the list on that save (`HouseholdNamingUserControlledFields`). The Refresh Household Names batch does not clear the list; it skips user-controlled fields.

### 3. Household Naming Format Tokens

NPSP naming strings use a double-brace token syntax:

- `{!{!FirstName}} {!LastName}` — evaluates per Contact and concatenates with NPSP's configured connector (e.g., " and ")
- Tokens are Contact field API names: `{!Salutation}`, `{!FirstName}`, `{!LastName}`, or any other Contact field such as `{!MailingCity}`. The `npo01__` prefix in older copies of this skill does not belong to any NPSP package.
- Defaults set by NPSP: Household Name Format `{!LastName} Household`, Formal Greeting `{!{!Salutation} {!FirstName}} {!LastName}`, Informal Greeting `{!{!FirstName}}`, Contact Overrun Count 9 (`UTIL_CustomSettingsFacade.configHouseholdNamingSettings`).

Tokens are resolved by NPSP Apex — they are NOT Salesforce formula language. Putting them in formula fields or Flow formulas will not work.

### 4. Merging Households — NPSP Flow vs Native Merge

NPSP Household Accounts carry rollup fields (total giving, last gift date, etc.) that are maintained by NPSP Apex triggers. When two household Contacts are duplicates:

- **Preferred path:** Use the **NPSP Contact Merge** page (Visualforce page `CON_ContactMerge`, two or three Contacts at a time). It merges Contact records with NPSP-aware logic and suppresses duplicate Affiliation creation during the merge.
- **Native merge:** Apex triggers do fire on merge, and NPSP registers handlers for it. `ACCT_AccountMerge_TDTM` (Account, after delete) refreshes household names and member counts, recreates household soft credits, and re-runs rollups in a future method. `CON_ContactMerge_TDTM` (Contact, after delete) queues a fix-up job. The risks are timing and context: totals lag until the async job runs, and the Account fix-up is skipped entirely when the merge runs in a future or batch context, which is where many bulk dedupe tools run.

---

## Common Patterns

### Pattern 1: Household Naming for Mixed-Last-Name Couples

**When to use:** Two Contacts in the same household have different last names (e.g., one donor kept their maiden name after marriage, or unmarried partners share a household).

**How it works:**
1. Navigate to NPSP Settings > Households > Household Naming.
2. Keep the **Household Name Format** as `{!LastName} Household` with Name Connector "and". NPSP already lists each distinct last name, so it produces "Smith and Jones Household." A format of `{!LastName}` alone drops the word Household.
3. Optionally use `{!{!FirstName}} {!LastName}` as the Formal Greeting format to produce "Jane Smith and John Jones."
4. If you need an entirely custom name (e.g., "The Smith-Jones Family"), edit the Account Name directly. NPSP will set the customization flag and stop auto-updating that field. All other fields can still auto-update if not also manually edited.

**Why not the alternative:** Do not attempt to create a formula field on Account that concatenates Contact names — Contacts are children of the Account and cannot be referenced in Account formula fields.

### Pattern 2: Assigning a Primary Contact to a Household

**When to use:** A household has multiple Contacts and you need to designate one as the primary for mail merge, correspondence, or reporting.

**How it works:**
1. On the Contact record, set the `npo02__Household_Naming_Order__c` field to `0` (lowest value = first). Other household members get higher values (1, 2, etc.).
2. NPSP uses this order to determine which Contact's name appears first in generated household names and greeting strings.
3. The Account's primary contact is the `npe01__One2OneContact__c` lookup. `Primary_Contact__c` is a read-only checkbox formula on Contact (`Account.npe01__One2OneContact__c = Id`), so it cannot be written; it only acts as the second sort key.

**Why not the alternative:** Do not rely on Contact creation order to determine naming order. NPSP sorts by `npo02__Household_Naming_Order__c` (nulls last), then the primary contact, and only then by CreatedDate (`ContactSelector.householdMembersQueryFor`).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Two Contacts with different last names in one household | Configure household name format to use Last Name token with " and " connector | NPSP concatenates tokens across all household members using the configured connector |
| Household name must be fully custom (e.g., family trust name) | Edit Account Name directly; accept customization flag | NPSP preserves manually entered names and flags them so auto-update stops |
| Merging two duplicate household Contacts | Use the NPSP Contact Merge page from the Contact | NPSP-aware merge; native merges are fixed up later and asynchronously |
| Household name stopped updating after Contact name change | Check `npo02__SYSTEM_CUSTOM_NAMING__c` and Automatic Household Naming; blank the overridden field to release it | Refresh Household Names skips user-controlled fields |
| Contact should belong to an Organization Account, not a Household | Move Contact to existing Organization Account via the Account lookup; NPSP will leave the household or create a new one depending on settings | NPSP supports both Household and Organization account types; Organization accounts are not auto-named |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify model and settings:** Confirm NPSP is installed with Household Account model active. Go to NPSP Settings > Households and note the current Name Format, Formal Greeting, and Informal Greeting strings before making any changes.
2. **Audit customized households:** Run a SOQL query for `SELECT Id, Name, npo02__SYSTEM_CUSTOM_NAMING__c FROM Account WHERE RecordType.Name = 'Household Account' AND npo02__SYSTEM_CUSTOM_NAMING__c != null` to identify households with manual overrides before configuring naming changes. Rows whose value is only `;` have no user-controlled field. Bulk name refreshes overwrite a name only after its field is removed from that list.
3. **Configure naming format:** Update the Household Name Format, Formal Greeting Format, and Informal Greeting Format strings in NPSP Settings > Households > Household Naming. Use NPSP's documented token syntax (double-brace `{!Field}`).
4. **Refresh household names:** After changing format strings, click "Refresh Household Names" in NPSP Settings to trigger a batch re-generation of all household names. Monitor the batch job status in Setup > Apex Jobs.
5. **Designate primary contacts:** For households where naming order matters, set `npo02__Household_Naming_Order__c` on each Contact — 0 for primary, 1+ for others. Verify the Household Account Name and greetings regenerate correctly.
6. **Merge duplicates safely:** For any duplicate household Contacts, use the NPSP Contact Merge page. If a native or batch merge was used, check Apex Jobs for the NPSP fix-up jobs and re-run rollups for survivors merged in batch context. Confirm rollup fields on the surviving Household Account reflect the combined giving history. Queries for the audit are in `references/metadata-examples.md`.
7. **Validate:** Spot-check Household Account Name, Formal Greeting, Informal Greeting, and rollup totals on a sample of merged or renamed households before closing the task.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] NPSP Household Account model confirmed active (not Individual/Bucket model)
- [ ] Household Name Format, Formal Greeting, and Informal Greeting strings verified in NPSP Settings
- [ ] Batch name refresh completed and Apex Jobs show no failures
- [ ] Any manually customized household names audited and intentional overrides documented
- [ ] Duplicate household merges performed with the NPSP Contact Merge page, or native/batch merges followed by a rollup check
- [ ] Rollup totals (`npo02__TotalOppAmount__c`, `npo02__NumberOfClosedOpps__c`) verified on surviving household after any merge
- [ ] Primary Contact naming order (`npo02__Household_Naming_Order__c`) set correctly for multi-member households

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Merge fix-ups are asynchronous and context-sensitive**: NPSP repairs names and rollups after native Account and Contact merges, but in a future method or queueable. Merges run from batch or future Apex skip the Account fix-up.
2. **Customization list silently blocks name updates**: A household field that was manually edited is listed in `npo02__SYSTEM_CUSTOM_NAMING__c`. NPSP will not regenerate that field even when Contact names change, and Refresh Household Names skips it.
3. **NPSP token syntax is not Salesforce formula syntax** — Naming format strings use NPSP's own `{!Field}` template parser. Formula functions such as `UPPER()` or `IF()` are not evaluated. See `references/gotchas.md` for the full list, including the overrun and exclusion settings.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Household Naming Settings | NPSP Settings > Households with confirmed Name Format, Formal Greeting, and Informal Greeting strings |
| Refreshed Household Names | Batch job result showing all household accounts regenerated with new format |
| SOQL audit query | Query identifying households with manual customization flags for documentation |
| Merge completion record | Notes confirming which Contact was retained, which was deleted, and that rollup totals were verified post-merge |

---

## Related Skills

- `financial-account-setup` — For FSC Financial Accounts under household models (FSC uses ACR junction — incompatible with NPSP direct lookup)
- `duplicate-management` — For platform-level duplicate rules and matching rules that feed into the NPSP merge flow
- `gift-entry-and-processing` — NPSP gift entry relies on correct Household Account association for rollup accuracy
