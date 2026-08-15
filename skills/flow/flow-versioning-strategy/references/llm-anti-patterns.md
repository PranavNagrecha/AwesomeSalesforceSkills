# LLM Anti-Patterns — Flow Versioning

Mistakes AI assistants reliably make about flow versions and their lifecycle.

---

## Anti-Pattern 1: Breaking Change as a Version Bump

**What the LLM generates:** rename a required input variable, create a new
version, activate. Presented as the normal refactoring workflow.

**Why it happens:** "version" carries the semantics of source control everywhere
else in the model's experience, where a rename is a rename and the compiler
catches the callers.

**Correct pattern:** the flow's contract surface — inputs, outputs, and the
elements a paused interview can occupy — binds by *name* at run time, across
Apex, LWC, subflows, quick actions, and Experience Cloud pages. There is no
compile step over it. The test: if anything outside the flow has to change at the
same moment, it is a new flow, not a new version.

**Detection hint:** a rename of a `<variables><name>` that is marked
`isInput` or `isOutput`, in a change described as non-breaking.

---

## Anti-Pattern 2: Rollback by Redeploying Old Source

**What the LLM generates:** "to roll back, check out the previous commit and
deploy the flow metadata."

**Why it happens:** redeploy-the-previous-artifact is the correct rollback for
almost everything else, and flow metadata is a file in the repository like any
other.

**Correct pattern:** deploying flow metadata creates a **new version** whose
content matches the old one — it does not restore the old version. Roll back by
activating the version that already exists in the org, which is one click on the
flow's detail page. Capture the active version number before the deploy; it is
the only input the rollback needs.

**Detection hint:** a rollback procedure containing `sf project deploy` and a
flow.

---

## Anti-Pattern 3: Delete Every Non-Active Version

**What the LLM generates:** a cleanup script that deletes all versions where
`Status != 'Active'`, or all versions older than N days.

**Why it happens:** "clean up the old versions" is an unambiguously good-sounding
instruction, and status and age are the two attributes readily available.

**Correct pattern:** the condition is "zero interviews reference this version."
Obsolete means "no longer starting new interviews," not "unused" — obsolete
versions host every paused interview that began on them, and deleting one breaks
those at resume, weeks or months later, with no traceable connection to the
cleanup. Keep at least three inactive versions as rollback depth. If the script
enumerates statuses by hand instead, note that there are five — `Active`, `Draft`,
`Obsolete`, `InvalidDraft`, `UnderReview` — so a four-value list silently drops a
population from the inventory on top of the primary defect.

**Detection hint:** `Status != 'Active'` or `LastModifiedDate < LAST_N_DAYS` as
the sole predicate of a delete; or a hand-written status list with four entries.

---

## Anti-Pattern 4: Querying `Flow` Through the Standard API

**What the LLM generates:** `sf data query --query "SELECT VersionNumber, Status
FROM Flow"` with no `--use-tooling-api`.

**Why it happens:** `Flow` reads like an ordinary sObject and appears in
documentation constantly. Nothing in the name signals the API boundary.

**Correct pattern:** `Flow` is a Tooling API object; the standard API returns
"sObject type 'Flow' is not supported." Use `--use-tooling-api`, or use the
read-only standard views `FlowDefinitionView` and `FlowVersionView` (API 46.0 and
later) when the script should not require Tooling API access. Live interviews are
`FlowInterview`, on the standard API.

**Detection hint:** `FROM Flow` in a query with no tooling-api flag.

---

## Anti-Pattern 5: Assuming a Subflow Reference Is Pinned

**What the LLM generates:** "activating the new subflow version is safe — the
parent flows still reference the version they were built against."

**Why it happens:** dependency pinning is the norm in every package manager the
model has seen, and it is the behaviour a careful engineer would expect.

**Correct pattern:** resolution is late. The parent runs the child's *active*
version, and the latest version if the child has none active. Activating a new
child version changes every already-active parent's behaviour on its next
interview, with no redeploy. Search the metadata for `<flowName>` references
before activating, and treat the activation as a production change to all of
them. Deactivating the child does not stop callers — it drops them onto the
latest version, possibly an unfinished draft.

**Detection hint:** any claim that a parent flow is unaffected by a subflow
version change.

---

## Anti-Pattern 6: Adding `FlowDefinition` to a Deployment Package "for Safety"

**What the LLM generates:** a package that sets `status` on each flow *and*
includes a `FlowDefinition` with `activeVersionNumber`, on the theory that
belt-and-braces is safer.

**Why it happens:** two mechanisms that both express activation look
complementary rather than conflicting.

**Correct pattern:** they conflict, with documented precedence — "the active
version numbers in the flow definitions override the status fields in the flows."
A stale `FlowDefinition` silently wins over every carefully set `status` in the
package. Salesforce's recommendation, quoted rather than paraphrased: "In API
version 44.0, we recommend upgrading your flows to flow metadata file names
without version numbers and discontinue using the FlowDefinition object to
activate or deactivate a flow." That is a recommendation *made in* 44.0 about file
naming and about retiring `FlowDefinition` — do not restate it as "upgrade your
flows to API version 44.0", which is a different and unsupported claim. Keep
`FlowDefinition` out of routine packages; use it deliberately and standalone for a
rollback if at all.

**Detection hint:** a `FlowDefinition` component in a package that also contains
`Flow` components with `<status>`.

---

## Anti-Pattern 7: Cleanup Age Measured From Version Creation

**What the LLM generates:** "retain versions for 30 days after they are
superseded," with the 30 days measured from the version's creation or
deactivation date.

**Why it happens:** it is the shape of every log-retention and artifact-retention
policy, and it produces a rule that can be scripted.

**Correct pattern:** the clock that matters starts when the *last interview*
referencing that version finishes, not when the version was created or
superseded. A screen flow with an overnight pause and a scheduled flow with a
90-day wait need wildly different windows, so one org-wide number is wrong for
both. Measure the observed interview lifetime per flow and set the window from
its tail.

**Detection hint:** a retention rule keyed on `CreatedDate` or
`LastModifiedDate` of a flow version rather than on interview references.

---

## Anti-Pattern 8: Ignoring the API Version Bump on a Cosmetic Edit

**What the LLM generates:** "just fix the label and save" for a legacy flow, with
no mention of the API version.

**Why it happens:** the edit genuinely is cosmetic, and the API version field is
not where the model's attention goes.

**Correct pattern:** Flow behaviour is versioned and Flow Builder can move a
flow's API version forward on save. Crossing API 52.0 changes the run-mode
default; crossing 57.0 removes the executed-elements cap; runtime version 63.0
enables custom scheduled-flow batch sizes. A one-character label fix that crosses
one of those boundaries is not a cosmetic change. Note the version before and
after, and test the bump.

**Detection hint:** an edit to a flow whose `<apiVersion>` is well below current,
described as low-risk with no version discussion.

---

## Anti-Pattern 9: Promising That a Paused Interview Will Pick Up the New Logic

**What the LLM generates:** "activate the fix and the paused interviews will use
it when they resume."

**Why it happens:** it is how a deployed bug fix behaves in essentially every
other system: restart, and the running work picks up the new code.

**Correct pattern:** a paused interview resumes on the version it started on,
full stop. A fix does not reach interviews already in flight. If those interviews
must get the corrected behaviour, the options are to let them complete on the old
logic and correct the resulting data, or to delete the interviews and have the
work restarted — both of which are business decisions, not deployment steps.

**Detection hint:** a remediation plan for in-flight interviews whose only step
is activating a new version.
