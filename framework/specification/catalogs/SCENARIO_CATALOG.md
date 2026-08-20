# Known-truth scenario catalog

Generated from `qa/scenarios/*.json`. Ground truth is finding/evidence based, not exact prose.

| Scenario | Product | Domain | Lanes | Required findings | Setup |
|---|---|---|---|---|---|
| ACC-FLS | P03 | access | hermetic, scratch | 3 | Object access exists but field-level access blocks read/edit. |
| ACC-LICENSE | P03 | access | hermetic, scratch | 3 | User license prevents access regardless of assigned permission. |
| ACC-MUTING | P03 | access | hermetic, scratch | 3 | Permission-set group grant is muted. |
| ACC-OBJECT-CRUD | P03 | access | hermetic, scratch | 3 | User lacks required object CRUD despite UI visibility. |
| ACC-RECORD-SHARING | P03 | access | hermetic, scratch | 3 | CRUD/FLS pass but record-level sharing denies access. |
| ACC-RECORD-TYPE | P03 | access | hermetic, scratch | 3 | Record type assignment/default or business process blocks operation. |
| ACC-RESTRICTION-RULE | P03 | access | hermetic, scratch | 3 | Sharing grants access but a restriction rule removes visibility. |
| AFX-ACTION-CONTRACT | P11 | agentforce-quality-engineer | hermetic | 3 | Known-truth scenario for Agentforce Quality Engineer: AFX-ACTION-CONTRACT. |
| AFX-GROUNDING | P11 | agentforce-quality-engineer | hermetic | 3 | Known-truth scenario for Agentforce Quality Engineer: AFX-GROUNDING. |
| AFX-GUARDRAIL | P11 | agentforce-quality-engineer | hermetic | 3 | Known-truth scenario for Agentforce Quality Engineer: AFX-GUARDRAIL. |
| AFX-PERMISSION | P11 | agentforce-quality-engineer | hermetic | 3 | Known-truth scenario for Agentforce Quality Engineer: AFX-PERMISSION. |
| AFX-TEST-GAP | P11 | agentforce-quality-engineer | hermetic | 3 | Known-truth scenario for Agentforce Quality Engineer: AFX-TEST-GAP. |
| AFX-TOPIC-ROUTING | P11 | agentforce-quality-engineer | hermetic | 3 | Known-truth scenario for Agentforce Quality Engineer: AFX-TOPIC-ROUTING. |
| APX-ASSERTION | P02 | apex-test | hermetic, scratch | 3 | Assertion expected/actual mismatch with clear stack evidence. |
| APX-ASYNC-BOUNDARY | P02 | apex-test | hermetic, scratch | 3 | Assertion occurs before or after an async boundary is handled incorrectly. |
| APX-GOVERNOR | P02 | apex-test | hermetic, scratch | 3 | Shared automation causes governor-limit amplification. |
| APX-MISSING-MOCK | P02 | apex-test | hermetic, scratch | 3 | Callout occurs without a registered mock. |
| APX-MIXED-DML | P02 | apex-test | hermetic, scratch | 3 | Test performs setup and non-setup DML in one transaction. |
| APX-SHARED-ROOT | P02 | apex-test | hermetic, scratch | 3 | Several methods fail from one shared test factory defect. |
| APX-SHARING-CONTEXT | P02 | apex-test | hermetic, scratch | 3 | Test assumes record visibility or user context not present. |
| AUT-ASYNC-BRANCH | P05 | automation-transaction-profiler | hermetic | 3 | Known-truth scenario for Automation Transaction Profiler: AUT-ASYNC-BRANCH. |
| AUT-DML-AMPLIFICATION | P05 | automation-transaction-profiler | hermetic | 3 | Known-truth scenario for Automation Transaction Profiler: AUT-DML-AMPLIFICATION. |
| AUT-FLOW-TRIGGER-ORDER | P05 | automation-transaction-profiler | hermetic | 3 | Known-truth scenario for Automation Transaction Profiler: AUT-FLOW-TRIGGER-ORDER. |
| AUT-LEGACY-CONFLICT | P05 | automation-transaction-profiler | hermetic | 3 | Known-truth scenario for Automation Transaction Profiler: AUT-LEGACY-CONFLICT. |
| AUT-RECURSION | P05 | automation-transaction-profiler | hermetic | 3 | Known-truth scenario for Automation Transaction Profiler: AUT-RECURSION. |
| AUT-ROLLUP-REENTRY | P05 | automation-transaction-profiler | hermetic | 3 | Known-truth scenario for Automation Transaction Profiler: AUT-ROLLUP-REENTRY. |
| DATA-COUNT-MISMATCH | P09 | data-migration-reconciliation | hermetic | 3 | Known-truth scenario for Data Migration Reconciliation: DATA-COUNT-MISMATCH. |
| DATA-DUPLICATE | P09 | data-migration-reconciliation | hermetic | 3 | Known-truth scenario for Data Migration Reconciliation: DATA-DUPLICATE. |
| DATA-OWNER | P09 | data-migration-reconciliation | hermetic | 3 | Known-truth scenario for Data Migration Reconciliation: DATA-OWNER. |
| DATA-PARENT-MISSING | P09 | data-migration-reconciliation | hermetic | 3 | Known-truth scenario for Data Migration Reconciliation: DATA-PARENT-MISSING. |
| DATA-REJECTS | P09 | data-migration-reconciliation | hermetic | 3 | Known-truth scenario for Data Migration Reconciliation: DATA-REJECTS. |
| DATA-TRANSFORM | P09 | data-migration-reconciliation | hermetic | 3 | Known-truth scenario for Data Migration Reconciliation: DATA-TRANSFORM. |
| DEP-APEX-COMPILE | P01 | deployment | hermetic, scratch | 3 | Apex compilation fails due to a deterministic type/method mismatch. |
| DEP-COVERAGE | P01 | deployment | hermetic, scratch | 3 | Deployment result reports code-coverage failure. |
| DEP-DUPLICATE-SYMPTOMS | P01 | deployment | hermetic, scratch | 3 | Many component errors repeat one missing dependency. |
| DEP-MISSING-DEPENDENCY | P01 | deployment | hermetic, scratch | 3 | A component references a custom field absent from the target validation package/org. |
| DEP-ORG-MISMATCH | P01 | deployment | hermetic, scratch | 3 | Requested alias differs from the org associated with a cached job. |
| DEP-TEST-FAILURE | P01 | deployment | hermetic, scratch | 3 | Deployment validation fails because an Apex test method fails. |
| DRIFT-EXPECTED | P12 | multi-org-drift-analysis | hermetic | 3 | Known-truth scenario for Multi-Org Drift Analysis: DRIFT-EXPECTED. |
| DRIFT-FIELD | P12 | multi-org-drift-analysis | hermetic | 3 | Known-truth scenario for Multi-Org Drift Analysis: DRIFT-FIELD. |
| DRIFT-FLOW-VERSION | P12 | multi-org-drift-analysis | hermetic | 3 | Known-truth scenario for Multi-Org Drift Analysis: DRIFT-FLOW-VERSION. |
| DRIFT-PACKAGE | P12 | multi-org-drift-analysis | hermetic | 3 | Known-truth scenario for Multi-Org Drift Analysis: DRIFT-PACKAGE. |
| DRIFT-PERMISSION | P12 | multi-org-drift-analysis | hermetic | 3 | Known-truth scenario for Multi-Org Drift Analysis: DRIFT-PERMISSION. |
| DRIFT-SETTING | P12 | multi-org-drift-analysis | hermetic | 3 | Known-truth scenario for Multi-Org Drift Analysis: DRIFT-SETTING. |
| HLT-ALM | P10 | org-health-assessment | hermetic | 3 | Known-truth scenario for Org Health Assessment: HLT-ALM. |
| HLT-AUTOMATION-DEBT | P10 | org-health-assessment | hermetic | 3 | Known-truth scenario for Org Health Assessment: HLT-AUTOMATION-DEBT. |
| HLT-DATA-INTEGRITY | P10 | org-health-assessment | hermetic | 3 | Known-truth scenario for Org Health Assessment: HLT-DATA-INTEGRITY. |
| HLT-LIMITS | P10 | org-health-assessment | hermetic | 3 | Known-truth scenario for Org Health Assessment: HLT-LIMITS. |
| HLT-MAINTAINABILITY | P10 | org-health-assessment | hermetic | 3 | Known-truth scenario for Org Health Assessment: HLT-MAINTAINABILITY. |
| HLT-SECURITY | P10 | org-health-assessment | hermetic | 3 | Known-truth scenario for Org Health Assessment: HLT-SECURITY. |
| IMP-DYNAMIC-REFERENCE | P04 | change-impact-planner | hermetic | 3 | Known-truth scenario for Change Impact Planner: IMP-DYNAMIC-REFERENCE. |
| IMP-FIELD-DELETE | P04 | change-impact-planner | hermetic | 3 | Known-truth scenario for Change Impact Planner: IMP-FIELD-DELETE. |
| IMP-FIELD-TYPE | P04 | change-impact-planner | hermetic | 3 | Known-truth scenario for Change Impact Planner: IMP-FIELD-TYPE. |
| IMP-FLOW-ACTIVE | P04 | change-impact-planner | hermetic | 3 | Known-truth scenario for Change Impact Planner: IMP-FLOW-ACTIVE. |
| IMP-PACKAGE-BOUNDARY | P04 | change-impact-planner | hermetic | 3 | Known-truth scenario for Change Impact Planner: IMP-PACKAGE-BOUNDARY. |
| IMP-PERMISSION | P04 | change-impact-planner | hermetic | 3 | Known-truth scenario for Change Impact Planner: IMP-PERMISSION. |
| INT-AUTH | P08 | integration-incident-triage | hermetic | 3 | Known-truth scenario for Integration Incident Triage: INT-AUTH. |
| INT-DOWNSTREAM | P08 | integration-incident-triage | hermetic | 3 | Known-truth scenario for Integration Incident Triage: INT-DOWNSTREAM. |
| INT-IDEMPOTENCY | P08 | integration-incident-triage | hermetic | 3 | Known-truth scenario for Integration Incident Triage: INT-IDEMPOTENCY. |
| INT-RATE-LIMIT | P08 | integration-incident-triage | hermetic | 3 | Known-truth scenario for Integration Incident Triage: INT-RATE-LIMIT. |
| INT-SCHEMA-DRIFT | P08 | integration-incident-triage | hermetic | 3 | Known-truth scenario for Integration Incident Triage: INT-SCHEMA-DRIFT. |
| INT-TIMEOUT | P08 | integration-incident-triage | hermetic | 3 | Known-truth scenario for Integration Incident Triage: INT-TIMEOUT. |
| REL-DATA-SEQUENCING | P06 | release-readiness-review | hermetic | 3 | Known-truth scenario for Release Readiness Review: REL-DATA-SEQUENCING. |
| REL-DRIFT | P06 | release-readiness-review | hermetic | 3 | Known-truth scenario for Release Readiness Review: REL-DRIFT. |
| REL-MISSING-DEPENDENCY | P06 | release-readiness-review | hermetic | 3 | Known-truth scenario for Release Readiness Review: REL-MISSING-DEPENDENCY. |
| REL-ROLLBACK-GAP | P06 | release-readiness-review | hermetic | 3 | Known-truth scenario for Release Readiness Review: REL-ROLLBACK-GAP. |
| REL-SECURITY-RISK | P06 | release-readiness-review | hermetic | 3 | Known-truth scenario for Release Readiness Review: REL-SECURITY-RISK. |
| REL-TEST-GAP | P06 | release-readiness-review | hermetic | 3 | Known-truth scenario for Release Readiness Review: REL-TEST-GAP. |
| SEC-FLS | P07 | security-posture-review | hermetic | 3 | Known-truth scenario for Security Posture Review: SEC-FLS. |
| SEC-GUEST | P07 | security-posture-review | hermetic | 3 | Known-truth scenario for Security Posture Review: SEC-GUEST. |
| SEC-INJECTION | P07 | security-posture-review | hermetic | 3 | Known-truth scenario for Security Posture Review: SEC-INJECTION. |
| SEC-NAMED-CREDENTIAL | P07 | security-posture-review | hermetic | 3 | Known-truth scenario for Security Posture Review: SEC-NAMED-CREDENTIAL. |
| SEC-SESSION | P07 | security-posture-review | hermetic | 3 | Known-truth scenario for Security Posture Review: SEC-SESSION. |
| SEC-SHARING | P07 | security-posture-review | hermetic | 3 | Known-truth scenario for Security Posture Review: SEC-SHARING. |
