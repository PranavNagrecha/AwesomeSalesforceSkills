---
name: cumulusci-automation
description: "Use this skill when configuring CumulusCI (cci) for Salesforce project automation: authoring cumulusci.yml tasks and flows, customizing or composing standard flows, integrating Robot Framework acceptance tests, and running cci flows in CI pipelines with JWT-based authentication. Covers task class_path/options wiring, flow step ordering, org and source declarations, cross-project reuse via sources, and the standard flow library (dev_org, qa_org, ci_feature, install_beta). NOT for raw SFDX/sf CLI workflows without CumulusCI, scratch org pool management (use scratch-org-pools), unlocked or managed package versioning (use unlocked-package-development or second-generation-managed-packages), or Salesforce-native DevOps Center pipelines (use devops-center-pipeline)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "how do I customize a CumulusCI flow to add a pre-deployment step before deploying metadata"
  - "I want to write a cumulusci.yml task that calls a custom Python class with specific options"
  - "my cci flow run fails with a task class not found error and I don't know how to wire it up"
  - "how do I run Robot Framework acceptance tests with CumulusCI"
  - "I need to authenticate CumulusCI to a production org in GitHub Actions using JWT not a password"
  - "how do I reuse tasks or flows from another CumulusCI project using sources"
tags:
  - cumulusci
  - cumulusci-yml
  - robot-framework
  - ci-cd
  - flows
  - tasks
  - jwt-auth
  - devops
inputs:
  - "Existing cumulusci.yml file or description of the project's current CumulusCI configuration"
  - "Target org type (scratch org, sandbox, production) and authentication method available"
  - "CI platform (GitHub Actions, CircleCI, Jenkins, etc.) and secrets available"
  - "Name of the standard flow being customized or the new task being defined"
  - "Robot Framework test suite paths if acceptance testing is in scope"
outputs:
  - "cumulusci.yml task and flow declarations ready to paste into the project"
  - "cci flow run invocation commands with correct org alias and option flags"
  - "GitHub Actions workflow YAML integrating cci flow run with JWT authentication"
  - "Robot Framework task configuration in cumulusci.yml"
  - "Cross-project source declaration for reusing tasks or flows from another repo"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# CumulusCI Automation

This skill activates when a team needs to configure, extend, or debug CumulusCI — the open-source Python framework purpose-built for Salesforce development and release automation. It covers the full authoring surface of `cumulusci.yml`: task declaration (class_path and options), flow composition (ordered steps and option overrides), org definitions, cross-project source reuse, and Robot Framework integration. It also covers running flows in CI with JWT authentication.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What version of CumulusCI is installed?** Run `cci version`. Task class paths and flow structures changed significantly across major versions. This skill is grounded in the v4.x series. Class paths that existed in v3.x may have moved or been removed.
- **Is this a managed package, unlocked package, or unpackaged project?** CumulusCI's standard flows (dev_org, qa_org, install_beta) make different assumptions depending on the project type declared in the `project:` block of `cumulusci.yml`.
- **What is the practitioner trying to customize — a task, a flow, or both?** Tasks are the atomic execution unit (a Python class + options). Flows are ordered sequences of task steps. Most real-world customization involves either overriding an option on an existing task inside a flow, or inserting a custom step into an existing standard flow.

---

## Core Concepts

### 1. The cumulusci.yml Anatomy

`cumulusci.yml` is the single configuration file that governs the entire CumulusCI project. It has four top-level sections relevant to automation authoring:

- **`project:`** — Project name, package type (managed/unlocked/none), git branching config, and the default org alias.
- **`tasks:`** — Task declarations. Each entry names a task, gives it a `class_path` pointing to a Python class (built-in or custom), and sets `options` key-value pairs.
- **`flows:`** — Flow declarations. Each entry names a flow and lists numbered `steps`, where each step references a task or a sub-flow.
- **`orgs:`** — Scratch org shape configuration (which scratch org definition file to use, additional namespaces, etc.).
- **`sources:`** — Cross-project task/flow reuse by referencing another GitHub repo or local path.

CumulusCI ships with an extensive standard library of tasks and flows. Every entry in `cumulusci.yml` either declares a new task/flow from scratch or **extends** a standard one. Extending is done by declaring a task or flow with the same name and using the `options:` block or `steps:` block to override only what changes.

### 2. Task Configuration (class_path and options)

A task is defined by its Python `class_path` — the dotted module path to a class that inherits from `cumulusci.core.tasks.BaseTask` (or a subclass like `BaseSalesforceTask`). The built-in CumulusCI task library lives under `cumulusci.tasks.*`.

```yaml
tasks:
  deploy_community_settings:
    description: Deploy Community Settings metadata
    class_path: cumulusci.tasks.salesforce.Deploy
    options:
      path: unpackaged/config/community
      unmanaged: True
```

Key authoring rules:
- `class_path` must be a fully qualified Python dotted path. Relative paths or short names are not valid.
- `options` values set at the task level are the defaults. They can be overridden when the task is invoked inside a flow.
- A task defined in `cumulusci.yml` that references a built-in `class_path` effectively creates a named alias for that task with preset options.

