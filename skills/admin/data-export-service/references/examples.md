# Examples — Salesforce Data Export Service

## Example 1: Monthly evidence archive runbook for an Enterprise org

**Context:** A 3-million-row org running Enterprise Edition, no budget for Salesforce Backup and Restore yet, regulatory requirement to maintain "monthly evidence of record state" for 7 years.

**Problem:** The team currently schedules a weekly Data Export, downloads it irregularly, and has lost three months of exports to the 48-hour expiration window. The compliance team thinks they have backups.

**Solution:**

1. Reduce cadence to monthly (the obligation is monthly evidence, not weekly recovery). This frees the operator from weekly toil and matches the actual requirement.
2. Configure scope:

   ```
   Setup → Data Management → Data Export → Schedule Export
   - Frequency: Monthly
   - Day: 1st of month, 02:00 org time zone
   - Include All Data: yes (Account, Contact, Opportunity, Case, custom objects)
   - Include images, documents, and attachments: NO (binary content not required for evidence)
   - Include Salesforce Files: NO
   - File-size split: 512 MB
   - Notification recipient: data-export-ops@company.example
   ```

3. Build the runbook:

   - Notification arrives → on-call operator (rotation) downloads ZIP set within 12 hours
   - Operator runs `sha256sum *.zip` and posts to ledger
   - Operator uploads to AWS S3 bucket `acme-sfdc-monthly-exports` with object-lock retention 7 years
   - Operator records: export-date, downloaded-by, S3 object IDs, sha256 sums in a Jira ticket
   - Backup operator reviews within 24 hours; reconciles missing-month gaps

4. Architecture doc passage:

   > Salesforce data evidence archive: monthly Data Export Service runs to S3 with 7-year object-lock retention. This is **evidence archive, not backup**. Record-level restore is not in scope of this control. Restoration of accidentally-deleted records relies on Recycle Bin (15 days) and standard escalation. A formal record-level backup control will be implemented when Backup and Restore licensing is approved (FY tracking ticket: ARCH-1247).

5. Quarterly restore drill: on a clean sandbox, load the Account + Contact + Opportunity CSVs from the most recent archive via Data Loader, verify row counts match the export manifest, document outcome.

**Why it works:** the obligation is *evidence*, not RPO/RTO. Framing it correctly avoids the "we have backups" trap. The runbook makes the 48-hour window an SLA the team owns rather than a recurring failure mode.

---

## Example 2: One-time full-org snapshot for a data-warehouse seed

**Context:** A new BI initiative needs a single full-org CSV snapshot to seed a Snowflake warehouse before incremental Bulk-API replication starts.

**Problem:** The BI team initially asks the admin to run a Bulk API job per object — 200+ objects, 200+ jobs, days of work.

**Solution:**

```
Setup → Data Export → Export Now
- Include all data: yes
- Include all binary content: NO (warehouse only needs structured data; files come via separate channel)
- Notify: bi-team-lead@company.example
```

Generation completes in 2–6 hours for a mid-size org. The notification email contains 4–12 download links (one per ZIP chunk). BI team downloads, unpacks, loads into Snowflake staging tables. Subsequent replication runs through Bulk API CDC.

**Why it works:** Data Export's "all selected" checkbox does in one click what 200 Bulk API jobs would do; the one-time nature aligns with the service's strengths. From here on, ongoing replication should be Bulk API or Data Cloud Zero Copy — not Data Export.

---

## Example 3: Litigation hold targeted export

**Context:** Legal hold issued for a regulatory matter; in-scope data is Cases related to a specific contract type, plus the EmailMessages and ContentVersion attached to those Cases.

**Problem:** The naive answer is to schedule a full Data Export. That's overkill (8+ hours, multi-gigabyte ZIP set), and legal needs only specific Cases.

**Solution:** Data Export is **not** the right tool here — its scope is per-object, not per-record-filter. Use Bulk API 2.0 with a SOQL filter:

```
SELECT Id, CaseNumber, Subject, ... FROM Case WHERE ContractType__c IN ('TypeA', 'TypeB')
```

Then a related EmailMessage and ContentVersion query keyed by those Case Ids. Document the chain-of-custody, ship to legal.

**Why it works:** when the request has a record-level filter, Data Export Service is too broad and the operator ends up post-filtering CSVs offline (error-prone, audit-unfriendly). Recognizing the wrong-fit case is the skill, not just configuring the right one.

---

## Anti-Pattern: "we use weekly Data Export as our DR plan"

**What practitioners do:** schedule a weekly export; rotate operators; never test a restore. Tell auditors the org has a 7-day RPO backed by Salesforce-native tooling.

**What goes wrong:**
- The 48-hour expiry window means missed downloads silently lose entire weeks.
- There is no restore — to "recover," the team would have to manually load CSVs back via Data Loader, fix every Id reference, re-resolve every relationship, redo every record-type and ownership decision. For any org of size, this is a multi-week project, not an RTO.
- Big Objects, External Objects, and metadata are absent.
- Field history and Chatter feed history are absent.

When the first real incident hits — accidental mass-delete via Data Loader, mistaken hard-delete from a flow — the team realizes the "backup" cannot be restored in any reasonable timeframe and the RPO claim was fiction.

**Correct approach:** state the actual obligation, license a real backup product (Salesforce Backup and Restore, Own, Odaseva, Spanning, Veeam) or build an explicit data-warehouse pipeline with reverse-load capability, and either retire Data Export or recast it as evidence archive only. The architecture doc must reflect the reality, not the brochure.
