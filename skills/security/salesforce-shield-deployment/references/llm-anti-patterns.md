# LLM Anti-Patterns — Salesforce Shield Deployment

Mistakes AI assistants reliably make when asked to plan a Shield rollout.

## Anti-Pattern 1: Treating Shield as a Single Enablement Step

**What the LLM generates:** "Enable Shield in Setup, then configure your encryption
policy and monitoring."

**Why it happens:** Shield is sold and marketed as one product, so it reads as one
feature with one switch.

**Correct pattern:**

```
Shield is three separately-operated capabilities:

  Shield Platform Encryption   changes application behaviour; highest risk
  Event Monitoring             read-only observability; long onboarding pole
  Field Audit Trail            not self-service - "For information about
                               enabling Field Audit Trail, contact your
                               Salesforce representative."

Plan three phases with a gate between each:

  1. Field Audit Trail   - first, because its value is TIME-DEPENDENT. History
                           you do not start collecting today cannot be bought
                           later.
  2. Event Monitoring    - second, because it is the instrument you need to
                           observe phase 3.
  3. Platform Encryption - last, ONE OBJECT AT A TIME, because it is the only
                           one that changes query and report semantics.
```

**Detection hint:** a Shield plan with one enablement step, or one that enables
encryption before the monitoring that would show its effects.

---

## Anti-Pattern 2: Quoting a Fixed Field Audit Trail Retention Number

**What the LLM generates:** "Field Audit Trail retains history for up to 10 years."

**Why it happens:** The figure appears widely in vendor summaries and secondary
sources, and a concrete number is more satisfying than a mechanism.

**Correct pattern:**

```
State the mechanism, which is different in a way that changes the design:

  Without FAT: "Salesforce retains field history data for up to 18 months, and
                up to 24 months via the API."
  With FAT:    "Salesforce retains archived field history data until you delete
                it."

And on the policy field:
  archiveRetentionYears is "The number of years until you manually delete data
  from the archive. Use this field as a reminder for manually deleting data. By
  default, field history data isn't automatically deleted when Field Audit Trail
  is enabled."

So: unbounded retention until an explicit deletion. That satisfies a MINIMUM
retention requirement trivially. A MAXIMUM retention requirement ("must not
retain beyond N years") needs a deletion process you build and schedule
yourself - nothing deletes on your behalf.

Do not confuse this with archiveAfterMonths, which is capped: "a minimum of 1
month and a maximum of 18 months."
```

**Detection hint:** any specific retention year figure presented as a platform
guarantee, or `archiveRetentionYears` described as automatic deletion.

---

## Anti-Pattern 3: Describing the Retention Policy as a Setup Screen

**What the LLM generates:** "Go to Setup → Field Audit Trail and set the retention
period for each object."

**Why it happens:** Nearly every other Salesforce configuration is a Setup screen, so
the model produces the expected shape.

**Correct pattern:**

```
The policy is Metadata API:

  "Use Salesforce Metadata API to define a field history retention policy for
   the fields that have history tracking enabled. Then use REST API, SOAP API,
   and Tooling API to work with your archived data."

  <historyRetentionPolicy>
      <archiveAfterMonths>18</archiveAfterMonths>
      <archiveRetentionYears>7</archiveRetentionYears>
      <gracePeriodDays>30</gracePeriodDays>
      <description>...owner and requirement...</description>
  </historyRetentionPolicy>

Requires the RetainFieldHistory permission.

And warn about the invisible default: "Salesforce doesn't include the default
retention policy when you retrieve the object's definition through Metadata API.
Salesforce retrieves only custom retention policies with the object definition."
A retrieve showing no policy does not mean no policy is in effect - the defaults
are 18 months in production and ONE MONTH in sandboxes.
```

**Detection hint:** a Setup navigation path offered for field history retention, or
an audit method that infers "no policy" from an empty retrieve.

---

## Anti-Pattern 4: Enabling Encryption Across Several Objects at Once

**What the LLM generates:** "Enable encryption on Contact, Lead, Account, and Case in
the same change to complete the rollout efficiently."

**Why it happens:** Batching is normally good change management, and the prompt often
lists several objects.

**Correct pattern:**

```
Encryption changes query semantics SILENTLY - filters return fewer rows, reports
come back empty, automations stop firing, and nothing throws. Batching N objects
means N possible causes for every regression.

Per-object gate:

  BEFORE  inventory every SOQL WHERE clause, report filter, list view filter,
          duplicate rule matching key, and automation criterion on the candidate
          fields; decide drop / deterministic / do-not-encrypt for each;
          snapshot expected query and report results
  DURING  enable the policy for that object only; run the re-encryption job -
          enabling a policy encrypts SUBSEQUENT writes only
  AFTER   verify on Encryption Statistics per object; re-run the snapshot and
          diff. A row-count change with NO error is the signature failure.

Only then proceed to the next object.
```

