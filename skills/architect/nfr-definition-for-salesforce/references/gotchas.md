# Gotchas: NFR Definition for Salesforce

Non-obvious platform behaviours that make a non-functional requirement untestable, unachievable, or measured against the wrong number. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Limits Quick Reference" means the Salesforce Developer Limits and Allocations Quick Reference (Summer '26 PDF); "Apex Guide" means the Apex Developer Guide, Version 67.0; "Object Reference" means the Object Reference, Version 67.0; "WAF Reliable" means Salesforce Well-Architected, Trusted > Reliable (Wayback snapshot 2026-06-13).

## Gotcha 1: Only A Full Sandbox Approximates Production Volume, And Developer Pro Holds 1 GB, Not 200 MB

**What happens:** Performance NFRs validated in a Developer, Developer Pro, or Partial Copy sandbox produce optimistic results. Developer and Developer Pro sandboxes are for building on fictional data; Partial Copy and Full sandboxes carry copies of production data. Queries that perform well against 10,000 records often degrade non-linearly at millions of records. This corrects an earlier statement in this skill: the 200 MB data storage ceiling belongs to the Developer sandbox; Developer Pro holds 1 GB (2 GB with the SandboxStorage add-on).

**When it occurs:** Any time a performance NFR is tested in a sandbox that is not a Full sandbox with a representative data copy.

**How to avoid:** State in every performance NFR: "Validated in a Full sandbox with production-equivalent data volume (record count stated)." WAF Reliable recommends Scale Test to simulate traffic spikes in a Full sandbox. If no Full sandbox is available before go-live, the NFR is unverified and must be flagged as a go-live risk, not signed off as met.

**Source:** Tooling API Developer Guide, Version 67.0, SandboxInfo: `LicenseType` values `DEVELOPER`, `DEVELOPER_PRO`, `PARTIAL`, `FULL`; `Features` `SandboxStorage` "Increases the data storage available for Developer sandboxes from 200 MB to 400 MB and Developer Pro sandboxes from 1 GB to 2 GB." Metadata API Developer Guide, Version 67.0, development environments overview: Developer and Developer Pro sandboxes use fictional data; Partial Copy and Full are "loaded with copies of production data." WAF Reliable, Performance: "With Scale Test, you can validate these trade-offs by simulating traffic spikes in a Full sandbox."

---

## Gotcha 2: The Daily API Allocation Is One Org-Wide Pool, And Sandboxes Measure It Differently

**What happens:** Each integration team writes a throughput NFR assuming it has the whole allocation. The 24-hour inbound allocation is enforced against the aggregate of all API calls into the org, not per user or per integration. A load test in a Full sandbox does not reveal the shortfall: a Full sandbox not built from a template has a flat 5,000,000-call allocation, usually far above production's. Production can run past its limit "by a certain amount" before a hard cap, but that allowance does not exist in trial orgs, Developer Edition, or sandboxes, and Salesforce says not to rely on it.

**When it occurs:** When several integrations are designed separately, and when integration throughput is "proven" in a Full sandbox.

**How to avoid:** Keep one API budget table in the NFR register. Compute production's allocation with the edition formula (Enterprise: 100,000 plus licences multiplied by calls per licence type, plus purchased add-ons). List each integration's calls per day and keep the total under 80% of production's number, not the sandbox's. Track it with the `DailyApiRequests` value from the REST `/limits` resource and API Usage Notifications.

**Source:** Limits Quick Reference, Total API Request Allocations (edition table; Full Sandbox 5,000,000 "applies only to Full Sandboxes that aren't created from a template"; "enforced against the aggregate of all API calls made to the org"; "not on a per-user basis"); What Happens If You Reach or Exceed Your API Request Limit ("Don't rely on it on an ongoing basis"; "doesn't apply to trial orgs, Developer Edition, or sandboxes"). REST API Developer Guide, Version 67.0, Limits resource (`DailyApiRequests`).

---

## Gotcha 3: Platform Availability Is Shared Responsibility, And No Fetched Source States A 99.9% Figure

**What happens:** Teams treat a published uptime figure as the implementation's availability NFR. The platform handles infrastructure-level availability, but the availability of what the team builds, as customers experience it, is a shared responsibility, and "the risk of service interruption is never zero." Custom Apex failures, bad deployments, integration outages, and data loss from admin error sit on the customer side. UNVERIFIED (2026-10-03): the 99.9% infrastructure SLA figure used elsewhere in this skill was not found in any fetched source; trust.salesforce.com publishes status, and any contractual uptime commitment comes from the customer's own agreement.

