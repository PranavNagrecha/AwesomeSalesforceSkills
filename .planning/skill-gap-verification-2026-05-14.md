# Skill Gap Verification — 2026-05-14

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **997 skills**.

## Sources scanned

- **BACKLOG.yaml `RESEARCHED` entries (preferred per dashboard)** — 3 entries marked as "ready to build" since they have research notes attached. Verified against current corpus.
- **Topic-driven probing across niche/recent platform surfaces** — 15 phrasings spanning Agentforce reasoning loops, scratch org snapshots, FSL mobile offline, Data Cloud identity, Apex Quiddity, Files Connect, Web-to-X anti-spam, pre-chat forms, ApiVersion mismatch, DataWeave for Apex, Salesforce Mobile SDK (native), Headless Identity, Apex Schema describe, Bulk API 2.0, Approval recall.
- **Decision-tree branch gaps (Step A)** — last walked 2026-05-10; all branch-recommended technologies still resolve to existing skills at score ≥ 5. Not re-walked.
- **Cross-skill broken references (Step B)** — same 6 stale-rename entries enumerated 2026-05-13. All point to skills that exist under different slugs at high score. Doc-hygiene, not skill gap. Skipped.
- **Recent Salesforce release notes (Step C)** — last fresh scan 2026-05-11 confirmed catalog steady at 997. With zero net adds across 4 runs, re-fetching not productive.

## Threshold rules from scheduled-task brief

- Top hit > 4.0 same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta in plain language.
- Top hit < 2.5 across all phrasings → ACCEPT.

## Candidates verified (18 total — all rejected)

### BACKLOG `RESEARCHED` entries (3) — all reject auto

| # | Candidate | Phrasing | Best hit (same domain) | Decision |
|---|---|---|---|---|
| 1 | `email-deliverability-monitoring` | "email deliverability monitoring bounce management SPF DKIM DMARC" | `admin/email-deliverability-strategy` 11.931 | **REJECT auto** — near-max same-domain score; explicit triggers cover SPF/DKIM/DMARC, bounce, IPR, deliverability assessment. The "RESEARCHED" flag is stale — should be reclassified `DUPLICATE`. |
| 2 | `classic-to-lightning-migration` | "classic to lightning experience migration readiness check" | `admin/lightning-experience-transition` 11.742 | **REJECT auto** — near-max same-domain score; Readiness-Check-Driven Wave Plan pattern, Phase 0 discover checklist with Readiness Check PDF archive, Visualforce + JavaScript-button gap triage all present. Should be reclassified `DUPLICATE`. |
| 3 | `content-document-management` | "ContentVersion ContentDocument ContentDocumentLink file sharing libraries" | `data/attachment-to-files-migration` 7.572; `apex/apex-blob-and-content-version` 2.127 | **REJECT auto** — top hit >4.0; attachment-to-files-migration covers the three-object insert sequence (ContentVersion → ContentDocument → ContentDocumentLink) and the sharing translation map; apex-blob-and-content-version covers the Apex producer/consumer surface including the "envelope vs file vs share" mental model. `data/salesforce-files-architecture` (seen at 1.251 in chunks) is the missing-piece architecture skill. Comprehensive 3-skill coverage. |

### Topic-driven probes (15) — all reject