### 3. Flow Composition and Step Ordering

A flow is a numbered list of steps. Steps are executed in ascending numeric order. The numbers do not need to be consecutive — gaps allow inserting steps later without renumbering.

```yaml
flows:
  custom_dev_org:
    description: Custom dev org setup flow
    steps:
      1:
        flow: dev_org           # reference a standard sub-flow
      2:
        task: deploy_community_settings
        options:
          unmanaged: False      # override the task's default option at the step level
      3:
        task: load_dataset
        when: "'community' in org_config.installed_packages"
```

Key rules:
- A step references either a `task:` or a `flow:` (sub-flow), never both.
- The `when:` key accepts a Python expression evaluated at runtime. The expression has access to `org_config`, `project_config`, and `task_config` variables.
- Options set in a flow step override task-level defaults for that execution only.
- To extend a standard flow, declare a flow with the same name. CumulusCI merges your step additions with the standard flow's steps. Use numeric gaps or fractional step numbers to position new steps.

### 4. Robot Framework Integration

CumulusCI includes a built-in `robot` task that runs Robot Framework acceptance test suites against a scratch org. The task handles browser setup (SeleniumLibrary or Browser library), org credential injection, and result collection automatically.

```yaml
tasks:
  robot:
    options:
      suites: robot/tests
      output_dir: robot_results

flows:
  qa_org:
    steps:
      3:
        task: robot
```

The `robot` task class path is `cumulusci.tasks.robotframework.Robot`. CumulusCI injects the org's login URL and session credentials into the Robot environment as variables (`${LOGIN_URL}`, `${SESSION_ID}`) so test suites do not need to manage authentication.

---

## Common Patterns

### Pattern 1: Extending a Standard Flow With a Pre- or Post-Deployment Step

**When to use:** You need to add a custom configuration step (deploy extra metadata, run a script, load config data) before or after the standard `dev_org` or `qa_org` flow.

**How it works:**

```yaml
# cumulusci.yml
tasks:
  deploy_custom_settings:
    description: Deploy custom settings metadata after base deploy
    class_path: cumulusci.tasks.salesforce.Deploy
    options:
      path: unpackaged/config/custom
      unmanaged: True

flows:
  dev_org:
    steps:
      3.1:                         # Insert after step 3 of standard dev_org
        task: deploy_custom_settings
      3.2:
        task: load_custom_data
        options:
          dataset: dev
```

**Why not fork the standard flow entirely:** Declaring a fresh flow that copies all standard steps means you must maintain parity manually as CumulusCI upgrades. Extending by number gaps or fractional steps keeps you on the upgrade path automatically.

### Pattern 2: CI Flow with JWT Authentication in GitHub Actions

**When to use:** Running `cci flow run` in a CI pipeline that must authenticate to a Dev Hub or persistent org without interactive login.

**How it works:**

```yaml
# .github/workflows/ci.yml
name: CI Feature Branch
on:
  push:
    branches-ignore: [main, 'release/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install CumulusCI
        run: pip install cumulusci

      - name: Authenticate Dev Hub via JWT
        run: |
          printf '%s' "${{ secrets.DEVHUB_JWT_KEY }}" > /tmp/server.key
          chmod 600 /tmp/server.key
          sf org login jwt \
            --client-id "${{ secrets.DEVHUB_CLIENT_ID }}" \
            --jwt-key-file /tmp/server.key \
            --username "${{ secrets.DEVHUB_USERNAME }}" \
            --alias DevHub \
            --set-default-dev-hub
          rm /tmp/server.key

      - name: Run CI feature flow
        run: cci flow run ci_feature --org feature
```

JWT authentication requires a Connected App in the Dev Hub org with the certificate uploaded. The private key is stored as a GitHub Actions secret — never committed to the repository.

### Pattern 3: Cross-Project Source Reuse

**When to use:** Multiple CumulusCI projects share common tasks or flows (e.g., a team-wide data loading library or a set of org configuration flows maintained in a central repo).

**How it works:**

```yaml
# cumulusci.yml — consuming project
sources:
  shared_toolkit:
    github: https://github.com/myorg/cci-shared-toolkit
    tag: v1.2.0

flows:
  dev_org:
    steps:
      5:
        flow: shared_toolkit/configure_sharing_rules  # namespace/flow-name syntax
```

The `sources:` block declares a named source pointing to another GitHub repo. CumulusCI downloads the referenced repo and makes its tasks and flows available under the namespace prefix. Pinning to a specific `tag:` ensures reproducible builds.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to run a standard task with different options | Declare a new named task with same `class_path`, different `options` | Creates a reusable named variant; avoids inline option overrides scattered across flows |
| Need to add a step to an existing standard flow | Extend the flow by declaring it and adding fractional or gap step numbers | Stays on CumulusCI upgrade path; standard steps remain authoritative |
| Need to skip a step in a standard flow | Set `when: False` on the step in your flow extension | Cleaner than removing and re-listing all other steps |
| Need to run acceptance tests on every PR | Add `robot` task to `ci_feature` flow or a dedicated `ci_robot` flow | CumulusCI manages org credentials injection; no manual auth wiring needed |
| CI pipeline needs a persistent sandbox, not a scratch org | Use `cci flow run <flow> --org sandbox_alias` with sandbox org defined in `orgs:` | CumulusCI supports sandboxes as named orgs; not all flows are scratch-org-only |
| Custom Python logic needed in a flow | Write a class inheriting from `cumulusci.core.tasks.BaseTask`, reference it by full dotted path | Keeps custom logic in version control and testable; avoids shell task hacks |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner configuring CumulusCI automation:

1. **Confirm CumulusCI version and project type** — Run `cci version` and inspect the `project:` block of `cumulusci.yml`. Identify whether the project is managed, unlocked, or unpackaged. This determines which standard flows are applicable.
2. **Identify the standard flow or task to extend** — Run `cci flow info <flow-name>` or `cci task info <task-name>` to see the current step list and available options. Never guess — the info commands are authoritative for the installed version.
3. **Draft the cumulusci.yml change** — Write the task or flow declaration. For extensions, use fractional step numbers (3.1, 3.2) or gaps to insert new steps without renumbering. For new tasks, provide the full `class_path`.
4. **Validate locally** — Run `cci flow info <flow-name>` after editing to confirm CumulusCI can parse the change and the merged step order is correct. Run `cci task info <task-name>` to verify option resolution.
5. **Test against a scratch org** — Run `cci flow run <flow-name> --org dev` against a local dev scratch org before wiring into CI. Check the task output log in `.cci/logs/` for errors.
6. **Wire into CI and set up JWT auth** — Add the `cci flow run` invocation to the CI workflow YAML. Configure the Connected App for JWT in the target Dev Hub or sandbox and store the private key as a CI secret.
7. **Verify CI run end-to-end** — Trigger the CI workflow and confirm the flow completes successfully. Check that no tasks are silently skipped due to `when:` conditions evaluating unexpectedly.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `cci version` confirms v4.x; any v3.x-era class paths have been updated
- [ ] Every custom task has a valid `class_path` verified with `cci task info`
- [ ] Flow step numbers are non-colliding and in the correct execution order per `cci flow info`
- [ ] `when:` expressions use valid runtime variables (`org_config`, `project_config`) and have been tested
- [ ] JWT Connected App is configured with the correct certificate and callback URL in the target org
- [ ] CI secrets store the private key (never the SFDX auth URL for production orgs in shared repos)
- [ ] Robot Framework test paths in `options.suites` match actual file system paths
- [ ] Cross-project `sources:` entries are pinned to a specific release tag for reproducible builds

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`cci flow info` is the only reliable way to see merged step order** — When a project extends a standard flow, the merged result is not visible in `cumulusci.yml` alone. Without running `cci flow info`, it is easy to add a step that silently collides with a standard step number, causing the standard step to be replaced rather than augmented.

2. **Standard flow behavior depends on the `project.package.type` setting** — The `dev_org` flow runs different tasks for managed packages vs. unpackaged projects. A project configured as `managed` that should be `unpackaged` will trigger package install steps against a scratch org, which will fail. Always verify the `project:` block before debugging flow failures.

3. **`when:` conditions are evaluated in Python and fail silently on attribute errors** — If a `when:` expression references an `org_config` attribute that does not exist, the condition evaluates to `False` and the step is skipped with no error. Tasks that should run may be silently omitted.

4. **JWT private key permissions must be exactly 600 on Linux CI runners** — The `sf org login jwt` command will fail with a cryptic OpenSSL error if the key file has world-readable permissions. Write the key to a temp file and `chmod 600` it before use.

5. **Cross-project sources download on every cold run and can hit GitHub rate limits** — The `sources:` block triggers a GitHub API call and archive download on each run where the cache is cold. Parallel CI runs can exhaust the unauthenticated GitHub API rate limit (60 requests/hour per IP). Pin sources to a specific tag and cache the CumulusCI home directory between runs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `cumulusci.yml` task declarations | Named task entries with `class_path` and `options` ready to paste |
| `cumulusci.yml` flow declarations | Flow extension or new flow with ordered steps and optional `when:` guards |
| GitHub Actions workflow YAML | Complete CI workflow with JWT auth and `cci flow run` invocation |
| `cci flow info` validation output | Command to verify merged step order after editing |
| Robot Framework task configuration | `robot` task options block pointing to test suite path |

---

## Related Skills

- `scratch-org-pools` — Pre-created scratch org pools for parallel CI; pools are claimed via CumulusCI and are a natural complement to CI flows defined here
- `scratch-org-management` — Individual scratch org lifecycle and definition file authoring; the orgs CumulusCI flows run against
- `unlocked-package-development` — Unlocked package versioning; CumulusCI upload_beta and install_beta flows are central to unlocked package CI pipelines
- `second-generation-managed-packages` — Managed 2GP versioning; CumulusCI release_* standard flows target managed packages
- `github-actions-for-salesforce` — General GitHub Actions CI/CD setup; this skill covers the CumulusCI-specific layer on top