**When it occurs:** During NFR sign-off when "99.9% availability" is accepted without defining what availability means, and in post-incident reviews of customer-caused outages.

**How to avoid:** Define availability at two levels. Level 1: platform availability, quoted from the customer's contract and monitored on trust.salesforce.com. Level 2: application availability, team-owned, with RPO, RTO, alerting, and rollback procedures. Plan for planned maintenance as well as unplanned disruption.

**Source:** WAF Reliable, Availability: "The Salesforce Platform handles most infrastructure-level availability issues. However, the availability of the solutions that you build on the platform, and which is experienced by your customers, is a shared responsibility"; "Architects must prepare for Salesforce service disruptions like planned maintenance or unforeseen circumstances." Salesforce Well-Architected, Adaptable > Resilient (Wayback snapshot 2026-06-13), backup and restore: without a strategy "you can't restore clean versions of your production data and metadata when they're maliciously corrupted, when defects inadvertently make their way into production, or when a failure during a large data load corrupts production data."

---

## Gotcha 4: Licences Raise Daily Allocations But Never Per-Transaction Limits

**What happens:** Teams assume more licences raise every limit. Daily allocations do scale with licences: inbound API calls, and asynchronous Apex executions (250,000 or licences multiplied by 200, whichever is greater). Per-transaction limits do not: 50,000 SOQL rows, 150 DML statements, 10,000 ms CPU synchronous (60,000 ms asynchronous), 6 MB heap synchronous (12 MB asynchronous), 100 callouts with 120 seconds cumulative callout time. A transaction that needs 60,000 rows fails whether the org has 10 users or 10,000.

**When it occurs:** When scalability NFRs say "must handle X records" without naming the processing mode.

**How to avoid:** Every scalability NFR names its mode (synchronous, Batch Apex, Queueable, platform event, Bulk API 2.0) and the limit it is measured against. Express daily volumes against the licence-driven allocations and per-transaction volumes against the fixed ceilings.

**Source:** Apex Guide, Execution Governors and Limits: per-transaction table (SOQL rows 50,000; DML statements 150; heap 6 MB / 12 MB; CPU 10,000 / 60,000 ms; callouts 100; cumulative callout timeout 120 seconds) and Salesforce Platform Apex Limits ("250,000 or the number of applicable user licenses in your org multiplied by 200, whichever is greater"). Limits Quick Reference, Increasing Total API Request Allocations ("The total number of API requests allowed is defined by the users' licenses in the org").

---

## Gotcha 5: A Compliance NFR Is Met By Verified Configuration, Not By A Purchased Licence

**What happens:** A security NFR states "encryption at rest enabled via Shield Platform Encryption." The team adds it to the register, assumes the Shield purchase satisfies it, and signs off go-live. The encryption policy was never configured and tested, and sensitive data goes live unencrypted.

**When it occurs:** When compliance NFRs are written at the feature-purchase level ("we have Shield") rather than at the configuration and verification level.

**How to avoid:** Every compliance NFR carries a concrete acceptance test, run in UAT, that proves the control is on: which fields are in the encryption policy, which event types are logged and retained, which fields have history kept. "Shield Platform Encryption is licensed" is not an acceptance criterion. This revision replaces the earlier example criterion ("querying Account.SSN via REST API returns an encrypted token, not plaintext"): Platform Encryption encrypts data at rest while keeping app functionality, so an authorised API read is not where encryption shows. Verify the policy and key state instead. UNVERIFIED (2026-10-03): what an API read returns to a user without access to encrypted data was not confirmed in a fetched source.

**Source:** Salesforce Security Guide, Version 67.0, Salesforce Shield: "a trio of security tools" (Shield Platform Encryption, Event Monitoring, Field Audit Trail); Platform Encryption lets you "natively encrypt your most sensitive data at rest" while "keeping critical app functionality such as search, workflow, and validation rules", and "set encrypted data permissions to protect sensitive data from unauthorized users." Object Reference, EventLogFile: "Accessing this object requires View Event Log Files and API Enabled user permissions."

---

## Gotcha 6: Throughput NFRs Hit The Concurrent Long-Running Request Limit Before The Daily Allocation

