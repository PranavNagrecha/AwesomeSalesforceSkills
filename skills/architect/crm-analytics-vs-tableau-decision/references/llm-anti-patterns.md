# LLM Anti-Patterns — CRM Analytics vs Tableau Decision

Common mistakes AI coding assistants make when advising on the CRM Analytics vs Tableau platform decision. These patterns help the consuming agent self-check its own output before delivering a recommendation.

## Anti-Pattern 1: Conflating "Tableau CRM" (Old CRM Analytics Name) with Tableau Desktop/Server

**What the LLM generates:** "You can use Tableau CRM, which is Salesforce's version of Tableau, to connect your dashboards to Tableau Server for enterprise distribution." Or: "Tableau CRM supports Custom SQL queries and multi-source joins like Tableau Desktop."

**Why it happens:** LLMs trained on pre-2022 Salesforce documentation encounter the name "Tableau CRM" (Salesforce's old brand for Einstein Analytics) and conflate it with Tableau the BI product. The shared name fragment creates a persistent confusion that appears even in otherwise accurate responses.

**Correct pattern:**

```
"Tableau CRM" is a deprecated Salesforce marketing name for what is now called CRM Analytics
(formerly Einstein Analytics). CRM Analytics is a Salesforce-native embedded analytics product
inside the Salesforce org. It is entirely separate from Tableau Desktop, Tableau Server, Tableau
Cloud, and Tableau Next. Use the current canonical name "CRM Analytics" to avoid this ambiguity.
```

**Detection hint:** Flag any response that uses "Tableau CRM" without immediately clarifying it is the old name for CRM Analytics, or any response that attributes Tableau Desktop/Server capabilities (Custom SQL, multi-source connectors, Tableau Server publishing) to the Salesforce-embedded analytics product.

---

## Anti-Pattern 2: Recommending Tableau for Salesforce-Heavy Orgs Without Flagging the Extract-Only Connector Limitation

**What the LLM generates:** "Tableau is a great choice for your Salesforce data because it has richer visualizations and better self-service analytics. Connect it to Salesforce using the native connector and your team will have powerful dashboards in no time."

**Why it happens:** LLMs default to recommending Tableau as a general-purpose BI tool without surfacing the specific constraint that the Salesforce connector is extract-only. Training data includes many Tableau success stories but fewer explicit discussions of the connector's extract-only nature, so the constraint is omitted.

**Correct pattern:**

```
Tableau's native Salesforce connector is extract-only — it does not support live or direct query
against Salesforce. Every dashboard reflects the most recent extract refresh, not current Salesforce
record state. If near-real-time Salesforce data is required, CRM Analytics is the correct platform.
If daily batch refresh is acceptable and the use case involves cross-system data, Tableau is viable
with the extract lag documented and communicated to stakeholders.
```

**Detection hint:** Any Tableau recommendation for a Salesforce data use case that does not explicitly mention "extract-only," "refresh cadence," or "connector limitation" is missing a critical constraint.

---

## Anti-Pattern 3: Treating CRM Analytics and Tableau as License-Compatible or Interchangeable

**What the LLM generates:** "Your Salesforce users can access either platform — just assign the CRM Analytics permission set and they can also use Tableau through the same login."

**Why it happens:** LLMs model Salesforce as a unified platform and assume license entitlements flow across its product suite. In reality, CRM Analytics and Tableau have completely separate license models and user directories.

**Correct pattern:**

```
CRM Analytics uses Salesforce Permission Set Licenses (PSLs) assigned per user inside the
Salesforce org — separate from Salesforce user licenses, which are also required. Tableau uses
a separate Creator/Explorer/Viewer role model (or Tableau+ capacity model) with an independent
user directory. A Salesforce license does not grant Tableau access. A CRM Analytics PSL does not
grant Tableau access. Dual licensing is required if both platforms are deployed.
```

**Detection hint:** Any response that implies Salesforce users automatically have CRM Analytics or Tableau access, or that a single license grants access to both, is incorrect.

---

## Anti-Pattern 4: Ignoring the 30-Day Incremental Refresh Lookback Cap When Evaluating Tableau for Historical Salesforce Data

**What the LLM generates:** "Use Tableau's incremental refresh feature to keep your Salesforce data up to date efficiently — it will only pull changed records so the refresh is fast and complete."

**Why it happens:** LLMs describe incremental refresh as a performance optimization (which it is) without surfacing the 30-day lookback constraint specific to the Salesforce connector. General-purpose Tableau documentation for database connectors does not impose this limit, creating training data that omits the Salesforce-specific constraint.

**Correct pattern:**

```
Tableau's incremental refresh for the Salesforce connector has a 30-day lookback cap. Records
modified more than 30 days ago are not re-fetched in incremental mode. If a Salesforce record
is retroactively corrected (opportunity close date backdated, ownership changed), that change
will not appear in the Tableau extract until a full refresh runs. For use cases requiring
historical accuracy across Salesforce data, schedule periodic full extracts or route Salesforce
data through a warehouse with change data capture before connecting Tableau.
```

**Detection hint:** Any response recommending Tableau incremental refresh for Salesforce data without mentioning the 30-day cap is incomplete.

---

## Anti-Pattern 5: Treating Tableau Next as a Version Upgrade to Existing Tableau Licenses

**What the LLM generates:** "Upgrade your Tableau Server to the latest version and you will get Tableau Next capabilities including Agentforce integration and Data 360 connectivity."

**Why it happens:** LLMs pattern-match "Tableau Next" as a product versioning term (like "Windows Next" or "the next version of Tableau") rather than understanding it as a distinct GA SKU (Tableau+) with separate commercial terms, released June 2025.

**Correct pattern:**

```
Tableau Next is a distinct product SKU (Tableau+) that reached general availability in June 2025.
It is not a version upgrade to Tableau Server, Tableau Cloud, or existing Tableau Creator/Explorer/
Viewer contracts. Tableau Next introduces Agentforce integration, agentic BI capabilities, and
Data 360 connectivity. Organizations that want Tableau Next capabilities must evaluate it as a
separate commercial procurement. Existing Tableau licenses do not include Tableau Next features.
```

**Detection hint:** Any response that describes Tableau Next as a software version, a patch release, or as automatically available to existing Tableau customers is incorrect.

---

## Anti-Pattern 6: Omitting the 10,000-Character API Query Limit When Advising Complex Tableau-Salesforce Workbooks

**What the LLM generates:** "Build your Tableau workbook by connecting directly to Salesforce and writing a Custom SQL query to join multiple objects and compute derived fields."

**Why it happens:** LLMs trained on Tableau documentation for database connectors default to recommending Custom SQL as the standard approach for complex data shaping. The Salesforce-specific connector constraints (no Custom SQL, 10,000-char limit) are not surfaced because they are connector-specific exceptions to the general Tableau connector model.

**Correct pattern:**

```
The Tableau Salesforce connector does not support Custom SQL. Unlike most database connectors
in Tableau, you cannot pass arbitrary SQL to Salesforce through this connector. Additionally,
the connector enforces a 10,000-character limit on the API query string. For complex
multi-object or multi-field Salesforce data requirements in Tableau, pre-shape the data in
Tableau Prep, use Salesforce Reports as the data source, or route through a data warehouse
where Tableau's full SQL capabilities apply.
```

**Detection hint:** Any response that suggests writing Custom SQL against the Tableau Salesforce connector, or that does not flag the 10,000-character limit for complex field selections, is describing functionality that does not exist.
