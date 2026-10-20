# LLM Anti-Patterns — DevOps Center Pipeline

Common mistakes AI coding assistants make when generating or advising on Salesforce DevOps Center pipelines.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Describing Capabilities Without Asking Which DevOps Center

**What the LLM generates:** Either "DevOps Center can't run test suites or quality gates, so add GitHub Actions" or "DevOps Center enforces quality gates" — stated flatly, with no reference to which product the org runs.

**Why it happens:** Training data mostly describes the managed package. Lifecycle Center (the Summer '26 "next-generation DevOps Center") adds standard objects for test suites, test providers, and quality gates per stage (`DevopsTestSuiteStage`, `DevopsQualityGate`, API 67.0).

**Correct pattern:**

```text
1. Check DevHubSettings: enableDevOpsCenterGA (managed package, "an older
   version of Lifecycle Center") vs enableALMDevopsCorePref (Lifecycle
   Center, API 65.0+).
2. Lifecycle Center: evaluate DevopsTestSuite / DevopsQualityGate per stage
   before adding an external CI gate.
3. Lifecycle Center: validate-only deployment is not supported, so a
   production check-only run belongs in CLI/CI.
```

**Detection hint:** Any capability claim about DevOps Center with no mention of `enableDevOpsCenterGA` / `enableALMDevopsCorePref` or of the edition.

---

## Anti-Pattern 2: Promising Native Sync Between Work Items and External Trackers

**What the LLM generates:** "Your Jira stories will appear as DevOps Center work items automatically."

**Why it happens:** LLMs associate "work items" with project management tools and assume a connector exists.

**Correct pattern:**

```text
A WorkItem record is created in DevOps Center (Subject, Description, Status,
AssignedToId, ParentWorkItemId for subtasks). Do not promise a sync with an
external tracker unless the team has a configured integration; otherwise put
the external ticket key in the work item Subject and keep the trackers in step
with an integration the team owns.
```

**Detection hint:** "Automatically imported", "synced from Jira/ADO" with no named connector or integration.

---

## Anti-Pattern 3: "DevOps Center Only Supports GitHub"

**What the LLM generates:** "DevOps Center requires GitHub; Bitbucket teams must use the CLI."

**Why it happens:** Early DevOps Center material was GitHub-only and is over-represented in training data.

**Correct pattern:**

```text
SourceCodeRepoProvider.Provider = GITHUB (default) or BITBUCKET.
The connection uses the Named Credential named in SourceCodeRepoProvider.NamedCredential.
GitLab and Azure Repos are not values of that picklist: those teams mirror to a
supported provider or use a CLI-based pipeline.
```

**Detection hint:** "GitHub-only", "only GitHub is supported", or Bitbucket listed as unsupported.

---

## Anti-Pattern 4: Skipping Conflict Handling During Promotion

**What the LLM generates:** "Promote the bundle from Dev to QA" as a one-step process, with no plan for two work items that change the same component.

**Why it happens:** Conflict-free promotions are the happy path shown in tutorials.

**Correct pattern:**

```text
A work item that conflicts reaches Status = MERGE_CONFLICT and must be resolved
before promotion. Recovery operations recorded on DevopsRequestInfo:
REBASE, REBASE_AND_COMBINE (the absorbed item becomes COMBINED), BACK_SYNC.
Prevention: one work item per shared component where possible, smaller and
more frequent promotions, and a bundling stage (IsBundled) for related items.
```

**Detection hint:** Promotion instructions with no mention of `MERGE_CONFLICT`, rebase, or combine.

---

## Anti-Pattern 5: Recommending DevOps Center for ISV Package Versioning

**What the LLM generates:** "Use DevOps Center to create and promote your managed package versions."

**Why it happens:** LLMs treat DevOps Center as a general Salesforce DevOps solution without separating org development from package development.

**Correct pattern:**

```text
DevOps Center records commits, deploys, promotions, rebases, and back syncs
(DevopsRequestInfo.OperationType) between org environments. Package versions
are created against a Dev Hub with `sf package version create`, with
dependencies declared in sfdx-project.json — a separate pipeline.
```

**Detection hint:** "DevOps Center" paired with "package version", "namespace", or "ancestor".

---

## Anti-Pattern 6: Assuming QA Promotions Ran Tests

**What the LLM generates:** "QA passed in DevOps Center, so the Apex tests are green."

**Why it happens:** The model assumes every deployment runs tests, as production deployments do.

**Correct pattern:**

```text
DevopsEnvDeployment.TestLevel defaults to Default: no tests in sandboxes,
all local tests in production. Check the TestLevel on the QA deployment record;
set RunLocalTests or RunSpecifiedTests (+ RunTests) for sandbox stages.
```

**Detection hint:** A claim that tests passed in a sandbox stage with no `TestLevel` evidence.

---

## Anti-Pattern 7: Calling the new product "next-generation DevOps Center" as its current name

**What the LLM generates:** "Set `DevHubSettings.enableALMDevopsCorePref` to turn on the next-generation DevOps Center."

**Why it happens:** That was the Summer '26 wording of the field description, and it is the phrase in most release-note coverage.

**Correct pattern:** The setting is right; the name is not current. The Winter '27 Metadata API guide describes `enableALMDevopsCorePref` (API 65.0+) as enabling "the AI-powered, Lifecycle Center for change and release management", and `enableDevOpsCenterGA` (API 56.0+) as the DevOps Center managed package, "an older version of Lifecycle Center" (`api_meta.txt` 264 L117302–L117311). Use "Lifecycle Center" when searching current docs and Setup, and mention the old name once so readers of older material can follow.

**Detection hint:** "next-generation DevOps Center" presented as the current product name, or an `enableALMDevopsCorePref` instruction that never says "Lifecycle Center".
