# LLM Anti-Patterns — sfdx-hardis Integration

Scope: adopting a **third-party** Salesforce CLI plugin without letting it obscure the
platform underneath. sfdx-hardis is community open-source, not a Salesforce product, so this
file deliberately anchors on the Salesforce-side facts that make or break the integration and
defers every claim about the plugin's own behaviour to the plugin's documentation.

**Epistemic rule for this skill, stated once:** Salesforce docs are authoritative for
platform behaviour — what a deployment does, what `testLevel` means, what a retrieve returns.
The plugin's own docs are authoritative for its command names, flags and defaults, and those
change between releases. Do not assert a plugin flag from memory; check the version you have
installed.

## Anti-Pattern 1: Reciting plugin commands from memory as if they were platform commands

The characteristic failure here, and the one that wastes the most time. A model that has
seen a community plugin in training data will emit confident command lines — flags,
subcommand names, defaults — for a tool whose surface changes release to release and is not
covered by any Salesforce compatibility guarantee. The resulting instructions look exactly
like `sf` commands and are not verifiable the same way.

❌ Generate `sf hardis:some:command --some-flag` and present it as established.
✅ Emit the command you believe exists, then require verification against the installed
version before it goes into a pipeline:

```bash
sf plugins inspect sfdx-hardis      # what is actually installed
sf hardis --help                    # the command surface of THIS version
sf hardis <topic> --help            # flags for the command you intend to use
```

If `--help` disagrees with the suggestion, `--help` is right. A skill or an assistant that
cannot check should say the command is unverified rather than assert it.

## Anti-Pattern 2: Installing the plugin unpinned in CI

A plugin sits between the pipeline and the Salesforce CLI, so an unpinned install means a
third-party release can change deployment behaviour with no change on your side. The failure
arrives as "the pipeline broke and nobody touched it", which is the most expensive kind to
diagnose because the first hour goes on looking at your own diff.

❌ `sf plugins install sfdx-hardis` in a CI step.
✅ Pin the plugin and the CLI, and upgrade both deliberately:

```yaml
- name: Install a known toolchain
  run: |
    npm install --global @salesforce/cli@2.x.y     # pin the CLI too
    sf plugins install sfdx-hardis@<exact-version>
    sf plugins inspect sfdx-hardis                 # record it in the log
    sf version --verbose
```

Recording the versions in the job log is what makes a later bisect possible. Two layers of
tooling, both unpinned, is two independent sources of unexplained change.

## Anti-Pattern 3: Letting the wrapper hide the test level

The most consequential platform fact a wrapper can obscure. Whatever the plugin calls its
deploy command, the underlying operation is a Metadata API deployment, and `testLevel`
decides what is executed: `RunLocalTests` runs every test in the org except those from
installed managed and unlocked packages and is the default for production deployments
containing Apex classes or triggers; `RunSpecifiedTests` runs only what you name;
`NoTestRun` applies only to development environments and is not available for production.

❌ Adopt a wrapper's default because it is faster, without knowing which of those it selects.
✅ Determine what the wrapper passes through — from its `--help` or its configuration file,
not from memory — and set the level explicitly where the wrapper allows it. Anything
deploying Apex to production must satisfy the platform's 75% coverage requirement regardless
of which tool issues the call; no wrapper changes that.

Source: Metadata API `deploy()` — `checkOnly` and the `testLevel` values — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm

## Anti-Pattern 4: Treating monitoring output as authoritative about the org

Any drift monitor works by retrieving metadata and diffing it, so its conclusions inherit
the limits of a retrieve. Two categories are routinely misread. Metadata types not supported
for retrieve at the current API version simply do not appear, so "no drift" can mean "not
looked at". And managed-package components change on the vendor's schedule, producing diffs
that are real but not actionable.

❌ Report "the org matches the repo" on the strength of a clean monitor run.
✅ State the scope with the result. Check what is actually covered before trusting an
absence:

- Confirm which metadata types are retrievable at your API version before concluding a type
  is unchanged — Metadata Coverage is the reference for what is supported.
- Maintain an explicit ignore list for managed-package and org-generated components, and
  review it, so noise suppression does not quietly become blindness.
- Treat drift alerts as findings to triage, not as a feed to mute. A monitor everyone has
  muted is worse than none, because it is still cited as evidence.

Source: Metadata Types supported by the Metadata API — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_types_list.htm

## Anti-Pattern 5: Letting the plugin own the org credential

Wrapper tooling usually offers a guided authentication flow, and adopting it wholesale puts
a third-party plugin in the credential path. The platform-level requirement does not change:
CI has no human to complete a browser login, so the JWT bearer flow is the documented
approach, and the private key belongs in your secret store rather than in tool-managed state.

❌ Let a plugin's setup command create and store credentials that CI then depends on.
✅ Authenticate with `sf org login jwt` from your own secrets, and let the plugin operate
against an already-authenticated CLI:

```bash
# Your pipeline owns this step. The plugin consumes the resulting session.
umask 077; KEYFILE="$(mktemp)"; trap 'rm -f "$KEYFILE"' EXIT
printf '%s' "$SF_JWT_KEY" | base64 -d > "$KEYFILE"     # [REDACTED]
sf org login jwt --client-id "$SF_CLIENT_ID" --jwt-key-file "$KEYFILE" \
  --username "$SF_USERNAME" --alias prod
```

This also keeps the exit path open: if the plugin is dropped, the credential arrangement
survives. See `devops/pipeline-secrets-management` for the full treatment.

Source: Authorize an Org Using the JWT Flow — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm

## Anti-Pattern 6: Forking the plugin to add a step

The tempting response to a missing feature, and it converts a dependency you can upgrade into
one you maintain — including the ongoing work of tracking Salesforce CLI changes that the
upstream project would have absorbed for you.

❌ Fork, patch, and pin CI to the fork.
✅ Prefer, in order: configuration the plugin already supports; a separate step in your own
pipeline that runs plain `sf` commands before or after the plugin; a contribution upstream.
Anything you can express as a `sf project deploy start` or `sf data query` in your own YAML
is better held there, where it is readable by anyone who knows the CLI and survives the
plugin being replaced.

## Anti-Pattern 7: Adopting the tool where the platform's own option was the answer

The plugin is genuinely useful for teams running their own pipelines. It is not a universal
recommendation, and assistants reach for it because it is the most visible open-source name
in this space. Where the requirement is admin-friendly change management with work items and
promotions, DevOps Center is the Salesforce-provided path and carries support; where the
requirement is scripted CI on your own runners, the plugin fits.

❌ Recommend it as the default Salesforce DevOps answer.
✅ Say what is being traded. Choosing community open-source means no vendor support
commitment, a surface that changes on its own schedule, and an upgrade path you own — a
reasonable trade for a team that wants scriptable hooks, and a poor one for a team that
needs a supported product. Record which of those applies before adopting.
