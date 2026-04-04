# Well-Architected Notes — DevOps Center Pipeline

## Relevant Pillars

- **Operational Excellence** — DevOps Center is primarily an operational excellence tool. It replaces ad-hoc change set processes with a tracked, auditable, source-controlled release pipeline. The pipeline stage model enforces promotion sequencing, and the Work Item model gives every change a named owner and history. Teams operating DevOps Center should define a branch protection policy, a bundle cadence, and a promotion approval gate for production to fully realize the operational excellence benefits.

- **Security** — The GitHub OAuth connection and the Connected App used to authenticate DevOps Center to GitHub are security-sensitive. These credentials should be owned by a service account, not a personal GitHub account. If the individual's GitHub account is deactivated, the pipeline loses connectivity. Branch protection rules in GitHub prevent unauthorized direct pushes to stage branches, which is a security control as well as a reliability control.

- **Reliability** — The pipeline's reliability depends on the health of the GitHub connection and the source-tracking state of each stage org. Drift between org state and the stage branch in GitHub causes unreliable promotions. The reliability checklist for this skill (no out-of-band deployments, branch protection active, Work Items started before org changes) directly mitigates the most common reliability failures.

- **Adaptability** — DevOps Center's stage model is easy to extend: adding a new sandbox stage is a configuration change, not a code change. However, the tool has a ceiling — it does not support automated test execution, pre-promotion approval workflows, or gated rollbacks. Teams that outgrow the point-and-click model should plan a migration to a CLI-based CI/CD pipeline before the operational overhead of workarounds accumulates.

## Architectural Tradeoffs

**DevOps Center vs. SFDX CLI + CI/CD:** DevOps Center is purpose-built for admin and low-code teams that want source control benefits without investing in a CI/CD platform. It trades flexibility for ease of use. SFDX CLI + GitHub Actions (or equivalent) offers full automation, test gating, automated rollbacks, and multi-package support — but requires developer investment to set up and maintain. Choose DevOps Center when the team's primary skill is declarative configuration; choose CLI CI/CD when the team has developers and needs automated test gates or parallel deployments.

**Bundling strategy:** Aggressive bundling (always bundle all Work Items before promoting) reduces conflict risk but slows individual changes that are ready to ship. Selective bundling (promote simple independent Work Items individually, bundle only related ones) is faster but requires more judgment from the release manager. The right tradeoff depends on team size and metadata overlap: teams with heavy shared metadata (profiles, permission sets, shared flows) benefit more from consistent bundling.

**GitHub-only constraint:** DevOps Center's hard dependency on GitHub is an architectural lock-in. Teams already invested in Azure DevOps or GitLab must either introduce GitHub as a parallel system or forgo DevOps Center entirely. This tradeoff should be evaluated at adoption time, not after setup.

## Anti-Patterns

1. **Using DevOps Center as a deployment shortcut alongside SFDX CLI** — Mixing CLI deployments into DevOps Center-managed orgs causes source tracking drift and produces a pipeline state that no single tool owns. Either commit to DevOps Center for all changes in those orgs, or use SFDX CLI exclusively and skip DevOps Center.

2. **Skipping branch protection rules after pipeline setup** — Stage branches are DevOps Center infrastructure. Leaving them unprotected in GitHub allows accidental deletion or force-pushes that break the pipeline in ways that are time-consuming to recover from. Branch protection is a mandatory post-setup configuration step, not an optional best practice.

3. **Connecting DevOps Center to a personal GitHub account** — When DevOps Center's GitHub OAuth connection is tied to an individual developer's personal GitHub account, the pipeline breaks if that person leaves the team or revokes the OAuth token. All pipeline-critical integrations should use a dedicated service account or an organization-level OAuth app.

## Official Sources Used

- Salesforce DevOps Center Help — Plan Your Pipeline — https://help.salesforce.com/s/articleView?id=sf.devops_center_pipeline_plan.htm&language=en_US&type=5
- Salesforce DevOps Center Help — Promote Work Items Through Your Pipeline — https://help.salesforce.com/s/articleView?id=sf.devops_center_work_items_promote.htm&type=5&language=en_US
- Salesforce DevOps Center Help — To Bundle or Not to Bundle — https://help.salesforce.com/s/articleView?id=sf.devops_center_pipeline_bundling_stage.htm&language=en_US&type=5
- Salesforce DevOps Center Help — Set Up DevOps Center for GitHub — https://help.salesforce.com/s/articleView?id=platform.devops_center_configure.htm&language=en_US&type=5
- Salesforce DevOps Center Help — Review and Resolve Conflicts in GitHub — https://help.salesforce.com/s/articleView?id=sf.devops_center_promotion_resolve_conflicts_github.htm&language=en_US&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
