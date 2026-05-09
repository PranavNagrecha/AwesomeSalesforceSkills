# Skill Gap Verification — 2026-05-09

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **994 skills** (up from 981 on 2026-05-08; ~13 skills shipped in the 24 hours since the last verification run).

## Sources scanned

- **Decision-tree branch gaps** — re-walked every skill cited under `standards/decision-trees/*.md`. The single still-unresolved label `skills/integration/oauth-flows` continues to be a stale alias for `integration/oauth-flows-and-connected-apps` (flagged on 2026-05-05 and 2026-05-08); not a real gap.
- **Cross-skill broken references** — grep over `skills/**/SKILL.md` and `skills/**/references/*.md` produced 16 broken paths. 13 are the same stale labels enumerated on 2026-05-08 (admin/order-of-execution, apex/apex-security-crud-fls, devops/sfdx-cicd-pipeline, etc., all aliases for existing skills under different slugs). The 3 *new* hits since 2026-05-08:
  - `skills/apex/dynamic-soql` — covered by `apex/apex-dynamic-soql-binding-safety` + `apex/soql-fundamentals`; alias only
  - `skills/service/email-to-case` — exists at `admin/email-to-case-configuration`; stale label
  - `skills/territory/capacity` — false positive, the regex caught a hyphenless line break in `admin/fsl-shifts-and-crew/references/llm-anti-patterns.md` (`Resource skills/territory/capacity` was actually `... Resource skills, territory, capacity`)
  
  No real gap surfaced.
- **Topic-driven probing** — 16 candidate phrasings ran, spanning Agentforce (Atlas Reasoning Engine), integration (GraphQL, Pub/Sub, Heroku Connect, Salesforce Functions retirement), architect (Hyperforce, Industries data model, B2B vs B2C commerce), security (Apex Crypto, JWT EncryptedKey rotation), data (Salesforce Backup, Privacy Center), platform (User Mode SOQL, Custom Address fields, External Services), Lightning (LWS migration, headless quick actions, LMS), and tooling (DevOps Center, sf CLI custom plugin authoring, Salesforce Code Analyzer). All but **one** routed cleanly to existing skills with score ≥ 4.0 in the target domain. The one outlier:
  - **sf CLI custom plugin authoring** (oclif + `@salesforce/sf-plugins-core`, `SfCommand`, topic-separator v2, JSON contract, hooks, signed distribution) — three different phrasings produced top-skill scores of 2.249, 2.310, and 3.080, with the highest-scoring hit (`apex/cpq-apex-plugins`, 3.080) being a wrong-domain match (CPQ pricing plugins are an entirely different concept). Verbatim grep across the corpus for `oclif`, `sf-plugins-core`, `@salesforce/sf-plugins-core`, `SfCommand`, `plugin-template-sf` returned **zero hits**. The closest existing skill, `devops/salesforce-cli-automation`, covers *consuming* `sf` (and existing plugins) inside CI scripts, not *authoring* plugin packages — confirmed by reading its description: "automating Salesforce work with the unified Salesforce CLI ... shell scripts, Make/npm tasks, cron jobs, and CI steps". **Verified gap.**

## Candidate evaluation

Threshold rules (from scheduled-task brief):
- Top hit > 4.0 in same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta.
- Top hit < 2.5 across all phrasings → ACCEPT.

### A. devops/sf-cli-plugin-authoring — ACCEPT

| Phrasing | Top skill (score) | Delta articulated |
|---|---|---|
| `build sf CLI plugin oclif typescript Salesforce custom command` | `devops/salesforce-cli-automation` (2.249) | Existing skill covers consumer-side automation (running `sf` in CI). Authoring side — `SfCommand` lifecycle, flag factories, JSON contract design, sfdx → sf migration, oclif hooks, signed distribution — is not in any skill. |
| `author distribute custom Salesforce CLI plugin npm registry hooks lifecycle` | `apex/cpq-apex-plugins` (2.558, wrong-domain match) | "plugin" overload — CPQ Apex plugins (`SBQQ.CalculatorPlugin` interface) are unrelated to CLI plugins. |
| `sf-plugins-core requiredOrgFlag json output flag class jsonFlag config hooks` | `devops/salesforce-cli-automation` (2.310) | Same delta as above; existing skill mentions "plugins" only in the context of pinning versions for runner stability. |

