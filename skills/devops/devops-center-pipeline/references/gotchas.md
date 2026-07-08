# Gotchas — DevOps Center Pipeline

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deployment Errors Appear in Setup, Not in DevOps Center

**What happens:** A promotion fails. The DevOps Center UI shows a generic "Promotion failed" status with a "View Details" link. Many practitioners click around in DevOps Center looking for the error message and cannot find it.

**When it occurs:** Any time a Metadata API deployment error occurs during promotion — missing component dependencies, test class failures, validation rule errors in a profile, etc.

**How to avoid:** Always navigate to Setup > Environments > Deploy > Deployment Status to see the actual deployment error log. DevOps Center delegates the deployment to the Metadata API and surfaces only a high-level pass/fail status. The full component-level error log with line numbers and component names lives in the Deployment Status page, not in DevOps Center. Bookmark this page when running promotions.

---

## Gotcha 2: Stage Branch Protection Must Be Configured Manually in GitHub

**What happens:** A developer accidentally deletes the `stage/qa` branch in GitHub, or force-pushes to it to "clean up" old commits. DevOps Center loses track of the QA stage state and subsequent promotions fail with cryptic errors about missing refs or diverged branches.

**When it occurs:** Whenever developers have write access to the repository and are not aware that DevOps Center-managed branches are protected infrastructure — not ordinary feature branches.

**How to avoid:** Immediately after creating a pipeline, configure GitHub branch protection rules for all stage branches (e.g., `stage/*`, `main`). Set the following protections:
- Require pull request reviews before merging (DevOps Center creates PRs; direct pushes should be blocked)
- Do not allow force pushes
- Do not allow deletions

DevOps Center does not configure these protections automatically. This is a manual post-setup step.

---

## Gotcha 3: Source Tracking Drift from Profile and Permission Set Changes Made Outside Work Items

**What happens:** An admin activates a permission set assignment or makes a profile change in a DevOps Center-managed sandbox without an active Work Item. Source tracking captures the change and assigns it to a phantom or untracked state. When the admin later creates a Work Item and checks its tracked changes, the profile or permission set delta appears to be missing — or it appears in a different Work Item they were not working on.

**When it occurs:** Orgs managed by DevOps Center continuously track source changes via source tracking. Any metadata change in the org — even through Setup UI clicks — is tracked. If no Work Item is active when the change is made, DevOps Center may associate the change with the most recently active Work Item or leave it as untracked drift.

**How to avoid:** Always start a Work Item and ensure it is in the "In Progress" state in DevOps Center before making any changes in a managed sandbox. Treat "starting a Work Item" as the equivalent of opening a branch for work — because that is literally what it is. For planned permission set or profile changes, create a dedicated Work Item even if the change is small. Untracked drift can cause silent overwrites on the next promotion.

---

## Gotcha 4: Combining Work Items Is Irreversible

**What happens:** A practitioner combines two Work Items to resolve a metadata dependency, then realizes the dependency does not exist and the two items should be promoted separately on different schedules. DevOps Center has no "uncombine" action.

**When it occurs:** When the Combine Work Items action is used without confirming that both Work Items are truly ready to be promoted together. The combine action merges the feature branches in GitHub, and the original Work Item B is closed.

**How to avoid:** Before combining Work Items, confirm that both are completely ready for the same promotion window. Combining is a one-way operation: once combined, the changes travel together. If an item is not ready, do not combine — instead, manage the promotion order manually or resolve the dependency by including the prerequisite component in the earlier Work Item's branch directly.

---

## Gotcha 5: Which Git Hosts Are Supported Depends on Which DevOps Center You Have

**What happens:** A team tries to connect DevOps Center to GitLab, Azure DevOps Repos, or Bitbucket, and finds no option for their provider. Or the reverse: an architect reads a 2024-era article, tells the team "DevOps Center is GitHub-only," and the team walks away from a tool that would now accept their Bitbucket org.

**When it occurs:** Teams that standardized on a non-GitHub Git host before adopting DevOps Center — and anyone reasoning about provider support without first establishing which DevOps Center is in play.

**How to avoid:** Establish the product first, then the provider list.

- **Managed package:** GitHub only (github.com and GitHub Enterprise Server). Bitbucket, GitLab, and Azure Repos are not offered in the Setup wizard.
- **Next-generation DevOps Center:** a source control provider account on **GitHub or Bitbucket**. Salesforce's documentation names no other provider. GitLab and Azure Repos are not documented as supported, so do not plan a GitLab pipeline against them.

Teams on GitLab or Azure Repos today still need the SFDX CLI + CI/CD approach. Teams on Bitbucket no longer do, provided they are on next-generation. Confirm this before beginning any DevOps Center setup work, because it determines whether the tool is viable at all.

---

## Gotcha 6: New Managed-Package Installs Have Been Closed Since April 2026

**What happens:** An admin follows a setup guide that begins "Install DevOps Center from AppExchange," goes looking for the listing, and either cannot install it or assumes their org lacks some entitlement. Time gets spent on a permissions or edition theory that has nothing to do with the actual cause.

**When it occurs:** Any greenfield DevOps Center setup attempted from documentation, blog posts, or internal runbooks written before April 2026 — which is nearly all of the material a search will surface.

**How to avoid:** Know the two facts and read them together. New downloads and installations of the DevOps Center managed package are no longer supported. Orgs that previously installed it can continue using it and access it from the App Launcher. Nothing was removed from any org; the door was closed to new ones.

The correct move for a greenfield org is to enable next-generation DevOps Center in the Hub org — no package, no AppExchange, no install step. The correct move for an org already running the package is to keep running it and plan the documented switch deliberately. The failure mode is the middle path: an admin who half-believes the install should work, retries it, and eventually files a support case against a closed road.
