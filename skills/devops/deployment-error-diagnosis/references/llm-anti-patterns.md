# LLM Anti-Patterns — Deployment Error Diagnosis

Mistakes AI assistants make when triaging Salesforce deploy
errors.

---

## Anti-Pattern 1: "Just use --ignore-errors"

**What the LLM generates.** "If the deploy fails on test coverage,
add `--ignore-errors` to your sf project deploy command."

**Why it happens.** Make-it-work-now bias.

**Correct pattern.** Errors should be triaged. `--ignore-errors`
masks real problems and produces half-deployed targets.

**Detection hint.** Any deploy recipe with `--ignore-errors`
is suppressing signal that should be debugged.

---

## Anti-Pattern 2: Recommending field type change without migration

**What the LLM generates.** "Change the field type from Text to
Number in your field metadata XML and deploy."

**Why it happens.** Looks like a simple metadata change.

**Correct pattern.** Type changes on populated fields require
migration: new field of new type → migrate data → retire old. The
direct change rejects with `Cannot change type`.

**Detection hint.** Any "change field type" recommendation that
doesn't address existing data is going to hit the type-change
restriction.

---

## Anti-Pattern 3: Deploying inactive flow without status change

**What the LLM generates.** Suggesting to deploy a flow file with
`<status>Draft</status>` or `<status>Inactive</status>`.

**Why it happens.** "Deploy what you have"; status awareness isn't
salient.

**Correct pattern.** Set `<status>Active</status>` for in-use
flows. Use `<status>Obsolete</status>` to retire. Don't deploy
`Draft`.

**Detection hint.** Any flow deployment without confirming the
status field is going to fail or deploy inactive.

---

## Anti-Pattern 4: Suggesting full-profile export instead of scoped permset

**What the LLM generates.** "Export the profile with
`sf project retrieve start --metadata Profile:Sales_User` and
deploy it."

**Why it happens.** Profile-based mental model from older
Salesforce era.

**Correct pattern.** Permission Sets + Permission Set Groups,
scoped exports. Or scope the profile retrieve via package.xml
to limit cross-reference failures.

**Detection hint.** Any "deploy profile" recommendation without
addressing scoped FLS is going to produce cross-reference
failures.

---

## Anti-Pattern 5: Diagnosing test coverage failure without querying ApexCodeCoverageAggregate

**What the LLM generates.** "Add tests until your coverage hits
75%."

**Why it happens.** "Add tests" is the right shape; *which*
tests is the LLM's gap.

**Correct pattern.** Query `ApexCodeCoverageAggregate` to
identify the highest-uncovered classes; target those for new
tests; that's the most efficient path to the threshold.

**Detection hint.** Any coverage-failure recipe that says "write
more tests" without saying "for which classes" is incomplete.

---

## Anti-Pattern 6: Removing `entity is in use` references blindly

**What the LLM generates.** "Find every place the field is used
and remove the references."

**Why it happens.** Right shape, missing nuance.

**Correct pattern.** Each reference needs a deliberate
disposition: deactivate, replace with another field, accept the
field stays. Blindly removing breaks features.

**Detection hint.** Any "find and remove references" advice that
doesn't ask "what should each reference become?" is going to
break things.

---

## Anti-Pattern 7: Mixing wildcards and explicit `<members>` in package.xml

**What the LLM generates.** package.xml with both
`<members>*</members>` and `<members>Specific__c</members>` for
`CustomField`.

**Why it happens.** "Be both flexible AND specific" feels safe.

**Correct pattern.** Pick one. Wildcard for "all of this type"
or explicit list. Mixing is implementation-defined and can produce
surprising deploys.

**Detection hint.** Any package.xml with mixed wildcard + explicit
for the same type is deploy-time-dependent.

---

## Anti-Pattern 8: Prescribing a Whole-Org Recompile to Find Invalid Classes

**What the LLM generates.** "Run Compile All Classes in Setup (or deploy
everything) to find which classes are invalid; the platform can't hand
back errors for a subset."

**Why it happens.** Through API 67.0 there was no resource that returned
compile errors for only the broken classes (`ApexClass.IsValid` flags
classes whose dependencies changed, without the errors), and older forum
answers say so.

**Correct pattern.** At API 68.0 / Winter '27+, read the compilation
results for only the classes and triggers with validation errors, from
Setup or the Tooling API `apexCompileResults` resource
(salesforce_apex_developer_guide.txt L45121-45123). Fix or co-deploy
exactly those, and keep the full recompile for the case where you need it.

**Detection hint.** A large-org recompile recommendation that never
mentions `apexCompileResults` is on the 67.0 model.

