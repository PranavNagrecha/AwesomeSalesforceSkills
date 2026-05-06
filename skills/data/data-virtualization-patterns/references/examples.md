# Examples — Data Virtualization Patterns

## Example 1 — Read-only customer master via OData 4.0

**Context.** Enterprise customer master lives in SAP. Sales reps need
a Contact-related list showing the customer's other accounts in SAP,
but writes happen in SAP, not Salesforce.

**Configuration.**

- External Data Source: OData 4.0 adapter, named credential pointing
  at SAP Gateway, OAuth 2.0 with refresh token.
- External Object: `SAP_Customer__x` (the `__x` suffix marks
  External Objects).
- Sync table definitions from the SAP metadata document.
- Indirect Lookup: `Contact.SAP_Customer_Number__c` (External Id,
  unique) -> `SAP_Customer__x.CustomerNumber`.

**What works.** Lightning record page on Contact shows a related
list of SAP customer rows. SOQL like
`SELECT Name, CustomerNumber FROM SAP_Customer__x WHERE Region = 'EMEA'`
runs against SAP through the adapter. Reports support a limited
joined-style format.

**What does not work.** Cannot add a record-triggered flow on
`SAP_Customer__x`. Cannot add a validation rule. Cannot create a
roll-up from `SAP_Customer__x` up to Account. Cannot full-text search
across External Object fields the way Salesforce search indexes
custom objects.

---

## Example 2 — Indirect Lookup gotcha: External Id field uniqueness

**Context.** Configure `Contact.External_Customer_Id__c` as an
Indirect Lookup target for `External_Customer__x`. Forget to mark
the field Unique.

**What goes wrong.** Indirect Lookup requires the matching field on
the Salesforce parent to be marked External Id AND Unique. Without
uniqueness, the platform refuses the lookup definition or behaves
unpredictably across multiple matches.

**Right answer.** On the Salesforce parent object's External Id
field: set `External Id = true`, `Unique = true`, optionally
`Case Sensitive = true` if the source distinguishes case.

---

## Example 3 — Callout-budget arithmetic

**Context.** Lightning record page renders three components that
each query an External Object: a related list, a custom LWC, and a
custom Apex controller. Each component issues a callout per page
render.

**Math.**

- Page render = 3 callouts against External Objects.
- A bulk operation that touches 30 records sequentially could
  multiply this — 90 callouts per record, well over the 100-per-
  transaction sync callout limit.
- A scheduled job iterating External Object queries can blow through
  the per-24-hour external-object callout cap.

**Mitigation.**

- Cache where appropriate — Custom Apex adapters can implement
  short-window caching at the connector layer.
- Prefer single broader queries over many narrow ones (fetch a page
  of 200 once, not 200 calls of one).
- For batch use cases, use the Salesforce Connect "high data volume"
  setting which alters caching / pagination behavior.

---

## Example 4 — Cross-org adapter for two Salesforce orgs

**Context.** Acquired company keeps their Salesforce org running.
The parent org needs to display the acquired company's Cases on
Account record pages without migrating data.

**Configuration.**

- External Data Source: Salesforce (cross-org) adapter on the parent.
- Auth: Per-User authentication with named credential pointing at
  the acquired org's My Domain.
- Object: `Acq_Case__x` mirroring the Case fields the parent org
  needs.
- Indirect Lookup: `Account.Acquired_Account_Id__c` (External Id)
  -> `Acq_Case__x.AccountId`.

**What is special vs OData adapter.** Cross-org uses the Salesforce
REST API under the hood, so the source's sharing rules apply. A user
in the parent org sees only what their cross-org user identity can
see in the source org — sharing crosses orgs.

---

## Example 5 — Writable External Object via OData 4.0

**Context.** Source system supports OData 4.0 writes. Want users to
edit `External_Account__x` from a Salesforce record page and have
the write propagate to the source.

**Configuration.** External Data Source flagged as writable. Field-
level write capability per External Object field.

**Failure modes to plan for.**

- **Source rejects the write.** OData adapter surfaces the error;
  user sees a save error. Nothing was committed in Salesforce
  (External Objects do not store local rows).
- **Source accepts but slow.** UI hangs waiting for the response.
  Page-load timeouts apply.
- **Salesforce automation reaction is impossible.** No triggers fire
  on External Object writes; no flow can react to the change.

**Practical guidance.** Writable External Objects work for
"editable display" use cases. For anything where the write needs to
trigger downstream Salesforce automation, stage the write through a
regular custom object that fires a trigger that calls the external
system, rather than going through External Object writes.

---

## Example 6 — Decision: virtualize vs replicate for invoice history

**Context.** Finance team wants invoice history visible on Account
pages. 2M invoices, growing 50K per month. Source = Oracle ERP.

**Virtualize tradeoffs.** Zero storage cost; always-fresh data;
limited search and reporting; one callout per page render against
Oracle (Oracle's load-tolerance sets the ceiling).

**Replicate tradeoffs.** 2M-row custom object adds storage; need
incremental sync (CDC, scheduled batch, or push from Oracle); full
search, reporting, automation, history tracking available; data is
24h stale by default.

**Decision factors.**

- Reporting requirements (replicate wins).
- Source latency / load (virtualize loses if Oracle is slow).
- Storage budget (replicate loses).
- Need to fire automation on invoice arrival (replicate wins).
- Data residency / compliance (virtualize wins because data never
  lands).

**Default for this profile.** Replicate the recent N months
(rolling), virtualize the older "lookup-only" tail. Hybrid is often
the right answer for high-volume financial history.
