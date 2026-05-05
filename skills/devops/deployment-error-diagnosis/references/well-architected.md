# Well-Architected Notes — Deployment Error Diagnosis

## Relevant Pillars

- **Reliability** — Permission Sets + Permission Set Groups
  scaled better than profile-based deploys; profiles' verbose
  exports produce the most cross-reference failures.
- **Operational Excellence** — Capture the FULL error message
  before triage. The first line often points at a symptom; the
  underlying cause is 30 lines down.

## Architectural Tradeoffs

- **Permission Set / PSG vs profile.** PS / PSG scoped exports
  are cleaner; profiles were the original pattern. Modern orgs
  default to PS / PSG; legacy orgs may have profile-heavy
  configuration that's hard to migrate.
- **Wildcards vs explicit members.** Wildcards are easier to
  maintain (new metadata flows automatically); explicit lists
  give more control over deploy boundaries. Mixing them is the
  bug-trap.
- **`Inactive` retire vs `Obsolete` retire vs delete.** Obsolete
  preserves history without running new invocations; delete
  removes everything; inactive is a hybrid (Apex). Pick by audit
  retention requirement.

## Anti-Patterns

1. **`--ignore-errors` / `--ignore-warnings` in CI.** Masks real
   failures.
2. **Full-profile exports against varied targets.** Cross-reference
   failures multiply.
3. **Deploying inactive flow without setting Active or Obsolete.**
   Deploy fails.
4. **Type-change attempts on populated fields.** Use migration
   pattern instead.
5. **Wildcard + explicit `<members>` for the same type.**
   Implementation-defined behavior.
6. **PermissionSetGroup before its component PermissionSets.**
   Resolution-order failure.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- SFDX Project Configuration — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_ws_config.htm
- ApexCodeCoverageAggregate Object — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_apexcodecoverageaggregate.htm
- Profile Metadata Reference — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_profile.htm
- PermissionSet Metadata Reference — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_permissionset.htm
- Flow Metadata Reference (status values) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Sibling skill — `skills/devops/sfdx-cicd-pipeline/SKILL.md` (when one exists)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
