# Examples — Copado Essentials

## Example 1: First-Time Pipeline Setup Fails Because Environment Branches Don't Exist

**Context:** A team of four developers and two admins installs Copado Essentials for the first time. They have a Developer Integration sandbox, a UAT sandbox, and a Production org. They create a pipeline, add three stages, assign org credentials, and click "Promote" on their first user story. The promotion fails with a Git error.

**Problem:** The team assumed Copado would create the environment branches (`develop`, `staging`, `main`) the same way it creates `feature/*` branches — on demand. It does not. Environment branches must exist in the remote repository before Copado can reference them as pipeline stage targets. The Git error message does not clearly distinguish between "branch doesn't exist" and "authentication failure," so the team spends an hour rotating credentials before diagnosing the real issue.

**Solution:**

```text
Pre-pipeline Git setup steps:
1. Initialize the remote repository (GitHub/GitLab/Bitbucket)
2. Create the three environment branches:
   git checkout -b develop && git push origin develop
   git checkout -b staging && git push origin staging
   git checkout -b main && git push origin main
   (or create them through the Git provider UI)
3. Return to Copado Essentials and configure the pipeline stages,
   assigning:
     Stage 1 (Dev Integration sandbox) -> branch: develop
     Stage 2 (UAT sandbox)             -> branch: staging
     Stage 3 (Production)              -> branch: main
4. Create a test user story, click "Create Feature Branch" to
   verify feature/US-0001 is created from develop
5. Promote the test story through Stage 1 to confirm end-to-end
```

**Why it works:** Separating branch creation from pipeline configuration ensures Copado has valid branch references before it attempts any Git operations. Copado only creates `feature/*` branches; all other branches in the promotion topology are the team's responsibility to create and maintain.

---

## Example 2: Wrong Promotion Order Breaks Metadata Dependency Between Two User Stories

**Context:** A development team is working on two user stories simultaneously. User Story US-1015 creates a new custom field `Account.Annual_Revenue_Tier__c`. User Story US-1008 adds a validation rule on Account that references `Annual_Revenue_Tier__c`. Both stories are ready to promote to UAT on the same day.

**Problem:** By default, Copado promotes user stories in ascending reference number order. US-1008 (lower reference number) is promoted before US-1015. The UAT sandbox receives the validation rule referencing a field that does not yet exist in that environment. The Metadata API deploy fails with `Error: Field Annual_Revenue_Tier__c does not exist`. The failure is logged as a deployment error, and the team initially suspects a sandbox refresh issue rather than a promotion ordering problem.

**Solution:**

```text
Merge order override configuration:
1. Open User Story US-1015 (creates the field)
   -> Set Merge Order = 1
2. Open User Story US-1008 (references the field in validation rule)
   -> Set Merge Order = 2
3. Trigger bulk promotion from the pipeline view
   -> Copado promotes US-1015 first (merge order 1), then US-1008 (merge order 2)
   -> UAT receives the field before the validation rule that references it
4. Document the dependency in both user story records:
   US-1008 description: "Depends on US-1015 (field creation). Merge order 2."
   US-1015 description: "Must promote before US-1008. Merge order 1."
```

**Why it works:** The merge order field explicitly overrides Copado's default ascending-reference-number sort. By assigning lower integers to prerequisite stories, teams encode metadata dependency knowledge into the pipeline rather than relying on developers to manually sequence promotions or remember inter-story dependencies under release day pressure.

---

## Example 3: In-App Conflict Resolution for Two Stories Modifying the Same Flow

**Context:** Two developers independently modify the same Screen Flow (`Contact_Onboarding`) in their respective feature branches. Developer A (US-2041) added a new screen element; Developer B (US-2039) changed a decision element condition. Both promote to the Integration sandbox on the same sprint close day.

**Problem:** In Work Items mode, Copado detects the conflict when US-2039 (lower reference, promoted first) merges successfully, and then US-2041's promotion fails because the Flow metadata in its feature branch diverges from the current `develop` branch state. The Copado Conflicts tab shows `Contact_Onboarding.flow-meta.xml` as conflicting.

**Solution:**

```text
Conflict resolution steps (Work Items mode):
1. Open User Story US-2041 -> navigate to Copado Conflicts tab
2. Identify: Contact_Onboarding.flow-meta.xml conflicts with US-2039's merged state
3. Strategy chosen: manual merge (both changes must be preserved)
4. Developer A pulls the feature branch locally:
   git fetch origin
   git checkout feature/US-2041
   git merge origin/develop   # brings in US-2039's merged changes
5. Resolve the conflict in VS Code (Flow XML diff)
   or use Flow Builder export/import for simple element combination
6. Commit and push the resolved branch:
   git add force-app/main/default/flows/Contact_Onboarding.flow-meta.xml
   git commit -m "Resolve conflict: combine screen (US-2041) + decision (US-2039)"
   git push origin feature/US-2041
7. Return to Copado UI -> re-trigger promotion for US-2041
   Copado re-evaluates conflict state; promotion succeeds
```

**Why it works:** Copado re-checks conflict state on each new push to the feature branch. By resolving the conflict locally and pushing, the team provides Copado a clean merge candidate without losing either developer's changes. Flow XML conflicts require file-level resolution because Flow metadata is complex XML that requires developer review to combine correctly.

---

## Anti-Pattern: Manually Merging Feature Branches to Environment Branches Outside Copado

**What practitioners do:** A developer grows impatient with Copado's promotion queue and directly merges their feature branch into `develop` using `git merge` from the command line or through a GitHub PR that bypasses Copado.

**What goes wrong:** Copado tracks pipeline state through its own managed objects (Deployment records, User Story status fields). When a feature branch is merged into an environment branch outside Copado, the corresponding User Story record in Salesforce retains its "In Progress" or "Promotion Pending" status. Copado does not detect the external merge. When the team later attempts to promote the same user story through Copado, Copado re-attempts to merge the branch (which is now a no-op at the Git level) and may deploy an empty changeset or produce a conflict error if the environment branch has diverged in the meantime.

**Correct approach:** All merges to environment branches must go through Copado's promotion flow. If a user story must bypass Copado for an emergency, mark the user story as "Cancelled" in Copado after the manual merge so pipeline state reflects reality. Never leave a manually-merged story in an active pipeline state inside Copado.
