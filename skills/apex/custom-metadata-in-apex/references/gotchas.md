# Gotchas - Custom Metadata In Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Tests Quietly Depend On Org Metadata

**What happens:** A test passes because the org already contains the expected `__mdt` records.

**When it occurs:** Teams rely on metadata visibility in tests but never name the dependency. Test isolation covers "standard objects, custom objects, and custom settings data", but "objects that are used to manage your organization or metadata objects can still be accessed in your tests" (Apex Developer Guide L40707–40709, L40727–40729). Custom **settings** are on the other side of that line — tests "must use `SeeAllData=true` to see existing custom settings data in the organization" (L13515–13516) — so a team migrating settings to custom metadata sees tests that suddenly pass with no fixture at all, and concludes nothing.

**How to avoid:** Make expected records explicit in the test design and naming. Reading org configuration is a legitimate assertion — that the deployment contract holds — but it belongs in a test whose name says so, like `theDefaultRecordIsDeployedToThisOrg` in `references/code-examples.md` § 4. Every other test injects its rows.

---

## Gotcha 2: Runtime DML Thinking

**What happens:** Architects choose CMT for configuration and then treat it like ordinary data in business logic.

**When it occurs:** The read/write difference was never surfaced early. The platform is unambiguous: "Apex code can create, read, and update (but not delete) custom metadata records… You can edit records in memory but not upsert or delete them. Apex code can deploy custom metadata records, but not via a DML operation. Moreover, DML operations aren't allowed on custom metadata in the Partner or Enterprise APIs." (Metadata API Developer Guide L41317–41322.) The Object Reference says the same thing by omission: the supported calls on a `Custom Metadata Type__mdt` object are `describeSObjects(), describeLayout(), query(), retrieve()` — there is no `create()`, `update()`, `upsert()` or `delete()` (Object Reference L5671–5672).

**How to avoid:** Keep reads in business logic and isolate create or update behavior behind metadata deployment workflows. The in-memory half of that rule is a gift, not a restriction: it is what lets a test build `__mdt` sObjects and inject them with no DML at all.

---

## Gotcha 3: Package Visibility Drift

**What happens:** A pattern that worked in an unpackaged org breaks once managed-package visibility or subscriber-control rules matter.

**When it occurs:** Teams ignore namespace, protected records, or ownership of edits. Two separate switches decide this, and they are frequently confused. The **type** carries `visibility`, a `SetupObjectVisibility` enum of `Public` / `Protected` / `PackageProtected`, defaulting to `Public` (Metadata API Developer Guide L41363–41377). Each **record** carries its own boolean `protected` (L41480–41519). Protection only means anything inside a managed package: "With unpackaged metadata, both developer-controlled and subscriber-controlled access behave the same: like subscriber-controlled access" (L41321–41322), and the Apex Reference Guide states the security consequence outright — "Protected custom metadata types behave like public custom metadata types when they are outside of a managed package. Public custom metadata types are readable for all profiles, including the guest user. Do not store secrets, personally identifying information, or any private data in these records." (L170826–170830.)

**How to avoid:** Decide early whether records are package controlled or subscriber controlled, and set both switches deliberately. Never treat `protected` as a secret store outside a managed package — use a Named Credential or an encrypted field instead (same Apex Reference Guide warning, L170830–170832).

---

## Gotcha 4: `getAll()` And `getInstance()` Silently Truncate At 255 Characters

**What happens:** A configuration value comes back cut off mid-string, with no exception and no warning. Downstream code compares it to the full value, the comparison fails, and the failure looks like a data problem rather than an API one.

**When it occurs:** On every `getAll()` and every `getInstance()` overload, against any field whose content can exceed 255 characters. "Only the first 255 characters are returned for any field in a custom metadata type record, so longer text fields get truncated. If you want all the field data from a custom metadata type record, use a SOQL query." (Apex Reference Guide L204569–204572; the same sentence is repeated for `getInstance(recordId)` at L204605–204607, `getInstance(developerName)` at L204645–204647, and `getInstance(qualifiedApiName)` at L204678–204680.)

**How to avoid:** Keep the cache accessors for short scalars — a flag, a threshold, a class name, a queue developer name — and move any field that could carry a template, a JSON blob, or a long description to a SOQL read. The switch costs nothing: custom metadata records carry no SOQL query limit inside a transaction (Apex Developer Guide L19616–19619).

---

## Gotcha 5: `SucceededPartial` Is Reported As Success

