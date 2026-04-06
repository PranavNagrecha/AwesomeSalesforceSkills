# LLM Anti-Patterns — DevOps Center Pipeline

Common mistakes AI coding assistants make when generating or advising on Salesforce DevOps Center pipelines.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating DevOps Center as a Full CI/CD Platform

**What the LLM generates:** "Use DevOps Center to run Apex tests, enforce code quality gates, and automate deployment on merge" as if DevOps Center provides the same capabilities as GitHub Actions, Jenkins, or Copado.

**Why it happens:** DevOps Center is Salesforce's built-in deployment tool, and LLMs position it as equivalent to external CI/CD platforms. In reality, DevOps Center manages source tracking, work items, and promotions but does not natively support custom test gates, code quality scanning, or complex branching strategies.

**Correct pattern:**

```text
DevOps Center capabilities:
- Source-tracked development with automatic change detection
- Work item management (link changes to user stories)
- Promotion between pipeline stages (dev -> QA -> UAT -> prod)
- Conflict detection and resolution during promotion
- GitHub repository integration for source control

DevOps Center does NOT provide:
- Custom CI/CD scripts or quality gates
- Apex test threshold enforcement (tests run during deploy, but no custom gate)
- Code scanning (PMD, Salesforce Code Analyzer) integration
- Custom approval workflows beyond stage promotion
- Rollback automation

For CI/CD quality gates, pair DevOps Center with GitHub Actions
or another CI tool that runs on the same Git repository.
```

**Detection hint:** Flag recommendations that claim DevOps Center provides code scanning, custom quality gates, or automated rollback. Check for missing mention of its limitations versus full CI/CD platforms.

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

## Anti-Pattern 3: Not Understanding the GitHub Repository Requirement

**What the LLM generates:** "Set up DevOps Center with your Bitbucket or GitLab repository" when DevOps Center currently only supports GitHub as the Git provider.

**Why it happens:** LLMs generalize Git integration across all platforms. DevOps Center's exclusive GitHub requirement is a significant constraint not always present in training data.

**Correct pattern:**

```text
DevOps Center Git requirements:
- ONLY GitHub is supported (GitHub.com or GitHub Enterprise Server)
- Bitbucket, GitLab, Azure Repos are NOT supported
- Requires a GitHub OAuth connection from Salesforce to GitHub
- Repository must contain a valid sfdx-project.json at the root

If your team uses Bitbucket or GitLab:
- DevOps Center is not an option (use SFDX CLI + your CI platform instead)
- Or mirror from GitHub to your primary Git host
```

**Detection hint:** Flag DevOps Center setup instructions that mention Bitbucket, GitLab, or Azure Repos. Check for missing GitHub-only requirement.

---

## Anti-Pattern 4: Skipping Conflict Resolution During Promotion

**What the LLM generates:** "Promote the bundle from Dev to QA" as a one-step process without addressing what happens when multiple work items modify the same metadata component and create a merge conflict during promotion.

**Why it happens:** Conflict-free promotions are the happy path shown in tutorials. LLMs skip the conflict resolution workflow because it is a branching-and-merge concern that requires understanding Git merge semantics.

**Correct pattern:**

```text
DevOps Center conflict resolution:

When conflicts occur during promotion:
1. DevOps Center detects conflicting changes and blocks promotion
2. Developer must resolve conflicts:
   - In DevOps Center UI (simple conflicts)
   - In a Git client (complex conflicts) — pull the branch, resolve, push
3. After resolution, re-attempt the promotion

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
