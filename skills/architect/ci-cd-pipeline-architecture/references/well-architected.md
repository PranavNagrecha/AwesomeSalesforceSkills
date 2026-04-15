# Well-Architected Notes — CI/CD Pipeline Architecture

## Relevant Pillars

- **Operational Excellence** — The primary pillar. A well-designed CI/CD pipeline is the operational backbone of Salesforce delivery. The pipeline enforces repeatable, auditable change management; automates quality verification; and produces the deployment artifacts (runbooks, validation IDs, test reports) that constitute operational evidence. Pipeline architecture directly maps to the Well-Architected principle of "Automate where you can" and "Make good things easy to do."

- **Reliability** — Quality gates protect production reliability. Validation-only deploys, Apex test thresholds, and regression suites are the mechanisms that prevent unreliable changes from reaching production. A pipeline with insufficient gates is a reliability risk; a pipeline with gates that are too strict or frequently broken is an operational reliability risk for the delivery team itself.

- **Security** — Pipeline architecture determines who can promote to production and under what conditions. Human approval gates, branch protection rules, JWT Bearer Flow authentication for CI service accounts, and the separation of CI credentials from developer credentials are security architecture decisions made at the pipeline level. Skipping a human gate before production in a SOX-governed org is a control failure, not just a process gap.

- **Performance** — Indirectly relevant. The pipeline design determines how long the feedback loop is for developers. Pipelines with too many sequential gates slow delivery and incentivize stage-skipping. The Well-Architected principle of "Right-size your feedback loops" applies: gates should be fast enough to not block developer flow, and expensive tests (Full Sandbox regression, load testing) should be deferred to later pipeline stages.

- **Scalability** — Pipeline topology must scale with team growth. A 2-stage pipeline appropriate for a 3-person team becomes a bottleneck at 30 people. The architecture must account for parallel feature branches, concurrent sandbox usage, and the addition of new release trains without redesigning from scratch.

---

## Architectural Tradeoffs

### Gate Count vs. Deployment Velocity

Adding more quality gates reduces defect escape rate but increases cycle time. The Well-Architected framework recommends the minimum number of gates that satisfy the risk profile of the org. A test coverage gate and a static analysis gate at Stage 1 are high-leverage and low-cost. A full regression suite at every stage is expensive and slows releases. Gate placement should reflect where in the pipeline the risk of that class of defect is highest, not just "add gates everywhere."

### DevOps Center vs. CLI-Driven Pipeline

DevOps Center provides a GUI-driven promotion experience that lowers the barrier for admin-led teams but imposes the 15-stage limit and does not support custom quality gate configuration or code scanning. A CLI-driven pipeline (GitHub Actions, GitLab CI, Jenkins) requires more upfront engineering but is unlimited in stage count and can enforce any gate logic. The tradeoff is team capability vs. platform constraint: organizations with dedicated DevOps engineers benefit from CLI pipelines; admin-led teams benefit from DevOps Center. A hybrid is valid: DevOps Center manages promotion; an external CI tool manages quality gates.

### Automated Promotion vs. Manual Gate

Automated promotion (every commit that passes gates advances to the next stage) enables true continuous delivery but requires very high test coverage and gate reliability. A single flaky gate breaks the automation. Manual gates (a human approves each promotion) are slower but appropriate for regulatory environments or teams where test coverage is not yet sufficient. The architecture should document which gates are automated and which are manual, and establish a roadmap for automating manual gates as test coverage improves.

---

## Anti-Patterns

1. **No gate between QA and production** — A single-stage pipeline that deploys directly from source to production (or from a developer sandbox with no formal QA step) is the most common pipeline anti-pattern in Salesforce orgs. It eliminates all automated quality enforcement and makes every deploy a rollback risk. Even a minimal validation-only deploy with RunLocalTests is better than no gate.

2. **Treating the CI YAML file as the pipeline architecture** — Configuring a GitHub Actions or GitLab CI workflow without documenting the stage sequence, gate criteria, and rollback strategy produces an unmaintainable pipeline. When requirements change (new sandbox, new gate, new team), there is no architecture to update — only a YAML file to reverse-engineer.

3. **Using the same sandbox for development and CI validation** — Sharing a sandbox between active developer work and CI validation jobs creates race conditions: a CI validation job may fail because a developer has deployed an incomplete change to the same sandbox. Dedicated CI sandboxes (or scratch orgs for Stage 1) isolate CI validation from active development.

---

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce DX Developer Guide: Deploying and Testing — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_develop.htm
- Salesforce DevOps Center Help: Plan Your Pipeline — https://help.salesforce.com/s/articleView?id=sf.devops_center_pipeline_plan.htm
- Salesforce CLI Command Reference: sf project deploy validate — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_commands_unified.htm
- Salesforce Well-Architected: Operational Excellence — https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
