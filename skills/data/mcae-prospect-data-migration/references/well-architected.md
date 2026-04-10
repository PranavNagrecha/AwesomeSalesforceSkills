# Well-Architected Notes — MCAE Prospect Data Migration

## Relevant Pillars

- **Security** — Prospect data imported into MCAE must comply with data residency requirements. MCAE stores prospect records and engagement history in Salesforce-managed infrastructure, and custom field data flows bidirectionally through the Salesforce Connector. Before migrating, confirm that the target MCAE Business Unit's data residency setting (if applicable) is consistent with the data residency requirements of the source records. Personally identifiable information (PII) in prospect fields — email, name, phone, company — must be handled according to the organization's data classification policy during CSV staging and upload.
- **Reliability** — The reliability of a prospect migration depends on the completeness and correctness of the Salesforce Connector field mapping before import. A migration that appears to succeed (correct record count, no import errors) but silently drops custom field values is unreliable in the operational sense: downstream campaigns and automations that depend on those fields will behave incorrectly. Reliability requires a pre-import field mapping verification step and a post-import spot-check protocol.
- **Operational Excellence** — A well-operated MCAE prospect migration produces a clear scope document that specifies what was imported, what was excluded (engagement history), the cut-over date, and the downstream remediation plan (score suppression, re-engagement campaign). This documentation is the operational artifact that allows the team to troubleshoot, repeat, or extend the migration later. Without it, teams lose the ability to explain discrepancies between expected and actual prospect state.

## Architectural Tradeoffs

**Completeness vs. accuracy of historical signal:** The primary tradeoff in an MCAE prospect migration is the decision to acknowledge the engagement history gap rather than attempt to approximate it via custom fields. Importing open counts and click counts into custom prospect fields preserves a numerical approximation of historical engagement but decouples those numbers from the MCAE scoring engine, which only responds to tracked activity events. The architecturally correct position is to treat engagement history as a clean break: import profile fields, document the gap, and rebuild engagement signal through post-migration campaigns.

**Speed of import vs. correctness:** Splitting large CSVs into 100,000-row chunks and running sequential imports is slower than attempting to import everything in one file. The tradeoff is necessary because MCAE silently truncates files that exceed the row limit, making a single large import unreliable for datasets over 100,000 records.

**Self-service CSV import vs. Salesforce Support-assisted BU migration:** CSV import is fast, self-service, and available at any time. It is correct for external prospect imports (from CRM or ESP). For cross-BU migrations, the self-service CSV approach drops engagement history and can create orphaned sync relationships. Support-assisted migration is slower and requires a case, but it is the architecturally sound path for BU consolidations.

## Anti-Patterns

1. **Importing engagement metrics into custom prospect fields as a scoring proxy** — Storing historical open counts in custom fields gives the impression that prospect scores reflect prior engagement, but MCAE scoring rules do not read custom fields to calculate score. The score displayed on the prospect record remains at zero. This creates a misleading data state where the custom field value suggests engagement but the prospect score used by automation rules does not. The correct approach is to document the engagement history gap, suppress score-gated rules during the warm-up period, and let scores rebuild from live MCAE activity.

2. **Running a cross-BU migration via CSV without Salesforce Support involvement** — A self-service CSV import from a source BU export into a destination BU creates new prospect records with field values but severs the connection to the source BU's engagement history. Salesforce Support's BU migration process is more complete and preserves more of the prospect record relationship structure. Self-service CSV migration for BU-to-BU moves is an anti-pattern because it appears to work but silently drops data that the team will later discover is missing.

3. **Skipping the pre-import field mapping verification** — Running a full 100,000-record import without first verifying that all custom fields are connector-mapped and then spot-checking a small test import is an operational anti-pattern. The consequence is silent data loss discovered only after the full migration completes, requiring a remediation import. The cost of a pre-import verification is minutes; the cost of discovering silent data loss after a full import is hours of rework plus stakeholder trust issues.

## Official Sources Used

- Salesforce Help — Import Prospects — https://help.salesforce.com/s/articleView?id=sf.pardot_import_prospects.htm&type=5
- Salesforce Help — Considerations for Prospect Imports — https://help.salesforce.com/s/articleView?id=sf.pardot_import_prospects_considerations.htm&type=5
- Salesforce Help — Default Prospect Field Mapping — https://help.salesforce.com/s/articleView?id=sf.pardot_import_default_field_mapping.htm&type=5
- Salesforce Help — Map Custom Fields — https://help.salesforce.com/s/articleView?id=sf.pardot_import_custom_field_mapping.htm&type=5
- Salesforce Help — MCAE Limits — https://help.salesforce.com/s/articleView?id=sf.pardot_limits.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
