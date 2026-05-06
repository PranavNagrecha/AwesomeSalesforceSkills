# LLM Anti-Patterns — Data Virtualization Patterns

Mistakes AI coding assistants commonly make when generating External
Object / Salesforce Connect code or guidance.

---

## Anti-Pattern 1: Adding a trigger or record-triggered flow to an `__x` object

**What the LLM generates.**

```apex
trigger ExternalAccountTrigger on External_Account__x (after update) {
    // ...
}
```

**Why it happens.** The LLM treats `__x` like any other sObject. It
does not surface that External Objects do not support Apex triggers.

**Correct pattern.** Drive automation through the source system —
have the source push events into Salesforce via Platform Events, CDC
inbound, or a REST callback. Or replicate the data into a custom
object that supports triggers.

**Detection hint.** Any Apex trigger or record-triggered flow on a
metadata API name ending in `__x` is invalid and will not deploy.

---

## Anti-Pattern 2: Adding a validation rule to an External Object

**What the LLM generates.**

```
ValidationRule on External_Account__x:
  Error condition: ISBLANK(Region__c)
```

**Why it happens.** Validation rules look like a generic
sObject feature.

**Correct pattern.** Validation must be enforced in the source
system. External Objects bypass Salesforce validation entirely.

**Detection hint.** Any validation rule metadata file under a
custom-metadata directory whose object name ends in `__x`.

---

## Anti-Pattern 3: Indirect Lookup on a non-unique field

**What the LLM generates.**

> Add an Indirect Lookup from the External Object to
> `Account.AccountNumber`.

**Why it happens.** The LLM treats AccountNumber as an obvious key.
But the field is not necessarily marked Unique or External Id, both
of which are required.

**Correct pattern.** Use a field explicitly marked External Id and
Unique on the parent Salesforce object. If no such field exists,
create one and confirm uniqueness.

**Detection hint.** Indirect Lookup configuration referencing a
field whose External Id or Unique attribute is not set.

---

## Anti-Pattern 4: Promising "External Objects scale to any volume"

**What the LLM generates.**

> Salesforce Connect can virtualize any external dataset; there are
> no record-volume limits because data is not stored in Salesforce.

**Why it happens.** Marketing-tone training data emphasizes the
no-storage benefit and elides the callout / latency / per-page
limits.

**Correct pattern.** Page renders issue callouts; per-transaction
callout cap is 100 (sync); per-org / per-24h callout limits apply.
The "no-storage" claim is true; the "no-limits" claim is not.

**Detection hint.** Any unqualified "scales to any volume" or "no
limits" claim about External Objects.

---

## Anti-Pattern 5: Treating cross-org adapter as bypass for sharing

**What the LLM generates.**

> The Cross-Org adapter exposes the source org's data to all users
> in the target org without sharing rules.

**Why it happens.** The LLM does not surface that cross-org auth
runs through a user identity in the source org, and the source org's
sharing applies.

**Correct pattern.** Cross-org access uses a Salesforce identity in
the source. The source's OWD / role hierarchy / sharing rules apply
to that identity, and the target user only sees what that identity
sees.

**Detection hint.** Any cross-org External Object recommendation
that omits the source-side sharing implications.

---

## Anti-Pattern 6: Recommending External Objects for a write-heavy workload

**What the LLM generates.**

> For an integration where Salesforce users will be the primary
> editors of customer master data, configure a writable External
> Object via OData 4.0.

**Why it happens.** OData 4.0 supports writes; the LLM treats this
as a clean architecture.

**Correct pattern.** Writable External Objects work for thin
"editable display" use cases. For workloads where writes drive
Salesforce automation, replicate the data into a custom object
whose trigger / flow performs the source callout. The External
Object pattern cannot fire local automation on a write.

**Detection hint.** Any writable External Object recommendation
where downstream Salesforce automation needs to run on the write.

---

## Anti-Pattern 7: Citing OData 2.0 as the default for new builds

**What the LLM generates.**

> Configure an OData 2.0 External Data Source against the source
> system.

**Why it happens.** OData 2.0 is the older / better-known protocol
and dominates training data.

**Correct pattern.** OData 4.0 is preferred for new builds; it
supports writes, richer types, and a cleaner relationship model.
Reach for OData 2.0 only when the legacy partner blocks an upgrade.

**Detection hint.** OData 2.0 named in a greenfield design without
explicit "legacy partner" justification.