Top score across all phrasings is 3.080 (and that's a wrong-domain CPQ match). All three correct-domain candidates score < 2.5. ACCEPT — verified gap with rich official-source backing in the Salesforce CLI Reference, the DX Developer Guide, the upstream `salesforcecli/cli` repo, and the oclif framework docs.

## Candidates rejected

| Candidate | Top hit | Score | Reason rejected |
|---|---|---|---|
| Atlas Reasoning Engine deep-dive | `agentforce/custom-agent-actions-apex` | 5.848 | Atlas concepts already named and described in custom-agent-actions; reasoning loop covered in `architect/conversational-ai-architecture` (5.757). Delta absent. |
| Salesforce GraphQL connection pagination | `integration/graphql-api-patterns` | 8.454 | Skill exists at high score with explicit cursor-pagination examples. |
| Pub/Sub API gRPC subscription deep-dive | `integration/pub-sub-api-patterns` | 6.401 | Skill exists; covers Subscribe vs ManagedSubscribe, FetchRequest, replay IDs. |
| Salesforce Code Analyzer v5 | `devops/salesforce-code-analyzer` | 10.702 | Skill exists at near-max score; v4→v5 migration covered. |
| Heroku Connect bidirectional sync | `integration/heroku-salesforce-integration` | 10.380 | Skill exists; covers Connect, AppLink, External Objects, demo-plan caps. |
| Hyperforce data residency | `architect/hyperforce-architecture` | 10.325 | Skill exists; covers IP allowlist migration, Schrems II nuance, region semantics. |
| Salesforce Functions retirement | `integration/salesforce-functions-replacement` | 12.149 | Skill exists at near-max score. |
| Marketing Cloud Engagement deep-dive | `admin/marketing-cloud-engagement-setup` + 22 related skills | 7.734 | Marketing-cloud coverage is dense (22 skills); no specific sub-topic gap surfaced. |
| Industries CPQ / Vlocity OmniScript versioning | `omnistudio/industries-cpq-vs-salesforce-cpq` | 10.253 | Skill exists at near-max score. |
| Salesforce Connect external object odata | `data/data-virtualization-patterns` | 9.084 | Skill exists; integration/salesforce-connect-external-objects (2.122) covers a different angle. |
| Tableau dashboard embed | `integration/tableau-salesforce-connector` | 7.131 | Skill exists; covers embedding, live vs extract, Tableau for Salesforce SKU. |
| Slack Connect / Workflow Builder | `integration/slack-workflow-builder` | 10.792 | Skill exists at near-max score. |
| Privacy Center / GDPR right to erasure | `data/data-cloud-consent-and-privacy` + `security/gdpr-data-privacy` | 8.598 | Two skills cover; Privacy Center discussed explicitly. |
| Apex Crypto digital signatures | `apex/apex-encoding-and-crypto` | 9.439 | Skill exists; HMAC, RSA-SHA256, signWithCertificate covered. |
| User Mode Apex SOQL/DML | `apex/apex-dynamic-soql-binding-safety` (8.688) + `apex/apex-with-without-sharing-decision` | 2.017 (initial), 8.688 (refined) | Coverage distributed across 3+ skills with depth; refined phrasing (`WITH USER_MODE` + `Database.queryWithBinds`) returns 8.688 hit. |
| Apex External Services schema registration | `flow/flow-external-services` | 10.689 | Skill exists at near-max score. |
| Mobile Publisher branded apps | `admin/mobile-publisher` | 12.090 | Skill exists at near-max score. |
| Apex callout HTTP/2 / retry / idempotency | `apex/apex-callout-retry-and-resilience` + `integration/api-error-handling-design` | 4.666 + 3.926 | Two skills cover; idempotency-key pattern called out in api-error-handling-design Pattern 3. |
| LWC Locker → LWS migration | `lwc/lwc-locker-to-lws-migration` | 2.799 | Skill exists; threshold borderline but explicit migration runbook present. |
| Lightning headless quick actions | `lwc/lwc-quick-actions` (6.851) + `admin/custom-button-to-action-migration` | 6.851 | Skill exists. |
| Salesforce CMS workspaces / managed content | `admin/experience-cloud-cms-content` | 7.734 | Skill exists; covers workspaces, content types, channels, audience targeting. |
| Compound Address fields | `admin/compound-field-patterns` | 6.239 | Skill exists. |
| API version compatibility / Apex behavior changes | `devops/api-version-management` | 6.302 | Skill exists; per-version behavior gotchas documented. |
| Hyperforce IP allowlist migration | `architect/hyperforce-architecture` (6.259) + `architect/integration-security-architecture` (3.797) | 6.259 | Two skills cover; IP-allowlist migration walkthrough already in hyperforce-architecture/examples.md. |
| Industries Common Data Model | `architect/industries-data-model` | 5.104 | Skill exists; covers FSC, Insurance, Communications, Health Cloud objects. |
| B2B vs B2C Commerce platform selection | `architect/b2b-vs-b2c-architecture` | 6.504 | Skill exists. |
| MetadataAPI quick deploy / resume | `devops/post-deployment-validation` | 7.934 | Skill exists; quick-deploy and resume mechanics documented. |
| JWT bearer flow / EncryptedKey rotation | `apex/apex-jwt-bearer-flow` (2.268) + `security/service-account-credential-rotation` (3.797) | 3.797 | Two skills cover with depth; rotation mechanics documented. |
| Salesforce Surveys / Feedback Management | `admin/salesforce-surveys` (skill exists in folder) + `architect/customer-effort-scoring` (3.137) | n/a | Dedicated skill exists. |
| Salesforce Backup product | `data/salesforce-backup-and-restore` | 5.928 | Skill exists. |
| Apex savepoint / rollback nesting | `apex/apex-savepoint-and-rollback` | 8.573 | Skill exists. |
| Apex REST custom resource versioning | `apex/apex-rest-services` | 7.146 | Skill exists; versioning explicitly in Output Artifacts. |
| LWC LMS / Aura PubSub migration | `lwc/lwc-pubsub-patterns` | 5.596 | Skill exists; LMS vs c/pubsub tradeoffs documented. |
| Reactive screen flow formula recompute | `flow/flow-reactive-screen-components` (4.360) + `flow/flow-formula-and-expression-patterns` (1.542) | 4.360 | Skill exists; recompute behavior documented in gotchas. |

## Outcome

**1 skill accepted, 0 wired to run-time agents (`runtime_orphan: true`).**

Wiring rationale (per AGENT_RULES.md Step 6 judgment-call test "an agent should cite a skill only when reading it would change the agent's output for a real invocation"):

The 56 user-facing run-time agents are CRM-and-architecture-focused (refactor Apex, design objects, audit sharing, plan release trains, etc.). None of them author or audit `sf` CLI plugin code. The closest candidate, `deployment-risk-scorer`, scores deployment risk on metadata changes — not on CI runner configuration where a custom plugin lives. The `release-train-planner` covers release cadence but doesn't audit plugin source. Forcing a citation into either would dilute their `Mandatory Reads` with off-topic noise.

Marking `runtime_orphan: true` is the explicit-intent mechanism AGENT_RULES added precisely for developer-facing reference skills.

## Routing scores after build

| Query | Top skill (score) |
|---|---|
| `create custom sf CLI plugin SfCommand class flag oclif scaffold` | devops/sf-cli-plugin-authoring (**6.995**) |
| `migrate sfdx plugin command to sf v2 topic separator deprecate aliases` | devops/sf-cli-plugin-authoring (**5.971**) |
| `sf-plugins-core requiredOrgFlag json output flag class jsonFlag config hooks` | devops/sf-cli-plugin-authoring (**6.995**) |

The new skill ranks #1 on all three target queries with scores well above the >2.5 fixture-required ranking.

## Validation result

`python3 scripts/validate_repo.py --changed-only` — **1 skill validated, 0 errors, 0 warnings.**

`python3 scripts/validate_repo.py --domain devops` — **67 skills validated, 0 errors, 2 warnings** (both pre-existing, on `bitbucket-pipelines-for-salesforce` near-duplicating `github-actions-for-salesforce` and `gitlab-ci-for-salesforce`; not related to the new skill).

Checker script `check_sf_cli_plugin_authoring.py` verified on synthetic plugin trees: detects colon `topicSeparator`, missing `@salesforce/sf-plugins-core` dependency, `console.log` calls, `process.exit()` calls, hand-parsing of `process.argv`, `SfCommand<any>` declarations, `Promise<any>` returns from `run()`, invented `Flags.<name>()` factories (email, url, password, json, regex), unknown-factory warnings, alias-without-deprecate warnings, and missing/empty `messages/` directory. Clean tree returns "No issues found." with exit 0.

## Backlog observations

The catalog continues to saturate (994 skills as of 2026-05-09; +13 in 24h). The cross-skill broken-reference list is still 13–16 stale aliases — a documentation cleanup wave, not a skill-gap signal. Two phrasings that scored 1.5–2.5 on first probe (Marketing Cloud Engagement, screen-flow image display) resolved to existing skills on more careful examination — vocabulary mismatch, not missing knowledge. Steady-state outcome remains "0–1 skills shipped per run."
