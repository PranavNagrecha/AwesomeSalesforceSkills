# LLM Anti-Patterns — Einstein Analytics Basics

Common mistakes AI coding assistants make when generating or advising on Salesforce CRM Analytics (formerly Einstein Analytics / Tableau CRM).
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending CRM Analytics when standard Reports and Dashboards suffice

**What the LLM generates:** "Use CRM Analytics to build a dashboard showing Opportunity pipeline by stage."

**Why it happens:** LLMs default to the more advanced tool because it appears frequently in training data. A pipeline-by-stage dashboard is a basic reporting need that standard Reports and Dashboards handle well without additional licensing costs. CRM Analytics requires separate licenses (CRM Analytics Plus or similar) that many orgs do not have.

**Correct pattern:**

```
Tool selection decision:
- Data is in Salesforce, single object or simple joins,
  standard grouping/filtering → Standard Reports & Dashboards.
- Data spans multiple systems, needs complex transformations,
  row-level security beyond sharing, or predictive analytics
  → CRM Analytics.
- Data needs full SQL, complex visualizations, or is mostly
  outside Salesforce → Tableau.

Start with the simplest tool that answers the business question.
Only move to CRM Analytics when standard reporting hits a wall.
```

**Detection hint:** If the output recommends CRM Analytics for a requirement that involves a single Salesforce object with standard grouping, the tool is over-engineered. Check if the use case involves cross-system data or complex transformations.

---

## Anti-Pattern 2: Ignoring license requirements for CRM Analytics

**What the LLM generates:** "Enable CRM Analytics and start building datasets and lenses."

**Why it happens:** LLMs skip the licensing prerequisite. CRM Analytics requires specific add-on licenses (CRM Analytics Plus, CRM Analytics Growth, or Einstein Analytics licenses depending on the era). Without the correct license assigned to the user, CRM Analytics Setup options are invisible and the platform is inaccessible.

**Correct pattern:**

```
Before building in CRM Analytics:
1. Confirm org-level license: Setup → Company Information →
   check for "CRM Analytics" or "Analytics" in Permission Set Licenses.
2. Assign user licenses: create a Permission Set with "CRM Analytics Plus User"
   or equivalent, and assign it to each analytics user.
3. If no CRM Analytics license exists, the org cannot use CRM Analytics.
   Standard Reports & Dashboards do not require additional licenses.
4. License types:
   - CRM Analytics Plus: full access (build datasets, lenses, dashboards).
   - CRM Analytics Growth: limited (view, interact, but limited building).
   - Einstein Analytics (legacy name): same platform, older license name.
```

**Detection hint:** If the output jumps to building datasets without checking or mentioning license requirements, the licensing step is missing. Search for `license` or `Permission Set License` in the setup instructions.

---

## Anti-Pattern 3: Confusing CRM Analytics datasets with live Salesforce data

**What the LLM generates:** "The CRM Analytics dashboard shows real-time Salesforce data automatically."

**Why it happens:** LLMs assume CRM Analytics queries Salesforce directly like standard reports. CRM Analytics uses datasets that are copies of Salesforce data, loaded via dataflows or recipes on a refresh schedule. Data in CRM Analytics dashboards can be stale by hours or a day depending on the sync schedule.

**Correct pattern:**

```
CRM Analytics data freshness model:
- Datasets are COPIES of Salesforce data, not live queries.
- Data is loaded via dataflows (legacy) or recipes (current):
  - Scheduled sync: runs at defined intervals (e.g., daily at 2 AM).
  - Can be triggered manually or via API.
- Default sync frequency depends on license tier and configuration.
- Dashboard data reflects the last successful sync, NOT real-time.

For real-time data needs:
- Use standard Salesforce Reports & Dashboards.
- Or use Direct Data in CRM Analytics (available for some connectors)
  which queries live data without a dataset.
```

**Detection hint:** If the output says CRM Analytics dashboards show "real-time" or "live" data without mentioning sync schedule or dataset refresh, the freshness model is wrong. Search for `real-time` or `live` combined with CRM Analytics.

---

## Anti-Pattern 4: Using outdated product names interchangeably

**What the LLM generates:** "Set up Einstein Analytics in your org by going to Setup → Wave Analytics."

**Why it happens:** The product has been renamed multiple times: Wave Analytics → Einstein Analytics → Tableau CRM → CRM Analytics. LLMs mix names from different eras and reference obsolete Setup paths. Current Salesforce Setup uses "CRM Analytics" or "Analytics Studio."

**Correct pattern:**

```
Current naming (as of Spring '25):
- Product name: CRM Analytics (or "Salesforce CRM Analytics").
- Setup path: Setup → CRM Analytics → Settings.
- Builder interface: Analytics Studio (accessed via App Launcher).
- Previous names (for reference only):
  - Tableau CRM (used 2021-2022)
  - Einstein Analytics (used 2017-2021)
  - Wave Analytics (used 2015-2017)
- API/metadata names may still use "wave" or "analytics" prefixes
  (e.g., WaveRecipe, AnalyticsDataset).
```

**Detection hint:** If the output uses "Wave Analytics" or navigates to a deprecated Setup path, it is referencing an outdated product era. Search for `Wave` or `Tableau CRM` as the current product name.

---

## Anti-Pattern 5: Building complex dataflows without considering row-level security

**What the LLM generates:** "Create a dataflow that loads all Opportunity data into a dataset. All CRM Analytics users can see the dashboard."

**Why it happens:** LLMs focus on getting data into datasets and forget that CRM Analytics has its own security model separate from Salesforce sharing rules. By default, a dataset may be visible to all CRM Analytics users. Without configuring Security Predicates or inheriting sharing from Salesforce, users may see data they should not see in Salesforce itself.

**Correct pattern:**

```
CRM Analytics security is NOT inherited from Salesforce by default:
1. Security Predicate: a filter applied to the dataset that restricts
   rows based on the running user's identity.
   Example: 'OwnerId' == "$User.Id" || 'ManagerId' == "$User.Id"
2. Row-Level Security dataset: a separate dataset mapping users to
   the records they can see, joined at query time.
3. Salesforce Sharing Inheritance: available for datasets synced via
   the "Data Sync" feature (not classic dataflows).
4. App-level sharing: CRM Analytics apps can be shared with specific
   users, roles, or groups — but this controls app access, not row-level data.

Always configure row-level security for datasets containing sensitive data.
```

**Detection hint:** If the output creates a dataset without mentioning Security Predicates, row-level security, or sharing, the data may be over-exposed. Search for `Security Predicate` or `row-level security` in the dataset configuration.
