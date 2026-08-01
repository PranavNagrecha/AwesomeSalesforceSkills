# Examples — Pull Request Policy Templates

## Example 1: Ownership rules that match a real Salesforce source tree

**Context:** A single-package DX repository where Apex developers were approving Flow
changes and nobody was reviewing profile changes at all.

**Problem:** The first CODEOWNERS file was generated from a generic example and used paths
like `/src/apex/` and `/flows/`. None of those exist in source format, so no rule matched
anything — the file was reviewed, merged, and had no effect. The policy looked present and
was inert.

**Solution:** Paths taken from the actual tree, with ownership at the granularity where
review responsibility genuinely differs.

```text
# .github/CODEOWNERS
# A default owner so nothing in the tree is unowned.
*                                                       @org/platform-team

# --- Code -----------------------------------------------------------------
force-app/main/default/classes/                         @org/apex-team
force-app/main/default/triggers/                        @org/apex-team
force-app/main/default/lwc/                             @org/frontend-team
force-app/main/default/aura/                            @org/frontend-team

# --- Declarative automation ----------------------------------------------
force-app/main/default/flows/                           @org/automation-team

# --- Access control: high blast radius, needs a second discipline ---------
force-app/main/default/profiles/                        @org/security-team
force-app/main/default/permissionsets/                  @org/security-team
force-app/main/default/permissionsetgroups/             @org/security-team
force-app/main/default/sharingRules/                    @org/security-team

# --- Data model ----------------------------------------------------------
force-app/main/default/objects/                         @org/data-model-team
# Fields live under objects/<Object>/fields/, so field-level rules are expressible.
force-app/main/default/objects/Account/fields/          @org/data-model-team @org/sales-team

# --- Irreversible ---------------------------------------------------------
manifest/destructiveChanges.xml                         @org/platform-team @org/security-team

# --- Project shape: changes here alter what ships ------------------------
sfdx-project.json                                       @org/platform-team
config/                                                 @org/platform-team
.github/workflows/                                      @org/platform-team
```

**Why it works:** every path exists, so every rule fires. The escalations are concentrated
where the change is irreversible or org-wide — profiles, permission sets, sharing rules,
destructive changes — rather than spread evenly across a tree where most changes are a new
class or a new component.

**Two Salesforce-specific details generic templates miss.** Fields sit under
`objects/<Object>/fields/`, so field-level ownership is possible and an object-level rule
will not catch a field change on its own. And in a monorepo the tree is
`packages/<pkg>/main/default/...` — every path above needs the package prefix, and a rule
copied from a single-package example matches nothing at all.

**Why team handles, not usernames:** an individual owner makes a departure or a holiday into
an unmergeable path, and the fix is an administrative override. Once the override is the
normal path the policy has stopped meaning anything. The team is the durable object;
membership changes without touching this file.

---

## Example 2: A required check that actually consults the target org

**Context:** Deploy failures roughly twice a week, all of them "works in dev". The PR
pipeline was green every time.

**Problem:** The required check ran ESLint, PMD and Jest and was named "validation". None of
those consult an org, so none of them could see a field reference that does not exist in
production, a picklist value missing from the target, or a profile referencing a permission
the target does not have. The check was measuring the source in isolation and the failures
were all about the destination.

**Solution:** A check-only deployment against a staging org, with the test level chosen for
the job it is doing, plus a template that captures what the deploy cannot infer.

```yaml
name: PR gate
on:
  pull_request:
    branches: [main]

jobs:
  static:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run lint && npm test

  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to staging
        run: bash scripts/jwt-login.sh staging     # see devops/pipeline-secrets-management

      - name: Validation deploy — consults the real org, saves nothing
        run: |
          sf project deploy validate \
            --target-org staging \
            --source-dir force-app \
            --test-level RunSpecifiedTests \
            --tests $(cat manifest/pr-tests.txt | tr '\n' ' ') \
            --wait 60

      - name: Report org-wide coverage without blocking on it
        run: |
          sf apex run test --target-org staging --code-coverage --result-format json \
            --wait 30 > coverage.json || true
          python3 scripts/summarise_coverage.py coverage.json >> "$GITHUB_STEP_SUMMARY"
```

```markdown
<!-- .github/pull_request_template.md — four sections, one screen -->
## What changed and why

## Deployment notes
<!-- Anything the deploy cannot do by itself: picklist values that must exist first,
     remote site settings, order dependencies against another PR, post-deploy data fixes. -->

## Test evidence
<!-- Which tests cover this, and which org the validation ran against. -->

## Rollback
<!-- What "undo" means here. If this deletes a field, removes a picklist value or narrows a
     permission, say so — reverting the commit does not undo any of those. -->
```

**Why it works:** `sf project deploy validate` performs the deployment against the target
without saving the components, so the target org's real state is consulted — which is the
only way the four failure classes above can be caught before merge.

**Why `RunSpecifiedTests` here:** test level is a cost decision. `RunLocalTests` runs every
test in the org except those from installed managed and unlocked packages, and it is the
default for production deployments containing Apex classes or triggers — the right level for
the pre-production gate and too slow for PR feedback, where a slow gate is an ignored gate.
`NoTestRun` is not available for production at all.

**Why coverage is reported rather than enforced here:** the platform's 75% requirement is an
org-wide figure across all Apex, not a per-PR delta. Blocking a PR on the org-wide number
blocks every PR equally once the org drifts under the line, including the PR that would fix
it. Enforce 75% on the pre-production validation where it is a genuine deployability gate,
and on a PR assert only what the author controls — coverage of the classes they changed.

**Getting the required-check names right:** a required check is matched by the name the
provider reports, which for a matrix job includes the matrix value. Copy the names verbatim
from a completed run rather than inventing them, and re-check after any matrix change —
adding a package renames every check it produces, and a required check that never arrives
either blocks forever or is silently skipped.
