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
