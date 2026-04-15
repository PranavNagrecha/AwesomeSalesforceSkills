# Gotchas — Nonprofit Data Quality

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Address Verification Does Not Retroactively Process Historical Records

**What happens:** An org administrator enables an address verification integration (Cicero, Google Geocoding, or SmartyStreets) under NPSP Settings > Address Settings and expects all existing `npsp__Address__c` records to be verified. In practice, only records created or updated after the integration is configured are sent through the verification service. Records created before the setup date retain `npsp__Verified__c = false` indefinitely.

**When it occurs:** Any org that migrated constituent data before enabling address verification, or any org that switched verification providers and previously had records verified with a different service (those records may retain old verification status fields that do not match the new provider's schema).

**How to avoid:** After enabling address verification, execute the `ADDR_Addresses_TDTM` batch class from Developer Console Anonymous Apex or the NPSP Bulk Data Processes UI (`/lightning/n/npsp__Batch_Data_Entry`). Use a batch size of 20–25 to stay within the per-transaction external callout limit. Monitor with `AsyncApexJob` queries until all records are processed.

---

## Gotcha 2: NCOA Requires a Separately Licensed Add-On and Is Incompatible With Agentforce Nonprofit

**What happens:** Practitioners assume NCOA processing is a standard NPSP feature or can be enabled with a configuration change. In reality, NCOA in Salesforce requires the **Insights Platform Data Integrity** add-on — a separately licensed premium subscription. There is no workaround using base NPSP.

Additionally, Insights Platform Data Integrity is explicitly **incompatible with Agentforce Nonprofit** orgs. Orgs running Agentforce Nonprofit cannot use the Insights Platform Data Integrity add-on.

**When it occurs:** Any time a nonprofit asks about NCOA processing in Salesforce without having the add-on licensed. Commonly discovered when a fundraising team asks for "NCOA processing" before a direct mail campaign without knowing the licensing model.

**How to avoid:** Before recommending NCOA in any work plan, confirm the Insights Platform Data Integrity add-on is in the org's license inventory. Check under Setup > Company Information > Licenses. If the org does not have it, the only alternatives are third-party NCOA processing (external to Salesforce, with results imported back via the `npsp__Address__c` object) or a manual address correction process.

---

## Gotcha 3: Native Salesforce Contact/Account Merge Breaks NPSP Rollup Fields

**What happens:** Using the standard Salesforce Contact merge (from the Contacts list view, the Account detail page Merge Contacts button, or programmatically via `Database.merge()`) does not invoke NPSP's TDTM trigger framework. As a result, Household Account rollup fields — including `npo02__TotalOppAmount__c`, `npo02__LastOppAmount__c`, `npo02__NumberOfClosedOpps__c`, and `npo02__AverageAmount__c` — are not recalculated. The surviving Household Account shows stale or incorrect giving totals until a manual recalculation is triggered.

Additionally, `npe4__Relationship__c` records linked to the losing Contact are not transferred to the winner and may be orphaned.

**When it occurs:** Data stewards using the standard UI merge tools, or developers using `Database.merge()` in Apex without awareness of NPSP's trigger dependencies.

**How to avoid:** Always use the **NPSP Contact Merge** button (available on the Contact record page when NPSP is installed) or navigate directly to `/apex/NPSP__merge?id={WinnerContactId}`. NPSP Contact Merge fires all relevant TDTM handlers including `RLLP_OppRollup` and `REL_Relationships_TDTM`. If standard merges have already occurred, trigger manual rollup recalculation for affected Household Accounts using `RLLP_OppRollup` batch Apex.

---

## Gotcha 4: Direct Edits to Contact Mailing Address Fields Are Overwritten by NPSP

**What happens:** If any process (manual edit, Flow, Apex trigger, data loader update) writes directly to Contact mailing address fields (`MailingStreet`, `MailingCity`, `MailingState`, `MailingPostalCode`), NPSP's address management synchronization process will overwrite those values with the fields from the linked default `npsp__Address__c` record on the next synchronization event (which can be triggered by a Contact save, a scheduled batch, or the seasonal address activation batch).

**When it occurs:** Flows or Apex triggers that update Contact address fields for formatting or standardization purposes; data loader jobs that set mailing addresses directly on Contact without going through the `npsp__Address__c` object; manual edits in the Contact record UI when NPSP's "Let NPSP manage household addresses" setting is active.

**How to avoid:** All address edits in an NPSP org must be made on the `npsp__Address__c` record, not on Contact or Account address fields. When writing Flows or Apex for address standardization, target `npsp__Address__c` as the object.

---

## Gotcha 5: Seasonal Address Activation Does Not Re-trigger Address Verification

**What happens:** Seasonal `npsp__Address__c` records (those with `npsp__Seasonal_Start_Month__c` and `npsp__Seasonal_End_Month__c` populated) are made active by a scheduled NPSP batch job. When a seasonal address becomes the active default, NPSP sets `npsp__Default_Address__c = true` on that record and synchronizes the address to the Contact and Household Account. However, the seasonal activation batch does not invoke the address verification callout — so a seasonal address that was never verified remains unverified even after being set as the default.

**When it occurs:** Any org using NPSP's seasonal address feature where seasonal addresses were loaded without going through the verification workflow. Discovered when constituents' summer/winter addresses show `npsp__Verified__c = false` even though the org has address verification configured.

**How to avoid:** After loading seasonal `npsp__Address__c` records, explicitly trigger address verification by saving the records (which fires the trigger and invokes verification for new/updated records), or run the `ADDR_Addresses_TDTM` batch scoped to unverified records after the seasonal load completes.
