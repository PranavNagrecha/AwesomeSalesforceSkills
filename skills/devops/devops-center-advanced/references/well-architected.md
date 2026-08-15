# Well-Architected Notes — DevOps Center Advanced Workflows

## Relevant Pillars

- **Operational Excellence** — the value of DevOps Center is that the org's state
  is derivable from one artifact: the work item and its branch. Every practice in
  this skill exists to protect that property, and every failure mode in it is a
  case where two writers broke it.
- **Reliability** — an un-reconciled bypass is a scheduled future incident. The
  reconciliation step is not paperwork; it is the thing that stops the next
  normal promotion from reverting the fix.
- **Security** — governance over who (and now *what*) can commit and promote is
  a release-integrity control. Next-generation DevOps Center extends policy
  coverage to coding agents, which is the newest version of the same question.

## Architectural Tradeoffs

- **Managed package vs next-generation:** the managed package is mature and
  broadly documented; next-generation removes the install/upgrade cycle, adds
  Bitbucket (beta), surfaces change tracking through DX Inspector inside the org,
  and governs agents. The decision should turn on a named blocker, not on which
  is newer — and it is not a decision at all in Government Cloud Plus or the EU
  Operating Zone, or below Professional Edition with API access.
- **UI promotion vs CLI pipeline commands:** clicking Promote is legible to
  admins and unautomatable; `sf project deploy pipeline start` puts the same
  operation behind CI at the cost of depending on a beta interface. Pilot the
  latter, keep the former as the fallback.
- **Bypass latency vs pipeline discipline:** a fast pipeline makes the bypass
  unattractive, which is the only durable way to reduce bypass rate. Adding
  approval gates to a slow pipeline increases bypass rate rather than reducing
  it.
- **Work-item retention vs list usability:** closed work items feel like the
  audit trail, but the durable audit artifacts are the commits and pull requests.
  A retention window trades a small amount of navigational history for a list
  people can actually use.
- **Shared stage orgs vs per-team orgs:** shared UAT is cheap and serializes
  promotions behind test runs; per-team orgs remove the contention and multiply
  the drift surface. Front-loading validation against a cheaper stage is the
  middle path.

## Hygiene

- Every promotion traces to a work item; no non-work-item branch merges into a
  pipeline branch.
- `--test-level` is explicit on every deploy and validate command.
- Production promotion is `deploy validate` then `deploy quick --job-id`.
- The bypass runbook exists in writing, includes pre-state capture, and ends in a
  cascade down the pipeline.
- Bypass count is reviewed monthly and trends toward zero.
- Permission sets and profiles are retrieved-merged-committed, never
  delta-committed.
- Flow edits are serialized at work-item assignment time; flow conflicts are
  resolved in Flow Builder, never in a text editor.
- Merged branches and closed work items are pruned on a stated cadence.
- Agent commit policy is set before agent write access is granted.

## Related

- `devops/permission-set-deployment-ordering` — the full-replace hazard and the
  ConnectedApp cross-reference ordering rule.
- `devops/flow-deployment-activation-ordering` — flow activation and version
  pointers across a pipeline.
- `devops/salesforce-cli-automation` — the CLI surface these runbooks are built
  from.
- `devops/deployment-error-diagnosis` — reading a failed promotion.
- `devops/metadata-api-retrieve-deploy` — what the underlying API actually does
  with each metadata type.
- `admin/devops-process-documentation` — first-time DevOps Center setup, which
  this skill deliberately does not cover.

## Official Sources Used

- Next Generation DevOps Center — AI-powered, click-based central development hub with governance for coding agents and users; instant setup with no package download; SLDS 2 UI; flexible environment support; integrated change tracking via DX Inspector — https://help.salesforce.com/s/articleView?id=platform.next_generation_devops_center.htm&type=5
- Set Up Next Generation DevOps Center — requires a GitHub or Bitbucket account; MCP tools require an MCP-enabled IDE and a user-facing MCP client — https://help.salesforce.com/s/articleView?id=platform.next_gen_devops_center_setup.htm&type=5
- Considerations to Set Up Next Generation DevOps Center — Professional Edition with API access or higher, Lightning Experience, not available in Government Cloud Plus or the EU Operating Zone — https://help.salesforce.com/s/articleView?id=platform.next_gen_devops_center_setup_considerations.htm&type=5
- Install and Configure DevOps Center (Managed Package) — the separately documented managed-package product — https://help.salesforce.com/s/articleView?id=platform.devops_center_setup.htm&type=5
- Promote Work Items Through Your Pipeline — each pipeline stage corresponds to an environment and a branch; a minimum pipeline has one test stage and a production stage — https://help.salesforce.com/s/articleView?id=platform.devops_center_work_items_promote.htm&type=5
- DX Inspector — appears at the top of any page or builder in a sandbox, scratch org, or Developer Edition org; track changes, create work items, commit metadata, create change requests without switching tabs — https://help.salesforce.com/s/articleView?id=platform.devops_center_dx_inspector.htm&type=5
- Set Up DevOps Center for Bitbucket (Beta) — https://help.salesforce.com/s/articleView?id=sf.devops_center_configure_bitbucket.htm&type=5
- Salesforce CLI Command Reference, `sf project deploy` — `validate`, `quick`, `start`, `preview`, `report`, `resume`, `cancel`, and the beta `pipeline start / validate / quick / report / resume` subcommands — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_commands_unified.htm
- (Optional) Install Salesforce CLI DevOps Center Plugin (Beta) — the `project deploy pipeline` subcommands ship in `@salesforce/plugin-devops-center`, not the base CLI; install with `sf plugins install @salesforce/plugin-devops-center` — https://help.salesforce.com/s/articleView?id=platform.devops_center_cli_install.htm&type=5
- salesforcecli/plugin-devops-center (source) — command list including `project deploy pipeline start / validate / quick / report / resume`; "This command is currently in beta. Any aspect of this command can change without advanced notice. Don't use beta commands in your scripts." — https://github.com/salesforcecli/plugin-devops-center
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/
- Salesforce Well-Architected — Adaptable — https://architect.salesforce.com/docs/architect/well-architected/adaptable/adaptable
