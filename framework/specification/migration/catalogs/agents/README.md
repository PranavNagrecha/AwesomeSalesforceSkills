# Existing Agent V2 Migration Matrix

These profiles do not rewrite the existing agent knowledge. They define how each current agent should enter the V2 framework: exposure, evidence, context, and QA expectations.

| Agent | Class | Status | Org | Recommended V2 exposure | QA priority |
|---|---|---|---:|---|---|
| `admin-skill-builder` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `agentforce-action-reviewer` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `agentforce-builder` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `apex-builder` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P0 |
| `apex-refactorer` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `architect-skill-builder` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `assignment-and-auto-response-rules-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `audit-router` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `automation-migration-router` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `bulk-migration-planner` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `business-hours-and-holidays-configurator` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `case-escalation-auditor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `changeset-builder` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P0 |
| `code-reviewer` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `config-workbook-author` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `content-researcher` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `csv-to-object-mapper` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `currency-monitor` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `custom-metadata-and-settings-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `data-loader-pre-flight` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P0 |
| `data-model-reviewer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `data-skill-builder` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `deployment-risk-scorer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P0 |
| `dev-skill-builder` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `devops-skill-builder` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `duplicate-rule-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `email-template-modernizer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `entitlement-and-milestone-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `experience-cloud-admin-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `field-audit-trail-and-history-tracking-governor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `field-impact-analyzer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `fit-gap-analyzer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `flow-analyzer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `flow-builder` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P0 |
| `flow-orchestrator-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `integration-catalog-builder` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `knowledge-article-taxonomy-agent` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `lead-routing-rules-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `lightning-record-page-auditor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `list-view-and-search-layout-auditor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `lwc-auditor` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `lwc-builder` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P0 |
| `lwc-debugger` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `my-domain-and-session-security-auditor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `object-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `omni-channel-routing-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `omnistudio-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `orchestrator` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `org-assessor` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `org-drift-detector` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `path-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `permission-set-architect` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P0 |
| `picklist-governor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `process-flow-mapper` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `profile-to-permset-migrator` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `prompt-library-governor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `quick-action-and-global-action-auditor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `record-type-and-layout-auditor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `release-planner` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `release-train-planner` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `report-and-dashboard-auditor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `reports-and-dashboards-folder-sharing-auditor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `sales-stage-designer` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
| `sandbox-strategy-designer` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `security-scanner` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P0 |
| `security-skill-builder` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `sharing-audit-agent` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `soql-optimizer` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `story-drafter` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `task-mapper` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `test-class-generator` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `trigger-consolidator` | `runtime` | `stable` | false | command/catalog specialist; not default subagent | P1 |
| `user-access-diff` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P0 |
| `validation-rule-auditor` | `runtime` | `deprecated` | false | redirect-only; never host subagent | P1 redirect integrity |
| `validator` | `build` | `stable` | false | maintainer-only; never product auto-route | P2 |
| `waf-assessor` | `runtime` | `stable` | true | command/catalog specialist; not default subagent | P1 |