**What happens:** An integration NFR promises 50 parallel workers calling Salesforce. Each call takes 25 seconds because it runs heavy logic. Production allows 25 concurrent inbound requests lasting 20 seconds or longer; beyond that the API returns `REQUEST_LIMIT_EXCEEDED` and no new long requests start until the count drops. The daily allocation is nowhere near exhausted. REST and SOAP calls also time out at 10 minutes, except queries.

**When it occurs:** Integration and portal designs with many parallel clients, and synchronous APIs that wrap slow Apex.

**How to avoid:** State throughput NFRs as concurrency and duration, not only calls per day: "at most 10 concurrent requests, p95 under 5 seconds." Move slow work to asynchronous processing so requests stay under 20 seconds. Note that requests shorter than 20 seconds have no concurrency limit.

**Source:** Limits Quick Reference, Concurrent API Request Limits ("concurrent inbound requests (calls) with a duration of 20 seconds or longer"; Production orgs and Sandboxes 25; Developer Edition and Trial orgs 5; `REQUEST_LIMIT_EXCEEDED`; "There isn't a limit on the number of concurrent requests shorter than 20 seconds") and API Timeout Limits ("10 minutes, except for any query call").

---

## Gotcha 7: Page-Time Evidence Lives In Event Monitoring, And Usage Metrics Do Not Exist In Sandboxes

**What happens:** A performance NFR says "p95 Lightning record page under 3 seconds in production" but names no data source. Salesforce records Effective Page Time (EPT) per page view in the Lightning Page View event type of `EventLogFile`, which needs Event Monitoring access. The Lightning usage objects (`LightningUsageByPageMetrics`, `LightningUsageByFlexiPageMetrics`, `LightningUsageByBrowserMetrics`) are "Not available in sandbox orgs", so a sandbox test cannot use them. Event Monitoring logs "are a source of truth but are not durable."

**When it occurs:** When go-live criteria include production performance but nobody checked whether Event Monitoring is licensed or who has View Event Log Files.

**How to avoid:** Name the measurement source in each performance NFR: Lightning Page View `EFFECTIVE_PAGE_TIME` from `EventLogFile` in production, or browser instrumentation in a Full sandbox. Confirm the permission (View Event Log Files plus API Enabled) and export the logs to keep evidence, because they are not durable.

**Source:** Object Reference, EventLogFile Supported Event Types, Lightning Page View Event Type (`EFFECTIVE_PAGE_TIME`: "how many milliseconds it takes for the page to load before a user can interact with the page"; `DURATION`; the non-durable note); EventLogFile Special Access Rules; LightningUsageByPageMetrics, LightningUsageByFlexiPageMetrics, LightningUsageByBrowserMetrics ("Not available in sandbox orgs").

---

## Gotcha 8: Scheduled Apex Runs Under Synchronous Limits

**What happens:** A batch-window NFR assumes the nightly scheduled job gets asynchronous limits (60,000 ms CPU, 12 MB heap, 200 SOQL queries). Scheduled Apex is asynchronous in timing but runs under synchronous limits, so the job fails at 10,000 ms CPU or 100 queries as volume grows.

**When it occurs:** Batch-window and nightly-processing NFRs where the scheduled class does the work itself instead of starting a Batch Apex or Queueable job.

**How to avoid:** Write the NFR against the real execution context. Keep the scheduled class as a thin starter that enqueues Batch Apex or Queueable work, and size the window on that work's limits and on the daily asynchronous execution allocation.

**Source:** Apex Guide, Execution Governors and Limits, note: "Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs."

---

## Gotcha 9: Record Counts Alone Miss Data Skew, Which Breaks Scale First

**What happens:** A scalability NFR says "must support 20 million Contacts" and passes a volume test, then degrades in production because 2 million Contacts hang off one placeholder Account. Volume and relationships affect scalability more than record counts alone.

**When it occurs:** Data models with a catch-all parent record, one integration user owning most records, or lookups that concentrate children.

**How to avoid:** Add skew limits to scalability NFRs: no parent with more than 10,000 child records, no single owner of a disproportionate share of records. Flag the org as large data volume at tens of thousands of users, tens of millions of records, or hundreds of gigabytes of record storage, and plan LDV design work.

**Source:** WAF Reliable, Scalability: large data volume is "tens of thousands of users, tens of millions of records, or hundreds of gigabytes of total record storage"; "The volume of data and the relationships between objects in your org affects scalability and will likely have a greater impact on scalability than the number of records alone"; "no parent should have more than 10,000 child records."
