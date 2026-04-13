# Well-Architected Notes — NPSP API and Integration

## Relevant Pillars

- **Reliability** — NPSP gift integrations must be fault-tolerant. BDI processing failures on individual DataImport records must be captured and remediated without losing gift data. Idempotency is critical: the same gift should not be imported twice. Use unique external ID fields on DataImport to enable idempotent upserts.
- **Security** — Gift data includes payment method information and donor financial details. DataImport records containing credit card or bank account data must have field-level security restricting access to authorized integration users only. Elevate payment tokens must never be stored in custom fields.
- **Performance Efficiency** — Large BDI batch imports should be scheduled during off-peak hours. CRLP rollup recalculation after large imports requires a separate batch run. Integrations that invoke BDI processing synchronously in Apex are subject to the same governor limits as any DML-heavy transaction.

## Architectural Tradeoffs

**Synchronous BDI processing vs. asynchronous batch:** For small gift volumes (< 200 per transaction), `BDI_DataImport_API.processDataImportRecords()` can be called synchronously. For large volumes, insert DataImport records and trigger the BDI batch job asynchronously. Synchronous processing provides immediate error feedback; async processing scales to large volumes without governor limit issues.

**Custom field mapping via Advanced Mapping vs. post-processing:** BDI Advanced Mapping handles custom field population during the BDI pipeline. Alternatively, custom fields can be populated in a post-processing Apex trigger on the resulting Opportunity. Advanced Mapping is preferred because it keeps gift data complete within the BDI pipeline and reduces trigger complexity.

## Anti-Patterns

1. **Direct Opportunity and OppPayment inserts** — The #1 NPSP integration anti-pattern. All gift data must flow through BDI to trigger NPSP's TDTM processing for allocations, soft credits, and rollups.
2. **Using ERD Installments API to verify Opportunity creation** — `getInstallments()` returns projections, not persisted records. Checking for Opportunities after calling this API always returns nothing. Use the scheduled batch job for Opportunity creation.
3. **Neglecting CRLP recalculation after large imports** — NPSP household rollup fields are not updated in real-time. After bulk imports, a manual CRLP batch run is required to update household giving totals.

## Official Sources Used

- Recurring Donations Schedules API (NPSP Help) — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_rd2_schedule_api.htm
- Recurring Donations Installments API (NPSP Help) — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_rd2_installments_api.htm
- NPSP Data Import Administrator Guide — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Data_Importer.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
