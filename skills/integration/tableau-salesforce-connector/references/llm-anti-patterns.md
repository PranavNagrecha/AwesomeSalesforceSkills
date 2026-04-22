# LLM Anti-Patterns — Tableau ↔ Salesforce Connector

Common mistakes AI coding assistants make when wiring Tableau to Salesforce.

## Anti-Pattern 1: Default live connection for every dashboard

**What the LLM generates:** Every Tableau workbook configured with live connection to Salesforce for "freshness."

**Why it happens:** The model defaults to live because it sounds safer; it does not model API-limit impact.

**Correct pattern:**

```
Per-dashboard decision. Live = few, contextual, embedded. Extract =
most executive/analytical views. Org-wide live mode exhausts API
limits and throttles every other integration. Budget live dashboards
against API headroom and prefer extracts by default.
```

**Detection hint:** A Tableau environment with zero extracts and all live data sources against Salesforce.

---

## Anti-Pattern 2: Iframe embedding without Connected App + CSP update

**What the LLM generates:** `<iframe src="https://tableau.example.com/...">` dropped into a record page.

**Why it happens:** The model treats Tableau like any embed and forgets Salesforce CSP + Tableau Connected App requirements.

**Correct pattern:**

```
Tableau embedding requires (a) Tableau Connected App for
authentication, (b) Salesforce CSP Trusted Sites + CORS allowlist,
and (c) ideally the Tableau Viz LWC for native integration. Raw
iframe without Connected App shows a login wall inside the record
page.
```

**Detection hint:** A Lightning page with an iframe Tableau embed and no Tableau Connected App defined.

---

## Anti-Pattern 3: Tableau row-level security unchecked against Salesforce sharing

**What the LLM generates:** Extract is open to all Tableau Creators; users see all Salesforce data.

**Why it happens:** The model treats extract ACLs as a Tableau-only concern and ignores Salesforce sharing intent.

**Correct pattern:**

```
Tableau RLS must replicate Salesforce sharing intent (or use CRM
Analytics which inherits natively). Build user filters / Tableau
permissions from the Salesforce role or tenant mapping. An open
extract inside Tableau Server is a data exfiltration path.
```

**Detection hint:** A Tableau extract of Salesforce data with no user filter and Tableau "All Users" group has access.

---

## Anti-Pattern 4: Non-selective SOQL in a live dashboard on a large object

**What the LLM generates:** Custom SQL on Opportunity with no selectivity; dashboard fails on large orgs.

**Why it happens:** The model writes the analyst SQL without considering Salesforce selectivity rules.

**Correct pattern:**

```
Live dashboards on large-object tables require indexed, selective
filters (Account, Owner, RecordType, custom indexed fields). Build
the dashboard with default filters applied and force selectivity via
parameter defaults. Non-selective SOQL on a 10M row object errors
out regardless of API budget.
```

**Detection hint:** Tableau data source with custom SQL doing `SELECT * FROM Opportunity` with no WHERE clause.

---

## Anti-Pattern 5: Over-scoped Connected App OAuth token

**What the LLM generates:** Tableau Connected App with `full` scope for simplicity.

**Why it happens:** The model picks the widest scope to avoid scope-miss errors.

**Correct pattern:**

```
Tableau Connected App scope should be the minimum needed: `api` and
specific object read access. Avoid `full`, `web`, or `refresh_token`
beyond what the refresh cadence needs. Over-scoped tokens give
Tableau more Salesforce reach than reporting requires.
```

**Detection hint:** Connected App metadata with `<scopes>Full</scopes>` for Tableau integration.
