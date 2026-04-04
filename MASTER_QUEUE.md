# MASTER_QUEUE.md — Universal Salesforce Skill Build Queue

<!--
PURPOSE:
  Single source of truth for the full Role × Domain × Cloud skill matrix.
  This file drives the expanded vision: every SF role, every cloud, every task.

VISION:
  One public repo. Every Salesforce professional (Admin, BA, Dev, Data, Architect)
  drops it into Claude, Cursor, or any AI and gets role-appropriate, task-accurate
  Salesforce guidance grounded in official docs — not training data guesses.

AGENT INSTRUCTIONS (read before doing anything):
  1. Read CLAUDE.md and AGENT_RULES.md first. This file does not override them.
  2. Find the first row with status RESEARCHED (preferred) or TODO in the queue below.
  3. Change status to IN_PROGRESS and record your agent name + ISO timestamp in the Notes column.
  4. python3 scripts/search_knowledge.py "<skill-name>" --domain <domain>
       → If has_coverage: true, the skill exists. Mark DUPLICATE and move to next.
       → If has_coverage: false, proceed.
  5. Read official sources for this domain from standards/official-salesforce-sources.md BEFORE writing anything.
  6. python3 scripts/new_skill.py <domain> <skill-name>
  7. Fill every TODO marker in every generated file with real, doc-grounded content.
       SKILL.md body must be 300+ words. Include "NOT for ..." in description.
       Triggers must be 3+ natural-language symptom phrases, 10+ chars each.
  8. python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
       Fix every ERROR before continuing. Do not use --skip-validation.
  9. Add query fixture to vector_index/query-fixtures.json.
       Run python3 scripts/search_knowledge.py "<query>" and confirm skill appears in top 3.
  10. python3 scripts/validate_repo.py → must exit 0.
  11. Mark row DONE. Commit: skill package + registry/ + vector_index/ + docs/SKILLS.md.
  12. Move to the next TODO row.

STATUS KEY:
  TODO        → Not started. Needs research before building.
  RESEARCHED  → Deep research done, notes in Notes column. Ready to build next session.
  IN_PROGRESS → Being built or researched. Do not touch — another agent is working on it.
  DONE        → Complete. validate_repo.py passes. Committed.
  DUPLICATE   → Skill already exists. Skipped.
  BLOCKED     → Stopped. Read Notes before continuing.
-->

---

## Progress Summary

| Phase | Cloud / Domain | Total Cells | Skills Planned | Skills Done | TODO |
|-------|----------------|-------------|----------------|-------------|------|
| 0 | Domain Sweeps (Cross-Cloud) | — | 120 | 55 | 65 |
| 1 | Core Platform | 5 roles | 310 | 62 | 248 |
| 2 | Sales Cloud | 5 roles | 29 | 0 | 29 |
| 3 | Service Cloud | 5 roles | 29 | 0 | 29 |
| 4 | Experience Cloud | 5 roles | 26 | 0 | 26 |
| 5 | Marketing Cloud / MCAE | 5 roles | 28 | 0 | 28 |
| 6 | Revenue Cloud (CPQ) | 5 roles | 25 | 0 | 25 |
| 7 | Field Service (FSL) | 5 roles | 24 | 0 | 24 |
| 8 | Health Cloud | 5 roles | 25 | 0 | 25 |
| 9 | Financial Services Cloud | 5 roles | 24 | 0 | 24 |
| 10 | Nonprofit Cloud (NPSP) | 5 roles | 23 | 0 | 23 |
| 11 | Commerce Cloud | 5 roles | 25 | 0 | 25 |
| 12 | Agentforce / Einstein AI | 5 roles | 22 | 0 | 22 |
| 13 | OmniStudio / Industries | 5 roles | 22 | 0 | 22 |
| 14 | CRM Analytics / Tableau | 5 roles | 24 | 0 | 24 |
| 15 | Integration (Cloud-Specific) | 5 roles | 23 | 0 | 23 |
| 16 | DevOps (Cloud-Specific) | 5 roles | 22 | 0 | 22 |
| 17 | Data Cloud | 3 roles | 13 | 0 | 13 |
| 18 | Slack Integration | — | 5 | 0 | 5 |
| 19 | Additional Industry Clouds | — | 16 | 0 | 16 |
| **Total** | | | **643** | **117** | **524** |

---

## Execution Order

Build phases sequentially. Within each phase, build roles in this order:
**Admin → BA → Dev → Data → Architect**

Reason: Admin defines the data model and configuration that Dev and Architect skills
reference. BA skills assume Admin config exists. Data skills assume Dev patterns exist.
Architect skills synthesize all of the above.

Phase 0 (domain sweeps) builds before all cloud phases because cross-cloud skills
are prerequisites for cloud-specific skills.

---

## Phase 0 — Domain Sweeps (Cross-Cloud)

These skills apply across all clouds. Build before cloud-specific phases.

### DevOps Domain

> Domain folder: `devops`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | scratch-org-management | Creating, configuring, and managing scratch orgs: definition files, limits, expiration, shape snapshots. NOT for SFDX CLI basics (use sf-cli-and-sfdx-essentials). | Agent 2026-04-04T00:00:00Z |
| DONE | sandbox-refresh-and-templates | Sandbox refresh cycles, sandbox templates, post-refresh automation (SandboxPostCopy interface), data handling during refresh. NOT for sandbox type selection (use sandbox-strategy). | Agent 2026-04-04T00:00:00Z |
| DONE | change-set-deployment | Creating, uploading, and deploying change sets: component dependencies, inbound/outbound limitations, troubleshooting. NOT for SFDX-based deployments. | Agent 2026-04-04T10:00:00Z |
| DONE | unlocked-package-development | Designing, creating, and versioning unlocked packages: package dependencies, namespace management, installation. NOT for 2GP managed packages. | Agent 2026-04-04T06:00:00Z |
| DONE | second-generation-managed-packages | 2GP package development: versioning, patch orgs, ISV partner considerations, AppExchange listing. NOT for unlocked packages. | Agent 2026-04-04T08:00:00Z |
| DONE | devops-center-pipeline | DevOps Center setup: creating pipelines, work items, bundling changes, conflict resolution, release tracking. NOT for CLI-based deployment. | Agent 2026-04-04T10:30:00Z |
| DONE | github-actions-for-salesforce | CI/CD with GitHub Actions for Salesforce: SFDX auth, test runs, deployment steps, secret management, reusable workflows. NOT for other CI tools. | Agent 2026-04-04T12:00:00Z |
| DONE | bitbucket-pipelines-for-salesforce | CI/CD with Bitbucket Pipelines: pipe configuration, SFDX integration, deployment automation. NOT for GitHub Actions. | Agent 2026-04-04T00:00:00Z |
| DONE | gitlab-ci-for-salesforce | CI/CD with GitLab CI for Salesforce: runner configuration, deployment jobs, SFDX integration. NOT for other CI tools. | Agent 2026-04-04T00:00:00Z |
| DONE | environment-strategy | Planning org environments: scratch orgs vs sandboxes vs production, branching strategy alignment, environment matrix. NOT for sandbox types (use sandbox-strategy). | Agent 2026-04-04T00:00:00Z |
| DONE | source-tracking-and-conflict-resolution | SFDX source tracking: pull/push conflicts, force overwrite decisions, tracking files, conflict markers. NOT for Git merge conflicts. | Researched 2026-04-04. Sources: [developer.salesforce.com sfdx_dev — Resolve Conflicts, Track Changes, Enable Source Tracking in Sandboxes]. Key: conflicts via SourceMember RevisionCounter in .sf/orgs/<id>/maxRevision.json; resolve via --forceoverwrite or --ignore-conflicts; sandbox tracking requires per-sandbox opt-in; tracking corruption recovered by deleting local tracking files and re-retrieving. |
| RESEARCHED | salesforce-code-analyzer | Salesforce Code Analyzer (Scanner CLI): PMD rules, ESLint for LWC, Graph Engine, custom rules, CI integration. NOT for manual code review. | Researched 2026-04-04. Sources: [developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide v5 — overview, PMD/ESLint/RetireJS/Regex/Graph Engine, migration from v4]. Key: v5 GA (replaces v4 retired Aug 2025); command is sf code-analyzer run with code-analyzer.yml config; --severity-threshold for CI gates; --rule-selector AppExchange for managed pkg security review; Graph Engine performs dataflow/taint analysis. |
| RESEARCHED | release-management | Release planning: version numbering, rollback strategy, release notes generation, go/no-go criteria, release calendar. NOT for deployment mechanics. | Researched 2026-04-04. Sources: [developer.salesforce.com 2GP version numbering, help.salesforce.com sandbox preview, DevOps Center overview, Trailhead Advanced Release Readiness]. Key: 3 seasonal platform releases/year; sandbox preview 4-6 weeks before production; org-based projects need custom versioning convention (no native version); 2GP uses Major.Minor.Patch.Build; rollback requires pre-planned retrieve+redeploy (no undo button). |
| RESEARCHED | permission-set-deployment-ordering | Permission set and profile deployment dependencies: assignment during deployment, ordering, cross-reference handling. NOT for permission set design (use permission-set-architecture). | Researched 2026-04-04. Sources: [Metadata API Dev Guide — PermissionSet, PermissionSetGroup, Special Behavior in Deployments; help.salesforce.com cross-reference id error]. Key: API v40+ full-replace (not merge) — absent permissions silently wiped; referenced objects/fields must exist before PS lands; PSGs require constituent PSets deployed first; known bug: ConnectedApp in both PS and PSG in same batch causes cross-reference error. |
| RESEARCHED | data-seeding-for-testing | Test data creation for sandboxes and scratch orgs: data plans, record factories, data import scripts. NOT for production data migration. | Researched 2026-04-04. Sources: [developer.salesforce.com sfdx_dev Test Data + Snapshots; Apex Dev Guide SeeAllData; CumulusCI docs; Snowfakery docs]. Key: 3 seeding layers — Apex @testSetup (unit tests), sf data import tree plan JSON (scratch/dev sandbox, 200MB cap), CumulusCI datasets+Snowfakery (partial/full sandbox); @isTest(SeeAllData=true) incompatible with @testSetup; Scratch Org Snapshots capture data+metadata but consume allocations. |
| RESEARCHED | destructive-changes-deployment | Managing destructiveChanges.xml: pre vs post destroy manifests, safe deletion patterns, dependency handling. NOT for package.xml basics. | Researched 2026-04-04. Sources: [Metadata API Dev Guide — Deleting Components; Salesforce CLI project deploy start; Ant Migration Tool Guide destructive changes]. Key: 3 manifest variants — Pre.xml (deletions before additions), plain destructiveChanges.xml (same), Post.xml (after additions — required when deleted component still referenced); sf CLI --pre-destructive-changes/--post-destructive-changes flags; undeletable via API: Record Types, Picklist values, active Flow versions. |
| RESEARCHED | continuous-integration-testing | Running Apex tests in CI: code coverage gates, parallel test execution, test result parsing, selective test runs. NOT for writing test classes (use test-class-standards). | Researched 2026-04-04. Sources: [SF CLI Command Ref apex commands; Apex Dev Guide code coverage, testing best practices; Metadata API deploy subset tests]. Key: RunLocalTests=75% org-wide, RunSpecifiedTests=75% per-class/trigger in package (stricter); --code-coverage collects but does not enforce threshold; --result-format junit for CI report ingestion; known bug: --code-coverage+--wait returns 0% (poll with sf apex get test instead); @isTest(isParallel=true) opts class into parallel. |
| RESEARCHED | org-shape-and-scratch-definition | Org shape snapshots, scratch org definition file features: settings, edition selection, feature flags, org preferences. NOT for scratch org CLI commands (use scratch-org-management). | Researched 2026-04-04. Sources: [developer.salesforce.com sfdx_dev — scratch org def file, features, settings, org shape]. Key: `orgPreferences` deprecated since Winter '20 — use `settings` instead; Org Shape (Enterprise+ Dev Hub only) excludes some features (MultiCurrency, PersonAccounts) that must still be declared explicitly; `--release` flag pins preview vs. current release; distinct from scratch-org-management which covers lifecycle/CI — this skill covers schema depth of the def file itself. |
| RESEARCHED | git-branching-for-salesforce | Branching models for SF projects: feature branches, release branches, org-based vs artifact-based development alignment. NOT for Git basics. | Researched 2026-04-04. Sources: [developer.salesforce.com sfdx_dev — branches/packaging, architect.salesforce.com Well-Architected]. Key: package version ancestry is linear — parallel branches cannot produce separate 2GP version lineages; org-based model=changeset/deploy, artifact-based=unlocked/2GP packages; Salesforce DX docs name trunk-based and GitFlow as the two dominant models; non-duplicate from environment-strategy (which covers env topology) and unlocked-package-development (which covers version lineage). |
| RESEARCHED | post-deployment-validation | Post-deploy smoke tests, validation deploy vs quick deploy, monitoring after deployment, rollback triggers. NOT for pre-deployment planning. | Researched 2026-04-04. Sources: [Metadata API Dev Guide — deployRecentValidation SOAP+REST, deploy monitoring; SF CLI ref — project deploy validate/quick/resume]. Key: validation deploy = checkOnly:true, earns qualified validation ID; quick deploy = POST to validatedDeployRequestId, skips tests, valid for 10 days, returns NEW deploy ID; rollback = re-deploy prior version (no native undo); RunSpecifiedTests requires 75% per-class in package (stricter than RunLocalTests); Deployment Status page shows per-test drill-down during/after deploy. |
| RESEARCHED | vscode-salesforce-extensions | VS Code for Salesforce: extension pack setup, Apex LSP, deploying from editor, code completion, debugging integration. NOT for CLI commands. | Researched 2026-04-04. Sources: [Salesforce Extensions for VS Code docs — Installation, Apex Language Server, Deploy on Save, Development Models; developer.salesforce.com]. Key: Apex LSP requires JDK 21 (recommended) or 11/17 and activates only when sfdx-project.json is the top-level folder; deploy-on-save differs by org type — source-tracked orgs trigger project:deploy:start, non-tracked orgs trigger force:source:deploy; two debugger options — Apex Interactive Debugger (live, requires license) vs Apex Replay Debugger (replays captured debug log, no license). |
| TODO | migration-from-change-sets-to-sfdx | Transitioning from change set deployment to SFDX source-driven development: org conversion, team onboarding. NOT for greenfield SFDX setup. | |
| RESEARCHED | deployment-error-troubleshooting | Common deployment errors: dependency resolution, component validation failures, API version mismatches, test failures. NOT for Apex runtime errors. | Researched 2026-04-04. Sources: [Metadata API Dev Guide — DeployMessage/DeployDetails; help.salesforce.com Troubleshoot Deployment Failures; help.salesforce.com Dependent class is invalid; Salesforce CLI Troubleshooting Guide]. Key: DeployMessage.componentFailures is the canonical error surface (not top-level errorStatusCode); dependency errors from missing transitive dependencies or pre-broken classes in target; rollbackOnError defaults false for sandboxes (partial deploy risk); RunSpecifiedTests uses per-class 75% (stricter than RunLocalTests org-wide 75%); API version mismatch shows as UNSUPPORTED_API_VERSION or metadata XML shape differences. |
| TODO | salesforce-dx-project-structure | sfdx-project.json configuration: source paths, package directories, namespace, API version, plugin configuration. NOT for CLI commands. | |
| TODO | scratch-org-pools | Automating scratch org creation pools for CI: CumulusCI pool management, prebuilt orgs, parallel test execution. NOT for single org creation. | |
| TODO | metadata-coverage-and-dependencies | Tracking metadata dependencies: impact analysis before deployment, dependency graphs, metadata coverage report. NOT for package.xml generation. | |
| TODO | automated-regression-testing | End-to-end testing with Provar/Selenium: regression suites for Salesforce, test automation strategy, UI test patterns. NOT for Apex unit testing. | |
| TODO | rollback-and-hotfix-strategy | Rollback planning: hotfix deployment procedures, emergency change processes, safe rollback patterns. NOT for release planning. | |
| TODO | salesforce-devops-tooling-selection | Comparing DevOps tools (Gearset, Copado, Flosum, AutoRABIT, native SFDX): selection criteria, feature comparison. NOT for implementing any specific tool. | |
| TODO | pre-deployment-checklist | Pre-deploy validation steps: metadata review, test execution requirements, backup procedures, dependency verification. NOT for post-deployment. | |
| TODO | go-live-cutover-planning | Go-live cutover planning: deployment sequencing, code freeze procedures, mock deployments, go/no-go checklists, rollback triggers, hypercare support model, smoke testing. NOT for deployment mechanics (use post-deployment-validation). | |
| TODO | performance-testing-salesforce | Performance testing for Salesforce: load testing approaches, concurrent user simulation, API throughput benchmarks, LWC rendering performance, governor limit headroom analysis. NOT for Apex code optimization (use apex-cpu-and-heap-optimization). | |
| TODO | multi-package-development | Managing multiple packages in one project: inter-package dependencies, deployment ordering, namespace strategy. NOT for single package development. | |
| TODO | api-version-management | Managing API versions across metadata: deprecation tracking, upgrade planning, version alignment across components. NOT for REST API usage. | |
| TODO | org-cleanup-and-technical-debt | Identifying unused metadata: removing deprecated components, org health maintenance, dead code detection. NOT for code-level refactoring. | |
| TODO | copado-essentials | Copado deployment pipelines: user stories, branch management, conflict resolution, promotion paths. NOT for native SFDX CLI workflows. | |
| TODO | cumulusci-automation | CumulusCI for Salesforce development: task and flow configuration, robot framework integration, CI automation. NOT for native SFDX. | |
| TODO | metadata-api-coverage-gaps | Metadata types not supported by Metadata API or SFDX: manual migration workarounds, known coverage gaps by release, tracking unsupported components. NOT for Metadata API usage (use metadata-api-and-package-xml). | |
| TODO | environment-specific-value-injection | Managing environment-specific values across orgs: Named Credential per-env config, Custom Metadata for env settings, post-deploy scripts, CI variable substitution. NOT for sandbox refresh (use sandbox-refresh-and-templates). | |
| TODO | sandbox-data-isolation-gotchas | Sandbox data pitfalls: production data leaking into sandbox emails, scheduled jobs running in sandboxes, integration endpoints hitting production, post-copy cleanup. NOT for sandbox strategy (use sandbox-strategy). | |

