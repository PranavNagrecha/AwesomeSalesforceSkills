# Worked Example — Project Configuration That Survives the Second Batch

The first migration batch usually works on a default project. The second batch breaks it. Someone adds a package directory for the integration team's code, or retrieves at the CLI's API version instead of the org's, and the next deploy targets the wrong folder or drops fields. This example fixes the project file before batch two and makes the checker part of the cut-over gate.

## Starting point (after batch one)

```text
acme-crm/
├── sfdx-project.json
├── .forceignore
├── manifest/package.xml          # batch one: ApexClass, ApexTrigger
└── force-app/main/default/...    # retrieved in source format
```

## The project file for batch two

```json
{
  "packageDirectories": [
    { "path": "force-app", "default": true },
    { "path": "integration-app" }
  ],
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "67.0"
}
```

Why each line is there:

- **`packageDirectories` is required.** Each path is relative to the project, and `./integration-app` would mean the same thing. An absolute path isn't allowed.
- **Exactly one `"default": true`.** With one directory the default is implied. Once there are two, you have to mark one. The CLI retrieves into the default directory, and `sf project convert mdapi` writes its output there unless you pass `--output-dir`. With two directories and neither one marked, the project breaks that rule, and it's unclear where the next retrieve will land.
- **`sourceApiVersion` pinned to the org's release.** This value decides which fields each metadata type returns on deploy, retrieve, and convert. The DX guide's example is a field added to CustomTab in API 63.0: source retrieved at 57.0 or earlier doesn't include that field, and the project commands error on it. Pin the version once, in the project file, and change it in its own commit.

## `.forceignore` additions for batch two

```text
# profiles: the team grants access through permission sets
**/profiles/**

# 1GP package installs are not source; deploying one installs or upgrades the package
**/installedPackages/**
```

The DX guide recommends permission sets over profiles. It also says teams that keep profiles should list them in `.forceignore`, because a retrieved profile depends on the org, the tracking state, and the other metadata in the same request. `InstalledPackage` represents a 1GP install, and it has to be the only type in its manifest, so it has no place in a feature deploy.

## Gate before each batch and before cut-over

```bash
python3 skills/devops/migration-from-change-sets-to-sfdx/scripts/check_migration_from_change_sets_to_sfdx.py \
  --manifest-dir acme-crm --expected-api-version 67.0 --strict
```

On the files above, once `integration-app/` exists, the checker exits 0. These were the failures in the first draft of batch two:

| Draft mistake | Checker result |
|---|---|
| Second directory added, `"default": true` left off both | ERROR: two packageDirectories and none is default |
| `"path": "/Users/dev/acme-crm/integration-app"` | ERROR: path is absolute |
| `sourceApiVersion` left at `"59.0"` from an old template | WARN: expected 67.0 (`--strict` fails the gate) |
| A colleague's metadata-format `objects/Invoice__c.object` copied into `force-app` | WARN: metadata-format `.object` file; convert it with `sf project convert mdapi --root-dir <dir>` |
| Profiles retrieved with batch one and no ignore rule | WARN: profiles in source that `.forceignore` does not exclude |

An empty project folder gets a WARN and exit 0, so a freshly cloned, not-yet-generated repo doesn't break CI. A folder that has files but no `sfdx-project.json` is an ERROR and exits 1, because no other check means anything until `sf project generate` has run.
