# Gotchas — Data Virtualization Patterns

Non-obvious External Object / Salesforce Connect behaviors that bite
real implementations.

---

## Gotcha 1: External Objects do not support Apex triggers

**What happens.** Admin or developer tries to add a trigger to
`External_Account__x`. The setup UI does not even show the option;
SOAP `compileAndTest` silently rejects the trigger metadata.

**When it occurs.** Anyone porting custom-object automation to an
External Object discovers this on the first attempt at parity.

**How to avoid.** Plan automation requirements before choosing
virtualization. If automation must react to external row changes,
the source must push events into Salesforce (CDC inbound, Platform
Events, REST callback), or the data must be replicated into a
regular custom object.

---

## Gotcha 2: Validation rules and record-triggered flows do not run on External Objects

**What happens.** Validation logic added to the parent custom object
is expected to also constrain the External Object, but External
Objects bypass validation entirely.

**When it occurs.** Writable External Objects (OData 4.0). The write
goes to the remote source; Salesforce validation is not in the path.

**How to avoid.** Push validation to the source system. Document
clearly that Salesforce-side validation is not authoritative for
External Object writes.

---

## Gotcha 3: Indirect Lookup requires Unique + External Id on the Salesforce side

**What happens.** Indirect Lookup definition fails with a vague
error, or behaves unpredictably across duplicate matches.

**When it occurs.** Salesforce parent's External Id field is not
marked Unique, or is marked External Id but not Unique.

**How to avoid.** On the Salesforce parent's External Id field:
External Id = true AND Unique = true. Without both, Indirect Lookup
will not work reliably.

---

## Gotcha 4: Callouts to External Objects count against per-transaction limits

**What happens.** A page render or bulk operation issues many
External Object queries; the operation fails with a callout-limit
error.

**When it occurs.** Sync callout cap is 100 per transaction across
all callouts; External Object queries count. A page with multiple
External Object related lists multiplies the count quickly.

**How to avoid.** Profile the callout count of the page or batch.
For batch operations, prefer one broad query over many narrow ones.
Consider replication for batch-heavy workloads.

---

## Gotcha 5: Reports against External Objects are limited

**What happens.** Standard report types referencing External Objects
support a restricted subset of features. Many cross-object joins,
roll-ups, and filtered groupings either are not available or behave
differently from native objects.

**When it occurs.** Reporting requirements arrive after the External
Object is configured.

**How to avoid.** Validate the reporting requirements during the
virtualize-vs-replicate decision. If reporting is a hard
requirement, replication is usually the safer path.

---

## Gotcha 6: External Object data does not appear in Salesforce search index by default

**What happens.** Global search does not return External Object
rows; users complain that the data is "missing" even though it
displays on related lists.

**When it occurs.** Default search scope. Some External Object
configurations support search in scope but with caveats; not all
adapters / data sources support it.

**How to avoid.** Confirm search support for the specific adapter
and data source. If global search across External Objects is a
requirement and not supported, either replicate the data or scope
expectations explicitly with users.

---

## Gotcha 7: Writable External Object writes do not fire Salesforce automation

**What happens.** Update on `External_Account__x` propagates to the
remote source; no triggers fire, no flows fire, no roll-ups
recalculate locally.

**When it occurs.** Any writable External Object configuration where
the write was expected to behave like a custom-object DML.

**How to avoid.** Stage writes through a regular custom object whose
trigger / flow does the callout. The custom object becomes the
"event surface" Salesforce automation reacts to.

---

## Gotcha 8: 24-hour callout cap for Salesforce Connect varies by edition / license

**What happens.** Production org hits a daily ceiling on External
Object callouts and queries fail until the rolling window resets.

**When it occurs.** Heavy External Object use on editions / licenses
with lower allowances. The cap is checked against a rolling 24-hour
window, not a calendar day.

**How to avoid.** Confirm the per-org allowance for your edition /
license tier in the official documentation. Monitor callout
consumption with Setup -> System Overview or via Tooling API
metrics.