**Detection hint:** an encryption plan naming more than one object per change, or one
with no re-encryption step and no query regression snapshot.

---

## Anti-Pattern 5: Counting Event Monitoring as Done When It Is Enabled

**What the LLM generates:** "Enable Event Monitoring and connect your SIEM. Shield
monitoring is now in place."

**Why it happens:** Enablement is a discrete, checkable action; capability is not.

**Correct pattern:**

```
Detection requires someone looking, a permission to look with, an alert path,
and retention long enough to answer questions about the past.

The same question has three homes with three DIFFERENT permissions:

  Real-Time Event Monitoring   LoginEvent      View Real-Time Event Monitoring Data
  Event Log Files              EventLogFile    View Event Log Files
  Login History                LoginHistory    Manage Users

Close the phase with a scripted incident rehearsal:
  "User X may have exported customer data at 02:00 last Tuesday."
  Who has the permission? Pull the login. Correlate the export. Cross-check
  Setup Audit Trail. Produce a timeline. RECORD HOW LONG EACH STEP TOOK AND
  WHAT WAS MISSING.

That last line is the deliverable. And check retention against the requirement:
Login History alone is "up to 20,000 records of user logins for the past 6
months." If the obligation is measured in years, the SIEM pipeline is part of
this phase, not a follow-on.
```

**Detection hint:** an Event Monitoring plan with no rehearsal, no named analyst
persona, and no retention comparison against the compliance requirement.

---

## Anti-Pattern 6: Assuming Field History Captures Automation-Driven Changes

**What the LLM generates:** "Enable field history tracking on the audited fields and
all changes will be recorded."

**Why it happens:** "Tracks changes to the field" is the feature's description, and
the exceptions live several paragraphs down.

**Correct pattern:**

```
Three documented gaps that matter for an audit:

  - "If Process Builder, an Apex trigger, or a Flow causes a change on an object
     that the current user doesn't have permission to edit, Salesforce doesn't
     track that change. Field history honors the permissions of the current user
     and doesn't record changes that occur in the system context."
     Automation-driven changes can be INVISIBLE - exactly the class an audit
     cares about.

  - "Salesforce tracks changes to fields with more than 255 characters as edited,
     and doesn't record their old and new values." Tracked, but useless for a
     before/after audit.

  - Untrackable entirely: formula, roll-up summary, auto-number, Created By,
     Last Modified By, Expected Revenue on Opportunity, Master Solution Title
     and Details, long text, multi-select.

Validate the compliance scope FIELD BY FIELD against these before committing.
Where a formula is named, track its inputs. Where automation performs the
change, cover it with Event Monitoring or a custom audit object.
```

**Detection hint:** a compliance scope accepted wholesale, or a plan that names a
formula or roll-up field for history tracking.

---

## Anti-Pattern 7: Forgetting `FieldHistoryArchive` in a Deletion Workflow

**What the LLM generates:** a right-to-be-forgotten or data-destruction procedure
that deletes records and their related history.

**Why it happens:** The cascade from record to history is real and the model stops
there.

**Correct pattern:**

```
The cascade does NOT reach the archive:

  "If you delete a record in your production data, the delete cascades to the
   related history tracking records, but Salesforce doesn't delete the history
   copied into the FieldHistoryArchive big object."

Every deletion runbook needs FieldHistoryArchive as an explicit, separate step.
Salesforce documents a distinct procedure for deleting data there. A process
that stops at the record has not completed, and the residual copy is exactly
what a regulator asks about.

Related: enabling Platform Encryption does not encrypt already-archived history
- "If you turn on Platform Encryption, the previously archived data remains
unencrypted." State that position in the compliance documentation rather than
leaving it to be discovered.
```

**Detection hint:** a deletion or erasure workflow with no `FieldHistoryArchive`
step.

---

## Anti-Pattern 8: Writing a Transaction Security Policy with an MFA Action for API Events

**What the LLM generates:** "Create a transaction security policy with a multi-factor
authentication action so large exports are challenged rather than blocked."

**Why it happens:** The MFA action exists and is the less disruptive option, so the
model picks it as the balanced answer.

**Correct pattern:**

```
The MFA action degrades to a hard block on most surfaces:

  "The multi-factor authentication action isn't available in the Salesforce
   mobile app, Lightning Experience, or via API for any events. Instead, the
   block action is used. For example, if a multi-factor authentication policy is
   triggered on a list view performed via the API, ..."

So an "MFA challenge" policy is, for every integration and for Lightning
Experience, a BLOCK policy. Design it as one.

Test each policy against every surface the covered event can occur on -
Lightning, mobile, and API - not only the browser where it was authored. Where a
block is unacceptable on an API path, scope the policy to exclude it rather than
relying on a challenge that will never appear.
```

**Detection hint:** an MFA-action transaction security policy recommended for an API
or report-export event with no mention of the block fallback.
