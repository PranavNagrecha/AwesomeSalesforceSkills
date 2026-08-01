# Well-Architected Notes — sfdx-hardis Integration

**Authority, stated first because it governs everything else:** sfdx-hardis is community
open-source, not a Salesforce product. Its own documentation is the authority for its command
names, flags, defaults and behaviour, and those change on the project's release schedule
rather than the platform's. Salesforce documentation remains the authority for what the
platform does underneath — what a deployment performs, what each `testLevel` executes, what a
retrieve can and cannot return. Any guidance that blurs those two is guessing, and this skill
treats an unverified plugin flag as a claim to check rather than a fact to repeat.

**Operational Excellence:** a plugin sits between the pipeline and the CLI, which makes both
layers part of the change surface. Unpinned, a third-party release can alter deployment or
retrieval behaviour with no commit on your side — and the investigation starts by examining
your own diff, which is where the hour goes. Pinning the plugin and the CLI, and printing
both versions into the job log, is what makes a later bisect possible at all.

**Reliability:** the platform requirements do not move because a wrapper is in front of them.
Deploying Apex to production still requires at least 75% coverage with passing tests, and
`testLevel` still decides what actually runs. A wrapper that speeds validation up by
selecting a narrower level has deferred the failure to the production deploy rather than
removed it, and it is worth knowing which level is being passed before the speed is treated
as a gain.

**Observability, and its limits:** a drift monitor concludes by retrieving metadata and
diffing it, so it inherits every limitation of a retrieve. Types not supported at your API
version do not appear, which means an empty report can mean "nothing changed" or "nothing was
looked at" — indistinguishable unless the scope is published with the result. Keeping the
comparison manifest and the ignore list in the repository, where they show up in diffs and
get reviewed, is what stops noise suppression from becoming blindness while the report is
still cited as evidence.

**Security:** credential ownership should not transfer to the tool. CI has no human to
complete a browser login, so the JWT bearer flow is the documented path, and keeping that
step in your own pipeline — key from your secret store, session established before the plugin
runs — means the arrangement survives an upgrade, a reconfiguration or a decision to stop
using the plugin.

**Fit:** this is a trade, not a default. Community open-source here means no vendor support
commitment, a surface that moves independently, and an upgrade path you own — reasonable for
a team running scripted CI on its own runners, poor for a team that needs a supported product
with admin-friendly change management, where DevOps Center is the Salesforce-provided option.
Record which of those describes the team before adopting, because the answer determines
whether the trade was ever the right one.

## Official Sources Used

Salesforce documentation — authoritative for platform behaviour:

- Metadata API `deploy()` — `checkOnly` and the `testLevel` values that a wrapper passes through — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
- Apex Code Coverage — the 75% production requirement no tool changes — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_code_coverage_intro.htm
- Authorize an Org Using the JWT Flow — the CI credential path that should stay in your pipeline — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm
- Metadata Types — what the Metadata API can retrieve, and therefore the ceiling on any drift monitor's scope — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_types_list.htm
- DevOps Center — the Salesforce-provided alternative this tool is chosen instead of — https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm

Third-party documentation — authoritative for the plugin's own behaviour, and the only
non-Salesforce source in this skill:

- sfdx-hardis project documentation — command surface, flags and defaults, which vary by release; always confirm against `sf hardis --help` for the installed version — https://sfdx-hardis.cloudity.com/
