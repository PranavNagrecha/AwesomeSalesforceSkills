# Examples — Data Cloud vs CRM Analytics Decision

## Example 1: “We only bought CRM Analytics — why is marketing asking for Data Cloud?”

**Context:** A B2C retailer runs pipeline dashboards in CRM Analytics sourced from Opportunity and Account. Marketing wants web and loyalty events combined with CRM for paid media audiences.

**Problem:** Leadership believes CRM Analytics datasets can absorb unlimited external feeds without a separate customer data platform, so Data Cloud is deprioritized as “another BI tool.”

**Solution:** Document that CRM Analytics serves analytics and embedded KPIs on governed datasets, while Data Cloud owns high-volume ingestion, harmonization to DMOs, identity resolution, and activation to destinations such as ad platforms. Recommend Data Cloud for cross-channel profiles and keep CRM Analytics as the visualization layer on DMO-backed Direct Data where product-supported, plus CRM-native datasets for pure CRM slices.

**Why it works:** Separates “metrics and dashboards” from “identity graph and outbound segments,” which matches Salesforce’s Data 360 layering described in official architecture guidance.

---

## Example 2: Analytics on the unified profile without rebuilding joins

**Context:** Service leaders want handle-time trends correlated with email engagement stored in a marketing platform already ingested into Data Cloud.

**Problem:** A project plan proposes exporting marketing tables into custom CRM objects nightly so CRM Analytics can join them in a recipe—doubling storage and bypassing harmonized DMO semantics.

**Solution:** Keep marketing data in Data Cloud, validate DMO mappings and identity coverage, then route CRM Analytics to the harmonized entities through the supported Direct Data path documented for CRM Analytics and Data Cloud. Reserve CRM-to-CRM recipes for dimensions that truly belong in core CRM.

**Why it works:** Uses the harmonized model once, avoids competing golden-record definitions, and aligns analytics consumers with the same semantics activation uses.

---

## Anti-Pattern: Ordering licenses before defining the data boundary

**What practitioners do:** Purchase both SKUs, assign a team to “turn on dashboards,” and defer harmonization design until later.

**What goes wrong:** Dashboards ship on brittle CRM copies of external data while Data Cloud sits underutilized; identity rules never catch up, and segments contradict reports.

**Correct approach:** Decide the owning platform per use case first, fund DMO mapping and identity resolution when Data Cloud is selected, then layer CRM Analytics consumption with explicit data contracts.

---

## Example 3: Worked Decision Record with a Use-Case Ownership Register

**Context:** A B2C retailer runs Sales Cloud and Service Cloud, has CRM Analytics licences for 40 analysts, a Snowflake warehouse with modeled order history, web events in an external tag manager, and a Marketing Cloud Engagement account. The steering committee asks: "Do we need Data Cloud, or can CRM Analytics do it?"

**The register** is the decision's working data. It lives next to the record at `docs/architecture/data/use-case-register.yaml` in the architecture repository. It is not Salesforce metadata and has no `package.xml` member.

```yaml
# docs/architecture/data/use-case-register.yaml
# One row per use case. owner = the platform accountable for the outcome.
version: 2026-10-03
use_cases:
  - id: UC-01
    name: Weekly pipeline and forecast dashboards
    sources: [Opportunity, OpportunityLineItem, User]      # CRM objects only
    needs: [analytics]
    owner: crm_analytics
    path: crm_sync -> recipe -> dataset                       # Gotcha 7: sync alone is not a dataset
    freshness: daily

  - id: UC-02
    name: Paid-media audiences from web + loyalty + CRM
    sources: [web_events, loyalty_db, Contact]
    needs: [ingestion, identity_resolution, segmentation, activation]
    owner: data_360
    contract_check: "Segmentation and Activation purchased?"  # Gotcha 1
    freshness: hourly

  - id: UC-03
    name: Service handle time vs email engagement
    sources: [Case, AgentWork, mc_engagement]
    needs: [harmonization, analytics]
    owner: data_360            # harmonized DMOs
    consumer: crm_analytics
    path: dmo_to_dataset       # documented conversion; Direct Data UNVERIFIED for these DMOs
    freshness: daily

  - id: UC-04
    name: Lifetime value by customer for service agents
    sources: [snowflake.orders]
    needs: [identity_join, calculated_insight]
    owner: data_360
    ingest_or_federate: federate   # Gotcha 6: warehouse model is trusted
    query_path: not_soql           # Gotcha 5: calculated insight objects are not SOQL-queryable
    freshness: daily

risks:
  - id: R-01
    text: Data 360 usage is credit-metered; nightly full reprocessing multiplies consumption.
    owner: Data Platform Lead
    review: monthly during proof of concept
```

**The decision record** at `docs/adr/0071-data-360-and-crm-analytics-roles.md`:

```markdown
# ADR-0071: Data 360 owns identity and activation; CRM Analytics stays the analysis layer

## Status
Accepted (2026-10-03), Data Architecture Board

## Context
- Register rows UC-02 and UC-04 need identity resolution and calculated
  insights; UC-02 needs activation to ad platforms. These are Data 360
  capabilities (Data 360 Architecture, developer guide).
- UC-01 uses CRM objects only and already runs in CRM Analytics.
- Snowflake holds trusted order history. Data 360 offers read-only zero
  copy federation, so ingestion is not required for UC-04.
- Data 360 usage is tracked as credit consumption (digital wallet).
- SOQL cannot query calculated insight objects and caps Data 360
  results at 12 MB (SOQL and SOSL Reference, Data 360 Objects).

## Decision
Adopt Data 360 for UC-02, UC-03, UC-04. Keep CRM Analytics for UC-01 and
as the consumer for UC-03 through DMO-to-dataset conversion. Federate
Snowflake orders rather than ingest them.

## Consequences
### Positive
- One identity graph feeds audiences and service analytics.
### Negative
- Consumption cost is variable; owner and monthly review in R-01.
- UC-03 freshness is bounded by conversion and recipe schedules (daily).
- Two platform teams; the register names the owner per use case.

## Alternatives Considered
### CRM Analytics only, with external data loaded into custom objects
Rejected: no identity resolution or activation for UC-02; duplicates
Snowflake storage in CRM.
### Data 360 only, retire CRM Analytics
Rejected: UC-01 dashboards and 40 trained analysts would be rebuilt for
no new capability.

## Date
2026-10-03
```

**Why it works:** every row has one owning platform and a named path, the record cites the documented capability behind each assignment, and the variable cost has an owner.