| # | Candidate | Best hit (score) | Decision |
|---|---|---|---|
| 4 | agentforce-reasoning-loop | `architect/conversational-ai-architecture` 4.661 | **REJECT auto** — top hit >4.0; covers Agentforce session concurrency vs Omni-Channel capacity, reasoning-loop re-evaluation cost from imperative instructions. `agentforce/agentforce-guardrails` (1.524) covers prompt-induced loop amplification. |
| 5 | scratch-org-snapshot | `devops/scratch-org-snapshots` 5.623 | **REJECT auto** — same-domain skill exists; covers `sf org create snapshot`, source-tracking interaction. |
| 6 | fsl-mobile-offline-briefcase-deep | `admin/fsl-mobile-workflow-design` 7.186 | **REJECT auto** — near-max same-domain score; Briefcase priming, offline-first architecture, briefcase field audit all present. |
| 7 | data-cloud-identity-resolution | `admin/data-cloud-identity-resolution` 10.114 | **REJECT auto** — direct same-name skill at near-max score; ruleset, match rules, reconciliation, vs CRM Duplicate Rules disambiguation all covered. |
| 8 | apex-quiddity-request-type | `apex/salesforce-debug-log-analysis` 7.402 | **REJECT auto** — same-domain skill near-max; Quiddity tag, request type, callout signature analysis present. |
| 9 | files-connect-external-source | `integration/file-and-document-integration` 3.198; `data/salesforce-files-architecture` 1.740 | **REJECT** — both same-domain; file-and-document-integration has dedicated "Files Connect (External File Surfacing)" section AND Gotcha 5 ("Does Not Support Write-Back"); salesforce-files-architecture has explicit `## Files Connect` section. Coverage is in two adjacent skills. A standalone Files Connect skill would create N-way overlap. |
| 10 | web-to-lead-spam-protection | `security/recaptcha-and-bot-prevention` 9.512 | **REJECT auto** — direct hit; covers Web-to-Case/Lead reCAPTCHA wiring, 500/day exhaustion protection, Headless Identity registration. |
| 11 | pre-chat-form-prefill | `admin/messaging-and-chat-setup` 7.759 | **REJECT auto** — same-domain near-max; Gotcha 3 + Anti-Pattern 3 dedicated to pre-chat fields and the "don't auto-link Contact" pitfall. |
| 12 | api-version-mismatch-deploy | `devops/api-version-management` 3.623; `devops/deployment-error-troubleshooting` 2.828; `flow/flow-deployment-and-packaging` (Gotcha 11) | **REJECT** — coverage in 3 adjacent skills, each owning a slice: api-version-management Gotcha 5 (package.xml vs component apiVersion); deployment-error-troubleshooting "API Version Mismatch" section; flow-deployment-and-packaging Gotcha 11 (source ahead of target). No clean delta for a fourth skill. |
| 13 | dataweave-for-apex | `integration/dataweave-for-apex` 11.669 | **REJECT auto** — direct same-name skill at near-max score. |
| 14 | salesforce-mobile-sdk-native | `lwc/lwc-mobile-offline-and-briefcase` 2.964 (top across 3 phrasings); `admin/fsl-mobile-app-setup` 2.827; `lwc/lwc-offline-and-mobile` 2.524; `admin/mobile-publisher` 2.286 | **REJECT (borderline 2.5–4.0)** — Mobile SDK (the open-source forceios/forcedroid/MobileSync native SDK toolkit) IS genuinely uncovered as a primary surface. **However**, the catalog's collective signal is that Mobile SDK is deliberately out-of-scope: `admin/mobile-publisher` Anti-Pattern 2 explicitly says "Suggesting custom native screens / SDKs is NOT a Mobile Publisher feature"; `lwc/lwc-mobile-offline-and-briefcase` Gotcha 7 frames SmartStore as "legacy Mobile SDK… not the same surface as Briefcase"; `lwc/headless-experience-cloud` is the modern path for branded native UX. The skill would document a declining technology (Salesforce has been redirecting customers to Mobile Publisher + Headless Experience Cloud since 2023). Per brief anti-pattern "Building a skill because a topic 'feels uncovered' — always verify" — uncovered ≠ gap when the absence is by design. REJECT. |
| 15 | headless-identity-experience-cloud | `lwc/experience-cloud-authentication` 10.967 | **REJECT auto** — direct same-domain hit; Headless Identity registration, OIDC/SAML, self-registration handlers all covered. |
| 16 | apex-schema-describe | `apex/apex-schema-describe` 6.246 | **REJECT auto** — direct same-name skill; hot-path describe cache, getRecordTypeInfosByDeveloperName, dynamic field map all present. |
| 17 | bulk-api-2-vs-1-comparison | `integration/bulk-api-2-patterns` 6.060; `data/bulk-api-patterns` 4.036 | **REJECT auto** — two same-domain skills ≥ 4.0; bulk-api-patterns Anti-Pattern 1 is literally "Using Bulk API v1 Endpoints When v2 Is Intended" — direct comparison content. |
| 18 | approval-process-recall | `admin/approval-process-apex-patterns` 5.973; `admin/approval-processes` 2.639 | **REJECT auto** — same-domain >4.0; Pattern D "Recall a submission when the source record is invalidated" with `ApprovalRecaller` example; Gotcha 9 covers post-recall query semantics. |

## Outcome

**0 skills built. Catalog steady at 997 skills.**

Five consecutive scheduled runs (2026-05-10, 2026-05-11, 2026-05-12, 2026-05-13, 2026-05-14) have now produced zero new skills with verified-saturation as the explanation. The combined verification trail covers ~60 unique candidates against the 997-skill corpus.

## Notable observations

- **The 3 `RESEARCHED` BACKLOG entries are all duplicates at the 7.5+ score level.** They should be reclassified `DUPLICATE` with notes pointing at the canonical skill. This is the same hygiene debt called out on 2026-05-13 for the TODO entries — the queue dashboard's "RESEARCHED (preferred)" recommendation is misleading agents toward already-built topics. Out of scope for this scheduled run (the brief carves out documentation hygiene) but worth surfacing for the next maintenance pass.
- **Mobile SDK is the only "uncovered" topic and it's uncovered by design.** Three adjacent skills (`admin/mobile-publisher`, `lwc/lwc-mobile-offline-and-briefcase`, `lwc/headless-experience-cloud`) explicitly route customers AWAY from Mobile SDK as the wrong path for modern branded native UX. Authoring a Mobile SDK skill would directly contradict this collective routing signal.
- **Pattern matches prior runs and memory.** Memory note `project_skill_coverage_gaps.md` records "catalog saturated… build N new requires manual gap verification". 72 skills added since that baseline, all through verified-gap pipeline, and the verification yield has now dropped to zero for 5 days running.

## Validation result

No skills changed. `validate_repo.py` not run for this report.
