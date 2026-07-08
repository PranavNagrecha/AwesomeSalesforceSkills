# LLM Anti-Patterns — DevOps Center Pipeline

Common mistakes AI coding assistants make when generating or advising on Salesforce DevOps Center pipelines.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Stating DevOps Center's CI/CD Ceiling Without Naming Which DevOps Center

**What the LLM generates:** A flat capability claim in either direction. Most often the stale denial — "DevOps Center can't enforce quality gates or run tests automatically; pair it with GitHub Actions if you need a test gate" — which was true of the managed package and is now false for next-generation. Occasionally the reverse: "Use DevOps Center to run your PMD scan and auto-rollback on failure," which is true of neither product.

**Why it happens:** For three years DevOps Center *was* the managed package, and "no test gating" was its defining limitation versus Copado, Gearset, and Jenkins. Essentially the whole corpus repeats it. Next-generation DevOps Center ships automated test execution and configurable quality gates, so the limitation became a per-product fact — and an LLM reproducing the modal answer denies a capability the user's org actually has.

**Correct pattern:**

```text
Establish the product, THEN the capability list.

Both products provide:
- Source-tracked development with automatic change detection
- Work item management (link changes to user stories)
- Promotion between pipeline stages (dev -> QA -> UAT -> prod)
- Conflict detection during promotion; resolution in the provider
- Source control integration

Managed package does NOT provide:
- Configurable quality gates or test pass thresholds
  (tests run during the Metadata API deploy; there is no gate to configure)
- Automated test execution outside the deploy
- Rollback automation

Next-generation DOES provide (do not deny these):
- DevOps Center Testing, in three phases:
    * Left-Shift Testing      - on review creation in DX Inspector
    * Testing Before Promotion - before a work item advances a stage
    * On-Demand Testing        - manual re-verification before retrying
- Quality gate rules: checkpoints that let only work items meeting
  your criteria move to the next stage. Three criteria, any one of
  which fails the gate and blocks promotion:
    * severity level threshold  (a test at/above severity fails)
    * test pass percentage      (overall pass rate below the threshold)
    * essential test failures   (a test marked essential fails)
- Data Commit and Deployment via DX Inspector (metadata AND data)

Neither product documents:
- Automated rollback (revert via a new forward promotion)
- Arbitrary custom CI scripts

Do not assert that a specific scanner (PMD, Salesforce Code Analyzer)
is or is not a supported test provider. Test providers are configured
on the Tests tab of the pipeline view; check what the org offers.

AI-based recommendations (Salesforce DX MCP Server + DevOps Center MCP
tools) cover work item management, conflict resolution, and deployment
failure resolution. A recommendation is advice a human reads and
verifies -- it is not itself a gate, and it does not merge for you.
Quality gates are the gate. These are two separate features.
```

**Detection hint:** Flag any absolute sentence of the form "DevOps Center does/doesn't support quality gates, test thresholds, or automated testing" that does not first name the product. Specifically flag the stale denial — "no test gating," "no quality gates," "pair it with GitHub Actions for a test gate" — applied to next-generation. Flag conflation of MCP recommendations with quality gates: they are different features and the recommendation is not a gate. Flag claims of automated rollback in either product.

---

## Anti-Pattern 2: Confusing DevOps Center Work Items with Jira or Azure DevOps Tickets

**What the LLM generates:** "Create a work item in DevOps Center and link it to your Jira ticket" or "Import your user stories from Azure DevOps into DevOps Center work items" — implying native integration with external project management tools.

**Why it happens:** LLMs associate "work items" with project management tools. DevOps Center work items are internal to Salesforce and do not natively sync with Jira, Azure DevOps, or other tools.

**Correct pattern:**

```text
DevOps Center work items:
- Created within DevOps Center (not imported from external tools)
- Represent a unit of change (one or more metadata components)
- Linked to a Git branch automatically
- Promoted through pipeline stages
- No native sync with Jira, Azure DevOps, ServiceNow, or Rally

To connect with external tools:
- Manually reference the Jira ticket ID in the work item name/description
- Use Salesforce APIs or middleware to sync status between systems
- Consider Copado or Gearset if native Jira/ADO integration is required
```

**Detection hint:** Flag references to Jira or Azure DevOps "integration" with DevOps Center without clarifying that it is not native.

---

## Anti-Pattern 3: Stating Git Provider Support Without Naming Which DevOps Center

**What the LLM generates:** A flat provider claim in either direction — "DevOps Center only supports GitHub, so Bitbucket is out" (stale for next-generation), or "Set up DevOps Center with your GitLab repository" (wrong for both products).

**Why it happens:** LLMs generalize Git integration across all platforms, and the overwhelming majority of DevOps Center training data predates April 2026, when provider support stopped being a single fact and became a per-product fact.

**Correct pattern:**

