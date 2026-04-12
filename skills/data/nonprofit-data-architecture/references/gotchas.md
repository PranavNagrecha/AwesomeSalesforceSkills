# Gotchas — Nonprofit Data Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: NPSP, Nonprofit Cloud (NPC), and FSC Household Groups Are Three Incompatible Architectures

**What happens:** A practitioner familiar with one nonprofit data model applies its patterns to an org on a different model. NPSP uses the HH_Account record type on standard Account to group household members. Nonprofit Cloud (NPC) is a separate product built on different foundational objects and does not use HH_Account at all. Financial Services Cloud (FSC) uses the `AccountContactRelationship`-based Household Group object (a different Account record type called "Household"). Applying NPSP SOQL, rollup patterns, or configuration guidance to an NPC or FSC org will produce schema errors, missing data, or incorrect calculations with no obvious error message.

**When it occurs:** Any time an org description mentions "nonprofit" or "household" without specifying the exact product. Mergers and acquisitions also produce orgs with FSC Household objects alongside NPSP HH_Account records — both can coexist in the same org.

**How to avoid:** Before applying any guidance from this skill, run `SELECT Id FROM npo02__Household_Settings__c LIMIT 1` to confirm NPSP is active. Then run `SELECT Id FROM RecordType WHERE SObjectType = 'Account' AND DeveloperName = 'HH_Account'` to confirm the HH_Account record type exists. If either query fails, you are not in a standard NPSP environment.

---

## Gotcha 2: pmdm__ Is a Separate Managed Package — PMM Is Not Part of NPSP Core

**What happens:** Code or configuration that references `pmdm__ServiceDelivery__c`, `pmdm__ProgramEngagement__c`, or `pmdm__Program__c` fails with "No such column" or "Invalid type" errors in NPSP orgs that do not have PMM installed. This is a silent incompatibility — NPSP does not list PMM as a dependency and will install fine without it.

**When it occurs:** Any time you attempt to query or reference PMM objects in an org where the Program Management Module package has not been installed. Also occurs after a sandbox refresh if PMM was installed in production but the sandbox was refreshed from a template org that did not include it.

**How to avoid:** Check installed packages via `SELECT SubscriberPackage.Name, SubscriberPackageVersion.MajorVersion FROM InstalledSubscriberPackage WHERE SubscriberPackage.NamespacePrefix = 'pmdm'` (in Tooling API) or verify via Setup > Installed Packages. Add a feature flag or org detection guard before any code path that accesses pmdm__ objects.

---

## Gotcha 3: CRLP and Legacy Rollup Mode Running Simultaneously Corrupt Rollup Fields

**What happens:** When CRLP is enabled but the legacy rollup scheduled batch job (`RLLP_OppRollup_BATCH`) is still running on a scheduled basis, both engines write to the same `npo02__TotalOppAmount__c` and related rollup fields. Each engine may overwrite the other's results depending on execution order. The result is rollup values that are inconsistently accurate — some Contacts show correct totals, others show doubled values or stale values from the last batch run.

**When it occurs:** During or after a CRLP migration when the legacy batch job was not explicitly removed from the scheduled jobs list. NPSP's migration wizard does not always remove the legacy job automatically in older NPSP versions.

**How to avoid:** After enabling CRLP, navigate to Setup > Scheduled Jobs and delete any job named `RLLP_OppRollup_BATCH` or `Opportunity Rollups`. Then run the NPSP Health Check (Nonprofit Success Pack > System Tools > NPSP Health Check) to confirm no conflicting rollup configuration is detected.

---

## Gotcha 4: npo02__ Rollup Fields on Contact vs. Account Have Different Scopes

**What happens:** Both `Contact` and `Account` (Household Account) have fields named `npo02__TotalOppAmount__c`, `npo02__LastOppAmount__c`, and related rollup fields. These fields have completely different scopes and often return different values. The Contact-level field aggregates only Opportunities where `npsp__Primary_Contact__c` equals that Contact. The Account-level field aggregates all Opportunities linked to the Household Account regardless of primary contact. For a household with two donors, the Account total is the household total, while each Contact's total is their individual giving.

**When it occurs:** Reports or dashboards that mix Contact-level and Account-level rollup fields without understanding the scope difference. This is especially common in household summary reports where the developer queries the wrong object.

**How to avoid:** For household-level giving totals (e.g., "total household giving"), always read rollup fields from the Account record. For individual constituent giving history (e.g., "this person's giving"), read from the Contact record. Document the scope in any report or dashboard that surfaces these fields.

---

## Gotcha 5: HH_Account Record Type DeveloperName Is Fixed But Display Name Is Configurable

**What happens:** NPSP allows administrators to rename the Household Account record type's display name through standard record type management. Queries and validation rules that filter on `RecordType.Name = 'Household Account'` break silently in orgs where the record type was renamed (e.g., to "Household", "Family Account", or an org-specific name).

**When it occurs:** Any org where an administrator renamed the Household Account record type. This is more common in large nonprofits that customize the UI extensively. The change is invisible until a query or validation built against the display name fails.

**How to avoid:** Always filter household accounts by `RecordType.DeveloperName = 'HH_Account'` — the developer name is protected by the NPSP package and cannot be changed. Never use `RecordType.Name` in code or query logic for NPSP account type detection.
