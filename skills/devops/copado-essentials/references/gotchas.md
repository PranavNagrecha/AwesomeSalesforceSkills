# Gotchas — Copado Essentials

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Empty User Story Task List Produces a Silent No-Op Deployment

**What happens:** A user story is promoted successfully — Copado shows a green deployment status, the Deployment record shows "Completed" — but no changes appear in the target org. The developer assumes the sandbox is stale or that a previous deployment already covered the changes.

**When it occurs:** When a User Story has no User Story Task child records, or when the task records reference component names that do not match the actual files committed to the feature branch (e.g., due to manual renaming of the component after the task was created). Copado deploys based on the task-tracked component list, not by comparing the full feature branch diff to the environment.

**How to avoid:** Before promoting any user story, verify that the User Story Tasks tab shows at least one task with the correct component API name and type. After deploying to a sandbox, confirm the target org reflects the expected changes by spot-checking at least one component in Setup. Establish a team norm that developers add task records when committing metadata, not after promotion.

---

## Gotcha 2: The Reference Field Character Set Determines Branch Name Validity

**What happens:** A developer clicks "Create Feature Branch" and nothing happens — no branch appears in the remote repository, and Copado shows no error in the UI. Or Copado creates a branch with a mangled name that does not match the `feature/{user-story-number}` pattern.

**When it occurs:** When the user story reference field contains spaces, parentheses, slashes, or other characters that are invalid in Git branch names. Copado takes the reference field value verbatim to construct the branch name. A reference like `US (2024-Q1) #42` produces an invalid Git branch name and the creation fails silently or creates an unintended branch name.

**How to avoid:** Standardize the user story reference field format to alphanumeric characters with hyphens only (e.g., `US-2024-001`). If using an auto-number format field, confirm the autonumber pattern does not include spaces or special characters. Git branch names cannot contain spaces, `~`, `^`, `:`, `?`, `*`, `[`, or `\`.

---

## Gotcha 3: Pipeline Mode Change Leaves In-Flight User Stories in an Inconsistent State

**What happens:** After switching the pipeline from Work Items mode to Deployments with Pull Requests mode (or vice versa), user stories that were already in promotion show neither the in-app approval UI (Work Items) nor a linked PR (Pull Requests). They appear stuck in "Promotion Pending" indefinitely.

**When it occurs:** When an administrator changes the pipeline deployment mode while user stories are in an active promotion state. Copado does not migrate in-flight promotion records to the new mode's workflow. The existing promotion records remain tied to the previous mode's process, but the pipeline no longer routes them correctly.

**How to avoid:** Before changing the deployment mode on any pipeline, complete or cancel all in-flight user story promotions first. Audit the pipeline stage view for any story in a "Promoting" or "Pending Approval" state. After the mode change, validate with a new test user story before reopening promotions to the team.

---

## Gotcha 4: Copado Essentials Consumes Salesforce Org Custom Object Limits

**What happens:** After installing Copado Essentials, the org approaches its custom object limit sooner than expected. Other managed packages or admin-created custom objects start failing to deploy with "Maximum number of custom objects reached" errors.

**When it occurs:** Copado Essentials installs a set of custom objects for its pipeline, user story, deployment, and credential records. In orgs with many installed packages and high admin-created object counts, the additional Copado objects can push the org toward the custom object ceiling. This is more likely in smaller editions or in heavily customized Enterprise orgs.

**How to avoid:** Before installing Copado Essentials, audit the org's current custom object count via Setup > Custom Objects and compare to the edition limit. After installation, re-check the count. If the org is within 10-15% of the limit, evaluate whether to consolidate or archive unused custom objects before adding Copado.

---

## Gotcha 5: Default Ascending Merge Order Silently Violates Metadata Dependencies

**What happens:** Multiple user stories are promoted together, and the resulting deployment to the target org fails partway through with a cryptic Metadata API error — often "field does not exist" or "referenced component not found." The team investigates the failed components individually and cannot find anything wrong with them in isolation.

**When it occurs:** When two user stories have a metadata dependency (Story A creates a component; Story B references it) and Story B has a lower user story reference number than Story A. Copado's default ascending-reference-number promotion order deploys Story B before Story A, causing the reference to resolve against a component that does not yet exist in the target environment.

**How to avoid:** During sprint planning or user story creation, identify cross-story metadata dependencies and immediately set merge order integers on dependent stories. Treat merge order configuration as part of the "Definition of Ready" for user stories that create foundational metadata (custom fields, custom objects, permission sets, custom metadata types). Do not rely on developers remembering dependency order at promotion time under sprint-close pressure.