```text
Establish the product, THEN the provider list:

Managed package (installed before April 2026):
- ONLY GitHub (GitHub.com or GitHub Enterprise Server)
- Bitbucket, GitLab, Azure Repos are NOT supported
- Requires a GitHub OAuth connection from Salesforce to GitHub
- Repository must contain a valid sfdx-project.json at the root

Next-generation DevOps Center (April 2026 onward):
- A source control provider account on GitHub OR Bitbucket
- GitLab and Azure Repos: not named as supported providers in
  Salesforce documentation — never plan a pipeline against them

If your team uses GitLab or Azure Repos:
- DevOps Center is not an option (use SFDX CLI + your CI platform instead)

If your team uses Bitbucket:
- Next-generation DevOps Center is an option; the managed package is not
```

**Detection hint:** Flag any absolute sentence of the form "DevOps Center supports/doesn't support <provider>" that does not first name the product. Flag GitLab or Azure Repos being described as available, or as a roadmap item the team can wait for — the documentation says neither.

---

## Anti-Pattern 4: Skipping Conflict Resolution During Promotion

**What the LLM generates:** "Promote the bundle from Dev to QA" as a one-step process without addressing what happens when multiple work items modify the same metadata component and create a merge conflict during promotion.

**Why it happens:** Conflict-free promotions are the happy path shown in tutorials. LLMs skip the conflict resolution workflow because it is a branching-and-merge concern that requires understanding Git merge semantics.

**Correct pattern:**

```text
DevOps Center conflict resolution:

When conflicts occur during promotion:
1. DevOps Center detects conflicting changes and blocks promotion
2. Developer resolves the conflict OUTSIDE DevOps Center — there is
   no in-app merge editor. Open the pull request in the connected
   provider and resolve it there, or pull the branch in a Git client,
   resolve, and push.
3. On next-generation DevOps Center, the DevOps Center MCP tools can
   propose a resolution first. Read it, verify it against the metadata,
   then still land the merge in the provider.
4. After the PR is merged, re-attempt the promotion

Conflict prevention strategies:
- Assign metadata components to work items (avoid two items editing
  the same object or Flow)
- Use smaller, more frequent promotions (reduces conflict surface area)
- Communicate across team members working on the same objects
- Review component assignments in the pipeline view before promoting
```

**Detection hint:** Flag promotion instructions that do not mention conflict detection or resolution. Look for "promote" without a "what if conflicts" section.

---

## Anti-Pattern 5: Recommending DevOps Center for ISV Package Development

**What the LLM generates:** "Use DevOps Center to manage your managed package development and release lifecycle" when DevOps Center is designed for org development, not package development (2GP or unlocked packages).

**Why it happens:** LLMs treat DevOps Center as a general Salesforce DevOps solution without distinguishing between org development model and package development model.

**Correct pattern:**

```text
DevOps Center is for ORG development:
- Source tracking against target orgs (sandboxes, scratch orgs)
- Metadata deployment between org stages
- Change tracking at the component level

DevOps Center is NOT for package development:
- No package version creation (sf package version create)
- No package installation management
- No namespace handling for managed packages
- No ancestor version or dependency management

For package development (ISV), use:
- sf CLI (sf package version create, sf package install)
- GitHub Actions or Jenkins for CI/CD
- sfdx-project.json for package directory and dependency configuration
```

**Detection hint:** Flag DevOps Center recommendations in ISV, managed package, or unlocked package contexts. Look for "DevOps Center" paired with "package version" or "namespace."

---

## Anti-Pattern 6: Opening Every Setup Answer with "Install DevOps Center from AppExchange"

**What the LLM generates:** A confident step-one install instruction — "Go to AppExchange, install the DevOps Center managed package, then enable it in Setup" — for an org being set up today. Often followed by a Setup-wizard GitHub OAuth walkthrough that no longer describes the current onboarding path.

**Why it happens:** DevOps Center shipped as a managed package in December 2022 and stayed one for over three years. Essentially the entire corpus of DevOps Center writing — official articles, Trailhead modules, conference talks, blog posts — opens with that install step. An LLM reproducing the modal answer reproduces a step that new orgs cannot perform, because new downloads and installations of the managed package were closed in April 2026.

**Correct pattern:**

```text
Branch on what the org already has:

Setup > Installed Packages shows DevOps Center:
- The org is on the managed package. It keeps working; reach it
  from the App Launcher. Nothing was taken away.
- Managed-package setup steps apply (GitHub OAuth via Setup wizard).

Setup > Installed Packages does NOT show DevOps Center:
- Do NOT send the user to AppExchange. New downloads and
  installations are no longer supported.
- Enable next-generation DevOps Center in the DevOps Center Hub org.
  No package, no install — turn it on and start using it.
- Then: add team members as users in the Hub org, assign DevOps Center
  permission sets, complete source control setup, configure
  .forceignore, create the project, build the pipeline.

Never present the install as a prerequisite the user simply hasn't
done yet. A missing package is a signal, not a defect.
```

**Detection hint:** Flag any DevOps Center setup sequence whose first step is an AppExchange install, a package version number, or "enable the managed package." Flag guidance that treats a missing `sf_devops` namespace as something to fix by installing. Check that the answer establishes which product the org runs before prescribing any step.