### Security Domain

> Domain folder: `security`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | platform-encryption | Salesforce Shield Platform Encryption: key management, deterministic vs probabilistic, field-level encryption, encrypted search. NOT for TLS/transport encryption. | Agent 2026-04-04T00:00:00Z |
| DONE | event-monitoring | Shield Event Monitoring: event log types, downloading logs, real-time event monitoring, threat detection policies. NOT for debug logs (use debug-logs-and-developer-console). | Agent 2026-04-04T00:00:00Z |
| DONE | field-audit-trail | Salesforce Shield Field Audit Trail: configuration, retention policies, querying archived field data, compliance requirements. NOT for field history tracking (use field-history-tracking). | Agent 2026-04-04T06:00:00Z |
| DONE | security-health-check | Running and interpreting Security Health Check scores: remediating findings, custom baselines, periodic review. NOT for org hardening implementation. | Agent 2026-04-04T10:00:00Z |
| DONE | transaction-security-policies | Transaction Security policies: condition builder, enhanced policies, enforcement actions, real-time monitoring. NOT for Event Monitoring log analysis. | Agent 2026-04-04T08:00:00Z |
| DONE | login-forensics | Login history analysis: identity verification, session management, login flow customization, suspicious login detection. NOT for MFA setup (use org-setup-and-configuration). | Agent 2026-04-04T10:30:00Z |
| DONE | network-security-and-trusted-ips | Trusted IP ranges, network access policies, CSP trusted sites, CORS configuration, My Domain security. NOT for org-wide session settings. | Agent 2026-04-04T12:00:00Z |
| DONE | sandbox-data-masking | Data masking in sandboxes: Salesforce Data Mask product, field-level masking, compliance-driven policies. NOT for sandbox refresh mechanics. | Agent 2026-04-04T00:00:00Z |
| DONE | api-security-and-rate-limiting | API rate limits, OAuth scope restriction, Connected App IP restrictions, API session policies, API usage monitoring. NOT for OAuth flows (use oauth-flows-and-connected-apps). | Agent 2026-04-04T00:00:00Z |
| DONE | certificate-and-key-management | Managing certificates in Salesforce: mutual TLS, certificate rotation, keystore management, self-signed vs CA-signed. NOT for Named Credential configuration. | Agent 2026-04-04T00:00:00Z |
| DONE | data-classification-labels | Data sensitivity classification: compliance categorization, field-level classification, data access policies, labeling. NOT for data masking. | Researched 2026-04-04. Sources: [help.salesforce.com — data_classification_metadata_fields, data_classification_set_up, einstein_data_detect; developer.salesforce.com Tooling API FieldDefinition]. Key: 4 classification attributes on every field (SecurityClassification, ComplianceGroup, BusinessOwnerId, BusinessStatus); Metadata API deployable since API v46.0; queryable via Tooling API FieldDefinition; classification is metadata-only — no runtime enforcement; Einstein Data Detect (Shield) auto-populates recommendations; ComplianceGroup not updatable via Tooling API (known gap); distinct from data-quality-and-governance which mentions GDPR erasure. |
| RESEARCHED | gdpr-data-privacy | Right to erasure implementation: data subject requests, consent management, data retention policies, individual rights. NOT for general data quality. | Researched 2026-04-04. Sources: [help.salesforce.com — Individual object, Privacy Center, Right to Be Forgotten, consent management objects/fields]. Key: Individual sObject (API v42) links to Contact/Lead/PersonAccount via IndividualId; ShouldForget=true is a flag only — no automated deletion; Privacy Center (separately licensed) provides RTBF policy engine and data portability; native consent model uses ContactPointTypeConsent + ContactPointConsent objects; no automated retention enforcement without Privacy Center or custom Batch Apex; anonymization (tokenization) recommended over hard delete for referential integrity. |
| RESEARCHED | guest-user-security | Guest user profile hardening: unauthenticated access controls, object permissions, Apex sharing, SOQL exposure. NOT for Experience Cloud site creation. | Researched 2026-04-04. Sources: [developer.salesforce.com communities_dev — guest user guidelines, secure sites; help.salesforce.com — secure_guest_user_sharing, guest_profile_best_practices; Apex Dev Guide — sharing/enforcement; securityImplGuide]. Key: guest user always runs system mode — cannot be changed; Spring '21 enforced OWD-based access (mandatory, breaking change); Apex without sharing + guest caller = SOQL exposes all records; mitigation: WITH USER_MODE in SOQL or class-level `with sharing`; guest sharing rules grant Read Only only; permission sets assignable to guest users since Spring '22; no duplicate skill exists. |
| RESEARCHED | experience-cloud-security | External user security: sharing sets, external org-wide defaults, community security best practices, portal security. NOT for internal sharing model. | Researched 2026-04-04. Sources: [developer.salesforce.com securityImplGuide — External OWD, Sharing Sets; help.salesforce.com communities_dev — Secure Sites Authenticated and Guest Users; help.salesforce.com Securely Share Experience Cloud Sites]. Key: External OWD is independent of internal OWD and must be equal or more restrictive; Sharing Sets grant access via lookup field relationship (not role hierarchy), Guest users excluded; Secure Guest User Record Access toggle forces all-private OWD for guests; Share Groups allow portal users to share among themselves; CSP/clickjack/LWS are site-level toggles. |
| RESEARCHED | connected-app-security-policies | IP relaxation, session policies, OAuth client assertion, PKCE, rotating client secrets, high-assurance sessions. NOT for basic Connected App setup. | Researched 2026-04-04. Sources: [help.salesforce.com — Manage OAuth Access Policies, IP Relaxation and Continuous IP, Session Policies, JWT Bearer Flow, Require High-Assurance Session, View and Rotate Consumer Key/Secret; Metadata API ConnectedApp; developer.salesforce.com REST API OAuth guide]. Key: IP Relaxation has 3 values with distinct security postures (Enforce/Relax with 2FA/Relax); PKCE requires disabling Require Secret for Web Server Flow; JWT Bearer clock drift of 60s causes invalid_grant; High-assurance has 3 states (default/Switch/Blocked); client secret rotation has NO grace period — staged ECA model (v65) promotes instantly. |
| TODO | shield-encryption-key-management | Tenant secrets, key rotation, key derivation, bring-your-own-key (BYOK), cache-only keys, key lifecycle. NOT for field-level encryption decisions. | |
| TODO | threat-detection-patterns | Real-time event monitoring rules, anomaly detection, session hijacking prevention, credential stuffing detection. NOT for Event Monitoring log downloads. | |
| TODO | xss-and-injection-prevention | XSS prevention in Visualforce and Apex: output encoding, Locker Service, CRLF injection, open redirect prevention. NOT for Apex CRUD/FLS enforcement. | |
| TODO | secure-coding-review-checklist | Security review checklist for AppExchange: ISV security requirements, Checkmarx patterns, common vulnerabilities. NOT for implementing fixes. | |
| TODO | recaptcha-and-bot-prevention | Bot prevention in Salesforce: Google reCAPTCHA integration for Experience Cloud, form spam prevention, rate limiting for guest submissions, CAPTCHA configuration. NOT for API rate limiting (use api-security-and-rate-limiting). | |
| TODO | session-management-and-timeout | Session security: timeout configuration by user type, concurrent session limits, session-level IP locking, logout messaging, inactivity handling, CMS ARC-AMPE session controls. NOT for SSO authentication (use oauth-flows-and-connected-apps). | |
| TODO | ip-range-and-login-flow-strategy | Login flow customization: IP-range-based login flows, conditional MFA, geo-restricted access, login flow Apex handlers, custom login pages per community. NOT for basic MFA setup (use org-setup-and-configuration). | |
| TODO | ferpa-compliance-in-salesforce | FERPA compliance patterns in Salesforce: student data protection, directory information controls, educational records handling, consent management for education orgs. NOT for HIPAA (use hipaa-compliance-architecture). | |

### Agentforce / Einstein AI Domain

> Domain folder: `agentforce`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | agentforce-agent-creation | Creating Agentforce agents end-to-end: agent definition, channel assignment, instructions, deployment, lifecycle. NOT for topic design (use agent-topic-design). | Agent 2026-04-04T00:00:00Z |
| DONE | einstein-trust-layer | Trust Layer configuration: data masking, zero data retention, toxicity detection, audit trail, grounding controls. NOT for agent action development. | Agent 2026-04-04T00:00:00Z |
| DONE | prompt-builder-templates | Prompt templates in Prompt Builder: flex templates, field merge, grounding with flows, testing prompts, template sharing. NOT for agent topic instructions. | Agent 2026-04-04T10:00:00Z |
| DONE | einstein-copilot-for-sales | Sales-specific AI: opportunity scoring, activity capture AI, email generation, pipeline inspection AI insights. NOT for core Agentforce setup. | Agent 2026-04-04T06:00:00Z |
| DONE | einstein-copilot-for-service | Service-specific AI: case classification, article recommendations, reply suggestions, work summaries, auto-routing. NOT for core Agentforce setup. | Agent 2026-04-04T10:30:00Z |
| DONE | model-builder-and-byollm | Model Builder configuration: bringing your own LLM, model selection, API configuration, cost and performance tradeoffs. NOT for Trust Layer. | Agent 2026-04-04T12:00:00Z |
| DONE | rag-patterns-in-salesforce | Retrieval Augmented Generation using Data Cloud: vector search, knowledge grounding, prompt grounding strategies. NOT for Data Cloud data model setup. | Agent 2026-04-04T00:00:00Z |
| DONE | agent-testing-and-evaluation | Testing agents: conversation testing, topic coverage, utterance testing, evaluation metrics, regression testing patterns. NOT for agent creation. | Agent 2026-04-04T00:00:00Z |
| DONE | agent-channel-deployment | Deploying agents to channels: web, Slack, API, mobile, embedded service, multi-channel coordination. NOT for agent logic design. | Agent 2026-04-04T00:00:00Z |
| DONE | einstein-bots-to-agentforce-migration | Migrating from legacy Einstein Bots to Agentforce: feature mapping, conversation design translation, cutover plan. NOT for new Agentforce setup. | Researched 2026-04-04. Sources: [help.salesforce.com — bots_service_asa_compare, bots_service_create_agent_from_bot, bots_service_asa_how_it_works; developer.salesforce.com Agentforce dev guide; architect.salesforce.com agentic-patterns]. Key: Beta "Create AI Agent from Bot" tool generates draft Topics from Enhanced Bots only — not lossless; dialog→Topic, step→Action, intent/utterances→topic instructions (LLM-semantic, no utterance training needed); Legacy Chat retiring Feb 14 2026 (critical deadline); hybrid bot+Agentforce pattern endorsed; context passes via MessagingSession custom fields + Flow before handoff; GenAiPlannerBundle on BotVersion makes it an Agentforce agent. |
| DUPLICATE | agentforce-data-cloud-grounding | Grounding agents with Data Cloud: data streams for grounding, DMOs, vector embeddings, search index configuration. NOT for standalone Data Cloud setup. | Covered by skills/agentforce/rag-patterns-in-salesforce — Data Streams, DMO field mapping, chunking, search index creation, retriever config, Data Kit packaging all present. |
| RESEARCHED | custom-agent-actions-apex | Building custom Apex invocable actions for Agentforce: input/output schema, error handling, security context. NOT for standard agent actions (use agent-actions). | Researched 2026-04-04. Sources: [developer.salesforce.com Agentforce dev guide — InvocableMethod for agents; Apex Dev Guide — InvocableMethod, callout modifier, Managed Apex for Agentforce; developer.salesforce.com blog — Apex Actions Best Practices]. Key: @InvocableMethod label/description and @InvocableVariable label/description on every input/output field are read by Atlas Reasoning Engine at runtime (poor descriptions degrade agent reasoning); Employee Agents run as logged-in user, Service Agents as designated agent user (security context differs); callout=true modifier required for HTTP callouts; bulk-safe List-in/List-out wrapper still needed; return structured DTO for success/failure (not raw exceptions). |
| RESEARCHED | agentforce-guardrails | Agent guardrails: topic classification boundaries, fallback handling, escalation rules, restricted topics, abuse prevention. NOT for Trust Layer. | Researched 2026-04-04. Sources: [help.salesforce.com — agent guardrails, topic instructions best practices, Escalation topic, action/topic filters; developer.salesforce.com Agentforce dev guide; architect.salesforce.com agentic-patterns]. Key: Guardrails = topic Scope field + agent-level system instructions + topic/action filters + Instruction Adherence monitoring; Escalation topic is a standard system construct requiring Omni-Channel; Classification Description (not Scope) drives LLM topic selection; over-use of must/never/always in instructions causes reasoning loops; fallback when no topic matches depends on agent-level instructions. |
| TODO | agentforce-observability | Agentforce session and message observability: extracting conversation data from Data Cloud, agent performance analytics, trace analysis, session query patterns, monitoring agent effectiveness. NOT for Einstein Trust Layer (use einstein-trust-layer). | |
| TODO | agentforce-persona-design | Agentforce persona design: tone and behavior encoding, persona templates, brand voice alignment, persona testing, multi-persona strategies, conversation style guidelines. NOT for agent topic design (use agent-topic-design). | |
| TODO | agent-script-dsl | Agent Script DSL (.agent files): syntax patterns, finite state machine architecture, metadata lifecycle, LSP validation, declarative agent behavior definitions, script testing. NOT for Apex-based agent actions (use custom-agent-actions-apex). | |
| TODO | sf-to-llm-data-pipelines | Preparing and exporting Salesforce data for LLM consumption: data extraction patterns, chunking strategies, embedding pipelines, knowledge base preparation for external AI. NOT for Agentforce grounding (use agentforce-data-cloud-grounding). | |
| DONE | einstein-prediction-builder | Einstein Prediction Builder: custom predictions, field selection, model training, scoring records, embedding predictions. NOT for Einstein Discovery. | Agent 2026-04-04T08:00:00Z |
| TODO | einstein-next-best-action | Next Best Action: strategies, recommendations, action flows, display in Lightning, recommendation filtering. NOT for Prediction Builder. | |

### OmniStudio Domain (Gaps)

