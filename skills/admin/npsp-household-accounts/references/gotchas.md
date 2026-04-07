# Gotchas — NPSP Household Accounts

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Native Account Merge Bypasses NPSP Triggers — Never Use It for Household Accounts

**What happens:** When you merge two Household Accounts using the standard Salesforce Account merge UI, the merge executes at the database layer without invoking NPSP Apex triggers. Rollup fields (`npo02__TotalOppAmount__c`, `npo02__LastCloseDate__c`, `npo02__NumberOfClosedOpps__c`) are NOT recalculated. Relationship records (`npe4__Relationship__c`) pointing at the deleted Contact become orphaned. The household name on the surviving Account may not regenerate.

**When it occurs:** Any time an admin or automated process uses the native Salesforce Account merge UI (`/merge?mergeType=Account`), a Dataloader merge, or an Apex `Database.merge()` call without invoking NPSP's merge APIs for Household Account records.

**How to avoid:** Always merge duplicate NPSP household Contacts using the **NPSP Merge Duplicate Contacts** flow, launched from the Contact record. This flow uses NPSP-aware APIs that fire triggers, recalculate rollups, and clean up relationship records. For mass deduplication, use NPSP's batch deduplication tools or a managed deduplication package that integrates with NPSP's merge flow.

---

## Gotcha 2: Manually Overridden Household Names Get a "Customized" Flag That Silently Blocks Future Auto-Updates

**What happens:** If a user directly edits the Account Name, Formal Greeting, or Informal Greeting on a Household Account, NPSP sets an internal flag (`npo02__SYSTEM_CUSTOM_NAMING__c`) on that Account. From that point forward, NPSP will NOT regenerate the flagged field when Contact names change. The Account silently retains the manual value even if the underlying Contact names change completely (e.g., a Contact is renamed or a new Contact is added to the household).

**When it occurs:** Any inline edit of the household name or greeting fields on the Account record, including edits made via the UI, API, or data import tools. The flag is also set if a Flow or Apex class writes directly to these fields on a Household Account.

**How to avoid:** Before editing a household name manually, confirm whether the override is truly permanent (e.g., a trust or family foundation name). If the name just needs a one-time correction, use NPSP Settings > Refresh Household Names after fixing the underlying Contact data. If a permanent manual name is needed, document the customized flag in your data dictionary so future admins know not to expect auto-updates on those records.

---

## Gotcha 3: NPSP Household Account Model and FSC Household Group Model Are Incompatible — Do Not Mix Guidance

**What happens:** NPSP uses a direct Contact-to-Account lookup (`AccountId` on Contact) for household membership — a Contact belongs to exactly one Account (the Household Account). Financial Services Cloud (FSC) uses an `AccountContactRelationship` (ACR) junction object — a Contact can be associated with multiple Accounts simultaneously. The two models have different APIs, different triggers, different rollup mechanisms, and different naming automation paths.

**When it occurs:** Admins or AI assistants that confuse the two models attempt to apply FSC household configuration steps (e.g., setting `Primary_Group_Member__c` on ACR, using the FSC Household Group record type) to NPSP orgs, or vice versa. Both orgs show "Household" terminology in the UI but the underlying data models are entirely different.

**How to avoid:** Always confirm the org's cloud product before advising household configuration. In an NPSP org: look for the `npo02__` namespace, the `HH_Account` record type, and the `npo02__Household_Settings__c` custom setting. In an FSC org: look for the `FinServ__` namespace, ACR records, and the Household Group record type. NEVER apply NPSP household merge or naming guidance to an FSC org, and vice versa.

---

## Gotcha 4: Every New Contact Is Auto-Enrolled in a Household Account Unless Explicitly Moved to an Organization Account

**What happens:** NPSP's default behavior is to create a new Household Account for every Contact that does not already have one. If a Contact is imported or created without an `AccountId`, NPSP creates a new Household Account named "[Last Name] Household." This can produce a large number of single-Contact household accounts in orgs with high Contact import volumes.

**When it occurs:** Contact imports via Data Loader, API, or third-party integrations that set `AccountId` to null. Also occurs if the Contact's `Account.RecordType` is not explicitly set to Organization before NPSP triggers fire.

**How to avoid:** During Contact imports, always set the `AccountId` to the correct existing Household or Organization Account. If a Contact represents a business or staff member (not a household donor), pre-create or reference an Organization Account record type and assign it before inserting the Contact. Review NPSP Settings > Accounts to configure which Contact record types trigger Household Account creation.

---

## Gotcha 5: NPSP Naming Token Syntax Does Not Accept Salesforce Formula Functions

**What happens:** NPSP Household Naming format strings use NPSP's own double-brace token parser (`{!FieldName}`), not the standard Salesforce formula language engine. If an admin enters formula functions such as `UPPER({!LastName})`, `IF(...)`, or `TEXT(...)` into the Household Name Format field in NPSP Settings, NPSP will render those as literal text rather than evaluating them. The resulting household names will contain the raw formula text as a string.

**When it occurs:** Admins familiar with Salesforce formula fields attempt to add conditional logic or text transformations to NPSP naming format strings. This is especially common when trying to handle edge cases like salutation prefixes, honorifics, or conditional connectors.

**How to avoid:** Use only the token names documented by NPSP (standard Contact field API names wrapped in `{!...}`). For complex naming logic that cannot be expressed with simple token concatenation, use an NPSP Custom Household Naming class — a custom Apex class that implements the `HH_NameSpec_IF` interface and is registered in NPSP Settings > Household Naming > Custom Household Naming Class.
