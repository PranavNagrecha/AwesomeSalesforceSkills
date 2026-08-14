# Gotchas — Tableau ↔ Salesforce Connector

Non-obvious platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: There is no live connection. The Salesforce CRM connector is extract-only.

**What happens:** Architecture decks routinely open with a "live vs extract"
trade-off for Salesforce data in Tableau. That trade-off does not exist for the
Salesforce CRM connector. Tableau's own documentation states: "Tableau Desktop,
Tableau Server, and Tableau Cloud are limited to extracts when using the
Salesforce CRM connector." A design that promises operational dashboards "always
showing current Salesforce data" via this connector cannot be built.

**When it occurs:** Design phase, usually surviving all the way to build because
the connector *looks* live in Tableau Desktop while you are authoring against a
small sample.

**How to avoid:** Set freshness expectations from the extract refresh schedule,
not from the connector. Where genuine live query is a hard requirement, the
connector is the wrong component — route through Salesforce Data Cloud (which
Tableau can query directly), or reconsider whether the requirement is really
"live" or really "refreshed hourly". Note also that extracts do not refresh
themselves: refresh schedules are configured explicitly in Tableau Cloud.

---

## Gotcha 2: Formula fields and long text silently vanish from the extract

**What happens:** Per Tableau: "text fields that are greater than 4096 characters
and calculated fields will not be included in the extract." Formula fields are
Salesforce's calculated fields. A dashboard built on `Days_Open__c` or
`Weighted_Amount__c` finds the column simply absent — no error, no warning, just
a field that is not in the data source.

**When it occurs:** Any Salesforce org, because formula fields are how most
Salesforce reporting logic is expressed. It bites hardest when the field existed
during a Desktop prototype against a different data source and disappeared on the
first real extract.

**How to avoid:** Audit the field list for `FieldDefinition.DataType` starting
with "Formula" before promising a metric, and decide per field: re-implement the
formula as a Tableau calculated field (moves the logic, splits the definition) or
materialise it into a stored field on the Salesforce side (keeps one definition,
costs storage and an automation). Do the same audit for Long Text Area fields
over 4096 characters.

---

## Gotcha 3: Joins are restricted to left and inner, with equality only

**What happens:** "Only left and inner joins are supported" and Salesforce
connections "do not support non-equi joins and must use the equality operator
(=)." A model that needs a full outer join (accounts with no opportunities *and*
opportunities with no account owner) or a range join (activity falling between a
campaign's start and end dates) cannot be expressed in the connector.

**When it occurs:** Coverage and gap analysis — exactly the questions executives
ask that reports in Salesforce cannot answer, which is often why Tableau was
bought.

**How to avoid:** Move the shaping upstream. Either land the data somewhere that
supports the join (Data Cloud, a warehouse) or perform the union in Tableau Prep
before the extract. Also budget for the query-length ceiling Tableau documents:
"The Force.com API restricts queries to 10,000 total characters" — a wide object
with hundreds of selected fields can exceed it, and the failure looks like a
connector error rather than a field-count problem.

---

## Gotcha 4: Extract refreshes consume the org's 24-hour API allocation

**What happens:** Each refresh is API traffic against the same allocation
everything else in the org shares. The daily allocation is edition- and
licence-derived: Developer Edition gets 15,000 calls per 24 hours; Enterprise and
Professional get a 100,000 base plus 1,000 per Salesforce or Platform licence;
Unlimited and Performance get the 100,000 base plus 5,000 per licence; a full
sandbox gets 5,000,000. Twenty workbooks refreshing hourly is 480 refresh cycles
a day landing on top of every integration the org already runs.

**When it occurs:** After the pilot succeeds and refresh cadence gets tightened
"because the data felt stale". The first symptom is usually an unrelated
integration failing.

**How to avoid:** Forecast refresh volume against the org's actual allocation
before scheduling, and stagger schedules off the hour so refreshes do not stack.
There is a second, separate ceiling: requests running 20 seconds or longer are
capped at **25 concurrent** for production orgs and sandboxes (5 for Developer
Edition and trials), and exceeding it returns the exception code
**`REQUEST_LIMIT_EXCEEDED`**. Large extracts are precisely the long-running
requests that consume that pool. Note also that incremental refresh does not
rescue you unboundedly — Tableau limits incremental refresh results to "the
previous 30 days".

---

## Gotcha 5: The connector needs five APIs enabled and a licence tier that has them

**What happens:** Tableau's Salesforce connector requires SOAP API, REST API for
metadata, Bulk API, REST API for non-Bulk objects, and the Replication SOAP APIs.
"API access requires Salesforce Professional Edition or higher." A Professional
Edition org without the API add-on, or a user whose profile lacks **API Enabled**,
fails at connection time in a way that reads like a credential problem.

**When it occurs:** Professional Edition orgs, and any org where the Tableau
service account was created by cloning a business-user profile.

**How to avoid:** Provision a dedicated integration user with a permission set
granting **API Enabled** plus read on exactly the objects and fields the
workbooks need — never a System Administrator clone. The extract inherits that
user's field-level security and sharing, which means the permission set is also
the row- and column-level security boundary for every dashboard built on it. On
the Tableau side, creating the connection requires the **Site Administrator
Creator** site role.

---

## Gotcha 6: Tableau View LWC filtering works on record pages only, on at most two fields

**What happens:** The Tableau View Lightning web component is dropped on a Home
or App page with an expectation of context filtering. Dynamic view filtering
"only work[s] on Lightning record pages" — on Home, App and Experience Cloud
pages the only "filter" available is component *visibility*, which shows or hides
the whole component rather than filtering the visualisation. On record pages the
component filters on up to two fields.

**When it occurs:** Executive Home-page dashboards, and Experience Cloud sites
where the design assumed the same behaviour as a record page.

**How to avoid:** Put context-filtered vizzes on record pages, and publish
pre-filtered views for Home and App pages. Two more failure modes worth checking
before blaming the embed: the configured URL must point to **a view, not a
workbook**, and field names "must be entered as they are defined in the data
source" — a Salesforce label typed where the data-source field name belongs
produces an unfiltered viz with no error. For SSO, the component "only supports
SAML as the SSO method" and the IdP "must be either the Salesforce IdP or the
same IdP that is used for your Salesforce instance"; a separate Tableau IdP means
users re-authenticate on every page load.
