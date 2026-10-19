# Worked Example — releasing a base and an extension built in parallel

`PkgBase` (path `pkg-base`) and `PkgExtn` (path `pkg-extension`) change in the same sprint. The base team creates versions with `--skip-validation` to move fast. This walk-through follows the sequence in the Salesforce DX Developer Guide's "Considerations for Promoting Packages with Dependencies".

## Sprint days 1–8: develop against `LATEST`

```json
{
  "path": "pkg-extension",
  "default": false,
  "package": "PkgExtn",
  "versionName": "v 2.3",
  "versionNumber": "2.3.0.NEXT",
  "dependencies": [
    { "package": "PkgBase", "versionNumber": "1.1.0.LATEST" }
  ]
}
```

Base builds 1.1.0.1 … 1.1.0.4 are created. Each extension build binds to whichever base build was newest when it was created. Because base builds skip validation, extension tests during this phase are only indicative.

## Day 9: promote the base, then re-point the extension

```bash
# 1. Promote the base build QA signed off (not necessarily the newest one).
sf package version promote --package "PkgBase@1.1.0-3" --no-prompt

# 2. Edit sfdx-project.json: "1.1.0.LATEST" -> "1.1.0.RELEASED"  (now resolves to 1.1.0.3)

# 3. Create the extension version that will ship, with validation.
sf package version create --package PkgExtn --installation-key-bypass --code-coverage --wait 30
```

If the team had promoted the extension built on day 8 instead, it would carry a dependency on base 1.1.0.4 — `LATEST` at that moment — which was never promoted.

## Day 10: prove the order, then promote the extension

Query the new extension version for its dependencies (Tooling API) and install in exactly that order into a fresh org:

```bash
sf data query --use-tooling-api -o devhub --json \
  -q "SELECT Dependencies FROM SubscriberPackageVersion WHERE Id = '04t000000000EXTAAA'"
# -> "Dependencies": {"Ids": [{"subscriberPackageVersionId": "04t000000000BASAAA"}]}
```

Run the clean-org install job from `examples.md` with those IDs, then promote `PkgExtn` 2.3.0.x. Record both 04t IDs against the release commit.

## What the checker says along the way

| Day | `check_packaging_dependency_graph.py --manifest-dir .` |
|---|---|
| 1–8 | `WARN: PkgExtn depends on PkgBase with LATEST; switch to RELEASED before creating the version you will promote` |
| 9 onward | clean; prints `install/promote order: PkgBase -> PkgExtn` |

The 04t IDs above are placeholders. Replace `devhub` with the alias of the org you query; dependency information comes from the version record, so query the org where the version is visible to you.
