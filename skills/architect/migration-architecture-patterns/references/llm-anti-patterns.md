# LLM Anti-Patterns — Migration Architecture Patterns

Mistakes AI coding assistants commonly make when advising on org
migration. The consuming agent should self-check before recommending a
migration design.

---

## Anti-Pattern 1: Skipping the metadata-audit phase

**What the LLM generates.** Step-by-step migration plans that begin
with "extract data from source" and "load data into target" without
a metadata-reconciliation step in between.

**Why it happens.** "Migrate data" is the named ask; metadata
reconciliation is implicit prerequisite work the LLM doesn't elevate
to a first-class step.

**Correct pattern.** Every migration plan starts with: (1) inventory
metadata in scope, (2) build a delta map between source(s) and
target, (3) reconcile every delta with a documented decision. THEN
data movement is designed.

**Detection hint.** Any migration plan whose first action is "export
data" or "use Bulk API to load" is missing the audit phase.

---

## Anti-Pattern 2: Treating Salesforce record IDs as portable

**What the LLM generates.** Recommendations that store Salesforce IDs
in external systems and assume they survive migration. Or migration
plans that move records without setting external-Id fields and
capturing the Id-remap mapping.

**Why it happens.** IDs feel like global identifiers; the LLM
doesn't surface that they're org-scoped.

**Correct pattern.** Migration design always includes:
- An external-Id strategy for every object in scope.
- A captured source-Id ↔ external-Id ↔ target-Id mapping table.
- An external-system inventory naming each system that holds source
  IDs and the plan to update them.

**Detection hint.** Any migration plan with no mention of external-Id
fields, Id-remapping, or external-system inventory is missing a
critical layer.

---

## Anti-Pattern 3: Regulatory split with a "convenience" runtime bridge

**What the LLM generates.** "Split the patient data into a new org for
HIPAA compliance, and add a Salesforce Connect bridge so the original
org can still query the patient records when needed."

**Why it happens.** The LLM optimizes for user convenience without
weighing the regulatory driver. Bridges are sympathetic; isolation
sounds like a barrier.

**Correct pattern.** Regulatory splits enforce isolation
architecturally. NO runtime bridge. Users who need both orgs get
named accounts in both, with full audit logging in both. The bridge
recommendation is wrong by construction in this scenario.

**Detection hint.** Any "split for regulatory isolation" plan that
includes the words "Salesforce Connect" or "cross-org adapter" or
"bridge" or "external object pointing back at source" is wrong.

---

## Anti-Pattern 4: Coexistence as the default answer

**What the LLM generates.** "Use coexistence to keep both orgs running
during the transition" — for migrations that are small enough to do
in a single hard cutover.

**Why it happens.** Coexistence sounds safer (less commitment, easier
to back out). The LLM doesn't surface its operational cost.

**Correct pattern.** Coexistence is justified when (a) volume /
complexity makes a single cutover too risky, or (b) both orgs must
permanently operate in parallel. Small-volume merges, divestitures,
and most splits do better with hard cutover. The decision criterion
is the cost of the bridge vs the risk of the single cutover, not
"safer is always better".

**Detection hint.** Any small-volume migration recommendation that
defaults to coexistence without justifying the bridge cost is
likely overengineering.

---

## Anti-Pattern 5: Bulk-migrating into target-org with automation enabled

**What the LLM generates.** ETL recipes that bulk-insert records
without disabling Process Builders, Flows, and Apex triggers.

**Why it happens.** "Insert the records and let the platform handle
the rest" is the cleaner-looking pattern. The LLM doesn't surface
that "the rest" includes welcome emails, auto-stamps, and
sub-record creation.

**Correct pattern.** Disable bulk-load-side automation for the
migration window via a Custom Metadata "migration mode" flag every
trigger framework respects. Migrate. Validate. Re-enable. Run a
controlled delta-update for any necessary follow-up logic.

**Detection hint.** Any bulk-migration plan with no "disable
automation" step in the runbook is going to send unintended
side-effects on first migration into a real target.

---

## Anti-Pattern 6: Recommending Salesforce-to-Salesforce as the bridge

**What the LLM generates.** "Use Salesforce-to-Salesforce to sync
records between the two orgs."

**Why it happens.** Salesforce-to-Salesforce shows up in older
training data as the recommended cross-org sync product. It's been
deprecated for years; Salesforce Connect, Platform Events, or
external middleware are the modern answers.

**Correct pattern.** Choose based on the crossing:
- Real-time read of records in the other org → Salesforce Connect
- Eventual-consistency sync → Platform Events + Apex subscriber
- Bulk batch sync → MuleSoft / middleware / Heroku Connect

**Detection hint.** Any reference to "Salesforce-to-Salesforce" or
"S2S" as a recommended pattern is dated.

---

## Anti-Pattern 7: Decommissioning the source org without exporting audit logs

**What the LLM generates.** "After cutover, decommission the source
org" with no preceding step to export retention-required logs.

**Why it happens.** Audit logs are infrastructure; the LLM treats
them as belonging to the platform rather than a deliverable that
needs explicit handling.

**Correct pattern.** Before any source-org decommission, export:
- Field History (or Field Audit Trail archive if Shield-enabled)
- Setup Audit Trail
- Login History
- Any custom audit objects required by compliance

Persist them in long-term storage that the compliance team can
query. Document retention schedules.

**Detection hint.** Any "and then decommission the source org" plan
without an audit-log export step is risking compliance escalations
months later when legal asks for historical records.

---

## Anti-Pattern 8: Ignoring Hyperforce region constraints

**What the LLM generates.** Migration plans that move data between
orgs in different regions without addressing data-residency
implications.

**Why it happens.** Region is a deployment detail in the LLM's
mental model; the LLM doesn't surface that crossing regions can
violate GDPR / regional data residency constraints.

**Correct pattern.** Verify region of source and target. If they
differ, document the residency posture explicitly and confirm with
compliance. The migration ETL itself may need to operate from the
appropriate region; data-in-transit between regions is not always
acceptable.

**Detection hint.** Any cross-region merge / split plan that doesn't
mention Hyperforce regions or data-residency review is missing a
compliance layer.
