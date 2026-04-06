# LLM Anti-Patterns — CumulusCI Automation

Common mistakes AI coding assistants make when generating or advising on CumulusCI configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Short Task Names Instead of Full class_path

**What the LLM generates:** Task declarations that use a short name or alias as `class_path` instead of the fully qualified Python dotted path.

```yaml
# Wrong — class_path is not a short name
tasks:
  my_deploy:
    class_path: Deploy
    options:
      path: src/
```

**Why it happens:** LLMs associate `class_path` with a simple string identifier from training data that shows incomplete snippets. The word "Deploy" appears near `class_path` in examples, leading to omission of the module prefix.

**Correct pattern:**

```yaml
tasks:
  my_deploy:
    class_path: cumulusci.tasks.salesforce.Deploy
    options:
      path: src/
      unmanaged: True
```

**Detection hint:** Any `class_path` value that does not contain at least one `.` is wrong for built-in CumulusCI tasks. All built-in task class paths start with `cumulusci.tasks.*`.

---

## Anti-Pattern 2: Using `sf org pool` or `sfdx force:org:pool` Commands

**What the LLM generates:** Instructions to manage scratch org pools using Salesforce CLI commands.

```bash
# Wrong — these commands do not exist
sf org pool create --count 10 --definition-file config/project-scratch-def.json
sfdx force:org:pool:get --alias ci_org
```

**Why it happens:** LLMs conflate CumulusCI's pool management with native Salesforce CLI commands because both tools are used together in CI contexts. The `sf` CLI has no pool management subcommands.

**Correct pattern:**

```bash
# CumulusCI pool commands
cci org pool create dev 10
cci org pool get dev --org ci_pool_org
cci org pool list dev
cci org pool prune dev
```

**Detection hint:** Any command matching `sf org pool`, `sfdx force:org:pool`, or `sf scratch pool` is hallucinated. Pool management is exclusively a CumulusCI feature.

---

## Anti-Pattern 3: Copying the Entire Standard Flow Instead of Extending It

**What the LLM generates:** A `cumulusci.yml` flow declaration that reproduces all steps of a standard flow (dev_org, qa_org, etc.) and then adds custom steps at the end.

```yaml
# Wrong — this is a fragile copy of the standard flow
flows:
  dev_org:
    steps:
      1:
        task: create_connected_app
      2:
        task: deploy
      3:
        task: deploy_unmanaged_ee
      4:
        task: snapshot_changes
      5:
        task: my_custom_step    # the only intended addition
```

**Why it happens:** LLMs default to explicit enumeration when asked to "add a step to a flow" rather than understanding CumulusCI's inheritance/merge model. Training data sometimes shows full flow definitions from older CumulusCI versions or blog posts that predate the extension pattern.

**Correct pattern:**

```yaml
# Correct — extend the standard flow by adding only the new step
flows:
  dev_org:
    steps:
      3.1:
        task: my_custom_step
```

**Detection hint:** Any flow extension that re-declares more than 2-3 steps of a well-known standard flow (`dev_org`, `qa_org`, `ci_feature`) is almost certainly a copy-and-mutate anti-pattern. Use `cci flow info` to verify the standard flow's existing steps before writing an extension.

---

## Anti-Pattern 4: Generating `when:` Conditions That Reference Non-Existent org_config Attributes

**What the LLM generates:** `when:` expressions referencing `org_config` properties that do not exist in CumulusCI's standard org configuration object.

```yaml
# Wrong — 'org_config.is_community_enabled' is not a real attribute
steps:
  2:
    task: deploy_community_settings
    when: "org_config.is_community_enabled"
```

**Why it happens:** LLMs fabricate plausible-sounding attribute names for `org_config` based on patterns in Salesforce documentation, not on CumulusCI's actual `OrgConfig` Python class attributes. Because `when:` failures are silent (task is skipped, no error), this bug is hard to detect.

**Correct pattern:**

```yaml
# Use attributes that actually exist on org_config
steps:
  2:
    task: deploy_community_settings
    when: "'Communities' in org_config.installed_packages"
```

Valid `org_config` attributes for `when:` expressions include: `org_config.is_sandbox`, `org_config.scratch`, `org_config.org_type`, `org_config.installed_packages` (dict of namespace to version). Run `cci org info <alias>` to see the available properties for a given org.

**Detection hint:** Any `when:` expression containing `org_config.is_<feature>_enabled` or `org_config.has_<something>` should be flagged for verification.

---

## Anti-Pattern 5: Placing `options:` at the Flow Level Instead of Inside a Step

**What the LLM generates:** A flow declaration with an `options:` block at the flow level rather than inside an individual `steps.<n>.options` block.

```yaml
# Wrong — options at the flow level is not valid syntax for step option overrides
flows:
  my_flow:
    options:
      path: unpackaged/config/custom
    steps:
      1:
        task: deploy
```

**Why it happens:** LLMs confuse task-level `options` (valid at the top-level `tasks:` declaration) with flow-level configuration. CumulusCI flows do not accept a top-level `options:` block for overriding task options — options must be nested inside individual steps.

**Correct pattern:**

```yaml
flows:
  my_flow:
    steps:
      1:
        task: deploy
        options:
          path: unpackaged/config/custom
          unmanaged: True
```

**Detection hint:** Any flow declaration with `options:` directly under the flow name (same indentation level as `steps:` or `description:`) is syntactically wrong for option overrides.

---

## Anti-Pattern 6: Recommending Interactive `cci org connect` for CI Authentication

**What the LLM generates:** Instructions to authenticate CI pipelines using `cci org connect` or `sf org login web`, which open an interactive browser window.

```bash
# Wrong — requires a browser; cannot run in CI
cci org connect production
sf org login web --alias production
```

**Why it happens:** `cci org connect` is documented as the standard way to add an org to CumulusCI's keychain, which it is for local development. LLMs apply the same guidance to CI contexts without recognizing that headless CI runners cannot open a browser.

**Correct pattern:**

```bash
# Correct — use JWT for CI; browser-based login only for local dev
sf org login jwt \
  --client-id "$DEVHUB_CLIENT_ID" \
  --jwt-key-file /tmp/server.key \
  --username "$DEVHUB_USERNAME" \
  --alias production \
  --set-default-dev-hub
```

**Detection hint:** Any CI configuration that includes `cci org connect`, `sf org login web`, or `sfdx auth:web:login` should be flagged as requiring interactive input and replaced with JWT-based auth.