**What happens:** A callback checks `result.status == Metadata.DeployStatus.Succeeded`, sees false, logs an error, and the on-call engineer chases a failure that half-applied. Or the opposite — the callback checks `result.success`, sees `true`, and reports a clean deployment that left some components unchanged.

**When it occurs:** Whenever a container holds more than one component. `Metadata.DeployStatus` has nine values, not two: `Canceled`, `Canceling`, `Failed`, `FinalizingDeploy`, `FinalizingDeployFailed`, `InProgress`, `Pending`, `Succeeded`, and `SucceededPartial` — the last described as "The deployment succeeded, but some components might not have been successfully deployed. Check Metadata.DeployResult for more details." (Apex Reference Guide L172206–172232.)

**How to avoid:** Branch on all three real outcomes and read `result.details.componentFailures`, a `List<Metadata.DeployMessage>` carrying `fullName`, `problem`, and `problemType` per component (L171401–171412, L171623–171692). `references/code-examples.md` § 5 does exactly this.

---

## Gotcha 6: The Callback Lags The Deployment

**What happens:** Code enqueues a metadata deployment, then reads the value back in the same or the next transaction and gets the old one. A retry loop built on that read never terminates.

**When it occurs:** Always, because the write path is asynchronous by construction. "Deployment is queued for asynchronous processing." (Apex Developer Guide L28194–28196.) And the callback lags even the deployment: "Because the callback is called as asynchronous Apex after deployment, there may be a brief period where the deploy has completed, but your callback has not been called yet." (Apex Reference Guide L171091–171094.) The queued job and the callback both count as asynchronous Apex jobs against the org's limits (Apex Developer Guide L28226–28229), and Salesforce caps how many Apex-originated deployments can be enqueued at once (L28229–28230, Apex Reference Guide L174160–174163).

**How to avoid:** Never read back in the same transaction, never call `enqueueDeployment` from a trigger or a per-record loop, and make the callback the only place that declares the change applied. `Metadata.Operations.enqueueDeployment` returns the job Id — persist it if a UI needs to poll.

---

## Gotcha 7: Two Components With The Same `fullName` In One Container

**What happens:** A loop builds one `Metadata.CustomMetadata` per change, two changes touch the same record, both go into the container, and the deployment errors instead of merging them.

**When it occurs:** Any time the container is populated from a collection rather than from one deliberate change. The method documentation carries the warning directly: "Avoid adding components to a `Metadata.DeployContainer` that have the same `Metadata.Metadata.fullName` because it causes deployment errors." (Apex Reference Guide L171293–171295.) `DeployContainer` offers `getMetadata()`, `removeMetadata(md)` and `removeMetadataByFullName(fullName)` (L171312–171356) precisely because containers get built up rather than declared.

**How to avoid:** Key the pending changes by `fullName` in a `Map` before you build the container, so one record produces one component carrying all its changed fields. Assert `getMetadata().size()` in the test, as `references/code-examples.md` § 7 does.

---

## Gotcha 8: An Omitted Field Is Not A Cleared Field

**What happens:** A deployment intended to blank a configuration value leaves the old value in place, and the behaviour it controls keeps running.

**When it occurs:** On updates. "Using null field values differs from leaving out the [values element] for a particular field entirely. If you leave out the [values element], the value of the field doesn't change. The field's value is null for newly deployed custom metadata records and left at its previous value for updated custom metadata records." (Metadata API Developer Guide L41753–41757.) So the same file means "create with null" the first time and "leave alone" every time after.

**How to avoid:** To clear a field, ship it explicitly — `<value xsi:nil="true"/>` in the `.md-meta.xml`, or a `Metadata.CustomMetadataValue` whose `value` is `null` in Apex. To leave a field alone, omit it. Reviewers should read an update's `<values>` list as a complete statement of what changes, and nothing else.

---

## Gotcha 9: `fieldManageability` Decides Who May Ever Change A Field Again

**What happens:** A packaged configuration field turns out to be un-tunable by the customer, or un-upgradable by the publisher — and the answer is baked into the field definition, not into a permission.

**When it occurs:** On packaged custom metadata types. `fieldManageability` is "Available only for fields on custom metadata types" and takes three values: `Locked` — "The field can't be updated"; `DeveloperControlled` — "The creator of the record can update the field with a package upgrade"; `SubscriberControlled` — "Anyone with proper permissions can update the field. The field can't be updated with a package upgrade." (Metadata API Developer Guide L43406–43413.) There is a second rule for relationship fields: when the field type is `MetadataRelationship`, a subscriber-controlled entity-definition field forces the field-definition field to be subscriber-controlled too, and an upgradeable one forces it to be either upgradeable or subscriber-controlled (L43414–43420).

