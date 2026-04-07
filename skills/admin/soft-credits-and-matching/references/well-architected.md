# Well-Architected Notes — Soft Credits and Matching Gifts (NPSP)

## Relevant Pillars

- **Reliability** — Soft credit rollup fields are batch-driven, not real-time. Reliable reporting depends on scheduled batch execution and explicit recalculation after bulk data changes. Any workflow that depends on reading soft credit totals must account for this lag or trigger recalculation before reading.
- **Operational Excellence** — The duplicate-OCR bug with Find Matched Gifts requires a post-run verification step to be part of standard operating procedure. Undocumented process gaps around this bug cause periodic data corruption that is difficult to detect without routine audits.
- **Performance** — Running rollup recalculation across large volumes of Contacts (tens of thousands) is a batch-intensive operation. Scheduling it during off-peak hours and scoping it to affected Contacts (rather than recalculating all) reduces contention with other nightly NPSP batch jobs.
- **Security** — OCR records are visible to any user with read access to the related Opportunity. Partial_Soft_Credit__c records follow the same object-level access. If soft credit attribution is sensitive (e.g., internal fundraiser performance data), consider field-level security on soft credit rollup fields and restrict access to Partial_Soft_Credit__c via profile or permission set.
- **Scalability** — The matching gift workflow is a manual, per-gift process in standard NPSP. For organizations with high matching gift volume, the lack of bulk automation (Find Matched Gifts must be clicked per Opportunity) becomes a throughput bottleneck. Custom automation (Flow or Apex) that replicates the Find Matched Gifts logic is needed at scale but requires care to avoid triggering the duplicate-OCR bug.

## Architectural Tradeoffs

**Manual per-gift Find Matched Gifts vs. automated OCR creation:** The standard Find Matched Gifts button provides NPSP-supported, tested logic that populates `npsp__Matching_Gift__c`, creates the OCR with the correct role, and handles Partial_Soft_Credit__c creation. Automating this with Flow or Apex reduces manual effort but requires the implementer to replicate all three side effects correctly and guard against the duplicate-OCR condition. Custom automation gains throughput but assumes ownership of correctness.

**Full soft credit per OCR vs. partial soft credits:** For most soft credit scenarios (board member attribution, relationship-based credits), giving the full opportunity amount as a soft credit is accurate and simpler — no Partial_Soft_Credit__c record is needed. Partial credits add complexity and a new failure mode (missing `npsp__Contact_Role_ID__c`). Use partial credits only when the credited amount genuinely differs from the full opportunity amount.

**Real-time vs. batch rollup expectations:** Organizations that report on soft credit totals in real time (e.g., live dashboards during a campaign) face a structural mismatch with NPSP's batch rollup model. The architectural decision is whether to (a) accept batch latency and educate stakeholders, (b) trigger manual recalculation after every soft credit change (operationally expensive), or (c) build a separate reporting layer on OCR and Partial_Soft_Credit__c records directly (bypassing rollup fields). Option (c) provides real-time accuracy but requires maintaining custom reports and training users away from standard NPSP rollup fields.

## Anti-Patterns

1. **Using OCR-based soft credits on the original gift to represent employer matching** — Giving an employer contact a soft credit role on the employee's donation Opportunity is a data model violation in NPSP. Matching gifts are a separate giving transaction (a separate Opportunity) and must be tracked as such. Soft crediting the employer on the employee's gift corrupts hard vs. soft credit reporting, leaves the Matching Gift opportunity unlinked, and breaks NPSP's matching gift reports.

2. **Skipping rollup recalculation after bulk soft credit changes** — Importing or updating hundreds of OCR or Partial_Soft_Credit__c records without triggering recalculation leaves stale totals in place for up to 24 hours. Staff who query Contact records during this window see incorrect data and may make incorrect stewardship or reporting decisions. Rollup recalculation must be part of every bulk data operation checklist.

3. **Treating Find Matched Gifts as idempotent** — The button creates new records every time it is run. Running it twice for the same combination of donor gift and Matching Gift opportunity produces duplicates. There is no system guard against this. Process documentation must explicitly prohibit re-running Find Matched Gifts for an already-matched gift without first removing the previously created OCR and Partial_Soft_Credit__c records.

## Official Sources Used

- Soft Credits Overview (NPSP Help) — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Soft_Credits_Overview.htm
- Manage Soft Credits (NPSP Help) — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Manage_Soft_Credits.htm
- Configure Matching Gifts (NPSP Help) — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Configure_Matching_Gifts.htm
- Donation Soft Credit Management with NPSP (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/npsp-donation-management/soft-credit-management
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