> Domain folder: `omnistudio` | Existing skills: dataraptor-patterns, integration-procedures, omniscript-design-patterns, omnistudio-security

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | flexcard-design-patterns | FlexCard creation: data sources, actions, templates, state management, flyout configuration, conditional visibility. NOT for OmniScript design (use omniscript-design-patterns). | Agent 2026-04-04T00:00:00Z |
| DONE | calculation-procedures | Calculation Procedure and Calculation Matrix setup: step types, matrix versioning, lookup tables, pricing calculations. NOT for DataRaptor transforms. | Agent 2026-04-04T00:00:00Z |
| DONE | omnistudio-debugging | OmniStudio debugging: console debugging, previewing, breakpoints, DataRaptor testing, error tracing, log analysis. NOT for Apex debugging. | Agent 2026-04-04T10:00:00Z |
| DONE | omnistudio-deployment-datapacks | DataPack export, import, version control, migration between orgs, CI/CD for OmniStudio components. NOT for SFDX deployment. | Agent 2026-04-04T12:00:00Z |
| DONE | omnistudio-performance | OmniStudio performance optimization: lazy loading, remote actions, caching, reducing API calls in OmniScripts. NOT for LWC performance. | Agent 2026-04-04T00:00:00Z |
| DONE | industries-cpq-vs-salesforce-cpq | Comparing Industries CPQ (Vlocity) with Salesforce CPQ: feature parity, migration paths, decision criteria. NOT for implementing either CPQ. | Agent 2026-04-04T00:00:00Z |
| DONE | omnistudio-lwc-integration | Embedding OmniScripts in LWC, calling LWC from OmniScripts, custom LWC elements in OmniStudio context. NOT for standalone LWC development. | Agent 2026-04-04T00:00:00Z |
| TODO | vlocity-to-native-omnistudio-migration | Migrating from Vlocity managed package to native OmniStudio: component mapping, data conversion, testing. NOT for new OmniStudio setup. | |
| TODO | omniscript-versioning | OmniScript version management: activation, deactivation, testing versions, rollback, version comparison. NOT for deployment. | |
| TODO | omnistudio-custom-lwc-elements | Creating custom LWC elements for OmniScripts: override patterns, event handling, custom validation in OmniStudio. NOT for standalone LWC. | |
| TODO | dataraptor-load-and-extract | DataRaptor Extract and Load patterns: multi-object operations, error handling, bulk operations, output mapping. NOT for DataRaptor Transform (use dataraptor-patterns). | |
| TODO | omnistudio-remote-actions | Configuring remote actions in OmniStudio: Apex vs Integration Procedure actions, response mapping, error handling. NOT for Integration Procedures themselves. | |
| DONE | business-rules-engine | Business Rules Engine (BRE) design: decision tables, rule matrices, eligibility determination, versioning, testing rules, runtime execution. NOT for Flow decision elements (use flow/* skills). | |
| TODO | document-generation-omnistudio | OmniStudio Document Generation: template design, merge fields, conditional sections, PDF output, batch generation, dynamic content. NOT for quote PDF templates (use cpq-quote-templates). | |

### Integration Domain (Gaps)

> Domain folder: `integration` | Existing skills: graphql-api-patterns, oauth-flows-and-connected-apps, salesforce-connect-external-objects

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | rest-api-patterns | Salesforce REST API CRUD operations: query endpoint, composite resources, versioning, error handling, pagination. NOT for GraphQL API (use graphql-api-patterns). | Agent 2026-04-04T00:00:00Z |
| DONE | soap-api-patterns | SOAP API usage: enterprise vs partner WSDL, when to use SOAP over REST, login and session management. NOT for REST API. | Agent 2026-04-04T00:00:00Z |
| DONE | streaming-api-and-pushtopic | Streaming API setup: PushTopic events, Generic Streaming, CometD client setup, replay, channel limits. NOT for Platform Events (use platform-events-apex). | Agent 2026-04-04T12:00:00Z |
| DONE | platform-events-integration | Platform Events for integration: publish from external systems, subscribe externally, replay ID handling, high-volume events. NOT for Apex-only event patterns (use platform-events-apex). | Agent 2026-04-04T00:00:00Z |
| DONE | change-data-capture-integration | CDC setup for integration: change event channels, external subscription, replay, entity selection, subscriber management. NOT for Apex CDC triggers. | Agent 2026-04-04T00:00:00Z |
| DONE | bulk-api-patterns | Bulk API 2.0 job lifecycle: serial vs parallel, ingest and query jobs, monitoring, failed records, large data volumes. NOT for Data Loader UI. | Agent 2026-04-04T00:00:00Z |
| DONE | composite-api-patterns | Composite API requests: sObject Tree, batch operations, subrequest limits, dependency management. NOT for single REST API calls. | Agent 2026-04-04T00:00:00Z |
| TODO | outbound-messages-and-callbacks | Workflow outbound messages: SOAP endpoint requirements, retry behavior, acknowledgment, monitoring delivery. NOT for Platform Events. | |
| TODO | external-services-openapi | External Services registration: OpenAPI spec import, invocable actions in Flow, parameter mapping, error handling. NOT for Apex callouts. | |
| TODO | mulesoft-salesforce-connector | MuleSoft Anypoint Salesforce connector: watermark pattern, batch processing, error handling, transformation. NOT for native Salesforce APIs. | |
| DONE | event-driven-architecture-patterns | Choosing between Platform Events, CDC, Streaming API, and outbound messages: decision matrix, architecture patterns. NOT for implementing any single pattern. | |
| TODO | webhook-inbound-patterns | Receiving webhooks in Salesforce via Apex REST endpoints: site.com routing, authentication, idempotency, error handling. NOT for outbound callouts. | |
| DONE | named-credentials-setup | Named Credentials configuration: per-user vs per-org, legacy vs enhanced, external credentials, principal types. NOT for callout code patterns. | Agent 2026-04-04T08:00:00Z |
| TODO | callout-limits-and-async-patterns | Callout governor limits: continuation pattern, queueable callouts, async callout chains, timeout handling. NOT for HTTP implementation details. | |
| TODO | api-led-connectivity | API-led connectivity pattern: system/process/experience API layers, API design principles for Salesforce. NOT for MuleSoft product features. | |
| TODO | file-and-document-integration | Document management integration: file upload patterns, virus scanning API, external document storage (EDM/SharePoint), file size validation, async file processing. NOT for Salesforce Files administration. | |
| TODO | stub-and-mock-testing-patterns | Integration stub testing: mock endpoints for sandbox environments, HttpCalloutMock in Apex, stub response configuration, test isolation for callouts, partner connectivity testing. NOT for Apex unit testing patterns (use test-class-standards). | |
| TODO | api-error-handling-design | API error response design: HTTP status code strategy, error payload structure, retry-safe error codes, client-side error parsing, timeout handling, circuit breaker patterns. NOT for Apex exception handling. | |
| TODO | retry-and-backoff-patterns | Integration retry strategies: exponential backoff, jitter, retry budget, idempotency keys, dead-letter queues, circuit breaker implementation in Apex callouts. NOT for Apex async retry (use apex-queueable-patterns). | |
| TODO | sis-integration-patterns | Student Information System integration with Salesforce: enrollment sync, transcript data, financial aid, advisor assignment, EDA/Education Cloud data mapping. NOT for generic integration patterns. | |

---

## Phase 1 — Core Platform (Foundation)

Core Platform skills apply across all clouds. Build these first.
Every skill here should work regardless of which Salesforce cloud the org has licensed.

### Core Platform × Admin Role

> Domain folder: `admin` | Official sources: Salesforce Help, Admin Trailhead, Admin Guide

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | custom-field-creation | How to create any field type on any object: type selection decision tree, naming, FLS, page layout placement, deployment. NOT for formula field logic (use formula-fields) or object design decisions. | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | object-creation-and-design | How to create a custom object: naming, API name, features (activities, chatter, history tracking), sharing model selection, tab creation. NOT for field design (use custom-field-creation). | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | picklist-and-value-sets | Global value sets vs object-local picklists, controlling and dependent fields, picklist value management, replacing picklist values in data. NOT for formula fields that reference picklists. | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | user-management | Creating, deactivating, and freezing users; assigning licenses, roles, and profiles; login hours and IP restrictions; delegated administration. NOT for permission sets (use permission-set-architecture). | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | org-setup-and-configuration | MFA enforcement, session settings, login policies, password policies, trusted IP ranges, My Domain, CSP settings. NOT for user-level security (use user-management or permission-sets-vs-profiles). | Reset — agent built but push failed |
| DONE | app-and-tab-configuration | Creating Lightning apps, configuring navigation items, adding tabs for custom objects, utility bar, app visibility by profile. NOT for Experience Cloud apps. | |
| DONE | global-actions-and-quick-actions | Object-specific quick actions vs global actions, action layouts, pre-filling fields, adding actions to page layouts and mobile. NOT for Flow-triggered actions. | |
| DONE | assignment-rules | Lead assignment rules, case assignment rules, rule entry criteria, queue assignment, round-robin patterns using Apex. NOT for approval process routing (use approval-processes). | |
| DONE | escalation-rules | Case escalation rules, time-based escalation, business hours configuration, escalation actions. NOT for assignment rules or approval processes. | |
| DONE | data-skew-and-sharing-performance | Recognizing data skew (account skew, ownership skew), impact on sharing recalculation, mitigation strategies. NOT for sharing model design (use sharing-and-visibility). | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | enterprise-territory-management | Territory hierarchies, territory types, assignment rules, territory models, activation, forecast by territory. NOT for role hierarchy (use sharing-and-visibility). | Agent 2026-04-04T00:00:00Z |
| DONE | custom-permissions | Creating and checking custom permissions: permission set integration, using in validation rules, Apex, and Flow. NOT for permission sets (use permission-set-architecture). | Agent 2026-04-04T06:00:00Z |
| DONE | delegated-administration | Delegated admin setup: group membership management, custom object admin delegation, limitations, use cases. NOT for user management (use user-management). | Agent 2026-04-04T12:00:00Z |
| DONE | dynamic-forms-and-actions | Dynamic Forms on Lightning record pages: field sections, visibility rules, dynamic actions, migration from page layouts. NOT for page layout design (use record-types-and-page-layouts). | Agent 2026-04-04T00:00:00Z |
| DONE | path-and-guidance | Path setup on opportunity and other objects: guidance steps, key fields, celebration confetti, path customization. NOT for sales process configuration. | Agent 2026-04-04T00:00:00Z |
| DONE | queues-and-public-groups | Queue creation, queue membership, case/lead queues, public groups, using groups in sharing rules and assignment. NOT for assignment rules (use assignment-rules). | Agent 2026-04-04T00:00:00Z |
| DONE | custom-metadata-types-and-settings | Custom Metadata Types vs Custom Settings: when to use each, hierarchical vs list, deployment behavior, accessing from Apex and Flow. NOT for custom objects (use object-creation-and-design). | |
| TODO | reports-and-dashboards-fundamentals | Standard reports and dashboards: report types, filters, grouping, chart types, dashboard components, dynamic dashboards, subscriptions, folders. NOT for CRM Analytics (use crm-analytics-* skills). | |
| TODO | email-templates-and-alerts | Email templates: Classic vs Lightning templates, merge fields, Visualforce email templates, email alerts in automation, deliverability settings, org-wide addresses. NOT for Marketing Cloud email. | |
| TODO | multi-language-and-translation | Multi-language Salesforce: Translation Workbench setup, custom label translations, picklist value translation, Experience Cloud language switcher, RTL language support, translated validation messages. NOT for Marketing Cloud localization. | |
| TODO | salesforce-surveys | Salesforce Surveys: survey creation, question types, branching logic, distribution, guest user surveys, survey invitation tracking, reporting on responses. NOT for custom form building or Experience Cloud feedback widgets. | |
| TODO | user-access-policies | User Access Policies: automatic permission set assignment based on user attributes, provisioning rules, dynamic group membership, login-based license management. NOT for permission set design (use permission-set-architecture). | |
| TODO | batch-job-scheduling-and-monitoring | Monitoring scheduled and batch jobs: Apex Jobs monitoring, Flow scheduled jobs, job queue management, concurrent limits, failure notification, retry patterns. NOT for writing batch Apex (use batch-apex-patterns). | |
| TODO | standard-object-quirks | Non-obvious behaviors of standard objects: Task/Event polymorphic WhoId/WhatId, Lead conversion field mapping gotchas, Account/Contact deletion cascades, Person Account dual-nature, Case comment quirks. NOT for object creation (use object-creation-and-design). | |
| TODO | picklist-field-integrity-issues | Picklist data integrity: unrestricted vs restricted picklists, values loaded via API bypassing picklist validation, record type picklist mapping drift, dependent picklist loading order. NOT for picklist setup (use picklist-and-value-sets). | |
| TODO | record-type-strategy-at-scale | Record type design patterns at scale: page layout explosion prevention, business process alignment, record type ID dependencies, migration between record types, sharing implications. NOT for basic record type setup (use record-types-and-page-layouts). | |
| TODO | salesforce-release-preparation | Preparing for Salesforce seasonal releases: sandbox preview, release notes review, regression testing, feature deprecation tracking, org readiness assessment, critical update management. NOT for deployment mechanics. | |
| TODO | org-limits-monitoring | Monitoring org-level limits: API call usage, storage consumption, custom object count, field-per-object limits, automation limits, setup audit trail, limit alert patterns. NOT for governor limits in Apex (use limits-and-scalability-planning). | |
| TODO | salesforce-support-escalation | Navigating Salesforce support: case severity levels, known issue tracking, Trailblazer Community resources, partner support tiers, Trust site monitoring, escalation paths. NOT for Service Cloud case management. | |
| TODO | lightning-page-performance-tuning | Lightning page performance: component count limits, lazy loading, conditional visibility for heavy components, page load analysis, Lightning Usage App metrics. NOT for LWC component performance (use lwc-performance). | |
| TODO | report-performance-tuning | Report and dashboard performance: filter optimization, report type selection impact, custom report types vs standard, dashboard refresh scheduling, report row limits. NOT for CRM Analytics (use crm-analytics-* skills). | |
| TODO | license-optimization-strategy | Salesforce license management: license type comparison, permission set license usage, feature license audit, login-based license strategy, license reclamation from inactive users. NOT for license purchasing decisions. | |
| TODO | system-field-behavior-and-audit | System fields and audit behavior: CreatedDate vs SystemModstamp, LastModifiedDate triggers, system field queryability, audit field overrides on insert, IsDeleted behavior, formula field recalculation timing. NOT for field history tracking (use field-history-tracking). | |
| TODO | in-app-guidance-and-walkthroughs | In-App Guidance setup: prompts, walkthroughs, floating prompts, docked prompts, targeting rules, scheduling, adoption tracking, user segment targeting. NOT for change management (use change-management-and-training). | |
| TODO | lightning-app-builder-advanced | Advanced Lightning App Builder: dynamic pages, component visibility filters, custom address fields in pages, template cloning, org vs app vs record pages, page assignment rules. NOT for LWC development. | |
| TODO | nfr-definition-for-salesforce | Non-functional requirements for Salesforce projects: performance benchmarks, scalability targets, availability SLAs, security requirements, data volume projections, concurrent user capacity. NOT for technical implementation. | |

### Core Platform × BA Role

> Domain folder: `admin` | BA skills live in admin domain — they produce requirements and process artifacts, not code.

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | requirements-gathering-for-sf | Eliciting and documenting Salesforce requirements: user story format for SF features, As-Is vs To-Be process mapping, gap analysis, stakeholder interview questions. NOT for technical design. | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DUPLICATE | process-mapping-and-automation-selection | Mapping business processes to Salesforce automation options: Flow vs Apex vs Workflow Email Alert vs Process Builder (legacy). Produces a recommendation, not an implementation. NOT for building the automation (use flow/* or apex/* skills). | Covered by admin/process-automation-selection · Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | data-model-documentation | Documenting the Salesforce data model: ER diagrams, object relationship maps, field inventory, field usage analysis. NOT for designing the model (use object-creation-and-design or architect skills). | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | uat-and-acceptance-criteria | Writing acceptance criteria for Salesforce features, UAT test script format, defect classification for SF, regression test planning. NOT for automated testing (use flow-testing or apex test-class-standards). | Claude Sonnet 4.6 · 2026-04-03T00:00:00Z |
| DONE | change-management-and-training | User adoption planning, Salesforce training material structure, release communication templates, change impact assessment. NOT for org deployment (use change-management-and-deployment). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |

### Core Platform × Dev Role

> Dev skills split across `apex`, `lwc`, `flow` domains as appropriate.

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | soql-fundamentals | Writing SOQL: SELECT syntax, WHERE filters, ORDER BY, LIMIT, OFFSET, relationship queries (child-to-parent, parent-to-child), aggregate functions, date literals. NOT for security enforcement (use soql-security) or query optimization (use apex-cpu-and-heap-optimization). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DONE | sf-cli-and-sfdx-essentials | sf CLI auth, project setup, scratch org creation, source push/pull, deploy/retrieve commands, manifest (package.xml) basics. NOT for full CI/CD pipelines (use devops skills). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DONE | metadata-api-and-package-xml | Metadata API concepts, package.xml structure, what can and cannot be retrieved, deployment order dependencies, destructiveChanges.xml. NOT for SFDX source format details (use sf-cli-and-sfdx-essentials). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DONE | debug-logs-and-developer-console | Setting up debug logs, reading log levels, Developer Console query editor, anonymous Apex execution, Apex replay debugger basics. NOT for production incident debugging strategy (use debug-and-logging). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DUPLICATE | named-credentials-and-callouts | Setting up Named Credentials for external callouts, using them in Apex HTTP requests, auth protocols supported. NOT for OAuth flows as a standalone pattern (use oauth-flows-and-connected-apps). | Covered by apex/callouts-and-http-integrations · Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |

#### Apex Domain Gaps

> Domain folder: `apex`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | continuation-callouts | Continuation pattern for long-running callouts from Visualforce/LWC: async HTTP, timeout handling, callback methods. NOT for synchronous callouts (use callouts-and-http-integrations). | Agent 2026-04-04T12:00:00Z |
| DONE | custom-iterators-and-iterables | Implementing Iterable and Iterator interfaces for batch Apex: custom collection traversal, lazy evaluation patterns. NOT for standard list iteration. | Agent 2026-04-04T00:00:00Z |
| DONE | apex-managed-sharing | Sharing records programmatically via Apex: Share objects, row cause, sharing recalculation, with/without sharing patterns. NOT for declarative sharing rules (use sharing-and-visibility). | Agent 2026-04-04T06:00:00Z |
| DONE | apex-email-services | Inbound email handling: InboundEmailHandler, email-to-Apex routing, parsing attachments, email service addresses, error handling. NOT for outbound email templates. | Agent 2026-04-04T10:30:00Z |
| DONE | dynamic-apex | Dynamic SOQL, dynamic SOSL, Schema.describe methods, runtime type inspection, dynamic field access, SObjectType. NOT for static SOQL (use soql-fundamentals). | Agent 2026-04-04T00:00:00Z |
| DONE | apex-scheduled-jobs | Scheduling Apex: Schedulable interface, cron expressions, monitoring scheduled jobs, job limits, chaining. NOT for Batch Apex scheduling (use batch-apex-patterns). | Agent 2026-04-04T08:00:00Z |
| DONE | apex-metadata-api | Metadata.Operations for deploying metadata from Apex: creating custom fields/objects programmatically, callback handling. NOT for Metadata API REST/SOAP (use metadata-api-and-package-xml). | Agent 2026-04-04T00:00:00Z |
| DONE | change-data-capture-apex | CDC trigger patterns in Apex: change event handling, header fields, replay, entity tracking configuration. NOT for platform events (use platform-events-apex). | |
| DONE | apex-queueable-patterns | Advanced Queueable patterns: chaining, Finalizer interface, stack depth management, transaction control, state passing. NOT for basic async Apex (use async-apex). | Agent 2026-04-04T10:00:00Z |
| RESEARCHED | error-handling-framework | Cross-cutting error handling framework: custom log objects, exception utility classes, error propagation patterns, integration error capture, UI error components. NOT for individual try/catch blocks. | Researched 2026-04-04. Sources: [Apex Dev Guide — Custom Exceptions, AuraHandledException; Platform Events Dev Guide — BatchApexErrorEvent, rollback-safe events; LWC Dev Guide — Handle Errors from Apex; developer.salesforce.com blog — Error Handling Best Practices]. Key: Log-via-Platform-Event is the only rollback-safe log pattern (PE survives transaction rollback); BatchApexErrorEvent fires automatically on batch failures (API v44+) with ExceptionType/StackTrace/JobId; AuraHandledException must stay at controller boundary only; typed exception hierarchy with error code enum enables branching without string parsing; correlation ID must be threaded manually through async job state for log linking. |
| RESEARCHED | test-data-factory-patterns | Test data factory design: reusable record creation methods, SObject hierarchy setup, bulk data generation, portal user factories, fixture patterns. NOT for test class structure (use test-class-standards). | Researched 2026-04-04. Sources: [Apex Dev Guide — Common Test Utility Classes, @testSetup, Data Isolation, Mixed DML in Tests, runAs]. Key: @IsTest utility class excluded from org code size limits; @testSetup handles baseline shared across all test methods (one-time per class), factory calls for per-method variation; Mixed DML restriction — User/setup objects cannot DML with non-setup objects in same transaction — portal user factories must use System.runAs(); bulk factories must guard 150 DML/10,000 row limits per transaction. |
| TODO | custom-logging-and-monitoring | Custom logging frameworks in Apex: log object design, log levels, integration log capture, retention policies, monitoring dashboards, log forwarding. NOT for debug logs (use debug-logs-and-developer-console). | |
| TODO | visualforce-fundamentals | Visualforce pages and controllers: standard/custom controllers, extensions, action methods, view state management, PDF rendering, Visualforce email templates. NOT for LWC development (use lwc/* skills). | |
| TODO | platform-cache-patterns | Platform Cache usage: session and org cache partitions, cache-aside patterns, TTL configuration, cache limits, fallback strategies, cache diagnostics. NOT for custom settings as cache. | |
| TODO | order-of-execution-deep-dive | Complete Apex order of execution: before triggers, validation rules, after triggers, workflow, process builder, flow, assignment rules, auto-response, DML cascading, recursion implications. NOT for trigger framework design (use trigger-framework). | |
| TODO | mixed-dml-and-setup-objects | Mixed DML operation errors: setup vs non-setup objects, System.runAs workarounds, future method separation, test class implications, common scenarios that trigger mixed DML. NOT for general DML patterns. | |
| TODO | record-locking-and-contention | Record locking in Salesforce: row-level locking, FOR UPDATE queries, lock contention in high-volume orgs, parent record locking on child insert, deadlock patterns, retry strategies. NOT for sharing model (use sharing-and-visibility). | |
| TODO | timezone-and-datetime-pitfalls | DateTime vs Date field behavior: timezone conversion pitfalls, user timezone vs org timezone, SOQL date literals, GMT storage, Visualforce timezone rendering, Flow datetime handling. NOT for formula field syntax. | |
| TODO | formula-field-performance-and-limits | Formula field compile size limits, cross-object formula performance impact, formula field recalculation timing, SOQL filter limitations on formulas, compiled character limit workarounds. NOT for formula syntax (use formula-fields). | |
| TODO | fflib-enterprise-patterns | FFLib (Apex Enterprise Patterns): Unit of Work, Domain layer, Selector layer, Service layer, Application factory, adoption strategy, when to use vs simpler patterns. NOT for basic trigger framework (use trigger-framework). | |
| TODO | generic-sobject-handling | Dynamic SObject patterns: generic SObject DML, Schema.getGlobalDescribe performance, describe caching, dynamic field access, type-safe generic methods, SObject.put/get patterns. NOT for static SOQL (use soql-fundamentals). | |
| TODO | feature-flags-and-kill-switches | Feature flag patterns in Salesforce: Custom Metadata-based toggles, Custom Permissions as flags, hierarchical custom settings for user-level flags, runtime feature gating, emergency kill switches. NOT for custom metadata basics (use custom-metadata-types-and-settings). | |
| TODO | governor-limit-recovery-patterns | Recovering from governor limit errors: CPU timeout analysis, heap size diagnosis, SOQL query optimization under pressure, bulkification retrofit, limit-safe coding patterns. NOT for general limits overview (use limits-and-scalability-planning). | |
| TODO | apex-performance-profiling | Apex performance analysis: Limits class usage, debug log analysis for CPU time, heap profiling, SOQL query plan analysis, identifying N+1 patterns, benchmark testing approaches. NOT for debug log setup (use debug-logs-and-developer-console). | |
| TODO | cross-object-formula-and-rollup-performance | Cross-object formula and rollup summary field performance: spanning relationship limits, rollup recalculation triggers, DLRS alternatives, rollup on large data volumes, formula spanning cascade effects. NOT for formula syntax. | |
| TODO | long-running-process-orchestration | Orchestrating long-running processes: chaining Queueable jobs, Continuations, Platform Event-driven state machines, process checkpointing, timeout handling, progress tracking patterns. NOT for basic async Apex (use async-apex). | |
| TODO | callout-and-dml-transaction-boundaries | Transaction boundaries with callouts: uncommitted work errors, callout-before-DML vs DML-before-callout, mixed transaction patterns, queueable callout separation, future method boundaries. NOT for callout implementation (use callouts-and-http-integrations). | |
| TODO | common-apex-runtime-errors | Common Apex runtime errors and fixes: UNABLE_TO_LOCK_ROW, MIXED_DML_OPERATION, FIELD_CUSTOM_VALIDATION_EXCEPTION, TOO_MANY_SOQL_QUERIES, System.LimitException diagnosis and resolution patterns. NOT for error handling framework design. | |
| TODO | trigger-and-flow-coexistence | Managing triggers and flows on the same object: execution order interactions, recursion prevention across automation types, before-flow vs after-trigger timing, context variable conflicts. NOT for trigger framework (use trigger-framework). | |
| TODO | pdf-generation-patterns | PDF generation in Salesforce: Visualforce renderAs PDF, page size and styling, dynamic PDF content, PDF from LWC via Visualforce, third-party PDF libraries, attachment and ContentVersion storage. NOT for quote PDF templates (use quote-pdf-customization). | |

#### LWC Domain Gaps

> Domain folder: `lwc`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | lwc-in-flow-screens | Embedding LWC in Flow screens: flow reactive properties, flow output variables, navigation, FlowAttributeChangeEvent. NOT for custom property editors (use custom-property-editor-for-flow). | Agent 2026-04-04T10:00:00Z |
| DONE | lwc-toast-and-notifications | Toast messages, platform notifications, lightning-alert, lightning-confirm, promise-based notification patterns. NOT for modal overlays (use lwc-modal-and-overlay). | Agent 2026-04-04T06:00:00Z |
| DONE | lwc-dynamic-components | Dynamic component creation with lwc:component, lazy loading, runtime component resolution, dynamic imports. NOT for static component composition. | Agent 2026-04-04T08:00:00Z |
| DONE | message-channel-patterns | Lightning Message Service: message channels, cross-DOM communication, publish/subscribe patterns, scope management. NOT for parent-child communication (use component-communication). | Agent 2026-04-04T12:00:00Z |
| DONE | lwc-imperative-apex | Imperative Apex calls from LWC: error handling, loading states, cacheable vs non-cacheable, data refresh patterns. NOT for wire service (use wire-service-patterns). | Agent 2026-04-04T10:30:00Z |
| DONE | lwc-base-component-recipes | Effective use of lightning-record-form, lightning-record-edit-form, lightning-record-view-form, datatable customization. NOT for custom form building (use lwc-forms-and-validation). | Agent 2026-04-04T00:00:00Z |
| DONE | aura-to-lwc-migration | Migrating Aura components to LWC: feature mapping, interoperability wrappers, event translation, navigation patterns, Aura-LWC coexistence. NOT for new LWC development. | Agent 2026-04-04T00:00:00Z |
| DONE | lwc-accessibility-patterns | LWC accessibility: ARIA attributes, keyboard navigation, screen reader support, WCAG 2.1 compliance, focus management, accessible data tables. NOT for general LWC styling. | |
| TODO | common-lwc-runtime-errors | Common LWC runtime errors and fixes: wire adapter failures, navigation errors, Lightning Locker/LWS conflicts, shadow DOM issues, async rendering bugs, slot projection problems, event propagation mistakes. NOT for LWC fundamentals. | |

#### Flow Domain Gaps

> Domain folder: `flow`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | flow-debugging | Flow debug log analysis: flow fault email configuration, debugging record-triggered flows, step-by-step tracing, test runs. NOT for Apex debugging (use debug-and-logging). | Agent 2026-04-04T10:30:00Z |
| DONE | auto-launched-flow-patterns | Auto-launched flow invocation: from Apex, from REST API, from platform events, from other flows, entry conditions. NOT for record-triggered flows (use record-triggered-flow-patterns). | Agent 2026-04-04T12:00:00Z |
| DONE | flow-collection-processing | Collection variables, loop elements, assignment operations on collections, collection filters, sorting, Transform element. NOT for individual record processing. | Agent 2026-04-04T00:00:00Z |
| DONE | flow-external-services | Calling external APIs from Flow via External Services: HTTP callout action, parsing responses, error handling. NOT for Apex callouts. | Agent 2026-04-04T00:00:00Z |
| DONE | flow-email-and-notifications | Send email action, custom notifications from Flow, SMS via Flow, Slack notifications, rich notification content. NOT for email templates (use email-templates-and-alerts). | |
| TODO | pause-elements-and-wait-events | Flow pause elements: wait event configuration, time-based resume, platform event resume, resume conditions. NOT for scheduled flows (use scheduled-flows). | |
| TODO | flow-runtime-error-diagnosis | Diagnosing Flow runtime errors: fault paths, unhandled fault emails, common runtime failures (null reference, SOQL limits, DML in loops), debug log correlation, error message interpretation. NOT for Flow design (use flow-debugging). | |

### Core Platform × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | data-model-design-patterns | Choosing object relationships (Lookup vs MD vs Junction), field type selection for data integrity, indexing strategy for query performance, data model anti-patterns. NOT for object creation steps (use object-creation-and-design). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DONE | data-migration-planning | ETL approach selection, migration sequence (parent before child), external ID strategy, validation rule bypass during migration, rollback planning. NOT for Data Loader mechanics (use data-import-and-management). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DONE | data-quality-and-governance | Data quality rules in Salesforce, validation rules as data gates, duplicate management strategy, field history as audit trail, GDPR/data retention considerations. NOT for Duplicate Rules configuration (use duplicate-management). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DONE | bulk-api-and-large-data-loads | Bulk API 2.0 vs REST API for large volumes, batch size guidance, serial vs parallel mode, monitoring bulk jobs, failed record handling. NOT for Data Loader UI steps (use data-import-and-management). | Already built |
| DONE | data-archival-strategies | Big Object usage, archival to external storage, field history truncation, record count limits and their impact, soft-delete and recycle bin behavior. NOT for data migration (use data-migration-planning). | Already built |
| DONE | soql-query-optimization | Selective queries, index usage, query plan tool, avoiding non-selective filters, skinny tables, field sets for dynamic queries. NOT for governor limits in Apex (use apex-cpu-and-heap-optimization). | Already built |
| DONE | field-history-tracking | Enabling field history, 18-month retention limit, History related list behavior, querying history objects (AccountHistory, etc.), limitations and alternatives. NOT for Event Monitoring (use security skills). | Agent 2026-04-04T12:00:00Z |
| DONE | external-data-and-big-objects | Big Objects for archival, async SOQL for Big Objects, External Objects vs Big Objects decision, custom index fields. NOT for Salesforce Connect (use salesforce-connect-external-objects). | Agent 2026-04-04T00:00:00Z |
| DONE | person-accounts | Person Account model: enabling person accounts, B2C data model, account-contact behavior differences, limitations, migration considerations, reporting impact. NOT for standard business accounts. | Agent 2026-04-04T00:00:00Z |
| DONE | batch-data-cleanup-patterns | Scheduled batch data cleanup: temporary record purging, retention policy enforcement, nightly cleanup jobs, storage optimization, recycle bin management, async deletion. NOT for data archival to external storage (use data-archival-strategies). | Agent 2026-04-04T00:00:00Z |
| DONE | data-storage-management | Salesforce storage management: file storage vs data storage, storage usage monitoring, storage optimization, large text field strategies, attachment alternatives, storage alerts. NOT for external storage integration. | |
| TODO | custom-index-requests | Custom indexing in Salesforce: requesting custom indexes from Salesforce Support, skinny tables, two-column indexes, when standard indexes aren't enough, index selectivity thresholds, monitoring index usage. NOT for SOQL optimization (use soql-query-optimization). | |
| TODO | external-id-strategy | External ID field design: choosing external ID fields, composite key strategies, upsert behavior, external ID indexing, migration use cases, cross-system record correlation patterns. NOT for data migration steps (use data-migration-planning). | |
| TODO | record-merge-implications | Record merge behavior: account merge, contact merge, lead merge, case merge, field value resolution rules, related record reparenting, trigger behavior during merge, losing record cleanup. NOT for duplicate management rules (use data-quality-and-governance). | |
| TODO | large-scale-deduplication | Large-scale deduplication: matching rule tuning, batch dedup jobs, third-party dedup tools (DemandTools, Cloudingo), merge automation, surviving record selection logic, post-merge data validation. NOT for duplicate rule configuration (use data-quality-and-governance). | |
| TODO | data-reconciliation-patterns | Data reconciliation between Salesforce and external systems: record count validation, field-level comparison, hash-based change detection, reconciliation reports, automated mismatch alerting. NOT for data migration (use data-migration-planning). | |
| TODO | sharing-recalculation-performance | Sharing recalculation triggers and performance: role hierarchy changes, territory reassignment, group membership changes, OWD changes, deferring sharing calculation, async sharing, monitoring recalculation. NOT for sharing model design (use sharing-and-visibility). | |

### Core Platform × Architect Role

> Domain folder: `architect` (skills live in `skills/architect/` with `category: architect`)

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| DONE | solution-design-patterns | When to use declarative vs programmatic solutions, layered automation model, design tradeoffs (Flow vs Apex vs LWC), future-proofing configuration decisions. NOT for individual feature design (use role-specific skills). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DONE | limits-and-scalability-planning | Governor limits that matter at scale (SOQL, DML, CPU, heap), org-wide limits (fields per object, custom objects, custom settings), planning for data volume growth. NOT for code-level optimization (use apex-cpu-and-heap-optimization). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DONE | multi-org-strategy | When to use a single org vs multiple orgs, hub-and-spoke patterns, data sharing across orgs, Connected App and API patterns for multi-org. NOT for sandbox strategy (use sandbox-strategy). | Claude Sonnet 4.6 · 2026-04-04T00:00:00Z |
| DONE | technical-debt-assessment | Identifying dead code, unused automations, overlapping flows and triggers, deprecated features in use, complexity indicators. Produces a findings report. NOT for implementing fixes. | Already built |
| DONE | well-architected-review | Applying Salesforce Well-Architected Framework pillars (Trusted, Easy, Adaptable) to an org assessment. Produces a structured review. NOT for individual pillar deep-dives. | Already built |
| DONE | platform-selection-guidance | Choosing the right Salesforce platform feature for a requirement: Flow vs Apex, LWC vs Aura (legacy), Custom Metadata vs Custom Settings vs Custom Objects, OmniStudio vs standard automation. NOT for implementation of the chosen option. | Already built |
| DONE | security-architecture-review | Reviewing an org's security posture: sharing model completeness, FLS coverage, Apex security patterns, exposed APIs, Shield needs. Produces findings. NOT for implementing fixes (use security/* skills). | Agent 2026-04-04T00:00:00Z |
| DONE | government-cloud-compliance | Government Cloud architecture: FedRAMP High, Hyperforce, GovCloud Plus, data residency, CMS ARC-AMPE controls, compliance automation patterns. NOT for general security (use security/* skills). | Agent 2026-04-04T00:00:00Z |
| DONE | integration-framework-design | Integration framework architecture: service interface pattern, factory pattern, centralized callout handling, dynamic service resolution, response logging, error propagation. NOT for individual API implementation. | Agent 2026-04-04T00:00:00Z |
| TODO | org-edition-and-feature-licensing | Salesforce edition selection: Enterprise vs Unlimited vs Performance feature differences, add-on licensing (Shield, CPQ, Health Cloud), feature availability by edition, upgrade path planning. NOT for license optimization (use license-optimization-strategy). | |
| TODO | ai-ready-data-architecture | Designing data architecture for AI readiness: data completeness for ML, structured vs unstructured data strategy, embedding-ready fields, knowledge article structure for RAG, data freshness requirements. NOT for Data Cloud setup. | |
| TODO | ha-dr-architecture | High availability and disaster recovery for Salesforce: Salesforce Trust site monitoring, backup strategies, cross-region considerations, business continuity planning, RTO/RPO targets, failover patterns for integrations. NOT for data backup mechanics (use salesforce-backup-and-restore). | |

---

## Phase 2 — Sales Cloud

### Sales Cloud × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | lead-management-and-conversion | Lead settings, lead conversion mapping, lead queues, auto-response rules, web-to-lead, lead processes. NOT for lead assignment rules (use assignment-rules). | |
| TODO | opportunity-management | Opportunity stages, sales processes, similar opportunities, big deal alerts, stage history tracking, contact roles. NOT for forecasting (use collaborative-forecasts). | |
| TODO | collaborative-forecasts | Collaborative Forecasts setup: forecast types, adjustments, quotas, forecast categories, forecast hierarchy, cumulative vs individual. NOT for custom report-based forecasting. | |
| TODO | products-and-pricebooks | Product catalog setup: standard vs custom pricebooks, multi-currency pricebooks, product schedules, archiving products. NOT for CPQ pricing (use Revenue Cloud skills). | |
| TODO | quotes-and-quote-templates | Quote configuration: quote templates, PDF generation, email quotes, quote sync to opportunity, discount approval. NOT for CPQ quote configuration. | |
| TODO | territory-management-sales | Enterprise Territory Management for Sales Cloud: territory types, assignment rules, territory-based forecasting. NOT for general ETM admin (use enterprise-territory-management). | |
| TODO | sales-engagement-cadences | Sales Engagement / High Velocity Sales setup: cadences, call scripts, email templates, work queue, sequence steps. NOT for Marketing Cloud campaigns. | |
| TODO | einstein-activity-capture-setup | Einstein Activity Capture configuration: email sync, calendar sync, activity metrics, privacy settings, user assignment. NOT for manual activity logging. | |

### Sales Cloud × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | sales-process-mapping | Mapping sales stages to opportunity stages: stage transition rules, win/loss analysis requirements, conversion criteria. NOT for implementation. | |
| TODO | pipeline-review-design | Pipeline inspection requirements: forecast category mapping, stage duration analysis, conversion metrics, review cadence. NOT for dashboard building. | |
| TODO | territory-design-requirements | Territory hierarchy design: alignment criteria, coverage model requirements, assignment rules, geographic considerations. NOT for ETM configuration. | |
| TODO | lead-scoring-requirements | Lead scoring model design: qualifying criteria, MQL/SQL definitions, handoff requirements, scoring dimensions. NOT for Einstein Lead Scoring. | |
| TODO | quote-to-cash-requirements | Quote-to-cash process mapping: approval requirements, discount policies, document output specs, order handoff. NOT for CPQ implementation. | |

### Sales Cloud × Dev Role

> Domain folder: `apex`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | opportunity-trigger-patterns | Apex trigger patterns for Opportunity: stage change automation, amount rollups, team member sync, split calculations. NOT for generic trigger patterns (use trigger-framework). | |
| TODO | quote-pdf-customization | Quote PDF generation with Visualforce: custom templates, dynamic sections, multi-language quotes, logo placement. NOT for LWC-based documents. | |
| TODO | territory-api-and-assignment | Territory2 API: territory assignment via Apex, territory member management, bulk territory assignment, rule evaluation. NOT for ETM admin setup. | |
| TODO | lead-conversion-customization | Customizing lead conversion with Apex: custom field mapping, related record creation, conversion triggers, LeadConvert. NOT for admin conversion setup. | |
| TODO | sales-engagement-api | Sales Engagement / HVS API: cadence enrollment via Apex, step customization, call result logging, action customization. NOT for cadence admin setup. | |
| TODO | einstein-activity-capture-api | Einstein Activity Capture data access: activity metrics API, email and event sync data, reporting on captured activities. NOT for email template design. | |

### Sales Cloud × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | lead-data-import-and-dedup | Lead data imports: matching rules for leads, dedup strategies, web-to-lead data quality, enrichment patterns. NOT for Data Loader mechanics. | |
| TODO | opportunity-pipeline-migration | Historical opportunity migration: stage history recreation, amount and date mapping, product line items, team members. NOT for generic data migration. | |
| TODO | product-catalog-data-model | Product and Pricebook data model: PricebookEntry management, product hierarchies, data loading sequence, bulk loading. NOT for CPQ product model. | |
| TODO | sales-reporting-data-model | Sales data model for reporting: opportunity snapshots, trending reports, custom report types for pipeline analysis. NOT for CRM Analytics. | |
| TODO | territory-data-alignment | Territory alignment data: account-territory assignments, territory history, bulk reassignment, territory coverage analysis. NOT for ETM configuration. | |

### Sales Cloud × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | sales-cloud-architecture | Sales Cloud solution architecture: process automation strategy, integration points, data model decisions, scalability. NOT for individual feature design. | |
| TODO | multi-currency-sales-architecture | Multi-currency in Sales Cloud: advanced currency management, dated exchange rates, reporting implications, rollup impact. NOT for multi-currency admin setup. | |
| TODO | cpq-vs-standard-products-decision | When to use Salesforce CPQ vs standard Products & Pricebooks: feature comparison, licensing impact, complexity tradeoffs. NOT for CPQ implementation. | |
| TODO | sales-cloud-integration-patterns | Sales Cloud integration: ERP sync, marketing automation, CPQ integration, quote-to-order, partner portal patterns. NOT for generic integration patterns. | |
| TODO | high-volume-sales-data-architecture | Handling large sales data volumes: opportunity archival, report optimization, data skew prevention in sales objects. NOT for generic data volume planning. | |

---

## Phase 3 — Service Cloud

### Service Cloud × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | case-management-setup | Case settings, support processes, case teams, case comments, case feeds, web-to-case, case auto-response. NOT for case assignment rules (use assignment-rules). | |
| TODO | omni-channel-routing-setup | Omni-Channel routing configuration: queue-based vs skills-based routing, agent capacity, presence statuses, routing logic. NOT for OmniStudio. | |
| TODO | entitlements-and-milestones | Entitlement process setup: milestone types, milestone actions, entitlement verification, SLA tracking, business hours. NOT for case escalation rules. | |
| TODO | knowledge-base-administration | Salesforce Knowledge setup: article types, data categories, publishing workflow, Lightning Knowledge, approval processes. NOT for Knowledge in Experience Cloud. | |
| TODO | email-to-case-configuration | Email-to-Case and On-Demand Email-to-Case setup: routing addresses, email threading, attachment handling, auto-response. NOT for email templates. | |
| TODO | service-console-configuration | Service Console app setup: utility bar, split view, macros, quick text, keyboard shortcuts, console navigation. NOT for generic Lightning app setup. | |
| TODO | messaging-and-chat-setup | Messaging for In-App and Web, Chat configuration: pre-chat forms, chat routing, embedded service deployment, queues. NOT for Agentforce bots. | |
| TODO | service-cloud-voice-setup | Service Cloud Voice configuration: Amazon Connect integration, call routing, transcription, after-call work, recording. NOT for CTI adapter development. | |

### Service Cloud × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | sla-design-and-escalation-matrix | SLA tier design: escalation matrix documentation, response/resolution time requirements, business hours alignment. NOT for entitlement configuration. | |
| TODO | knowledge-taxonomy-design | Knowledge article taxonomy: data category hierarchy, article lifecycle, content gap analysis, authoring guidelines. NOT for Knowledge admin setup. | |
| TODO | agent-console-requirements | Service console requirements: agent workflow mapping, case handling process, macro requirements, screen layouts. NOT for console configuration. | |
| TODO | case-deflection-strategy | Self-service strategy: knowledge article surfacing, chatbot requirements, case deflection metrics, ROI measurement. NOT for Experience Cloud setup. | |
| TODO | customer-effort-scoring | Customer effort metrics: CSAT design, survey requirements, service quality measurement, NPS integration. NOT for custom survey implementation. | |

### Service Cloud × Dev Role

> Domain folder: `apex`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | case-trigger-patterns | Apex triggers for Case: auto-assignment overrides, entitlement verification, SLA calculation, case merge handling. NOT for generic trigger patterns (use trigger-framework). | |
| TODO | knowledge-article-lwc | Custom Lightning components for Knowledge: article display, search, recommendation widgets, feedback collection. NOT for standard Knowledge setup. | |
| TODO | cti-adapter-development | CTI integration: Open CTI API, softphone panel, click-to-dial, screen pop, call logging via Apex, adapter patterns. NOT for Service Cloud Voice admin. | |
| TODO | omni-channel-custom-routing | Custom Omni-Channel routing via Apex: PendingServiceRouting, custom skills matching, overflow handling, priority routing. NOT for admin routing setup. | |
| TODO | entitlement-apex-hooks | Entitlement process Apex extension: custom milestone completion, SLA breach notifications, case status automation. NOT for admin entitlement setup. | |
| TODO | service-cloud-rest-api | Service Cloud specific REST APIs: Case API patterns, Knowledge API, Chat REST API, Messaging API endpoints. NOT for generic REST API. | |

### Service Cloud × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | case-history-migration | Migrating historical case data: case comments, email messages, attachments, activity history, status mapping. NOT for generic data migration. | |
| TODO | knowledge-article-import | Importing Knowledge articles: CSV import, article field mapping, category assignment, publishing status, bulk loading. NOT for Knowledge admin setup. | |
| TODO | service-metrics-data-model | Service reporting data model: case duration calculations, SLA compliance metrics, agent performance data, MTTR. NOT for CRM Analytics. | |
| TODO | omni-channel-reporting-data | Omni-Channel analytics data: agent work records, queue metrics, capacity utilization, wait time reporting. NOT for admin routing setup. | |
| TODO | service-data-archival | Case archival strategies: email message cleanup, attachment management, compliance retention, storage optimization. NOT for generic data archival. | |

### Service Cloud × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | service-cloud-architecture | Service Cloud solution architecture: channel strategy, routing model, knowledge strategy, integration points, scalability. NOT for individual feature design. | |
| TODO | omni-channel-capacity-model | Omni-Channel capacity planning: agent capacity allocation, channel weighting, skills matrix design, overflow strategy. NOT for routing configuration. | |
| TODO | knowledge-vs-external-cms | Decision framework for Salesforce Knowledge vs external CMS: hybrid approaches, content federation, search strategy. NOT for CMS implementation. | |
| TODO | einstein-bot-architecture | Einstein Bot / Agentforce for Service architecture: intent model, dialog design, handoff strategy, escalation paths. NOT for bot implementation. | |
| TODO | multi-channel-service-architecture | Multi-channel service strategy: phone, email, chat, messaging, social, channel prioritization, unified routing. NOT for individual channel setup. | |

---

## Phase 4 — Experience Cloud

### Experience Cloud × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | experience-cloud-site-setup | Site creation: template selection (LWR vs Aura), branding, navigation menus, domain configuration, page builder. NOT for internal Lightning apps. | |
| TODO | experience-cloud-member-management | Member profiles: external user licensing, registration flows, login page customization, self-registration. NOT for internal user management. | |
| TODO | experience-cloud-cms-content | CMS workspace setup: content types, content publishing, audience targeting, content scheduling, managed content. NOT for Knowledge articles. | |
| TODO | experience-cloud-guest-access | Guest user profile configuration: public access settings, unauthenticated page design, object-level security review. NOT for authenticated user features. | |
| TODO | experience-cloud-moderation | Content moderation setup: flagging rules, reputation system, member management, content approval workflows. NOT for CMS content publishing. | |
| TODO | experience-cloud-seo-settings | SEO configuration for Experience Cloud sites: page titles, meta descriptions, URL structure, robots.txt, sitemap. NOT for external SEO tools. | |

### Experience Cloud × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | portal-requirements-gathering | Requirements for customer/partner portals: user journey mapping, self-service capabilities, content requirements. NOT for implementation. | |
| TODO | self-service-design | Self-service portal design: knowledge base UX, case submission flow, community engagement requirements, deflection goals. NOT for Experience Cloud setup. | |
| TODO | partner-community-requirements | Partner community requirements: deal registration, lead distribution, MDF, co-marketing, partner tier management. NOT for partner portal configuration. | |
| TODO | community-engagement-strategy | Community engagement model: gamification requirements, ideation process, content contribution strategy, recognition. NOT for moderation configuration. | |

### Experience Cloud × Dev Role

> Domain folder: `lwc`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | lwr-site-development | LWR (Lightning Web Runtime) site development: custom themes, LWC for Experience Cloud, build configuration. NOT for Aura-based communities. | |
| TODO | experience-cloud-lwc-components | Building custom LWC for Experience Cloud: data access patterns, guest user Apex, community context, navigation. NOT for internal LWC. | |
| TODO | experience-cloud-authentication | Custom login flows: social sign-on, self-registration, passwordless login, SSO for external users, auth providers. NOT for internal SSO. | |
| TODO | headless-experience-cloud | Headless CMS API: content delivery API, building custom frontends against Experience Cloud data, channel access. NOT for standard site building. | |
| TODO | experience-cloud-api-access | API access for community users: guest user API limits, external user OAuth scopes, sharing enforcement. NOT for internal API security. | |
| TODO | experience-cloud-search-customization | Customizing search in Experience Cloud: federated search, search result components, search scope, global search. NOT for SOSL queries. | |
| TODO | experience-cloud-multi-idp-sso | Multi-IdP SSO for Experience Cloud: OIDC integration, multiple auth providers per site, federation ID mapping, tenant-specific login pages, vendor vs citizen portals. NOT for internal SSO or single auth provider. | |

### Experience Cloud × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | external-user-data-sharing | Sharing sets, external organization-wide defaults, external sharing rules, portal account sharing model. NOT for internal sharing model. | |
| TODO | community-user-data-migration | Migrating external user accounts: contact-user relationships, community membership data, profile assignment. NOT for internal user data. | |
| TODO | community-analytics-data | Experience Cloud analytics: login metrics, page view tracking, member engagement data, content performance data. NOT for CRM Analytics. | |
| TODO | partner-data-access-patterns | Partner user data visibility: partner role hierarchy, PRM data sharing, deal registration data, channel analytics. NOT for internal data access. | |

### Experience Cloud × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | experience-cloud-licensing-model | License selection: Customer Community, Partner Community, Customer Community Plus, login-based, channel licensing. NOT for internal licensing. | |
| TODO | multi-site-architecture | Multi-site Experience Cloud strategy: shared components, cross-site navigation, domain strategy, template reuse. NOT for single site setup. | |
| TODO | headless-vs-standard-experience | Decision framework for headless vs LWR vs Aura Experience Cloud: performance, development cost, flexibility tradeoffs. NOT for implementation. | |
| TODO | experience-cloud-performance | Experience Cloud performance: CDN configuration, caching strategy, component loading, page weight optimization. NOT for LWC performance (use lwc-performance). | |
| TODO | experience-cloud-integration-patterns | Integrating external systems with Experience Cloud: SSO, data sync, external content, third-party widgets. NOT for internal integration. | |

---

## Phase 5 — Marketing Cloud / MCAE (Pardot)

### Marketing Cloud × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | marketing-cloud-engagement-setup | Marketing Cloud Engagement setup: business units, user roles, sender profiles, delivery profiles, account configuration. NOT for MCAE/Pardot. | |
| TODO | mcae-pardot-setup | MCAE (Pardot) setup: business unit configuration, connector setup, Salesforce sync, user roles, account engagement. NOT for Marketing Cloud Engagement. | |
| TODO | email-studio-administration | Email Studio: email creation, templates, dynamic content, A/B testing, send classification, subscriber management. NOT for MCAE email. | |
| TODO | journey-builder-administration | Journey Builder setup: entry sources, activities, decision splits, wait times, goal tracking, exit criteria. NOT for Flow-based automation. | |
| TODO | marketing-cloud-connect | Marketing Cloud Connect configuration: Salesforce connector, synchronized data sources, tracking, scope configuration. NOT for MCAE connector. | |
| TODO | mcae-lead-scoring-and-grading | MCAE lead scoring model setup: grading criteria, score decay, automation rules for score-based actions, profiles. NOT for Einstein Lead Scoring. | |
| TODO | consent-management-marketing | Email consent management: subscription center, preference center, compliance (CAN-SPAM, GDPR), opt-out handling. NOT for general GDPR compliance. | |

### Marketing Cloud × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | campaign-planning-and-attribution | Campaign planning: attribution models, ROI tracking, multi-touch attribution requirements, campaign hierarchy design. NOT for campaign implementation. | |
| TODO | lead-nurture-journey-design | Lead nurture journey mapping: engagement scoring design, content strategy, conversion path, drip campaign structure. NOT for Journey Builder implementation. | |
| TODO | email-deliverability-strategy | Email deliverability requirements: sender reputation, authentication (SPF, DKIM, DMARC), list hygiene, warm-up. NOT for email template design. | |
| TODO | marketing-automation-requirements | Marketing automation requirements: lead lifecycle definition, MQL/SQL handoff criteria, scoring model design. NOT for implementation. | |
| TODO | marketing-reporting-requirements | Marketing reporting KPI definition: dashboard requirements, funnel metrics, campaign performance, attribution. NOT for dashboard building. | |

### Marketing Cloud × Dev Role

> Domain folder: `apex` or as noted

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | ampscript-development | AMPscript in Marketing Cloud: personalization strings, functions, lookups, conditional content, FOR loops. NOT for SSJS. | |
| TODO | ssjs-server-side-javascript | Server-Side JavaScript in Marketing Cloud: script activities, API calls, data extension operations, error handling. NOT for AMPscript. | |
| TODO | marketing-cloud-api | Marketing Cloud REST and SOAP APIs: authentication, data extension CRUD, triggered sends, journey injection. NOT for Salesforce core APIs. | |
| TODO | mcae-pardot-api | MCAE/Pardot API v5: prospect operations, list management, visitor tracking, form handler integration. NOT for Marketing Cloud API. | |
| TODO | marketing-cloud-custom-activities | Custom Journey Builder activities: custom split activities, custom entry sources, activity SDK, webhook integration. NOT for standard Journey Builder. | |
| TODO | marketing-cloud-data-views | System Data Views in Marketing Cloud: Sent, Open, Click, Bounce, Subscribers, Job data, query patterns. NOT for Data Extensions. | |

### Marketing Cloud × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | data-extension-design | Data Extension architecture: primary keys, sendable vs non-sendable, relationships, data retention policies. NOT for CRM data model. | |
| TODO | marketing-cloud-data-sync | Marketing Cloud Connect data sync: synchronized data extensions, data flow architecture, sync troubleshooting. NOT for manual imports. | |
| TODO | subscriber-data-management | Subscriber key strategy: all-subscribers list, publication lists, suppression lists, data hygiene, deduplication. NOT for CRM contact management. | |
| TODO | marketing-cloud-sql-queries | SQL queries in Marketing Cloud: Automation Studio queries, query activities, data extension joins, date functions. NOT for SOQL. | |
| TODO | mcae-prospect-data-migration | MCAE prospect data import: field mapping, custom object sync, engagement history, list import, sync validation. NOT for CRM data migration. | |

### Marketing Cloud × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | marketing-cloud-vs-mcae-selection | Choosing Marketing Cloud Engagement vs MCAE: feature comparison, licensing, integration complexity, use case fit. NOT for implementation. | |
| TODO | multi-bu-marketing-architecture | Multi-business unit Marketing Cloud architecture: BU hierarchy, shared content, data segregation, governance. NOT for single-BU setup. | |
| TODO | marketing-consent-architecture | Consent management architecture across Marketing Cloud and CRM: data model, sync patterns, compliance design. NOT for individual consent setup. | |
| TODO | marketing-data-architecture | Marketing data architecture: data extension design, relational data model, data flow from CRM to MC. NOT for CRM data model. | |
| TODO | marketing-integration-patterns | Marketing Cloud integration: real-time triggers, batch data sync, API patterns, journey injection, webhook patterns. NOT for generic integration. | |

---

## Phase 6 — Revenue Cloud (CPQ & Billing)

### Revenue Cloud × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | cpq-product-catalog-setup | CPQ product setup: product rules, option constraints, product bundles, feature configuration, product families. NOT for standard Products & Pricebooks. | |
| TODO | cpq-pricing-rules | CPQ pricing: price rules, price actions, block pricing, percent-of-total, contracted pricing, discount schedules. NOT for standard pricebook pricing. | |
| TODO | cpq-quote-templates | CPQ quote template design: line columns, template sections, conditional content, PDF output, multi-language. NOT for standard quote templates. | |
| TODO | cpq-approval-workflows | CPQ-specific approvals: discount approvals, advanced approvals, approval chains, smart approvals, escalation. NOT for standard approval processes. | |
| TODO | billing-schedule-setup | Salesforce Billing: billing schedules, invoice generation, payment terms, credit notes, revenue schedules. NOT for CPQ quoting. | |
| TODO | contract-and-renewal-management | Contract creation from quotes: renewal quoting, amendment quoting, subscription management, co-termination. NOT for standard contracts. | |
| TODO | cpq-guided-selling | CPQ guided selling setup: question-based product selection, quote wizard, recommendation rules, filtering. NOT for OmniStudio product selection. | |

### Revenue Cloud × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | pricing-model-design | Pricing strategy documentation: tiered pricing, volume discounts, subscription models, usage-based pricing requirements. NOT for CPQ implementation. | |
| TODO | quote-to-cash-process | Quote-to-cash end-to-end process mapping: approval workflows, order creation, billing triggers, revenue recognition. NOT for implementation. | |
| TODO | revenue-recognition-requirements | Revenue recognition requirements: ASC 606 compliance, performance obligations, allocation rules, scheduling. NOT for billing configuration. | |
| TODO | subscription-lifecycle-requirements | Subscription model requirements: amendments, renewals, cancellations, proration, co-termination, upgrade/downgrade. NOT for CPQ setup. | |

### Revenue Cloud × Dev Role

> Domain folder: `apex`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | cpq-apex-plugins | CPQ calculator plugin development: custom pricing logic, product rule evaluation, pre/post-calculate hooks. NOT for standard Apex triggers. | |
| TODO | cpq-custom-actions | CPQ custom actions: JavaScript in quote line editor, custom buttons, page security plugins, QLE customization. NOT for standard quick actions. | |
| TODO | billing-integration-apex | Billing API integration: invoice generation via Apex, payment gateway integration, credit note automation. NOT for admin billing setup. | |
| TODO | cpq-api-and-automation | CPQ API: quote calculation API, product API, amendment API, renewal API, cloning API, programmatic quoting. NOT for standard REST API. | |
| TODO | cpq-test-automation | Testing CPQ configurations: test class patterns for quotes, price rule testing, bundle validation, data setup. NOT for standard Apex testing. | |

### Revenue Cloud × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | product-catalog-migration-cpq | CPQ product catalog data migration: products, price rules, discount schedules, bundle structure, option setup. NOT for standard product import. | |
| TODO | historical-order-migration | Migrating historical orders and contracts: order line items, contract history, subscription data, billing records. NOT for opportunity migration. | |
| TODO | cpq-data-model | CPQ data model understanding: Quote, QuoteLine, Product, PriceRule, Subscription objects and relationships. NOT for standard data model. | |
| TODO | billing-data-reconciliation | Billing data reconciliation: invoice-to-payment matching, revenue recognition data, financial reporting alignment. NOT for CRM reporting. | |

### Revenue Cloud × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | cpq-architecture-patterns | CPQ solution architecture: bundle design, pricing engine performance, multi-currency CPQ, integration strategy. NOT for individual feature design. | |
| TODO | cpq-vs-industries-cpq | Deciding between Salesforce CPQ and Industries CPQ (Vlocity): feature comparison, industry fit, migration paths. NOT for implementation. | |
| TODO | cpq-performance-optimization | CPQ performance: quote calculation speed, large bundles, plugin optimization, caching strategies, batch calculations. NOT for generic Apex performance. | |
| TODO | cpq-integration-with-erp | CPQ to ERP integration: order sync, pricing sync, inventory check, configuration validation, error handling. NOT for generic integration. | |
| TODO | subscription-management-architecture | Subscription lifecycle architecture: amendment flow, renewal automation, co-termination design, billing integration. NOT for billing setup. | |

---

## Phase 7 — Field Service (FSL)

### FSL × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | fsl-work-order-management | Work Order configuration: work types, work order line items, service appointments, status flow, auto-creation. NOT for case management. | |
| TODO | fsl-service-territory-setup | Service territory setup: territory types, operating hours, territory members, territory hierarchy, polygons. NOT for ETM territories. | |
| TODO | fsl-resource-management | Service resource setup: skills, capacity, availability, preferred resources, resource types, certification. NOT for user management. | |
| TODO | fsl-scheduling-policies | Scheduling policy configuration: optimization objectives, work rules, service objectives, scheduling horizons, priorities. NOT for Omni-Channel routing. | |
| TODO | fsl-mobile-app-setup | Field Service Mobile app setup: app extensions, deep links, offline priming, service report templates, branding. NOT for internal Salesforce mobile. | |
| TODO | fsl-inventory-management | Inventory management: product items, product transfers, product requests, van stock, return orders, stock tracking. NOT for CPQ product catalog. | |
| TODO | fsl-shifts-and-crew | Shift management and crew scheduling: shift patterns, crew assignment, multi-day work orders, crew skills. NOT for individual resource scheduling. | |

### FSL × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | fsl-scheduling-optimization-design | Scheduling optimization requirements: travel time, skills matching, priority handling, SLA compliance metrics. NOT for scheduling configuration. | |
| TODO | fsl-sla-configuration-requirements | Field service SLA design: response time, resolution time, geographic considerations, priority matrix. NOT for Service Cloud SLAs. | |
| TODO | fsl-mobile-workflow-design | Mobile workforce workflow design: job lifecycle, parts tracking, customer signature, offline requirements. NOT for mobile app configuration. | |
| TODO | fsl-capacity-planning | Field workforce capacity planning: resource demand forecasting, territory coverage, seasonal adjustments, utilization. NOT for Omni-Channel capacity. | |

### FSL × Dev Role

> Domain folder: `apex`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | fsl-apex-extensions | Field Service Apex extension points: custom scheduling logic, appointment booking API, service resource API. NOT for standard Apex. | |
| TODO | fsl-mobile-app-extensions | Field Service Mobile extensions: custom LWC actions, deep links, custom flows in mobile, offline data. NOT for LWC in standard Salesforce mobile. | |
| TODO | fsl-service-report-templates | Custom service report templates: Visualforce-based reports, dynamic sections, customer signature capture. NOT for quote templates. | |
| TODO | fsl-scheduling-api | Field Service Scheduling API: appointment booking, resource optimization, bulk scheduling operations, availability check. NOT for admin scheduling policy. | |
| TODO | fsl-custom-actions-mobile | Custom actions for FSL Mobile: custom LWC screens, barcode scanning, GPS-based actions, photo capture. NOT for standard quick actions. | |

### FSL × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | fsl-work-order-migration | Work order and service appointment data migration: related records, resource assignments, parts used history. NOT for case migration. | |
| TODO | fsl-territory-data-setup | Service territory data loading: boundary polygons, member assignments, operating hours bulk setup, hierarchy. NOT for ETM territory data. | |
| TODO | fsl-resource-and-skill-data | Resource skill data management: skill certification tracking, capacity data, availability patterns, bulk assignment. NOT for user data. | |
| TODO | fsl-reporting-data-model | FSL reporting data model: job completion metrics, travel analytics, first-time fix rate data, utilization. NOT for CRM Analytics. | |

### FSL × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | fsl-optimization-architecture | FSL optimization architecture: scheduling engine configuration, real-time vs batch optimization, fallback rules. NOT for scheduling policy admin. | |
| TODO | fsl-offline-architecture | FSL offline-first architecture: data priming strategy, conflict resolution, offline data limits, sync patterns. NOT for LWC offline (use lwc-offline-and-mobile). | |
| TODO | fsl-integration-patterns | FSL integration: ERP parts sync, GPS/fleet management, IoT-triggered work orders, customer notifications. NOT for generic integration. | |
| TODO | fsl-multi-region-architecture | Multi-region FSL architecture: timezone handling, cross-territory scheduling, regional optimization, language. NOT for multi-org strategy. | |

---

## Phase 8 — Health Cloud

### Health Cloud × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | health-cloud-patient-setup | Patient/member account setup: person account configuration, care team roles, patient card, clinical data display. NOT for standard account setup. | |
| TODO | care-plan-configuration | Care plan templates: care plan goals, problems, tasks, care team assignment, care plan lifecycle. NOT for case management. | |
| TODO | care-program-management | Care program setup: enrollment, program tasks, program milestones, patient engagement, program outcomes. NOT for standard program management. | |
| TODO | health-cloud-timeline | Timeline configuration: custom timeline entries, activity filtering, clinical data display, event types. NOT for standard activity timeline. | |
| TODO | referral-management-health | Referral management setup: referral types, provider search, referral tracking, status flow, network management. NOT for Sales Cloud referrals. | |
| TODO | health-cloud-consent-management | Patient consent management: HIPAA authorization forms, consent templates, consent tracking, withdrawal handling. NOT for marketing consent. | |

### Health Cloud × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | care-coordination-requirements | Care coordination process mapping: care team workflow design, transition of care, handoff requirements. NOT for implementation. | |
| TODO | hipaa-workflow-design | HIPAA-compliant workflow requirements: minimum necessary standard, audit trail requirements, access control design. NOT for security implementation. | |
| TODO | patient-engagement-requirements | Patient engagement portal requirements: appointment scheduling, messaging, health assessments, education. NOT for Experience Cloud setup. | |
| TODO | clinical-data-requirements | Clinical data model requirements: HL7/FHIR data mapping, interoperability requirements, data governance. NOT for data migration. | |

### Health Cloud × Dev Role

> Domain folder: `apex`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | health-cloud-apis | Health Cloud APIs: Care Plan API, Clinical Data Model, Patient API, healthcare-specific objects and endpoints. NOT for generic REST API. | |
| TODO | fhir-integration-patterns | FHIR R4 integration: FHIR resources mapping, REST API patterns, CDS Hooks, SMART on FHIR, HL7 conversion. NOT for generic integration. | |
| TODO | health-cloud-lwc-components | Custom LWC for Health Cloud: patient card extensions, timeline components, care plan visualizations, dashboards. NOT for standard LWC. | |
| TODO | clinical-decision-support | Clinical decision support in Salesforce: rules engine, alert triggers, protocol compliance checks, care gap detection. NOT for standard Flow automation. | |
| TODO | health-cloud-apex-extensions | Health Cloud Apex extension points: care plan automation, referral processing, clinical data triggers, consent handling. NOT for standard Apex. | |

### Health Cloud × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | patient-data-migration | Patient data migration: person account mapping, clinical history, care plan history, HIPAA-compliant migration procedures. NOT for generic data migration. | |
| TODO | fhir-data-mapping | Mapping FHIR resources to Health Cloud data model: Patient, Observation, Condition, CarePlan resource mapping. NOT for FHIR integration code. | |
| TODO | health-cloud-data-model | Health Cloud data model: healthcare objects, clinical data model, relationship map, standard vs custom objects. NOT for standard data model. | |
| TODO | consent-data-model-health | Health Cloud consent data model: authorization records, consent history, sharing rules for PHI data. NOT for marketing consent data. | |
| TODO | clinical-data-quality | Clinical data quality: data validation, duplicate patient detection, record merging for patients, MPI patterns. NOT for generic data quality. | |

### Health Cloud × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | hipaa-compliance-architecture | HIPAA compliance architecture in Salesforce: encryption requirements, audit trails, access controls, BAA, risk assessment. NOT for general security. | |
| TODO | fhir-integration-architecture | FHIR integration architecture: connectivity patterns, data synchronization strategy, interoperability layer design. NOT for individual API calls. | |
| TODO | health-cloud-data-residency | Data residency for healthcare: Hyperforce, data localization, cross-border considerations, regulatory alignment. NOT for generic multi-region. | |
| TODO | health-cloud-multi-cloud-strategy | Health Cloud + Service Cloud + Experience Cloud integration strategy for healthcare organizations. NOT for individual cloud architecture. | |
| TODO | payer-vs-provider-architecture | Health Cloud architecture for payer vs provider: member management vs patient management, data model differences. NOT for implementation. | |

---

## Phase 9 — Financial Services Cloud

### FSC × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | financial-account-setup | Financial account configuration: account types, holdings, financial goals, financial account roles, rollup settings. NOT for standard accounts. | |
| TODO | household-model-configuration | FSC household model: household accounts, primary members, household rollups, financial rollups, relationship groups. NOT for NPSP households. | |
| TODO | fsc-referral-management | FSC referral management: referral types, referral scorecard, partner referrals, referral tracking, routing. NOT for Sales Cloud referrals. | |
| TODO | compliant-data-sharing-setup | Compliant Data Sharing configuration: sharing policies, data access levels, compliance walls, data isolation. NOT for standard sharing model. | |
| TODO | fsc-action-plans | Action Plan templates for FSC: client onboarding, account opening, review preparation, compliance tasks. NOT for standard tasks. | |
| TODO | fsc-relationship-groups | Relationship groups: group types, member roles, group-level rollups, wealth aggregation, household alternatives. NOT for standard account relationships. | |

### FSC × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | wealth-management-requirements | Wealth management process mapping: financial planning workflow, portfolio review, client lifecycle, advisor tools. NOT for implementation. | |
| TODO | compliance-documentation-requirements | Compliance documentation requirements: KYC workflows, AML checks, regulatory reporting, audit preparation. NOT for security implementation. | |
| TODO | client-onboarding-design | Client onboarding process design: document collection, approval steps, compliance checks, welcome journey. NOT for implementation. | |
| TODO | financial-planning-process | Financial planning process requirements: goal setting, risk assessment, recommendation workflow, review cycle. NOT for financial advice. | |

### FSC × Dev Role

> Domain folder: `apex`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | fsc-apex-extensions | FSC Apex extension points: financial rollup customization, compliant data sharing overrides, custom actions. NOT for standard Apex. | |
| TODO | fsc-compliant-sharing-api | Compliant Data Sharing API: programmatic policy management, access verification, sharing rule evaluation. NOT for admin setup. | |
| TODO | fsc-financial-calculations | Financial calculation patterns: portfolio performance, goal tracking, wealth rollups, custom aggregation logic. NOT for standard rollup summaries. | |
| TODO | fsc-document-generation | Document generation for FSC: disclosure documents, account statements, compliance reports, PDF generation. NOT for standard document templates. | |
| TODO | fsc-integration-patterns-dev | FSC-specific integration: core banking sync, market data feeds, custodian integration, payment processing. NOT for generic integration. | |

### FSC × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | financial-account-migration | Financial account data migration: account types, holdings, positions, transaction history, balance data. NOT for standard account migration. | |
| TODO | household-data-setup | Household data model setup: member relationships, primary designation, financial data aggregation, group setup. NOT for standard contact import. | |
| TODO | fsc-data-model | FSC data model: financial objects, relationship objects, rollup relationships, industry-specific standard objects. NOT for standard data model. | |
| TODO | financial-data-quality | Financial data quality: account validation, duplicate financial records, data reconciliation with source systems. NOT for generic data quality. | |

### FSC × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | fsc-architecture-patterns | FSC solution architecture: data model decisions, sharing model design, integration strategy, compliance framework. NOT for individual feature design. | |
| TODO | aml-kyc-process-architecture | AML/KYC process architecture: verification workflow, screening integration, risk scoring, regulatory compliance. NOT for implementation. | |
| TODO | wealth-management-architecture | Wealth management platform architecture: advisor workspace, client portal, portfolio analytics, integration. NOT for investment advice. | |
| TODO | insurance-cloud-architecture | Insurance-specific FSC architecture: policy administration, claims processing, underwriting workflow design. NOT for implementation. | |
| TODO | banking-lending-architecture | Banking and lending architecture: loan origination, account servicing, payment processing integration. NOT for implementation. | |

---

## Phase 10 — Nonprofit Cloud (NPSP)

### NPSP × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | npsp-household-accounts | NPSP Household Account model: household naming, household management, primary contact designation, merge rules. NOT for FSC households. | |
| TODO | gift-entry-and-processing | Gift entry setup: gift entry templates, batch gift entry, payment processing, donation allocation, receipting. NOT for standard opportunity creation. | |
| TODO | recurring-donations-setup | Recurring Donations setup: installments, schedules, amount changes, status tracking, payment methods. NOT for standard opportunity products. | |
| TODO | soft-credits-and-matching | Soft credit management: matching gifts, corporate giving attribution, soft credit roles, partial credits. NOT for standard opportunity contact roles. | |
| TODO | npsp-program-management | Program management module: program setup, cohorts, services, service deliveries, outcome tracking, attendance. NOT for case management. | |
| TODO | grant-management-setup | Grant management: funding requests, deliverables, milestones, compliance requirements, reporting, disbursements. NOT for standard opportunity tracking. | |
| TODO | npsp-engagement-plans | Engagement plan templates: donor stewardship, event follow-up, volunteer engagement, automated task creation. NOT for marketing campaigns. | |

### NPSP × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | fundraising-process-mapping | Fundraising process design: cultivation, solicitation, stewardship cycles, major gift workflow, donor pipeline. NOT for implementation. | |
| TODO | program-outcome-tracking-design | Program outcome measurement: logic model design, indicator tracking, impact reporting requirements, evaluation. NOT for CRM Analytics. | |
| TODO | donor-lifecycle-requirements | Donor lifecycle mapping: acquisition, retention, upgrade paths, lapsed donor re-engagement, segmentation. NOT for marketing automation. | |
| TODO | volunteer-management-requirements | Volunteer management process: recruitment, scheduling, hours tracking, recognition, skills matching. NOT for HR systems. | |

### NPSP × Dev Role

> Domain folder: `apex`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | npsp-trigger-framework-extension | Extending NPSP trigger framework (TDTM): custom trigger handlers, recursion management, NPSP-specific patterns. NOT for standard Apex triggers. | |
| TODO | gift-entry-customization | Gift entry customization: custom templates, payment gateway integration, form field customization, validation. NOT for standard form development. | |
| TODO | npsp-api-and-integration | NPSP API: gift processing API, recurring donation API, wealth screening integration, third-party connectors. NOT for standard Salesforce API. | |
| TODO | npsp-custom-rollups | Custom rollup summaries in NPSP: rollup configuration, custom fiscal years, custom filter groups, CRLP. NOT for standard rollup summaries. | |

### NPSP × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | constituent-data-migration | Constituent data migration: contact import, household creation, relationship mapping, duplicate detection. NOT for standard contact import. | |
| TODO | gift-history-import | Donation and gift history import: payment mapping, soft credit creation, campaign attribution, GAU allocation. NOT for standard opportunity import. | |
| TODO | npsp-data-model | NPSP data model: NPSP objects, relationship objects, GAU allocations, recurring donation objects, data dictionary. NOT for standard data model. | |
| TODO | nonprofit-data-quality | Nonprofit data quality: address standardization, duplicate household detection, NCOA processing, data hygiene. NOT for generic data quality. | |

### NPSP × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | npsp-vs-nonprofit-cloud-decision | Decision framework: NPSP (open source) vs new Nonprofit Cloud, migration path, feature comparison, timeline. NOT for implementation. | |
| TODO | nonprofit-platform-architecture | Nonprofit platform architecture: program management, fundraising, engagement, volunteer, reporting strategy. NOT for individual feature design. | |
| TODO | fundraising-integration-patterns | Fundraising system integration: payment gateway, wealth screening, email marketing, event platforms. NOT for generic integration. | |
| TODO | nonprofit-data-architecture | Nonprofit data architecture: constituent 360, household model, giving history, program participation, reporting. NOT for standard data model. | |

---

## Phase 11 — Commerce Cloud

### Commerce Cloud × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | b2b-commerce-store-setup | B2B Commerce store setup: storefront configuration, buyer groups, entitlements, account management, catalogs. NOT for B2C Commerce. | |
| TODO | b2c-commerce-store-setup | B2C Commerce (SFCC) store configuration: cartridges, site configuration, customer management, storefronts. NOT for B2B Commerce. | |
| TODO | commerce-product-catalog | Commerce product catalog: categories, product attributes, entitlement policies, catalog configuration, variants. NOT for CPQ product catalog. | |
| TODO | commerce-pricing-and-promotions | Commerce pricing: pricebooks for commerce, promotions, coupons, tiered pricing, cart-level discounts, rules. NOT for CPQ pricing. | |
| TODO | commerce-checkout-configuration | Checkout flow configuration: payment methods, shipping methods, tax calculation, guest checkout, order summary. NOT for CPQ quoting. | |
| TODO | commerce-order-management | Order management: order lifecycle, fulfillment, returns, exchanges, order status tracking, order summaries. NOT for CPQ orders. | |

### Commerce Cloud × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | b2b-vs-b2c-requirements | B2B vs B2C Commerce requirements: buyer journey differences, account-based vs consumer features, licensing. NOT for implementation. | |
| TODO | commerce-checkout-flow-design | Checkout flow UX design: cart requirements, payment options, shipping rules, guest vs registered experience. NOT for implementation. | |
| TODO | commerce-catalog-strategy | Product catalog strategy: taxonomy design, attribute management, search and navigation requirements, merchandising. NOT for catalog configuration. | |
| TODO | digital-storefront-requirements | Digital storefront requirements: branding, content management, personalization, mobile experience, accessibility. NOT for Experience Cloud requirements. | |

### Commerce Cloud × Dev Role

> Domain folder: `lwc` or `apex` as noted

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | commerce-extension-points | Commerce Cloud extension points: checkout extensions, pricing hooks, cart calculators, custom components. NOT for standard LWC. | |
| TODO | headless-commerce-api | Headless Commerce development: Commerce API, storefront API, custom frontends, React/Angular integration. NOT for standard storefront. | |
| TODO | commerce-payment-integration | Payment gateway integration: payment adapters, custom payment methods, PCI compliance patterns, tokenization. NOT for billing. | |
| TODO | commerce-search-customization | Commerce search: search indexing, faceted navigation, search ranking, product recommendations, Einstein search. NOT for SOSL. | |
| TODO | commerce-lwc-components | Custom LWC for Commerce: product display, cart components, checkout components, wishlist, comparison. NOT for standard LWC. | |
| TODO | commerce-order-api | Order management API: order creation, fulfillment API, returns processing, order status updates, webhooks. NOT for standard REST API. | |

### Commerce Cloud × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | product-catalog-migration-commerce | Commerce product catalog migration: category hierarchy, product attributes, images, pricing data, variants. NOT for CPQ product migration. | |
| TODO | commerce-order-history-migration | Order history migration: historical orders, customer purchase history, returns data, payment records. NOT for standard opportunity migration. | |
| TODO | commerce-analytics-data | Commerce analytics: conversion funnel data, cart abandonment, product performance, revenue metrics, trends. NOT for CRM Analytics. | |
| TODO | commerce-inventory-data | Inventory data management: stock levels, warehouse mapping, inventory sync, availability data, reorder points. NOT for FSL inventory. | |

### Commerce Cloud × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | b2b-vs-b2c-architecture | B2B vs B2C Commerce architecture decisions: platform features, integration patterns, data model differences. NOT for implementation. | |
| TODO | headless-commerce-architecture | Headless Commerce architecture: API-first design, frontend framework selection, performance strategy, caching. NOT for standard storefront. | |
| TODO | multi-store-architecture | Multi-store Commerce architecture: shared catalog, localization, multi-currency, multi-language, regional stores. NOT for single store. | |
| TODO | commerce-integration-patterns | Commerce integration: ERP integration, PIM, payment gateways, shipping providers, tax engines, OMS. NOT for generic integration. | |
| TODO | order-management-architecture | Order management architecture: fulfillment workflow, returns process, inventory management strategy, split orders. NOT for individual order setup. | |

---

## Phase 12 — Agentforce / Einstein AI (Cloud-Specific)

### Agentforce × Admin Role

> Domain folder: `agentforce`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | agentforce-sales-ai-setup | Einstein for Sales setup: opportunity insights, lead scoring, email insights, pipeline inspection, forecasting AI. NOT for core Agentforce setup. | |
| TODO | agentforce-service-ai-setup | Einstein for Service setup: case classification, article recommendations, reply recommendations, work summaries. NOT for core Agentforce setup. | |
| TODO | einstein-search-personalization | Einstein Search personalization: search results ranking, promoted results, searchable objects, natural language search. NOT for SOSL. | |
| TODO | einstein-activity-capture-admin | Einstein Activity Capture administration: email sync, calendar sync, activity metrics, privacy settings, exclusions. NOT for manual activity logging. | |
| TODO | ai-assistant-channel-setup | AI assistant channel deployment: embedded service bot, Slack Agentforce, API access, web deployment, mobile. NOT for standard messaging setup. | |

### Agentforce × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | ai-use-case-assessment | AI use case assessment: identifying AI opportunities, evaluating feasibility, ROI estimation, data readiness. NOT for implementation. | |
| TODO | agent-conversation-design | Conversational AI design: dialog flows, utterance mapping, fallback strategies, escalation criteria, persona. NOT for Agentforce configuration. | |
| TODO | ai-ethics-and-governance-requirements | AI governance requirements: bias mitigation, transparency, human oversight, audit requirements, responsible AI. NOT for Trust Layer configuration. | |
| TODO | ai-adoption-change-management | AI adoption strategy: user training, trust building, feedback collection, success measurement, rollout planning. NOT for general change management. | |

### Agentforce × Dev Role

> Domain folder: `apex` or `agentforce` as noted

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | prompt-template-development | Prompt template development: template types, dynamic fields, grounding with Data Cloud, prompt chaining, testing. NOT for prompt engineering theory. | |
| TODO | einstein-discovery-development | Einstein Discovery: story creation, model deployment, prediction integration, model management via API, scoring. NOT for CRM Analytics dashboards. | |
| TODO | ai-model-integration-apex | Integrating external AI models via Apex: Einstein Platform APIs, external model callouts, response parsing, caching. NOT for Agentforce actions. | |
| TODO | data-cloud-vector-search-dev | Data Cloud vector search development: embedding generation, search index configuration, RAG implementation. NOT for Data Cloud admin. | |
| TODO | agentforce-custom-channel-dev | Building custom Agentforce channels: API-based integration, webhook handling, conversation management, session state. NOT for standard channels. | |

### Agentforce × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | data-cloud-data-streams | Data Cloud data streams: ingesting data, mapping to DMOs, identity resolution, calculated insights, activation. NOT for CRM Analytics data. | |
| TODO | ai-training-data-preparation | Preparing data for Einstein: data quality for ML, feature engineering, label generation, dataset curation. NOT for generic data quality. | |
| TODO | vector-database-management | Vector database setup in Data Cloud: embedding management, search index optimization, data refresh strategies. NOT for standard data management. | |
| TODO | einstein-analytics-data-model | Einstein/CRM Analytics data model: datasets, dataflows, recipes, data sync from objects, augmented analytics. NOT for standard reporting. | |

### Agentforce × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | ai-platform-architecture | AI platform architecture: model selection, grounding strategy, trust layer design, multi-agent orchestration. NOT for individual agent design. | |
| TODO | data-cloud-architecture | Data Cloud architecture: data lake strategy, identity resolution design, activation targets, segmentation strategy. NOT for individual stream setup. | |
| TODO | ai-governance-architecture | AI governance architecture: model lifecycle, audit trail, responsible AI framework, regulatory compliance design. NOT for general security. | |
| TODO | conversational-ai-architecture | Conversational AI architecture: intent classification, dialog management, channel strategy, handoff design. NOT for chatbot configuration. | |

---

## Phase 13 — OmniStudio / Industries (Cloud-Specific)

### OmniStudio × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | industries-insurance-setup | Insurance-specific OmniStudio setup: policy administration objects, claim types, coverage configuration, quoting. NOT for generic OmniStudio. | |
| TODO | industries-communications-setup | Communications Cloud setup: order management, service catalog, contract lifecycle, subscriber management. NOT for generic OmniStudio. | |
| TODO | industries-energy-utilities-setup | Energy & Utilities Cloud setup: service points, usage data, rate plans, meter management, service orders. NOT for generic admin. | |
| TODO | industries-public-sector-setup | Public Sector Solutions setup: licensing, permits, inspections, case management for government, citizen portal. NOT for standard case management. | |
| TODO | omnistudio-admin-configuration | OmniStudio admin setup: namespace configuration, component access, user permissions, org settings, feature toggles. NOT for OmniScript design. | |

### OmniStudio × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | omniscript-flow-design-requirements | OmniScript flow design: screen requirements, branching logic, data requirements, user journey mapping. NOT for OmniScript development. | |
| TODO | flexcard-requirements | FlexCard layout requirements: data visualization, action requirements, embedded component needs, user context. NOT for FlexCard development. | |
| TODO | industries-process-design | Industry-specific process design: insurance claims, telecom order management, utility service requests. NOT for generic process mapping. | |
| TODO | omnistudio-vs-standard-decision | OmniStudio vs standard Flow/LWC decision framework: capability comparison, complexity assessment, team skills. NOT for implementation. | |

### OmniStudio × Dev Role

> Domain folder: `omnistudio`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | omnistudio-testing-patterns | OmniStudio testing: OmniScript preview testing, IP debugging, DataRaptor test strategies, automated testing. NOT for Apex testing. | |
| TODO | industries-api-extensions | Industries-specific API extensions: policy API, claim API, order API, industry-specific REST endpoints. NOT for standard REST API. | |
| TODO | omnistudio-custom-components | Custom OmniStudio components: custom LWC in OmniScripts, override elements, custom actions, validation. NOT for standard LWC. | |
| TODO | omnistudio-ci-cd-patterns | OmniStudio CI/CD: DataPack export/import in pipelines, version control, automated testing, environment promotion. NOT for standard SFDX CI/CD. | |
| TODO | calculation-procedure-development | Calculation Procedure development: step configuration, matrix lookups, complex calculations, pricing logic. NOT for Flow formulas. | |

### OmniStudio × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | industries-data-model | Industries data model: insurance objects, communications objects, energy objects, healthcare objects, relationships. NOT for standard data model. | |
| TODO | omnistudio-datapack-migration | DataPack migration: export/import procedures, environment-specific data, DataPack versioning, conflict resolution. NOT for standard data migration. | |
| TODO | industries-data-migration | Industry-specific data migration: policy migration, subscriber migration, utility account migration, data mapping. NOT for generic data migration. | |
| TODO | omnistudio-metadata-management | OmniStudio metadata management: component dependencies, cross-reference tracking, cleanup, impact analysis. NOT for standard metadata API. | |

### OmniStudio × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | omnistudio-vs-standard-architecture | OmniStudio vs standard platform architecture: when to use OmniStudio, complexity tradeoffs, team skill requirements. NOT for implementation. | |
| TODO | industries-cloud-selection | Industries Cloud selection: which industry cloud fits, customization vs configuration, licensing implications. NOT for implementation. | |
| TODO | omnistudio-scalability-patterns | OmniStudio scalability: high-volume OmniScript handling, caching strategies, API limit management, performance. NOT for generic scalability. | |
| TODO | industries-integration-architecture | Industries-specific integration: insurance ecosystem, telecom BSS/OSS, utility CIS integration, data exchange. NOT for generic integration. | |

---

## Phase 14 — CRM Analytics / Tableau

### CRM Analytics × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | crm-analytics-app-creation | CRM Analytics app creation: dashboard design, lens creation, data sources, app sharing, template selection. NOT for standard reports and dashboards. | |
| TODO | analytics-dataset-management | Dataset creation and management: dataflow scheduling, field selection, date handling, data refresh. NOT for standard report types. | |
| TODO | analytics-dashboard-design | Analytics dashboard design: chart types, bindings, faceting, dashboard interaction, mobile layout, filters. NOT for standard dashboards. | |
| TODO | einstein-discovery-setup | Einstein Discovery setup: story creation, model deployment, prediction fields, what-if analysis, recommendations. NOT for Prediction Builder. | |
| TODO | analytics-data-manager | Data Manager configuration: data sync, connected objects, local transformation, data monitoring, error handling. NOT for standard data management. | |
| TODO | analytics-permission-and-sharing | Analytics permissions: app sharing, row-level security predicates, dataset security, license management, folders. NOT for standard sharing. | |

### CRM Analytics × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | analytics-kpi-definition | KPI definition for analytics: metric design, calculation requirements, benchmarking, target setting, dimensions. NOT for dashboard building. | |
| TODO | analytics-requirements-gathering | Analytics requirements: data source mapping, visualization requirements, audience-specific views, drill-down needs. NOT for standard reporting requirements. | |
| TODO | data-storytelling-design | Data storytelling: narrative structure, insight communication, action-oriented dashboards, executive summaries. NOT for technical dashboard design. | |
| TODO | analytics-adoption-strategy | Analytics adoption: user training, dashboard discovery, embedded analytics strategy, self-service analytics. NOT for general change management. | |

### CRM Analytics × Dev Role

> Domain folder: `admin` (SAQL/JSON-based, not Apex)

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | saql-query-development | SAQL queries: aggregation, windowing, cogroup, filter, foreach, ORDER statements, nested queries, piggyback. NOT for SOQL. | |
| TODO | analytics-dashboard-json | Dashboard JSON editing: advanced bindings, custom queries, layout manipulation, step parameters, interactions. NOT for standard dashboard builder. | |
| TODO | analytics-recipe-design | Recipe creation: data transformation, join patterns, bucket fields, row-level computations, scheduling. NOT for SAQL queries. | |
| TODO | analytics-dataflow-development | Dataflow development: nodes, transformation types, append/update/upsert, scheduling, error handling, optimization. NOT for standard data processing. | |
| TODO | analytics-embedded-components | Embedding analytics: Analytics Dashboard Component in LWC, iframe embedding, context passing, action binding. NOT for standard LWC. | |
| TODO | einstein-discovery-deployment | Einstein Discovery model deployment: prediction fields on records, recommendations in Flow, model refresh, monitoring. NOT for Einstein Discovery setup. | |

### CRM Analytics × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | analytics-data-preparation | Data preparation for analytics: data cleansing, augmentation, external data integration, XMD metadata. NOT for CRM data quality. | |
| TODO | analytics-external-data | External data in CRM Analytics: CSV upload, external connectors, live datasets, Tableau bridge, streaming data. NOT for standard data import. | |
| TODO | analytics-dataset-optimization | Dataset optimization: field selection, date granularity, partitioning, row count management, performance tuning. NOT for SOQL optimization. | |
| TODO | analytics-data-governance | Analytics data governance: dataset lineage, access logging, data classification, retention, compliance. NOT for general data governance. | |

### CRM Analytics × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | crm-analytics-vs-tableau-decision | Decision framework: CRM Analytics vs Tableau Desktop/Server, feature comparison, licensing, integration depth. NOT for implementation. | |
| TODO | analytics-security-architecture | Analytics security: row-level security design, sharing predicates, dataset access strategy, cross-dataset security. NOT for standard sharing model. | |
| TODO | analytics-data-architecture | Analytics data architecture: dataset design, dataflow performance, incremental extraction, data lake strategy. NOT for standard data architecture. | |
| TODO | embedded-analytics-architecture | Embedded analytics architecture: dashboard context, filtering strategy, performance optimization, user experience. NOT for standard Lightning pages. | |

---

## Phase 15 — Integration (Cloud-Specific Patterns)

### Integration × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | integration-admin-connected-apps | Connected App management for integrations: policies, IP restrictions, refresh tokens, monitoring, user assignment. NOT for OAuth flows (use oauth-flows-and-connected-apps). | |
| TODO | remote-site-settings | Remote Site Settings and CSP Trusted Sites: managing external endpoints, security considerations, troubleshooting. NOT for Named Credentials. | |
| TODO | outbound-message-setup | Workflow outbound message configuration: endpoint setup, retry settings, field selection, monitoring delivery. NOT for Platform Events. | |
| TODO | integration-user-management | Integration user setup: dedicated user, API-only profiles, permission management, session policies, monitoring. NOT for standard user management. | |
| TODO | change-data-capture-admin | Change Data Capture admin setup: entity selection, channel management, monitoring, limits, enrichment. NOT for CDC Apex triggers. | |

### Integration × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | integration-pattern-selection | Integration pattern selection: point-to-point vs hub-and-spoke vs event-driven, decision criteria, cost analysis. NOT for implementation. | |
| TODO | api-contract-documentation | API contract documentation: request/response specs, error codes, versioning policy, rate limits, SLAs. NOT for API implementation. | |
| TODO | data-mapping-requirements | Data mapping documentation: field-level mapping, transformation rules, validation requirements, default values. NOT for data migration. | |
| TODO | integration-testing-requirements | Integration testing requirements: test scenarios, mock services, end-to-end validation criteria, performance testing. NOT for test implementation. | |

### Integration × Dev Role

> Domain folder: `integration`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | salesforce-to-salesforce-integration | Salesforce-to-Salesforce integration patterns: S2S feature, API-based sync, Platform Event bridging, data sharing. NOT for multi-org strategy. | |
| TODO | middleware-integration-patterns | Middleware integration: MuleSoft, Dell Boomi, Workato, Informatica patterns for Salesforce connectivity. NOT for native API. | |
| TODO | idempotent-integration-patterns | Idempotency in integrations: external ID upsert, duplicate prevention, retry-safe patterns, transaction boundaries. NOT for duplicate management. | |
| TODO | real-time-vs-batch-integration | Real-time vs batch integration patterns: trigger-based sync, scheduled batch, hybrid approaches, decision criteria. NOT for Batch Apex (use batch-apex-patterns). | |
| TODO | error-handling-in-integrations | Integration error handling: retry strategies, dead letter queues, error logging, notification patterns, circuit breaker. NOT for Apex exception handling. | |

### Integration × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | cdc-data-sync-patterns | Change Data Capture data sync: incremental replication, replay strategy, data consistency, ordering guarantees. NOT for CDC admin setup. | |
| TODO | integration-data-quality | Data quality in integration: data validation at boundaries, cleansing during sync, reconciliation, conflict resolution. NOT for CRM data quality. | |
| TODO | etl-vs-api-data-patterns | ETL tools vs API for data integration: Informatica Cloud, Jitterbit, MuleSoft Batch, tool selection criteria. NOT for Data Loader. | |
| TODO | data-virtualization-patterns | Data virtualization: Salesforce Connect patterns, External Objects, OData integration, live data access tradeoffs. NOT for Salesforce Connect admin (use salesforce-connect-external-objects). | |

### Integration × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | api-led-connectivity-architecture | API-led connectivity architecture: system, process, experience API layers, design principles, governance. NOT for individual API implementation. | |
| TODO | event-driven-architecture | Event-driven architecture: event design, event mesh, choreography vs orchestration, event sourcing patterns. NOT for Platform Events implementation. | |
| TODO | integration-security-architecture | Integration security: mTLS, OAuth patterns, API gateway, IP whitelisting, certificate management strategy. NOT for basic Connected App setup. | |
| TODO | hybrid-integration-architecture | Hybrid integration: on-premise to cloud patterns, reverse proxy, VPN, Private Connect, data residency. NOT for cloud-to-cloud only. | |
| TODO | mulesoft-anypoint-architecture | MuleSoft Anypoint Platform architecture: CloudHub, Runtime Fabric, API Manager, Exchange, governance. NOT for Salesforce-native integration. | |

---

## Phase 16 — DevOps (Cloud-Specific Deployment Patterns)

### DevOps × Admin Role

> Domain folder: `devops`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | cpq-deployment-administration | CPQ metadata deployment: product rules, pricing rules, quote templates, deployment ordering for CPQ components. NOT for standard change sets. | |
| TODO | omnistudio-deployment-admin | OmniStudio DataPack management: export, import, version control, environment-specific data in DataPacks. NOT for standard deployment. | |
| TODO | experience-cloud-deployment-admin | Experience Cloud site deployment: publishing, template versioning, content migration between environments. NOT for standard deployment. | |
| TODO | managed-package-installation | Installing and upgrading managed packages: pre-install checks, post-install configuration, version management. NOT for building packages. | |
| TODO | deployment-monitoring | Deployment monitoring: status tracking, component errors, test failures, deployment history, troubleshooting. NOT for Apex debugging. | |

### DevOps × BA Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | deployment-risk-assessment | Deployment risk assessment: change impact analysis, rollback planning, user communication, go-live checklist. NOT for deployment execution. | |
| TODO | devops-process-documentation | DevOps process documentation: runbook creation, deployment guides, environment matrix, onboarding docs. NOT for release planning. | |
| TODO | change-advisory-board-process | Change advisory board process: change request classification, approval workflows, change calendar, risk assessment. NOT for Salesforce approval processes. | |

### DevOps × Dev Role

> Domain folder: `devops`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | cpq-deployment-patterns | CPQ deployment ordering: product rules, pricing rules, quote templates, billing config, dependency sequence in CI/CD. NOT for generic SFDX deployment. | |
| TODO | health-cloud-deployment-patterns | Health Cloud deployment: care plan templates, clinical metadata, HIPAA-specific deployment ordering. NOT for generic deployment. | |
| TODO | fsc-deployment-patterns | FSC deployment: compliant data sharing config, household model metadata, industry-specific deployment ordering. NOT for generic deployment. | |
| TODO | experience-cloud-deployment-dev | Experience Cloud deployment scripting: site metadata retrieval, CMS content deployment, LWR template deployment. NOT for standard SFDX. | |
| TODO | managed-package-development | Building managed packages: namespace, versioned components, subscriber org patterns, package upgrade scripts, ISV patterns. NOT for unlocked packages. | |
| TODO | cross-cloud-deployment-patterns | Cross-cloud deployment: handling dependencies across Sales/Service/Experience Cloud metadata, deployment sequencing. NOT for single-cloud deployment. | |

### DevOps × Data Role

> Domain folder: `data`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | test-data-management-devops | Test data management: factory patterns, data setup scripts, anonymization, data generation, fixture files. NOT for production data migration. | |
| TODO | deployment-data-dependencies | Managing data dependencies in deployments: record type IDs, custom metadata records, environment-specific values. NOT for metadata deployment. | |
| TODO | sandbox-refresh-data-strategies | Managing data during sandbox refresh: post-copy automation, data selection, reference data seeding, cleanup. NOT for sandbox admin setup. | |
| TODO | cross-cloud-data-deployment | Cross-cloud data deployment: deploying shared reference data across Sales, Service, Marketing environments. NOT for data migration. | |

### DevOps × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | ci-cd-pipeline-architecture | CI/CD pipeline architecture for Salesforce: stages, quality gates, deployment automation, monitoring strategy. NOT for individual CI tool setup. | |
| TODO | cloud-specific-deployment-architecture | Cloud-specific deployment architecture: deployment ordering across clouds, cross-cloud metadata dependencies. NOT for generic deployment. | |
| TODO | package-development-strategy | Package development strategy: unmanaged vs unlocked vs managed, namespace decisions, ISV considerations. NOT for individual package creation. | |
| TODO | deployment-automation-architecture | End-to-end deployment automation: zero-downtime deployments, canary releases, automated rollback, monitoring. NOT for manual deployment. | |

---

## Phase 17 — Data Cloud

### Data Cloud × Admin Role

> Domain folder: `admin`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | data-cloud-provisioning | Data Cloud provisioning and setup: data spaces, data streams, ingestion API, activation targets, licensing. NOT for CRM Analytics. | |
| TODO | data-cloud-identity-resolution | Identity resolution rulesets: matching rules, reconciliation rules, unified profiles, cross-device identity. NOT for duplicate management in CRM. | |
| TODO | data-cloud-calculated-insights | Calculated insights creation: metrics, dimensions, streaming insights, scheduled refresh, insight configuration. NOT for standard formula fields. | |
| TODO | data-cloud-segmentation | Segmentation in Data Cloud: segment creation, filters, activation, audience publishing, segment refresh. NOT for Marketing Cloud segments. | |
| TODO | data-cloud-data-model-objects | Data Model Objects (DMOs): mapping, relationships, data transforms, data lake objects, schema management. NOT for standard CRM objects. | |

### Data Cloud × Dev Role

> Domain folder: `apex` or `integration`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | data-cloud-ingestion-api | Data Cloud Ingestion API: streaming and bulk ingestion, connector development, schema management, error handling. NOT for standard Bulk API. | |
| TODO | data-cloud-query-api | Data Cloud SQL queries: query profile data, calculated insights, data lake objects, query optimization. NOT for SOQL. | |
| TODO | data-cloud-activation-development | Data Cloud activation targets: custom activation, webhook triggers, CRM actions, Marketing Cloud push, Flow triggers. NOT for admin activation. | |
| TODO | data-cloud-vector-search | Vector search in Data Cloud: embedding configuration, search indexes, RAG integration, semantic search, similarity. NOT for SOSL. | |

### Data Cloud × Architect Role

> Domain folder: `architect`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | data-cloud-architecture-patterns | Data Cloud architecture: ingestion strategy, identity resolution design, activation workflow, data model planning. NOT for individual feature setup. | |
| TODO | data-cloud-integration-strategy | Data Cloud integration: connecting source systems, streaming vs batch, lakehouse patterns, data pipeline design. NOT for standard integration. | |
| TODO | data-cloud-vs-analytics-decision | Data Cloud vs CRM Analytics: when to use each, complementary patterns, data flow design, overlapping capabilities. NOT for implementation. | |
| TODO | data-cloud-consent-and-privacy | Data Cloud consent: consent framework, data subject requests, privacy compliance, data retention, GDPR/CCPA. NOT for general GDPR. | |

---

## Phase 18 — Slack Integration

> Domain folder: `integration`

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | slack-salesforce-integration-setup | Slack app for Salesforce setup: connected org, channel linking, record sharing, notifications, search. NOT for custom Slack apps. | |
| TODO | slack-workflow-builder | Slack Workflow Builder with Salesforce: triggers, steps, data actions, automated notifications, approval flows. NOT for Salesforce Flow. | |
| TODO | flow-for-slack | Flow actions for Slack: send Slack messages from Flow, create channels, post to Slack from automation, templates. NOT for Slack Workflow Builder. | |
| TODO | slack-connect-patterns | Slack Connect for cross-org communication: channel sharing, data security, compliance, external collaboration. NOT for Salesforce-to-Salesforce integration. | |
| TODO | agentforce-in-slack | Agentforce deployment in Slack: agent channel configuration, Slack-specific actions, user experience, permissions. NOT for core Agentforce setup. | |

---

## Phase 19 — Additional Industry Clouds

> Domain folder: varies by topic

| Status | Skill Name | Description | Notes |
|--------|------------|-------------|-------|
| TODO | loyalty-management-setup | Loyalty Management: program creation, tier rules, point accrual, redemption rules, partner loyalty, member portal. NOT for Marketing Cloud engagement. | admin |
| TODO | loyalty-program-architecture | Loyalty Management architecture: tier design, point economy, partner integration, fraud prevention, scaling. NOT for implementation. | architect |
| TODO | net-zero-cloud-setup | Net Zero Cloud (Sustainability Cloud): carbon accounting, emission factors, sustainability reporting, targets. NOT for standard reporting. | admin |
| TODO | sustainability-reporting | Sustainability reporting: ESG metrics, carbon footprint tracking, compliance reporting, disclosure frameworks. NOT for CRM Analytics. | admin |
| TODO | automotive-cloud-setup | Automotive Cloud: vehicle lifecycle, dealer management, lead distribution, inventory management, test drives. NOT for standard Sales Cloud. | admin |
| TODO | education-cloud-eda-setup | Education Cloud (EDA): student success hub, advisor workflows, enrollment management, academic data model. NOT for standard case management. | admin |
| TODO | consumer-goods-cloud-setup | Consumer Goods Cloud: visit execution, retail execution, route planning, compliance checks, off-shelf detection. NOT for Field Service. | admin |
| TODO | manufacturing-cloud-setup | Manufacturing Cloud: account-based forecasting, rebate management, sales agreements, partner performance. NOT for standard forecasting. | admin |
| TODO | public-sector-solutions-setup | Public Sector Solutions: licensing, permits, inspections, case management for government, citizen engagement. NOT for standard case management. | admin |
| TODO | media-cloud-setup | Media Cloud: ad sales management, audience segmentation, campaign management for media, revenue management. NOT for Marketing Cloud. | admin |
| TODO | salesforce-maps-setup | Salesforce Maps: route optimization, territory planning, live tracking, geolocation visualization, proximity search, drive-time analysis. NOT for Field Service scheduling. | admin |
| TODO | rebate-management-setup | Rebate Management: rebate types, payout calculations, accruals, partner rebates, program setup, compliance reporting. NOT for CPQ discounts. | admin |
| TODO | revenue-intelligence-setup | Revenue Intelligence: pipeline inspection, deal insights, forecast accuracy analytics, Einstein analytics for sales leaders. NOT for CRM Analytics setup (use crm-analytics-* skills). | admin |
| TODO | salesforce-erd-and-diagramming | Salesforce ERD and diagram generation: Mermaid/PlantUML data model diagrams for standard clouds (Sales, Service, FSL, Commerce, Revenue Cloud), OAuth flow diagrams, architecture diagram patterns, object relationship visualization. NOT for data model design decisions (use data-model-design-patterns). | architect |
| TODO | salesforce-backup-and-restore | Salesforce Backup & Restore: native backup service, Odaseva/OwnBackup, metadata backup, recovery procedures, retention policies, compliance. NOT for data archival (use data-archival-strategies). | devops |
| TODO | eda-data-model-and-patterns | Education Data Architecture (EDA) data model: Account record types for Academic, Household, Business, Administrative; Contact-centric model, Affiliations, Program Plans, Course Connections, Term/Course hierarchy. NOT for standard data model. | data |

---

## Handoff Log

| Agent | Task | Started | Completed | Notes |
|-------|------|---------|-----------|-------|
| Claude Opus 4.6 | Full queue population — Phase 0 + Phases 2-19 | 2026-04-04 | 2026-04-04 | 549 TODO rows added across 20 phases |
| Claude Opus 4.6 | Second pass + TDD extraction — 21 new skills | 2026-04-04 | 2026-04-04 | Added skills from TDD v1.5 (error handling framework, BRE, gov cloud, multi-IdP SSO, doc gen, etc.) + general gap fills (Visualforce, Platform Cache, reports, person accounts, Salesforce Maps, etc.) |
| Claude Opus 4.6 | Third pass — 14 more skills from SIP, BC/DR, Test Plan, R2/R3, Impl Plan docs | 2026-04-04 | 2026-04-04 | go-live-cutover-planning, performance-testing-salesforce, recaptcha-and-bot-prevention, session-management-and-timeout, multi-language, surveys, user-access-policies, batch-job-monitoring, stub-testing, api-error-handling, batch-data-cleanup, data-storage-management + 2 more |
| Claude Opus 4.6 | Fourth pass — 49 tribal-knowledge + RAG-gap skills | 2026-04-04 | 2026-04-04 | Deep research: platform gotchas (order-of-execution, mixed DML, record locking, timezone), enterprise patterns (fflib, feature flags), production survival (release prep, org limits, support escalation), troubleshooting (common Apex/LWC/Flow errors), data reality (external IDs, merge implications, dedup, reconciliation), integration hardening (retry/backoff), senior admin (page perf, report perf, license optimization), AI-era (sf-to-llm pipelines, ai-ready architecture), Higher Ed (EDA, SIS, FERPA), plus RAG-gap fills (in-app guidance, Lightning App Builder, PDF generation, HA/DR) |

---

## Anti-Patterns (Do Not Do These)

- Do not create a skill for a Cloud × Role cell before verifying no duplicate exists.
- Do not write content from memory. Every factual claim needs an official source.
- Do not create overlapping skills. Always run search_knowledge.py first.
- Do not hand-edit registry/, vector_index/, or docs/SKILLS.md.
- Do not mark DONE until validate_repo.py exits 0.
- Do not skip the query fixture step. Skills with no fixture produce a WARN that fails CI.