**How to avoid:** Choose per field, at design time, and write the choice into the `.field-meta.xml` — `SubscriberControlled` for the knobs customers tune, `DeveloperControlled` for values the package must be able to correct in an upgrade. A `SubscriberControlled` field can never again be fixed by a package upgrade.

---

## Gotcha 10: Relationship Values Are API Names, And Never To The Same Type

**What happens:** Code sets a `MetadataRelationship` field to a record Id and the deployment fails, or a designer models a parent/child hierarchy inside one custom metadata type and cannot deploy it.

**When it occurs:** On any custom metadata relationship field. "When setting the value for relationship fields, use the qualified API name of the related metadata, not the ID." (Apex Reference Guide L171050.) The same holds in XML for `EntityDefinition` and `FieldDefinition` fields, which take "qualified API names of custom and standard entities and their fields" — for example `v1__SalesAgreement__c` and `v1__CustomerReference__c` (Metadata API Developer Guide L41698–41706). And the self-reference is flatly ruled out: "No custom metadata relationship can relate records of the same type to each other." (Apex Reference Guide L174089.)

**How to avoid:** Pass developer names / qualified API names, never Ids. When a hierarchy is genuinely needed, model it as two types with a relationship between them — the pattern the Apex Reference Guide's own two-record example uses (L174080–174115) — rather than one self-referencing type.

---

## Gotcha 11: Long Text On A Custom Metadata Type Has No Safe Read Path

**What happens:** A field designed to hold a template, a mapping blob, or a long description is readable in Setup and through SOQL, but every cache accessor hands back the first 255 characters.

**When it occurs:** The 255-character truncation on `getAll()` and `getInstance()` is documented (Apex Reference Guide L204569–204572), and the `CustomMetadataValue` `xsi:type` table in the Metadata API Developer Guide enumerates ten field definitions that a deployed value may carry — Checkbox, Date, Date/Time, Picklist, Text, Phone, TextArea, URL, Email, and Number/Percent at scale 0 or otherwise (L41716–41749). `LongTextArea` is not among them, and `Metadata.CustomMetadataValue.value` supports only the primitives Boolean, Date, DateTime, Decimal, Double, Integer, Long and String (Apex Reference Guide L170977–170985, L171041–171049).

**UNVERIFIED (2026-09-05):** whether Setup outright *blocks* creating a Long Text Area field on a `__mdt` type is a help.salesforce.com claim and help.salesforce.com cannot be fetched. What the guides in scope do state is the 255-character read truncation, the `xsi:type` table's omission of `LongTextArea`, and the primitive list on `Metadata.CustomMetadataValue.value`. Treat the checker's `LongTextArea` rule as advisory on that basis.

**How to avoid:** Treat long text on a `__mdt` as a design smell rather than a field-type question. Split the value across several Text(255) rows keyed by sort order, or move the payload to a Static Resource and keep only its name in the custom metadata. If a long field already exists, every read of it must be SOQL, and this skill's checker flags a `LongTextArea` in a `__mdt` object definition for exactly that reason.

---

## Gotcha 12: The Full Name Loses A Suffix And Gains A Namespace

**What happens:** A deployment built in Apex fails with an unhelpful component error because `fullName` was assembled from the object's API name.

**When it occurs:** Whenever the string is built by hand. `Metadata.CustomMetadata.fullName` is `'MetadataTypeName.MetadataRecordName'` — the `__mdt` suffix is dropped (Apex Reference Guide L170844–170845). Inside a namespace both halves must be qualified: "the full name for a custom metadata MDType1__mdt component named Component1 that is contained in the myPackage namespace is `myPackage__MDType1__mdt.myPackage__Component1`" (Apex Developer Guide L28199–28203), and the guide's own note adds "If both the type and the record are in Namespace, use something like: `customMetadata.fullName = 'Namespace__MetadataTypeName.Namespace__MetadataRecordName'`" (Apex Reference Guide L170852–170855). `package.xml` follows the same rule from the other side — the records list under `CustomMetadata` as `picklist1234__ReusablePicklist.travelApp1234__Hotels` (Metadata API Developer Guide L41694–41696).

**How to avoid:** Build `fullName` from a constant for the type name, never from `SObjectType.getDescribe().getName()`, and derive the namespace prefix once rather than per component. A packaged deploy that works unpackaged and fails after packaging is almost always this.
