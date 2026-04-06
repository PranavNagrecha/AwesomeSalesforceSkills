# Gotchas — CumulusCI Automation

Non-obvious CumulusCI and Salesforce platform behaviors that cause real production problems.

## Gotcha 1: Extending a Standard Flow Replaces Steps With Matching Numbers

**What happens:** When you declare a flow in `cumulusci.yml` with the same name as a standard flow and add a step with a number that already exists in the standard flow, your step **replaces** the standard step entirely. It does not run alongside it. If you accidentally number a new step `2` and the standard flow's step `2` is `deploy_unmanaged_ee`, the deployment step is silently dropped.

**When it occurs:** Any time you extend a standard flow (`dev_org`, `qa_org`, `ci_feature`, etc.) and use a step number that happens to match an existing step in the standard flow definition. This is easy to trigger by numbering new steps sequentially from 1 without first running `cci flow info` to see the existing numbering.

**How to avoid:** Always run `cci flow info <flow-name>` before editing a flow. Use fractional step numbers (3.1, 3.2, 10.5) or large gaps (50, 60) that you are confident do not collide. Treat the standard flow's step numbers as reserved.

---

## Gotcha 2: `when:` Conditions That Reference Missing Attributes Silently Skip the Step

**What happens:** A task step with a `when:` expression that raises an `AttributeError` or `KeyError` during evaluation is skipped — it does not raise an error or print a warning in normal log output. The task simply does not run.

**When it occurs:** Common when `when:` expressions reference `org_config` attributes that only exist after certain features are enabled (e.g., `org_config.is_sandbox`, `org_config.installed_packages`), or when the expression references a `project_config` key that the current project does not define. In CI, the silent skip is often only discovered when the org is inspected post-run and the expected configuration is absent.

**How to avoid:** Test `when:` conditions locally with `cci flow run --debug` to see the evaluated condition values. Prefer simple boolean expressions over complex attribute chains. If checking for an installed package, verify the attribute name against `cci org info <org-alias>` output.

---

## Gotcha 3: Standard Flow Behavior Is Controlled by `project.package.type`

**What happens:** The standard flows `dev_org`, `qa_org`, `ci_feature`, and `release_*` include conditional branches that behave differently based on the `project.package.type` value in `cumulusci.yml` (`managed`, `unlocked`, or absent/empty for unpackaged). A project misconfigured as `managed` when it is actually unpackaged will trigger package install steps against a scratch org that has no managed package installed, causing failures that look like deployment errors.

**When it occurs:** Most often when a project was bootstrapped from a template for a managed package but the team later decided to use unlocked packages or unpackaged development. The `project.package.type` is not always updated when the development model changes.

**How to avoid:** Run `cci flow info dev_org` and verify the step list matches your expected development model. For unpackaged projects, confirm `project.package.type` is absent or set to an empty string. For unlocked packages, set it to `unlocked`.

---

## Gotcha 4: CumulusCI Sources Download on Every Cold Run and Can Hit GitHub Rate Limits

**What happens:** When `sources:` entries use `release: latest` or `branch: main`, CumulusCI queries the GitHub API and downloads a source archive on every flow run where the local cache is cold (new CI runner, cache miss, or first run). Each CI job can make 2-5 GitHub API calls. Parallel CI runs (10+ jobs) can exhaust the unauthenticated GitHub API rate limit (60 requests/hour per IP), causing `401 rate limit exceeded` failures that look like source configuration errors.

**When it occurs:** Parallel CI pipelines on GitHub Actions with self-hosted runners sharing an IP, or large teams on hosted runners where multiple workflows start simultaneously.

**How to avoid:** Pin `sources:` to a specific `tag:` rather than `release: latest`. Cache the CumulusCI home directory (`~/.cumulusci`) between runs using GitHub Actions' `actions/cache`. Set the `GITHUB_TOKEN` environment variable in CI so CumulusCI uses authenticated GitHub API calls (5000 requests/hour).

---

## Gotcha 5: The `robot` Task Requires the Browser Library to Be Installed Separately

**What happens:** Adding the `robot` task to a flow and running it without the Robot Framework browser library installed causes an `ImportError` or `Library not found` error that is reported as a task failure, not a missing dependency. The CumulusCI `pip install cumulusci` command does not install Robot Framework browser libraries — they must be installed explicitly.

**When it occurs:** Any new CI environment or fresh developer machine that installs CumulusCI but does not follow the Robot Framework setup steps. The error is especially confusing because `cci task info robot` succeeds and shows the task as valid; the failure only occurs at runtime.

**How to avoid:** In CI pipelines, add an explicit step after `pip install cumulusci` to install `robotframework-browser` (or `robotframework-seleniumlibrary` depending on the library in use) and run `rfbrowser init` if using the Browser library. Document the required browser library version in the project's `requirements.txt` or CI setup notes.

---

## Gotcha 6: Task Options Set in a Flow Step Do Not Persist Across Flows

**What happens:** When a task is invoked with an option override inside a flow step (e.g., `options: unmanaged: False`), that override applies only for that specific step invocation. If the same task is referenced in a different flow or re-invoked later in the same flow without the override, it uses the default from the `tasks:` block. Developers sometimes expect that setting an option in one flow will carry over to nested sub-flows.

**When it occurs:** Projects that use the same task in multiple flows with different option requirements, or that call sub-flows which internally reference the same task.

**How to avoid:** If you consistently need a task with different options in different contexts, define two named task variants in the `tasks:` block (e.g., `deploy_managed` and `deploy_unmanaged`) rather than relying on per-step option overrides.
