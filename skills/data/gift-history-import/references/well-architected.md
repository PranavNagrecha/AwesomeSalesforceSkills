# Well-Architected Notes — Gift History Import

## Relevant Pillars

### Operational Excellence

Gift history migration must be repeatable, auditable, and recoverable. Using DataImport__c as a staging table provides a built-in audit trail: every staging row records its import status, the resulting Opportunity ID, and any error message. This is operationally superior to direct Opportunity imports where failure attribution is lost after the import run.

### Reliability

NPSP gift data model completeness (Opportunity + Payment + OCR + GAU) is the reliability requirement. Any import approach that bypasses BDI produces structurally incomplete gift records that cannot be recovered without a remediation batch. Reliability requires using the BDI path as the only supported import mechanism.

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Operational Excellence | Use DataImport__c staging for auditability; validate post-import with SOQL; document batch run results |
| Reliability | BDI is the only path that preserves the full NPSP gift data model; validate OCR, GAU, and payment counts post-import |
| Security | Gift records contain financial data; apply appropriate FLS on Opportunity Amount and payment fields; audit who runs BDI batches |
| Performance | Chunk imports to ≤50,000 rows per batch; process each chunk before staging the next to avoid DataImport__c bloat |

---

## Cross-Skill References

- `data/constituent-data-migration` — Migrate Contact and Household records before gift records
- `data/nonprofit-data-architecture` — Overall NPSP data model design including GAU, household, and payment structure
- `apex/npsp-api-and-integration` — Apex-level BDI customization and NPSP trigger extension

---

## Official Sources Used

- Standard NPSP Data Import Fields — Salesforce Help: https://help.salesforce.com/s/articleView?id=sf.npsp_data_importer_fields.htm
- Configure NPSP Data Importer — Salesforce Help: https://help.salesforce.com/s/articleView?id=sf.npsp_data_importer_customize.htm
- How NPSP Data Importer Processes Data — Salesforce Help: https://help.salesforce.com/s/articleView?id=sf.npsp_data_importer_process.htm
- Advanced NPSP Mapping — Salesforce Help: https://help.salesforce.com/s/articleView?id=sf.npsp_data_importer_advanced_mapping.htm
