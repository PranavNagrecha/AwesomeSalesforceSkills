# Examples — Salesforce DevOps Tooling Selection

## Example 1: Regulated Financial Services Firm Selects Copado

**Context:** A financial services company with 200+ Salesforce users operates under SOC 2 Type II and must demonstrate that metadata never leaves the Salesforce trust boundary during deployments. The team is 60% admin, 40% developer. They currently use change sets and want to adopt source-driven development.

**Problem:** The team initially evaluated Gearset based on analyst recommendations and fast onboarding. During the security review, the CISO flagged that Gearset routes metadata through external SaaS infrastructure, which violates the firm's data handling policy. The team wasted six weeks on a proof-of-concept that could never pass procurement.

**Solution:**

```text
Selection criteria applied:
1. Compliance constraint: SOC 2 + data residency → eliminate SaaS-only tools (Gearset, AutoRABIT, Blue Canvas)
2. Team composition: 60% admin → need visual comparison UI, not CLI-only
3. Remaining candidates: Copado (native managed pkg) or Flosum (native)
4. ALM requirement: team needs user-story tracking and approval gates → Copado wins
5. POC: deployed Flow + Apex + Custom Metadata Type across 3 environments in Copado
6. Result: Copado selected; Flosum kept as fallback if Copado org-limit impact is too high
```

**Why it works:** By applying compliance constraints first, the team eliminated three of six options before investing in proof-of-concept time. This prevented the common mistake of evaluating tools on features before validating that they can even be deployed in the organization.

---

## Example 2: Startup Adopts Gearset for Speed-to-Value

**Context:** A 15-person startup with 3 Salesforce developers and 2 admins needs to move off change sets. Budget is limited, the team is comfortable with Git, and there are no regulatory compliance mandates. They use GitHub for source control and GitHub Actions for non-Salesforce CI/CD.

**Problem:** The team considered building a custom pipeline using Salesforce CLI and GitHub Actions but estimated 3-4 weeks of setup and ongoing maintenance for deployment comparison, conflict detection, and rollback capability.

**Solution:**

```text
Selection criteria applied:
1. Budget: limited but not zero → eliminate enterprise-priced tools (AutoRABIT)
2. Compliance: none → all hosting models acceptable
3. Team size: small, Git-literate → CLI-native or SaaS both work
4. Speed-to-value: most important axis → Gearset wins on onboarding time
5. POC: team deployed a complex metadata bundle in 20 minutes on first attempt
6. Backup plan: if Gearset cost scales poorly, fall back to CLI + GitHub Actions
```

**Why it works:** For teams without compliance constraints, speed-to-value is often the deciding factor. Gearset's comparison-based deployment model requires no pipeline configuration and handles metadata dependencies automatically, which removes the 3-4 week setup investment.

---

## Example 3: Large Enterprise Evaluates AutoRABIT for Consolidation

**Context:** A healthcare enterprise with 8 Salesforce orgs uses separate tools for CI/CD (custom Jenkins pipelines), static code analysis (PMD), and data migration (manual scripts). The DevOps team spends 30% of their time maintaining integrations between these tools.

**Problem:** Tool sprawl created fragile integrations that broke on every Salesforce release. The team needed a single platform that covers CI/CD, code analysis, and data migration to reduce maintenance burden.

**Solution:**

```text
Selection criteria applied:
1. Primary driver: reduce tool sprawl → favor all-in-one platforms
2. Candidates: AutoRABIT (CI/CD + CodeScan + data loader) vs Copado + separate tools
3. Compliance: HIPAA → verify AutoRABIT's compliance certifications and data handling
4. POC: migrated one org's pipeline to AutoRABIT; measured setup time and deployment accuracy
5. Result: AutoRABIT selected for 6 of 8 orgs; 2 orgs with simple needs kept on DevOps Center
```

**Why it works:** AutoRABIT's bundled CodeScan and data-migration modules eliminated three separate vendor relationships and their associated integration maintenance. The decision to keep simpler orgs on DevOps Center avoided over-provisioning.

---

## Anti-Pattern: Selecting a Tool Based on Feature Count Alone

**What practitioners do:** The team creates a feature checklist spreadsheet, scores each tool on the number of features it supports, and selects the tool with the highest total score — without weighting features by the team's actual needs.

**What goes wrong:** The selected tool has the most features but requires developer-level Git expertise that 70% of the team lacks. Admin users bypass the tool and deploy via change sets, creating an uncontrolled shadow deployment channel. Within 6 months, more deployments go through change sets than through the "selected" tool.

**Correct approach:** Weight selection criteria by the team's actual constraints. A tool that covers 60% of features but has 95% team adoption is more valuable than a tool that covers 95% of features with 40% adoption. Always include a team-usability proof-of-concept alongside the technical evaluation.
