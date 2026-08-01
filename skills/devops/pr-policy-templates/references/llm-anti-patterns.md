# LLM Anti-Patterns — Pull Request Policy Templates

Scope: the review policy that sits on top of a Salesforce source tree — ownership rules,
required checks, and the template that carries deployment context. Branching model belongs
to `devops/branching-strategy-salesforce`; pipeline construction to
`devops/github-actions-for-salesforce`. This file is about the policy, and specifically
about the parts that are Salesforce-shaped rather than generic.

## Anti-Pattern 1: Ownership rules written against a directory tree that does not exist

The failure that makes the whole policy inert without anyone noticing. Assistants generate
paths from generic examples — `/src/`, `/apex/`, `/flows/` — none of which match a real
Salesforce source tree, so no rule ever matches and every PR is approvable by anyone. The
policy file is present, reviewed, and doing nothing.

**Wrong** — nothing here matches a DX project:

```text
/src/apex/          @org/apex-team
/flows/             @org/flow-team
/profiles/          @org/security-team
```

**Right** — paths that exist in source format, at the granularity ownership actually differs:

```text
# Default owner, so nothing is unowned.
*                                                       @org/platform-team

# Code
force-app/main/default/classes/                         @org/apex-team
force-app/main/default/triggers/                        @org/apex-team
force-app/main/default/lwc/                             @org/frontend-team
force-app/main/default/aura/                            @org/frontend-team

# Declarative automation
force-app/main/default/flows/                           @org/automation-team

# Access control — irreversible or high-blast-radius, needs a second discipline
force-app/main/default/profiles/                        @org/security-team
force-app/main/default/permissionsets/                  @org/security-team
force-app/main/default/permissionsetgroups/             @org/security-team
force-app/main/default/sharingRules/                    @org/security-team

# Data model. Field-level ownership needs the object in the path.
force-app/main/default/objects/                         @org/data-model-team
force-app/main/default/objects/Account/fields/          @org/data-model-team @org/sales-team

# Project shape: a change here alters what ships
sfdx-project.json                                       @org/platform-team
config/                                                 @org/platform-team
```

Two things follow from source format specifically. Fields live under
`objects/<Object>/fields/`, so field-level ownership is expressible and object-level rules
will not catch it. And in a monorepo the tree is `packages/<pkg>/main/default/...`, so every
path above needs the package prefix — a rule copied from a single-package example silently
matches nothing.

## Anti-Pattern 2: Required checks named after jobs the pipeline does not emit

The second way to build a policy that enforces nothing. A required status check is matched
by name, and the name that matters is the one the CI provider reports — which for a matrix
job includes the matrix value, and for a reusable workflow may be prefixed. Generated
configuration invents tidy names like `ci` or `tests`, which never arrive, so the PR either
blocks forever or, if the provider treats unknown checks as absent, merges unchecked.

❌ Require `salesforce-validation` when the workflow reports
`validate (sales-core) / deploy-validate`.
✅ Take the names from a real run — open a completed PR and copy the reported check names
verbatim — and pin them in the branch protection configuration. Re-check them whenever the
matrix changes, because adding a package to a matrix changes every check name it produces.

## Anti-Pattern 3: A "validation" that never touched an org

The check most likely to be quietly hollow. Static analysis and unit tests do not catch
metadata that is invalid in the target org: a missing field reference, a picklist value not
present in production, a profile referencing a permission the target does not have. The only
thing that catches those is a real validation deployment.

❌ A required check that runs lint and Jest and is labelled "validation".
✅ A check-only deployment against an org that resembles the target, with an explicit test
level:

```yaml
- name: Validation deploy
  run: |
    sf project deploy validate \
      --target-org staging \
      --source-dir force-app \
      --test-level RunLocalTests \
      --wait 60
```

`checkOnly` validation performs the deployment without saving the components, which is the
whole point — the target org's real state is consulted. Choose the test level deliberately:
`RunLocalTests` runs every test in the org except those from installed managed and unlocked
packages and is the default for production deployments containing Apex, while
`RunSpecifiedTests` is the affordable choice for fast PR feedback. `NoTestRun` is not
available for production at all.

Source: Metadata API `deploy()` — `checkOnly` and the `testLevel` values — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm

## Anti-Pattern 4: Blocking on org-wide coverage as if it were PR coverage

Coverage is where a policy most often becomes unenforceable. The platform requirement is
that unit tests cover **at least 75% of your Apex code** for a production deployment — an
org-wide figure, computed across everything, not a per-PR delta. A gate that blocks a PR on
the org-wide number blocks every PR equally once the org drifts below the line, including the
PR that would fix it.

❌ "Block if org coverage < 75%" as a per-PR check.
✅ Distinguish the two questions. The org-wide 75% belongs on the pre-production validation,
where it is a genuine deployability gate. On a PR, assert something the author controls —
that the classes changed in this PR are covered — and report the org-wide number without
blocking on it. Pick one authoritative coverage check and delete the others; two overlapping
checks with different thresholds is how teams learn to ignore both.

Source: Apex Code Coverage — "unit tests must cover at least 75% of your Apex code, and those tests must pass" — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_code_coverage_intro.htm

## Anti-Pattern 5: Ownership assigned to people rather than groups

The rule that works for six months. An individual account as owner means their departure,
holiday or reassignment leaves every PR touching that path unmergeable, and the fix requires
someone with administrative rights — so the practical outcome is that the override becomes
the normal path and the policy stops meaning anything.

❌ `force-app/main/default/profiles/ @jsmith`
✅ A team handle with more than one member, even where one person does most of the reviewing.
The team is the durable object; membership changes without touching the policy file.

## Anti-Pattern 6: A template long enough that authors delete it

Generated templates run to a dozen headings because each individually seems reasonable. The
observable result is that authors clear the body and type one line, which removes the
deployment context the template existed to capture — and the failure is invisible, because
the file is still in the repo.

❌ Fifteen sections including "Screenshots", "Alternatives considered" and "Related tickets".
✅ Fewer sections than fit on one screen, each answering a question a reviewer or a
release manager genuinely cannot answer from the diff:

```markdown
## What changed and why

## Deployment notes
<!-- Manual steps, order dependencies, and anything the deploy cannot do by itself:
     picklist values, remote site settings, post-deploy data fixes. -->

## Test evidence
<!-- Which tests cover this, and the org the validation ran against. -->

## Rollback
<!-- What "undo" means here. For destructive metadata changes, say so explicitly. -->
```

Deployment notes and rollback are the two Salesforce-specific ones and the two that are
hardest to reconstruct later — a field deletion, a picklist value removal or a permission
change is not undone by reverting the commit.

## Anti-Pattern 7: Treating every metadata type as equally reversible

The policy applies one rule to all changes, so the reviewer of a label change carries the
same nominal responsibility as the reviewer of a field deletion. Real risk is concentrated
in a small set of types, and a policy that does not say so spends its reviewers' attention
uniformly on changes that do not need it.

❌ One reviewer requirement across the whole tree.
✅ Escalate on the types where the change is irreversible or has org-wide blast radius —
destructive changes in `destructiveChanges.xml`, profiles and permission sets, sharing
rules, and anything under `objects/*/fields/` that removes rather than adds. Those warrant a
named second discipline in the ownership rules; a new LWC does not.
