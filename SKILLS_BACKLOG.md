# SKILLS_BACKLOG.md
# Salesforce Skills — Master Build Checklist & Agent Handoff Registry

<!--
PURPOSE: Single source of truth for what is built, in-progress, and needed.
Read CLAUDE.md → AGENT_RULES.md → this file before doing any work.

AGENT WORKFLOW:
1. Find first status: TODO item
2. Change to IN_PROGRESS, record agent name + ISO timestamp
3. python3 scripts/search_knowledge.py "<topic>" --domain <domain>
4. python3 scripts/new_skill.py <domain> <skill-name>
5. Read the official-docs listed on the skill entry BEFORE writing content
6. Fill every TODO in every generated file with real, grounded content
7. python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>  (fix all ERRORs)
8. Add query fixture to vector_index/query-fixtures.json
9. python3 scripts/validate_repo.py  (must exit 0)
10. Mark DONE, update Handoff Log and Progress Summary, commit
-->

---

## Progress Summary

| Domain            | Total | Done | In Progress | Blocked | TODO |
|-------------------|-------|------|-------------|---------|------|
| Admin             | 25    | 19   | 0           | 0       | 6    |
| Apex              | 20    | 19   | 0           | 0       | 1    |
| LWC               | 14    | 14   | 0           | 0       | 0    |
| Flow              | 15    | 11   | 0           | 0       | 4    |
| OmniStudio        | 9     | 4    | 0           | 0       | 5    |
| AgentForce        | 14    | 2    | 0           | 0       | 12   |
| Security          | 12    | 2    | 0           | 0       | 10   |
| Integration       | 13    | 3    | 0           | 0       | 10   |
| Data              | 13    | 3    | 0           | 0       | 10   |
| DevOps            | 9     | 0    | 0           | 0       | 9    |
| Experience Cloud  | 7     | 0    | 0           | 0       | 7    |
| Service Cloud     | 6     | 0    | 0           | 0       | 6    |
| **TOTAL**         | **157** | **77** | **0**   | **0**   | **80** |

---

## Status Key

| Status      | Meaning                                                             |
|-------------|---------------------------------------------------------------------|
| TODO        | Not started. Any agent can pick this up.                            |
| IN_PROGRESS | Being built. Agent name + timestamp recorded. Do not touch.         |
| BLOCKED     | Stopped mid-build. Read the note field before continuing.           |
| DONE        | Complete. validate_repo.py passes. Committed.                       |
| SEEDED      | Raw content in Salesforce-RAG. Import and adapt, don't rewrite.     |

---

## Official Salesforce Documentation Index

**Rule: Read the listed docs for your skill BEFORE writing any content. Do not make factual claims without a source.**

### Core Platform

| Doc | URL |
|-----|-----|
| Apex Developer Guide | https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm |
| Apex Reference Guide | https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm |
| SOQL and SOSL Reference | https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm |
| Object Reference | https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm |
| Metadata API Developer Guide | https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm |
| REST API Developer Guide | https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm |
| Bulk API 2.0 Developer Guide | https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm |
| Platform Events Developer Guide | https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm |
| Change Data Capture Developer Guide | https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm |

### LWC and UI

| Doc | URL |
|-----|-----|
| LWC Best Practices | https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html |
| LWC Data Guidelines | https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html |
| Lightning Component Reference | https://developer.salesforce.com/docs/platform/lightning-component-reference/guide |
| Secure Apex Classes (LWC security) | https://developer.salesforce.com/docs/platform/lwc/guide/apex-security |

### Flow and Automation

| Doc | URL |
|-----|-----|
| Flow Reference | https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5 |
| Flow Builder | https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5 |

### Security

| Doc | URL |
|-----|-----|
| Salesforce Security Guide | https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5 |
| Shield Platform Encryption Guide | https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5 |
| Event Monitoring | https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/using_resources_event_log_files.htm |
| Named Credentials | https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm&type=5 |

### Integration and DevOps

| Doc | URL |
|-----|-----|
| Integration Patterns (Architects) | https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html |
| Salesforce DX Developer Guide | https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm |
| Salesforce CLI Reference | https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm |
| Salesforce Code Analyzer | https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/getting-started.html |

### OmniStudio and AgentForce

| Doc | URL |
|-----|-----|
| OmniStudio Developer Guide | https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm |
| Agentforce Developer Guide | https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html |
| Einstein Platform Services | https://developer.salesforce.com/docs/einstein/genai/guide/overview.html |
| Einstein Trust Layer | https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm&type=5 |

### Experience Cloud

| Doc | URL |
|-----|-----|
| Experience Cloud Developer Guide | https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_intro.htm |
| Experience Cloud Builder | https://help.salesforce.com/s/articleView?id=sf.community_builder_overview.htm&type=5 |
| Guest User Security Best Practices | https://help.salesforce.com/s/articleView?id=sf.networks_guest_access.htm&type=5 |
| Org-Wide Defaults for External Users | https://help.salesforce.com/s/articleView?id=sf.security_owd_external.htm&type=5 |
| Sharing Sets for External Users | https://help.salesforce.com/s/articleView?id=sf.networks_setting_light_users_sharing.htm&type=5 |
| Lightning Web Runtime (LWR) | https://developer.salesforce.com/docs/platform/lwr/guide/lwr-get-started.html |

### Service Cloud

| Doc | URL |
|-----|-----|
| Service Cloud Overview | https://help.salesforce.com/s/articleView?id=sf.service_cloud_overview.htm&type=5 |
| Entitlements and Milestones | https://help.salesforce.com/s/articleView?id=sf.entitlements_overview.htm&type=5 |
| Omni-Channel Routing | https://help.salesforce.com/s/articleView?id=sf.omnichannel_intro.htm&type=5 |
| Salesforce Knowledge | https://help.salesforce.com/s/articleView?id=sf.knowledge_whatis.htm&type=5 |
| Email-to-Case | https://help.salesforce.com/s/articleView?id=sf.setting_up_email_to_case.htm&type=5 |
| Escalation Rules | https://help.salesforce.com/s/articleView?id=sf.customize_caseescalation.htm&type=5 |
| Case Assignment Rules | https://help.salesforce.com/s/articleView?id=sf.customize_caseassign.htm&type=5 |

### Architecture

| Doc | URL |
|-----|-----|
| Well-Architected Overview | https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html |
| Large Data Volumes Best Practices | https://architect.salesforce.com/docs/architect/fundamentals/guide/large-data-volumes-introduction.html |

---

## Workflow Quick Reference

```bash
# Check coverage first — always
python3 scripts/search_knowledge.py "<topic>" --domain <domain>

# Scaffold
python3 scripts/new_skill.py <domain> <skill-name>

# READ THE OFFICIAL DOCS LISTED ON YOUR SKILL ENTRY BEFORE WRITING

# Sync (validates first — hard stop on errors)
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>

# Full validation
python3 scripts/validate_repo.py
```

---

## DOMAIN: Admin

### ADM-001 through ADM-015 — DONE
> All 15 original admin skills are complete. See handoff log.

### ADM-016
```yaml
skill:       custom-metadata-types
path:        skills/admin/custom-metadata-types/
status:      DONE
agent:       Codex
started:     2026-03-13T21:42:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Operational Excellence, Reliability
official-docs:
  - "Metadata API Developer Guide (Custom Metadata): https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custommetadata.htm"
  - "Custom Metadata Types (Help): https://help.salesforce.com/s/articleView?id=sf.custommetadata_about.htm&type=5"
  - "Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html"
rag-source:  Check Salesforce-RAG for custom metadata patterns
notes:       Built deployable-configuration guidance covering CMT vs Custom Settings vs Custom Objects, protected metadata boundaries, Apex and Flow access patterns, and a checker for public secret fields, environment-specific values, and runtime DML on __mdt.
```

### ADM-017
```yaml
skill:       process-automation-selection
path:        skills/admin/process-automation-selection/
status:      DONE
agent:       Codex
started:     2026-03-13T21:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Scalability, Operational Excellence
official-docs:
  - "Flow Reference: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5"
  - "Flow Builder: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5"
  - "Apex Developer Guide (triggers): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers.htm"
rag-source:  Check Salesforce-RAG for automation patterns
notes:       Built automation-selection guidance for Flow versus Apex trigger boundaries, retirement-focused Process Builder and Workflow Rule migration, order-of-execution overlap review, and a checker for legacy automation plus Flow/Apex collision risk.
```

### ADM-018
```yaml
skill:       list-views-and-compact-layouts
path:        skills/admin/list-views-and-compact-layouts/
status:      DONE
agent:       Codex
started:     2026-03-13T21:42:36Z
completed:   2026-03-13
files:       6
priority:    P2
waf-pillars: User Experience, Operational Excellence
official-docs:
  - "Compact Layouts (Help): https://help.salesforce.com/s/articleView?id=sf.compact_layout_overview.htm&type=5"
  - "List Views (Help): https://help.salesforce.com/s/articleView?id=sf.customviews.htm&type=5"
rag-source:  Check Salesforce-RAG for UX patterns
notes:       Built browse-and-scan UX guidance for list views, compact layouts, and search-result separation, with templates and a checker for list-view sprawl, broad filters, and overloaded compact layouts.
```

---

## DOMAIN: Apex

### APX-001 — DONE: soql-security
### APX-002 — DONE: trigger-framework
### APX-003 — DONE: governor-limits

### APX-004
```yaml
skill:       exception-handling
path:        skills/apex/exception-handling/
status:      DONE
agent:       Codex
started:     2026-03-13T17:47:08Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Reliability
official-docs:
  - "Apex Developer Guide — Exception Handling: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_exception_definition.htm"
  - "Apex Reference — Exception Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_exception.htm"
  - "Apex Developer Guide — Triggers and Exceptions: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_exceptions.htm"
rag-source:  SEEDED — import from Salesforce-RAG exception patterns
notes:       Built layered exception-handling guidance with `addError` vs rethrow decisions, bulk `SaveResult` patterns, boundary-safe `AuraHandledException` usage, and a swallowed-exception checker.
```

### APX-005
```yaml
skill:       async-apex
path:        skills/apex/async-apex/
status:      DONE
agent:       Codex
started:     2026-03-13T17:47:08Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Scalability, Performance, Reliability
official-docs:
  - "Apex Developer Guide — Async Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_async_overview.htm"
  - "Apex Reference — Queueable: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Queueable.htm"
  - "Apex Reference — Database.Batchable: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_database_batchable.htm"
rag-source:  Check Salesforce-RAG for async patterns
notes:       Built Queueable vs Batch vs Future vs Schedulable guidance with chaining constraints, scheduler-dispatch patterns, and an async anti-pattern checker.
```

### APX-006
```yaml
skill:       test-class-standards
path:        skills/apex/test-class-standards/
status:      DONE
agent:       Codex
started:     2026-03-13T17:47:08Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Apex Developer Guide — Testing: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing.htm"
  - "Apex Reference — Test Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_test.htm"
  - "Apex Developer Guide — Test Data Factory: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_utility_classes.htm"
rag-source:  SEEDED — import from Salesforce-RAG test patterns
notes:       Built test standards guidance for factories, `SeeAllData=false`, async and callout tests, and a checker for weak assertions and brittle test patterns.
```

### APX-007
```yaml
skill:       callouts-and-http-integrations
path:        skills/apex/callouts-and-http-integrations/
status:      DONE
agent:       Codex
started:     2026-03-13T17:47:08Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Reliability, Security
official-docs:
  - "Apex Developer Guide — HTTP Callouts: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_restful_http_httprequest.htm"
  - "Apex Developer Guide — Named Credentials: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm"
  - "Named Credentials (Help): https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm&type=5"
rag-source:  Check Salesforce-RAG for callout patterns
notes:       Built outbound HTTP guidance around Named Credentials, transaction boundaries, timeout/error handling, mock testing, and a checker for hardcoded endpoints and unsafe trigger callouts.
```

### APX-008
```yaml
skill:       apex-security-patterns
path:        skills/apex/apex-security-patterns/
status:      DONE
agent:       Codex
started:     2026-03-13T17:47:08Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Security
official-docs:
  - "Apex Developer Guide — Security: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security.htm"
  - "Secure Apex Classes: https://developer.salesforce.com/docs/platform/lwc/guide/apex-security"
  - "Apex Developer Guide — Sharing: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm"
rag-source:  Check Salesforce-RAG for security patterns
notes:       Built service-layer security guidance for `with` vs `without` vs `inherited sharing`, secure read/write patterns, and a checker for ambiguous sharing and missing CRUD/FLS enforcement.
```

### APX-009
```yaml
skill:       platform-events-apex
path:        skills/apex/platform-events-apex/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Scalability, Reliability
official-docs:
  - "Platform Events Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm"
  - "Platform Events — Apex: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_subscribe_apex.htm"
  - "Change Data Capture Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm"
rag-source:  Check Salesforce-RAG for event patterns
notes:       Built Platform Events vs CDC guidance with `EventBus.publish` result handling, thin event triggers, replay-aware consumer boundaries, and a checker for looped publish and weak subscriber design.
```

### APX-010
```yaml
skill:       apex-design-patterns
path:        skills/apex/apex-design-patterns/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Scalability, Reliability, Operational Excellence
official-docs:
  - "Apex Developer Guide — Classes: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_understanding.htm"
  - "Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html"
rag-source:  SEEDED — check Salesforce-RAG for design patterns
notes:       Built service, selector, domain, DI, and factory guidance with review heuristics for trigger-layer SOQL/DML, god classes, and test-hostile static seams.
```

### APX-011
```yaml
skill:       debug-and-logging
path:        skills/apex/debug-and-logging/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Operational Excellence
official-docs:
  - "Apex Developer Guide — Debug Logs: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging_debug_log.htm"
  - "Apex Developer Guide — System.debug: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_system.htm#apex_System_System_debug"
rag-source:  Check Salesforce-RAG for logging patterns
notes:       Built production logging guidance around `System.debug`, structured log records, async correlation, and a checker for noisy, unstructured, or sensitive debug output.
```

### APX-012
```yaml
skill:       batch-apex-patterns
path:        skills/apex/batch-apex-patterns/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Scalability, Performance
official-docs:
  - "Apex Developer Guide — Batch Apex: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_batch_interface.htm"
  - "Apex Reference — Database.Batchable: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_database_batchable.htm"
  - "Apex Reference — Database.executeBatch: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_database.htm"
rag-source:  Check Salesforce-RAG for batch patterns
notes:       Built Batch Apex guidance for `start/execute/finish`, scope sizing, `Database.Stateful`, chaining, and monitoring, plus a checker for unsafe scope and callout patterns.
```

### APX-013
```yaml
skill:       apex-rest-services
path:        skills/apex/apex-rest-services/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Security, Reliability
official-docs:
  - "Apex Developer Guide — Apex REST: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest.htm"
  - "REST API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm"
  - "Apex Developer Guide — @RestResource: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_rest_resource.htm"
rag-source:  Check Salesforce-RAG for REST service patterns
notes:       Built thin Apex REST endpoint guidance for routing, `RestContext`, explicit status codes, versioning, and a checker for weak HTTP method, sharing, and response handling.
```

### APX-014
```yaml
skill:       apex-mocking-and-stubs
path:        skills/apex/apex-mocking-and-stubs/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Apex Developer Guide — Test.setMock: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_httpcallout.htm"
  - "Apex Developer Guide — StubProvider: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_stub_api.htm"
  - "Apex Reference — Test Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_test.htm"
rag-source:  Check Salesforce-RAG for mock patterns
notes:       Built seam-focused test-double guidance for `Test.setMock`, `HttpCalloutMock`, `StaticResourceCalloutMock`, and `StubProvider`, plus a checker for missing seams and `Test.isRunningTest()` usage.
```

### APX-015
```yaml
skill:       invocable-methods
path:        skills/apex/invocable-methods/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Scalability, Operational Excellence
official-docs:
  - "Apex Developer Guide — @InvocableMethod: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm"
  - "Flow Reference — Apex Action: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_apex_invocable.htm&type=5"
rag-source:  Check Salesforce-RAG for invocable patterns
notes:       Built Flow-facing Apex action guidance for list-oriented contracts, wrapper DTOs, bulk-safe delegation, and a checker for weak invocable signatures and missing variable metadata.
```

---

## DOMAIN: LWC

### LWC-001 — DONE: lifecycle-hooks

### LWC-002 — DONE: wire-service-patterns
```yaml
skill:       wire-service-patterns
path:        skills/lwc/wire-service-patterns/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Performance, Reliability
official-docs:
  - "LWC Data Guidelines: https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
  - "Wire Service — getRecord: https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about.html"
rag-source:  SEEDED — check Salesforce-RAG for wire/data patterns
notes:       Built wire-service guidance for LDS-first adapter choice, reactive parameters, refreshApex and notify sync patterns, and a checker for duplicate read paths and weak refresh behavior.
```

### LWC-003
```yaml
skill:       component-communication
path:        skills/lwc/component-communication/
status:      DONE
agent:       Codex
started:     2026-03-13T21:42:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Reliability, Scalability
official-docs:
  - "LWC Best Practices — Component Communication: https://developer.salesforce.com/docs/platform/lwc/guide/events-parent-to-child.html"
  - "Lightning Message Service: https://developer.salesforce.com/docs/platform/lwc/guide/lwc-message-channel.html"
  - "LWC — Custom Events: https://developer.salesforce.com/docs/platform/lwc/guide/events-create-dispatch.html"
rag-source:  Check Salesforce-RAG for LWC communication patterns
notes:       Built LWC communication guidance covering @api properties, public methods, custom event propagation, and Lightning Message Service boundaries, plus a checker for pubsub use, shadowRoot coupling, weak event names, and unsubscribed LMS handlers.
```

### LWC-004 — DONE: lwc-security
```yaml
skill:       lwc-security
path:        skills/lwc/lwc-security/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Security
official-docs:
  - "Secure Apex Classes: https://developer.salesforce.com/docs/platform/lwc/guide/apex-security"
  - "Lightning Web Security: https://developer.salesforce.com/docs/platform/lwc/guide/lws-security.html"
  - "LWC Best Practices — Security: https://developer.salesforce.com/docs/platform/lwc/guide/security-lwc.html"
rag-source:  Check Salesforce-RAG for LWC security patterns
notes:       Built LWC security guidance for Lightning Web Security boundaries, unsafe DOM patterns, third-party library loading, and a checker for innerHTML, eval, manual DOM, and AuraEnabled exposure smells.
```

### LWC-005
```yaml
skill:       lwc-testing
path:        skills/lwc/lwc-testing/
status:      DONE
agent:       Codex
started:     2026-03-13T21:42:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "LWC Testing with Jest: https://developer.salesforce.com/docs/platform/lwc/guide/testing.html"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
rag-source:  SEEDED — check Salesforce-RAG for test patterns
notes:       Built Jest-first LWC testing guidance for wire adapters, imperative Apex mocks, async rerender handling, accessibility smoke checks, and a checker for missing Jest setup, missing component tests, and unmocked Apex imports.
```

### LWC-006
```yaml
skill:       lwc-performance
path:        skills/lwc/lwc-performance/
status:      DONE
agent:       Codex
started:     2026-03-13T22:15:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Performance
official-docs:
  - "Lightning Web Components Performance Best Practices: https://developer.salesforce.com/blogs/2020/06/lightning-web-components-performance-best-practices"
  - "LWC — Dynamic Components: https://developer.salesforce.com/docs/platform/lwc/guide/js-dynamic-components.html"
  - "LWC — Reactivity for Fields, Objects, and Arrays: https://developer.salesforce.com/docs/platform/lwc/guide/reactivity-fields.html"
  - "Lightning Component Reference: https://developer.salesforce.com/docs/platform/lightning-component-reference/guide"
rag-source:  Check Salesforce-RAG for LWC performance patterns
notes:       Built LWC performance guidance for payload reduction, progressive disclosure with `lwc:if` and tabs, stable list keys and bounded list rendering, modern reactivity caveats, and dynamic component constraints plus a checker for legacy directives, layout fetches, dynamic import setup, and list-key smells.
```

### LWC-007
```yaml
skill:       navigation-and-routing
path:        skills/lwc/navigation-and-routing/
status:      DONE
agent:       Codex
started:     2026-03-13T21:42:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: User Experience
official-docs:
  - "LWC — NavigationMixin: https://developer.salesforce.com/docs/platform/lwc/guide/navigate-using-navigation-mixin.html"
  - "LWC — PageReference Types: https://developer.salesforce.com/docs/platform/lwc/guide/reference-page-reference-type.html"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
rag-source:  Check Salesforce-RAG for navigation patterns
notes:       Built PageReference-centric navigation guidance for NavigationMixin, GenerateUrl, CurrentPageReference, namespaced URL state, Experience Cloud awareness, and a checker for hardcoded internal URLs, bad state keys, and incomplete page references.
```

### LWC-008
```yaml
skill:       lwc-accessibility
path:        skills/lwc/lwc-accessibility/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P1
waf-pillars: User Experience, Security
official-docs:
  - "LWC Best Practices — Accessibility: https://developer.salesforce.com/docs/platform/lwc/guide/accessibility.html"
  - "Lightning Design System Accessibility: https://www.lightningdesignsystem.com/accessibility/overview/"
  - "WCAG 2.1 (W3C): https://www.w3.org/TR/WCAG21/"
rag-source:  Check Salesforce-RAG for accessibility patterns
notes:       Built LWC accessibility guidance covering base-component-first semantics, accessible names, keyboard and focus management, modal focus return, and a checker for clickable containers, unlabeled icons, and missing image alt text.
```

### LWC-009
```yaml
skill:       lwc-forms-and-validation
path:        skills/lwc/lwc-forms-and-validation/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P1
waf-pillars: User Experience, Reliability
official-docs:
  - "LWC Data Guidelines: https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html"
  - "Lightning Component Reference — lightning-record-edit-form: https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-record-edit-form"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
rag-source:  Check Salesforce-RAG for form patterns
notes:       Built form guidance for record-edit-form versus custom inputs, reportValidity and fieldErrors handling, save-then-upload sequencing, and a checker for missing lightning-messages, missing reportValidity, and upload-without-record-id risk.
```

### LWC-010
```yaml
skill:       lwc-data-table
path:        skills/lwc/lwc-data-table/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P1
waf-pillars: Performance, User Experience
official-docs:
  - "Lightning Component Reference — lightning-datatable: https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-datatable"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
rag-source:  Check Salesforce-RAG for datatable patterns
notes:       Built datatable guidance for key-field stability, inline edit save lifecycle, row actions, bounded infinite loading, and a checker for missing key-field, onloadmore, and onsave wiring.
```

### LWC-011
```yaml
skill:       static-resources-in-lwc
path:        skills/lwc/static-resources-in-lwc/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P2
waf-pillars: Performance, Operational Excellence
official-docs:
  - "LWC — Static Resources: https://developer.salesforce.com/docs/platform/lwc/guide/create-components-javascript-libraries.html"
  - "Metadata API — StaticResource: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_staticresource.htm"
rag-source:  Check Salesforce-RAG for static resource patterns
notes:       Built static-resource guidance for resourceUrl, platformResourceLoader, zip path contracts, versioning, and a checker for CDN loading, missing resourceUrl imports, and unguarded renderedCallback loads.
```

### LWC-012
```yaml
skill:       lwc-modal-and-overlay
path:        skills/lwc/lwc-modal-and-overlay/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P1
waf-pillars: User Experience, Reliability
official-docs:
  - "Lightning Component Reference — lightning-modal: https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-modal"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
rag-source:  Check Salesforce-RAG for overlay patterns
notes:       Built overlay guidance for LightningModal versus toast choice, result-returning modal contracts, focus and dismissal behavior, and a checker for browser dialogs, unlabeled custom modals, and modal components without clear close paths.
```

---

## DOMAIN: Flow

### FLW-001 — DONE: fault-handling

### FLW-002 — DONE: flow-bulkification
```yaml
skill:       flow-bulkification
path:        skills/flow/flow-bulkification/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Scalability, Performance
official-docs:
  - "Flow Reference — Best Practices: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_best_practices.htm&type=5"
  - "Flow Builder: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5"
rag-source:  Check Salesforce-RAG for bulkification patterns
notes:       Built Flow bulkification guidance for before-save optimization, collection-first DML, invocable-Apex scale review, and a checker for loops, repeated lookups, and non-list-safe invocable signatures.
```

### FLW-003 — DONE: record-triggered-flow-patterns
```yaml
skill:       record-triggered-flow-patterns
path:        skills/flow/record-triggered-flow-patterns/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Reliability, Scalability
official-docs:
  - "Flow Reference — Record-Triggered Flows: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm&type=5"
  - "Flow Builder: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5"
  - "Flow Reference — $Record Variable: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_variables_record.htm&type=5"
rag-source:  Check Salesforce-RAG for record-trigger patterns
notes:       Built record-triggered Flow guidance for before-save versus after-save separation, prior-value gating, overlap control, and a checker for same-object flow sprawl and weak delta logic.
```

### FLW-004
```yaml
skill:       subflows-and-reusability
path:        skills/flow/subflows-and-reusability/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P1
waf-pillars: Operational Excellence, Scalability
official-docs:
  - "Flow Reference — Subflows: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_subflow.htm&type=5"
  - "Flow Builder: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5"
rag-source:  Check Salesforce-RAG for flow architecture patterns
notes:       Built subflow guidance for narrow contracts, explicit input-output variables, parent-child fault boundaries, and a checker for wide contracts, no fault connectors, and over-decomposition.
```

### FLW-005
```yaml
skill:       screen-flows
path:        skills/flow/screen-flows/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P1
waf-pillars: User Experience, Reliability
official-docs:
  - "Flow Reference — Screen Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen.htm&type=5"
  - "Flow Reference — Screen Components: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_fields.htm&type=5"
rag-source:  Check Salesforce-RAG for screen flow patterns
notes:       Built screen-flow UX guidance for late commit timing, standard versus custom screen components, Flow validation methods, and a checker for mutation-heavy screen flows plus custom components missing validation hooks.
```

### FLW-006
```yaml
skill:       flow-governance
path:        skills/flow/flow-governance/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P1
waf-pillars: Operational Excellence
official-docs:
  - "Flow Reference: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5"
  - "Flow Builder: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5"
rag-source:  Check Salesforce-RAG for governance patterns
notes:       Built governance guidance for naming, ownership, descriptions, interview labels, and activation discipline, plus a checker for generic names, missing descriptions, and unreadable screen-flow interview metadata.
```

### FLW-007
```yaml
skill:       scheduled-flows
path:        skills/flow/scheduled-flows/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P1
waf-pillars: Scalability, Reliability
official-docs:
  - "Flow Reference — Schedule-Triggered Flows: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_schedule.htm&type=5"
  - "Flow Builder: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5"
rag-source:  Check Salesforce-RAG for scheduled automation patterns
notes:       Built schedule-triggered guidance for bounded start criteria, idempotent markers, schedule versus scheduled path selection, and a checker for broad scheduled scope, unhandled background failures, and batch-style designs.
```

### FLW-008
```yaml
skill:       flow-testing
path:        skills/flow/flow-testing/
status:      DONE
agent:       Codex
started:     2026-03-15T14:06:32Z
completed:   2026-03-15
files:       6
priority:    P1
waf-pillars: Reliability
official-docs:
  - "Flow Testing Tool: https://help.salesforce.com/s/articleView?id=sf.flow_test.htm&type=5"
  - "Flow Reference: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5"
rag-source:  Check Salesforce-RAG for flow test patterns
notes:       Built Flow testing guidance for path matrices, Flow Tests versus Debug, boundary testing for Apex and LWC components, and a checker for flows without obvious FlowTest companions or negative-path coverage cues.
```

### FLW-009
```yaml
skill:       flow-and-apex-interop
path:        skills/flow/flow-and-apex-interop/
status:      TODO
priority:    P1
waf-pillars: Scalability, Reliability
official-docs:
  - "Apex Developer Guide — @InvocableMethod: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm"
  - "Flow Reference — Apex Action: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_apex_invocable.htm&type=5"
rag-source:  Check Salesforce-RAG for flow-apex patterns
notes:       @InvocableMethod design for Flow. Bulk-safe List<List<T>> contract. When callout is needed from Flow. NOT for Apex-called-Flow direction.
```

### FLW-010
```yaml
skill:       flow-migration-from-legacy
path:        skills/flow/flow-migration-from-legacy/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence, Reliability
official-docs:
  - "Migrate to Flow (Help): https://help.salesforce.com/s/articleView?id=sf.flow_migrate_from_process_overview.htm&type=5"
  - "Flow Reference: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5"
rag-source:  Check Salesforce-RAG for migration patterns
notes:       Process Builder to Flow migration guide. Workflow Rule to Flow migration. Salesforce retirement timeline. Safe cutover patterns. What doesn't translate directly.
```

---

## DOMAIN: OmniStudio

### OMS-001 — DONE: integration-procedures

### OMS-002 — DONE: omniscript-design-patterns
```yaml
skill:       omniscript-design-patterns
path:        skills/omnistudio/omniscript-design-patterns/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: User Experience, Performance
official-docs:
  - "OmniStudio Developer Guide — OmniScript: https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/os_omniscript_overview.htm"
rag-source:  SEEDED — import from Salesforce-RAG OmniStudio patterns
notes:       Built OmniScript design guidance for step structure, branching, save-resume, server-boundary design, and a checker for placeholder naming, over-chatty remote calls, and weak custom-LWC navigation patterns.
```

### OMS-003
```yaml
skill:       dataraptor-patterns
path:        skills/omnistudio/dataraptor-patterns/
status:      DONE
agent:       Codex
started:     2026-03-13T21:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Performance, Reliability
official-docs:
  - "OmniStudio Developer Guide — DataRaptors: https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/os_dataraptor_overview.htm"
rag-source:  SEEDED — import from Salesforce-RAG DataRaptor patterns
notes:       Built DataRaptor pattern guidance for Extract, Turbo Extract, Transform, and Load decisions, service-boundary escalation to IP or Apex, maintainable mapping design, and a checker for placeholder naming, Turbo misuse, and brittle load payloads.
```

### OMS-004
```yaml
skill:       flexcards
path:        skills/omnistudio/flexcards/
status:      TODO
priority:    P1
waf-pillars: User Experience, Performance
official-docs:
  - "OmniStudio Developer Guide — FlexCards: https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/os_flexcards_overview.htm"
rag-source:  Check Salesforce-RAG for FlexCard patterns
notes:       Child card architecture, action buttons, conditional visibility, data source selection, performance with large datasets.
```

### OMS-005
```yaml
skill:       calculation-procedures
path:        skills/omnistudio/calculation-procedures/
status:      TODO
priority:    P1
waf-pillars: Performance, Reliability
official-docs:
  - "OmniStudio Developer Guide — Calculation Procedures: https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/os_calc_proc_overview.htm"
rag-source:  Check Salesforce-RAG for calculation patterns
notes:       Calculation Matrix vs Calculation Procedure vs Apex formula decision. Testing Calculation Procedures.
```

### OMS-006
```yaml
skill:       omnistudio-testing
path:        skills/omnistudio/omnistudio-testing/
status:      TODO
priority:    P1
waf-pillars: Reliability
official-docs:
  - "OmniStudio Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm"
rag-source:  Check Salesforce-RAG for OmniStudio test patterns
notes:       Mocking DataRaptors in IPs, OmniScript debug mode, test coverage for Apex actions called from IPs, UI testing approach.
```

### OMS-007
```yaml
skill:       omnistudio-deployment
path:        skills/omnistudio/omnistudio-deployment/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence
official-docs:
  - "OmniStudio Developer Guide — Deployment: https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/os_deployment_overview.htm"
  - "Metadata API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm"
rag-source:  Check Salesforce-RAG for deployment patterns
notes:       Export/import JSON, dependency ordering (DataRaptors → IPs → OmniScripts), version management across environments, Tooling API support.
```

### OMS-008
```yaml
skill:       omnistudio-performance
path:        skills/omnistudio/omnistudio-performance/
status:      TODO
priority:    P1
waf-pillars: Performance, Scalability
official-docs:
  - "OmniStudio Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm"
rag-source:  Check Salesforce-RAG for OmniStudio performance patterns
notes:       Turbo Extract vs Extract performance. IP caching. Lazy-loading OmniScripts. Minimising callout chains in IPs.
```

### OMS-009
```yaml
skill:       omnistudio-security
path:        skills/omnistudio/omnistudio-security/
status:      DONE
agent:       Codex
started:     2026-03-13T21:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Security
official-docs:
  - "OmniStudio Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm"
  - "Secure Apex Classes: https://developer.salesforce.com/docs/platform/lwc/guide/apex-security"
  - "Salesforce Security Guide: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for OmniStudio security patterns
notes:       Built OmniStudio security guidance for guest and portal exposure, CRUD/FLS and sharing enforcement across OmniStudio-to-Apex boundaries, output minimisation, and a checker for hardcoded endpoints, unsafe Apex sharing, and public write risk.
```

---

## DOMAIN: AgentForce

### AGT-001
```yaml
skill:       agent-topic-design
path:        skills/agentforce/agent-topic-design/
status:      DONE
agent:       Codex
started:     2026-03-13T21:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: User Experience, Reliability
official-docs:
  - "Agentforce Developer Guide — Topics: https://developer.salesforce.com/docs/einstein/genai/guide/agent-topics.html"
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
rag-source:  Check Salesforce-RAG for agent/AI patterns
notes:       Built Agentforce topic-design guidance for capability boundaries, explicit exclusions, handoff rules, topic-selector use, and a checker for vague topic names, overlap risk, and oversized topic action sets.
```

### AGT-002
```yaml
skill:       agent-actions
path:        skills/agentforce/agent-actions/
status:      DONE
agent:       Codex
started:     2026-03-13T21:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Reliability, Security
official-docs:
  - "Agentforce Developer Guide — Actions: https://developer.salesforce.com/docs/einstein/genai/guide/agent-actions.html"
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
  - "Apex Developer Guide — @InvocableMethod: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm"
rag-source:  Check Salesforce-RAG for AI action patterns
notes:       Built Agentforce action guidance for Flow versus Apex versus prompt-template boundaries, confirmation-gated mutations, stable input and output contracts, and a checker for weak invocable schemas, generic naming, and missing confirmation cues.
```

### AGT-003
```yaml
skill:       prompt-template-design
path:        skills/agentforce/prompt-template-design/
status:      TODO
priority:    P0
waf-pillars: Reliability, User Experience
official-docs:
  - "Agentforce Developer Guide — Prompt Templates: https://developer.salesforce.com/docs/einstein/genai/guide/prompt-templates.html"
  - "Einstein Platform Services: https://developer.salesforce.com/docs/einstein/genai/guide/overview.html"
  - "Einstein Trust Layer: https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm&type=5"
rag-source:  SEEDED — core content from Salesforce-RAG
notes:       Grounding with merge fields, instruction clarity, role definitions, hallucination reduction, context window management, template types (Field Generation, Record Summary, Sales Email).
```

### AGT-004
```yaml
skill:       rag-with-data-cloud
path:        skills/agentforce/rag-with-data-cloud/
status:      TODO
priority:    P1
waf-pillars: Reliability, Scalability
official-docs:
  - "Agentforce Developer Guide — Retrieval: https://developer.salesforce.com/docs/einstein/genai/guide/data-library.html"
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
  - "Einstein Platform Services: https://developer.salesforce.com/docs/einstein/genai/guide/overview.html"
rag-source:  SEEDED — this is what Salesforce-RAG was built for. Import heavily.
notes:       Agentforce Data Library, vector store configuration, retriever setup, chunking strategy, semantic search tuning, relevance evaluation.
```

### AGT-005
```yaml
skill:       agent-testing-and-evaluation
path:        skills/agentforce/agent-testing-and-evaluation/
status:      TODO
priority:    P1
waf-pillars: Reliability
official-docs:
  - "Agentforce Developer Guide — Testing: https://developer.salesforce.com/docs/einstein/genai/guide/agent-testing.html"
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
rag-source:  Check Salesforce-RAG for evaluation patterns
notes:       Conversation test coverage, expected vs actual output validation, regression testing across prompt changes, evaluation metrics.
```

### AGT-006
```yaml
skill:       agent-security-and-trust
path:        skills/agentforce/agent-security-and-trust/
status:      TODO
priority:    P0
waf-pillars: Security, Reliability
official-docs:
  - "Einstein Trust Layer: https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm&type=5"
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
  - "Salesforce Security Guide: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for trust/AI security patterns
notes:       Einstein Trust Layer architecture, data masking before LLM calls, PII handling, audit trail for AI actions, toxicity filtering, zero data retention.
```

### AGT-007
```yaml
skill:       agentforce-architecture-patterns
path:        skills/agentforce/agentforce-architecture-patterns/
status:      TODO
priority:    P1
waf-pillars: Scalability, Reliability
official-docs:
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
  - "Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html"
rag-source:  SEEDED — import from Salesforce-RAG architecture patterns
notes:       Multi-agent orchestration, escalation path design, human-in-the-loop checkpoints, agent handoff between topics. Architecture principles, not code tutorial.
```

### AGT-008
```yaml
skill:       einstein-copilot-configuration
path:        skills/agentforce/einstein-copilot-configuration/
status:      TODO
priority:    P1
waf-pillars: User Experience, Operational Excellence
official-docs:
  - "Agentforce Developer Guide — Copilot: https://developer.salesforce.com/docs/einstein/genai/guide/copilot-builder.html"
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
rag-source:  Check Salesforce-RAG for copilot patterns
notes:       Custom copilot setup, standard vs custom actions, copilot instruction tuning, enabling/disabling standard capabilities. NOT for topic design (see AGT-001).
```

### AGT-009
```yaml
skill:       prompt-chaining-patterns
path:        skills/agentforce/prompt-chaining-patterns/
status:      TODO
priority:    P2
waf-pillars: Reliability, Performance
official-docs:
  - "Einstein Platform Services: https://developer.salesforce.com/docs/einstein/genai/guide/overview.html"
  - "Agentforce Developer Guide — Prompt Templates: https://developer.salesforce.com/docs/einstein/genai/guide/prompt-templates.html"
rag-source:  Check Salesforce-RAG for chaining patterns
notes:       Multi-step reasoning chains, passing context between prompt templates, intermediate result handling, failure recovery in chains.
```

### AGT-010
```yaml
skill:       data-cloud-for-agentforce
path:        skills/agentforce/data-cloud-for-agentforce/
status:      TODO
priority:    P1
waf-pillars: Scalability, Reliability
official-docs:
  - "Agentforce Developer Guide — Data Library: https://developer.salesforce.com/docs/einstein/genai/guide/data-library.html"
  - "Einstein Platform Services: https://developer.salesforce.com/docs/einstein/genai/guide/overview.html"
rag-source:  SEEDED — core content from Salesforce-RAG
notes:       Data Cloud as grounding source, vector index setup for agents, unified profile for personalisation, identity resolution for agent context.
```

### AGT-011
```yaml
skill:       agent-channel-configuration
path:        skills/agentforce/agent-channel-configuration/
status:      TODO
priority:    P2
waf-pillars: User Experience, Reliability
official-docs:
  - "Agentforce Developer Guide — Channels: https://developer.salesforce.com/docs/einstein/genai/guide/agent-channels.html"
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
rag-source:  Check Salesforce-RAG for channel patterns
notes:       Web chat, Slack, SMS, WhatsApp channel setup. Channel-specific capability limitations. Embedded service vs standalone agent.
```

### AGT-012
```yaml
skill:       agentforce-for-service
path:        skills/agentforce/agentforce-for-service/
status:      TODO
priority:    P1
waf-pillars: User Experience, Reliability, Scalability
official-docs:
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
  - "Einstein Trust Layer: https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm&type=5"
rag-source:  Check Salesforce-RAG for service cloud AI patterns
notes:       Case deflection, agent-to-Live-Agent handoff, case creation from conversation, knowledge article surfacing. Practical Service Cloud integration.
```

---

## DOMAIN: Security

### SEC-001
```yaml
skill:       crud-fls-enforcement
path:        skills/security/crud-fls-enforcement/
status:      TODO
priority:    P0
waf-pillars: Security
official-docs:
  - "Secure Apex Classes: https://developer.salesforce.com/docs/platform/lwc/guide/apex-security"
  - "Apex Developer Guide — Security: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security.htm"
  - "Apex Reference — Security.stripInaccessible: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Security.htm"
rag-source:  SEEDED — import from Salesforce-RAG CRUD/FLS examples
notes:       Schema.describe patterns, Security.stripInaccessible, WITH SECURITY_ENFORCED, User Mode queries. The canonical security enforcement reference. NOT a duplicate of soql-security.
```

### SEC-002
```yaml
skill:       sharing-model-architecture
path:        skills/security/sharing-model-architecture/
status:      TODO
priority:    P0
waf-pillars: Security, Scalability
official-docs:
  - "Salesforce Security Guide — Sharing: https://help.salesforce.com/s/articleView?id=sf.security_sharing.htm&type=5"
  - "Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm"
  - "Apex Developer Guide — Sharing: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security_sharing_rules.htm"
rag-source:  Check Salesforce-RAG for sharing model patterns
notes:       OWD design decisions, role hierarchy depth implications, all sharing rule types, Apex managed sharing, implicit sharing. Critical for Government Cloud.
```

### SEC-003
```yaml
skill:       shield-platform-encryption
path:        skills/security/shield-platform-encryption/
status:      TODO
priority:    P1
waf-pillars: Security, Reliability
official-docs:
  - "Shield Platform Encryption Guide: https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5"
  - "Shield Encryption — Key Management: https://help.salesforce.com/s/articleView?id=sf.security_pe_key_management.htm&type=5"
rag-source:  Check Salesforce-RAG for encryption patterns
notes:       Field-level encryption decision criteria, key management lifecycle, deterministic vs probabilistic, SOQL filter limitations on encrypted fields, performance impact.
```

### SEC-004
```yaml
skill:       named-credentials-and-secrets
path:        skills/security/named-credentials-and-secrets/
status:      TODO
priority:    P1
waf-pillars: Security
official-docs:
  - "Named Credentials (Help): https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm&type=5"
  - "External Credentials (Help): https://help.salesforce.com/s/articleView?id=sf.external_credentials_overview.htm&type=5"
  - "Apex Developer Guide — Named Credentials: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm"
rag-source:  Check Salesforce-RAG for credential management patterns
notes:       Never hardcode credentials. Named Credential types (legacy vs new per-user/org). External Credentials. Secure parameter storage.
```

### SEC-005
```yaml
skill:       injection-prevention
path:        skills/security/injection-prevention/
status:      TODO
priority:    P0
waf-pillars: Security
official-docs:
  - "Apex Developer Guide — Security: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security.htm"
  - "Secure Apex Classes: https://developer.salesforce.com/docs/platform/lwc/guide/apex-security"
  - "LWC Best Practices — Security: https://developer.salesforce.com/docs/platform/lwc/guide/security-lwc.html"
rag-source:  Check Salesforce-RAG for injection patterns
notes:       SOQL injection (bind variables vs String.escapeSingleQuotes), SOSL injection, XSS in LWC (innerHTML), formula injection. Complement soql-security — not a duplicate.
```

### SEC-006
```yaml
skill:       session-security-policies
path:        skills/security/session-security-policies/
status:      TODO
priority:    P1
waf-pillars: Security, Reliability
official-docs:
  - "Salesforce Security Guide — Sessions: https://help.salesforce.com/s/articleView?id=sf.security_user_session.htm&type=5"
  - "Salesforce Security Guide: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for session patterns
notes:       Session timeout configuration, IP restriction enforcement, concurrent sessions, two-factor authentication enforcement, high-assurance sessions.
```

### SEC-007
```yaml
skill:       audit-trail-and-event-monitoring
path:        skills/security/audit-trail-and-event-monitoring/
status:      TODO
priority:    P1
waf-pillars: Security, Operational Excellence
official-docs:
  - "Event Monitoring: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/using_resources_event_log_files.htm"
  - "Salesforce Security Guide — Audit Trail: https://help.salesforce.com/s/articleView?id=sf.monitorsetup.htm&type=5"
  - "Shield Event Monitoring: https://help.salesforce.com/s/articleView?id=sf.event_monitoring_intro.htm&type=5"
rag-source:  Check Salesforce-RAG for audit patterns
notes:       Setup Audit Trail coverage, Field History Tracking limits, Event Monitoring log types and analysis, Shield Event Monitoring for threat detection.
```

### SEC-008
```yaml
skill:       security-health-check
path:        skills/security/security-health-check/
status:      TODO
priority:    P1
waf-pillars: Security, Operational Excellence
official-docs:
  - "Salesforce Security Guide — Health Check: https://help.salesforce.com/s/articleView?id=sf.security_health_check.htm&type=5"
  - "Salesforce Security Guide: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for org health patterns
notes:       Health Check score interpretation, baseline standards, remediation priority order, automating health check monitoring.
```

### SEC-009
```yaml
skill:       api-security-and-rate-limiting
path:        skills/security/api-security-and-rate-limiting/
status:      TODO
priority:    P1
waf-pillars: Security, Reliability
official-docs:
  - "REST API Developer Guide — Limits: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm"
  - "Salesforce Security Guide — Connected Apps: https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm&type=5"
  - "Shield Event Monitoring: https://help.salesforce.com/s/articleView?id=sf.event_monitoring_intro.htm&type=5"
rag-source:  Check Salesforce-RAG for API security patterns
notes:       Connected App policies, IP allowlists, per-user API limits, OAuth scope restriction, JWT Bearer for service accounts, API abuse detection.
```

### SEC-010
```yaml
skill:       data-masking-and-anonymization
path:        skills/security/data-masking-and-anonymization/
status:      TODO
priority:    P1
waf-pillars: Security, Reliability
official-docs:
  - "Salesforce Security Guide: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5"
  - "Shield Platform Encryption Guide: https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm&type=5"
  - "Data Mask (Help): https://help.salesforce.com/s/articleView?id=sf.data_mask_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for data privacy patterns
notes:       Sandbox seeding with masked data, GDPR/CCPA right-to-erasure in Salesforce, anonymization strategies, Data Mask product, custom masking scripts.
```

---

## DOMAIN: Integration

### INT-001
```yaml
skill:       rest-api-patterns
path:        skills/integration/rest-api-patterns/
status:      TODO
priority:    P0
waf-pillars: Security, Reliability
official-docs:
  - "REST API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm"
  - "REST API — OAuth Flows: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_understanding_authentication.htm"
  - "REST API — Composite API: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_composite.htm"
rag-source:  SEEDED — import from Salesforce-RAG REST patterns
notes:       Connected Apps, all OAuth flows (Web Server, JWT Bearer, Device), API versioning strategy, error codes, rate limits, composite API for batch operations.
```

### INT-002
```yaml
skill:       platform-events-and-cdc
path:        skills/integration/platform-events-and-cdc/
status:      TODO
priority:    P1
waf-pillars: Scalability, Reliability
official-docs:
  - "Platform Events Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm"
  - "Change Data Capture Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm"
rag-source:  Check Salesforce-RAG for event-driven patterns
notes:       Platform Events vs CDC vs Streaming API decision. Replay ID management. High-volume considerations. Subscriber patterns outside Salesforce (external consumers).
```

### INT-003
```yaml
skill:       mulesoft-salesforce-patterns
path:        skills/integration/mulesoft-salesforce-patterns/
status:      TODO
priority:    P1
waf-pillars: Reliability, Scalability
official-docs:
  - "REST API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm"
  - "Integration Patterns (Architects): https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html"
  - "Bulk API 2.0 Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm"
rag-source:  Check Salesforce-RAG for MuleSoft patterns
notes:       Salesforce Connector configuration, Upsert patterns, watermark sync, error handling and DLQ strategy, API-led connectivity applied to Salesforce.
```

### INT-004
```yaml
skill:       external-services
path:        skills/integration/external-services/
status:      TODO
priority:    P1
waf-pillars: Reliability, Security
official-docs:
  - "External Services (Help): https://help.salesforce.com/s/articleView?id=sf.external_services.htm&type=5"
  - "REST API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm"
rag-source:  Check Salesforce-RAG for external service patterns
notes:       OpenAPI 3.0 import, Apex class generation, calling from Flow, limitations vs Apex callouts, authentication setup, version management.
```

### INT-005
```yaml
skill:       error-handling-in-integrations
path:        skills/integration/error-handling-in-integrations/
status:      TODO
priority:    P0
waf-pillars: Reliability
official-docs:
  - "REST API Developer Guide — Error Handling: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm"
  - "Platform Events Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm"
  - "Integration Patterns (Architects): https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html"
rag-source:  Check Salesforce-RAG for error handling patterns
notes:       Dead letter queue patterns, retry with exponential backoff, idempotency keys, error notification design, Platform Event-based error logging.
```

### INT-006
```yaml
skill:       bulk-api-patterns
path:        skills/integration/bulk-api-patterns/
status:      TODO
priority:    P1
waf-pillars: Scalability, Performance
official-docs:
  - "Bulk API 2.0 Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm"
  - "Bulk API 2.0 — Job Lifecycle: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_bulk_createjob.htm"
rag-source:  Check Salesforce-RAG for bulk API patterns
notes:       Bulk API 2.0 vs v1 comparison, job lifecycle, serial vs parallel mode, 24h rolling window limits, monitoring via AsyncApexJob.
```

### INT-007
```yaml
skill:       salesforce-to-salesforce-integration
path:        skills/integration/salesforce-to-salesforce-integration/
status:      TODO
priority:    P2
waf-pillars: Reliability, Security
official-docs:
  - "REST API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm"
  - "External Objects (Help): https://help.salesforce.com/s/articleView?id=sf.external_objects_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for S2S patterns
notes:       Native S2S (legacy) vs REST API approach, use cases, limitations, Connected App auth between orgs, External Objects for real-time lookup.
```

### INT-008
```yaml
skill:       outbound-messages-and-webhooks
path:        skills/integration/outbound-messages-and-webhooks/
status:      TODO
priority:    P1
waf-pillars: Reliability, Scalability
official-docs:
  - "Outbound Messaging (Help): https://help.salesforce.com/s/articleView?id=sf.workflow_outbound_messaging.htm&type=5"
  - "Platform Events Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm"
rag-source:  Check Salesforce-RAG for outbound patterns
notes:       Workflow-based Outbound Messages limitations, Platform Events as modern replacement, retries, acknowledgement, ordering guarantees.
```

### INT-009
```yaml
skill:       integration-architecture-patterns
path:        skills/integration/integration-architecture-patterns/
status:      TODO
priority:    P0
waf-pillars: Scalability, Reliability, Security
official-docs:
  - "Integration Patterns (Architects): https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html"
  - "Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html"
rag-source:  SEEDED — from official Salesforce Architects integration patterns doc
notes:       Request-Reply vs Fire-and-Forget vs Batch vs Remote Call-In. Pattern selection decision guide. Architecture decisions, not code.
```

### INT-010
```yaml
skill:       aws-and-salesforce-patterns
path:        skills/integration/aws-and-salesforce-patterns/
status:      TODO
priority:    P1
waf-pillars: Security, Reliability, Performance
official-docs:
  - "REST API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm"
  - "Platform Events Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm"
  - "Integration Patterns (Architects): https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html"
rag-source:  Check Salesforce-RAG for cloud integration patterns
notes:       EventBridge + Platform Events, S3 via Apex callout, Lambda as middleware, ACM SSL vs Salesforce cert, CloudFront custom domain patterns.
```

---

## DOMAIN: Data

### DAT-001
```yaml
skill:       large-data-volumes
path:        skills/data/large-data-volumes/
status:      TODO
priority:    P0
waf-pillars: Scalability, Performance
official-docs:
  - "Large Data Volumes Best Practices: https://architect.salesforce.com/docs/architect/fundamentals/guide/large-data-volumes-introduction.html"
  - "SOQL and SOSL Reference: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm"
  - "Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm"
rag-source:  Check Salesforce-RAG for LDV patterns
notes:       Skinny tables, custom indexes, SOQL query plan tool, archiving strategy, table locks under heavy load. Critical for Government Cloud.
```

### DAT-002
```yaml
skill:       soql-optimisation
path:        skills/data/soql-optimisation/
status:      TODO
priority:    P0
waf-pillars: Performance, Scalability
official-docs:
  - "SOQL and SOSL Reference: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm"
  - "Apex Developer Guide — SOQL: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL.htm"
  - "Large Data Volumes Best Practices: https://architect.salesforce.com/docs/architect/fundamentals/guide/large-data-volumes-introduction.html"
rag-source:  SEEDED — import from Salesforce-RAG SOQL patterns
notes:       Selective query criteria, standard vs custom index usage, query plan tool interpretation, anti-patterns (negation operators, leading wildcards).
```

### DAT-003
```yaml
skill:       data-architecture-design
path:        skills/data/data-architecture-design/
status:      TODO
priority:    P1
waf-pillars: Scalability, Reliability
official-docs:
  - "Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm"
  - "Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html"
rag-source:  SEEDED — import from Salesforce-RAG data architecture patterns
notes:       Object relationship types and limits, field type selection guide, schema design principles, junction object patterns, external ID strategy.
```

### DAT-004
```yaml
skill:       data-migration-patterns
path:        skills/data/data-migration-patterns/
status:      TODO
priority:    P1
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Bulk API 2.0 Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm"
  - "Data Loader Guide: https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5"
  - "Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm"
rag-source:  Check Salesforce-RAG for migration patterns
notes:       Migration sequencing (parent before child), external ID strategy, Bulk API 2.0 tooling, rollback design, post-migration validation.
```

### DAT-005
```yaml
skill:       data-cloud-architecture
path:        skills/data/data-cloud-architecture/
status:      TODO
priority:    P1
waf-pillars: Scalability, Reliability
official-docs:
  - "Agentforce Developer Guide — Data Library: https://developer.salesforce.com/docs/einstein/genai/guide/data-library.html"
  - "Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html"
rag-source:  SEEDED — core content from Salesforce-RAG
notes:       Data streams and ingestion, Data Model Objects, identity resolution, Calculated Insights, activation to Marketing Cloud and Agentforce.
```

### DAT-006
```yaml
skill:       field-history-tracking
path:        skills/data/field-history-tracking/
status:      TODO
priority:    P1
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Object Reference — FieldHistoryRetention: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_fieldhistory.htm"
  - "Salesforce Security Guide: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for audit patterns
notes:       20-field limit per object, storage impact, 18-month retention, Big Object archiving, alternatives for longer retention, GDPR implications.
```

### DAT-007
```yaml
skill:       data-quality-framework
path:        skills/data/data-quality-framework/
status:      TODO
priority:    P2
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm"
  - "Apex Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm"
rag-source:  Check Salesforce-RAG for data quality patterns
notes:       Completeness, accuracy, consistency, timeliness scoring. Apex-based quality monitoring. Complement duplicate-management admin skill.
```

### DAT-008
```yaml
skill:       archiving-and-big-objects
path:        skills/data/archiving-and-big-objects/
status:      TODO
priority:    P1
waf-pillars: Scalability, Performance
official-docs:
  - "Big Objects (Help): https://help.salesforce.com/s/articleView?id=sf.big_object_overview.htm&type=5"
  - "Bulk API 2.0 Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm"
  - "Async SOQL: https://help.salesforce.com/s/articleView?id=sf.async_soql.htm&type=5"
rag-source:  Check Salesforce-RAG for archiving patterns
notes:       Big Object design and limitations, Async SOQL, archiving pattern from standard objects, external archiving with Heroku/S3, data retention policy.
```

### DAT-009
```yaml
skill:       custom-indexes-and-skinny-tables
path:        skills/data/custom-indexes-and-skinny-tables/
status:      TODO
priority:    P1
waf-pillars: Performance, Scalability
official-docs:
  - "Large Data Volumes Best Practices: https://architect.salesforce.com/docs/architect/fundamentals/guide/large-data-volumes-introduction.html"
  - "SOQL and SOSL Reference: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm"
rag-source:  Check Salesforce-RAG for index patterns
notes:       When to request a custom index, skinny table eligibility, maintenance overhead, how to raise a support case. Complement soql-optimisation skill.
```

### DAT-010
```yaml
skill:       reporting-on-data-relationships
path:        skills/data/reporting-on-data-relationships/
status:      TODO
priority:    P2
waf-pillars: User Experience, Performance
official-docs:
  - "Report Types (Help): https://help.salesforce.com/s/articleView?id=sf.reports_report_type_overview.htm&type=5"
  - "Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm"
rag-source:  Check Salesforce-RAG for reporting patterns
notes:       Cross-object report limits, report type design, row limits in reports vs dashboards, reporting on junction objects.
```

---

## DOMAIN: DevOps

### DEV-001
```yaml
skill:       sfdx-and-scratch-orgs
path:        skills/devops/sfdx-and-scratch-orgs/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence
official-docs:
  - "Salesforce DX Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm"
  - "Salesforce CLI Reference: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm"
rag-source:  Check Salesforce-RAG for SFDX patterns
notes:       sfdx-project.json structure, scratch org definition files, feature flags, org shape, CLI key commands.
```

### DEV-002
```yaml
skill:       unlocked-packages
path:        skills/devops/unlocked-packages/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence, Scalability
official-docs:
  - "Salesforce DX Developer Guide — Packages: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev_packages_unlocked.htm"
  - "Salesforce CLI Reference: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm"
rag-source:  Check Salesforce-RAG for packaging patterns
notes:       Package design principles, dependency management, version strategy, installation ordering, upgrade safety.
```

### DEV-003
```yaml
skill:       ci-cd-for-salesforce
path:        skills/devops/ci-cd-for-salesforce/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence, Reliability
official-docs:
  - "Salesforce DX Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm"
  - "Metadata API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm"
  - "Salesforce CLI Reference: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm"
rag-source:  Check Salesforce-RAG for CI/CD patterns
notes:       GitHub Actions pipeline design, test gate configuration, deployment validation org patterns. NOT a product tutorial for Copado/Gearset.
```

### DEV-004
```yaml
skill:       git-branching-for-salesforce
path:        skills/devops/git-branching-for-salesforce/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence
official-docs:
  - "Salesforce DX Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm"
  - "Metadata API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm"
rag-source:  Check Salesforce-RAG for git patterns
notes:       Branch strategy for org-based vs source-driven development, metadata XML conflict resolution, PR standards.
```

### DEV-005
```yaml
skill:       code-review-standards
path:        skills/devops/code-review-standards/
status:      TODO
priority:    P0
waf-pillars: Operational Excellence, Security, Reliability
official-docs:
  - "Apex Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
  - "Flow Reference: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5"
  - "Salesforce Code Analyzer: https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/getting-started.html"
rag-source:  SEEDED — import Sprint 5 code review checklist from Salesforce-RAG
notes:       Apex + LWC + Flow + OmniStudio review checklists. Automated vs manual review split.
```

### DEV-006
```yaml
skill:       apex-pmd-and-code-scanner
path:        skills/devops/apex-pmd-and-code-scanner/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence, Security
official-docs:
  - "Salesforce Code Analyzer: https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/getting-started.html"
  - "Apex Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm"
rag-source:  Check Salesforce-RAG for linting patterns
notes:       PMD Apex ruleset configuration, Salesforce Code Analyzer CLI, critical rule categories, suppression patterns, CI integration.
```

### DEV-007
```yaml
skill:       environment-and-org-strategy
path:        skills/devops/environment-and-org-strategy/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence, Reliability
official-docs:
  - "Salesforce DX Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm"
  - "Sandbox (Help): https://help.salesforce.com/s/articleView?id=sf.create_test_instance.htm&type=5"
rag-source:  Check Salesforce-RAG for environment patterns
notes:       Org topology design (Developer/Partial/Full sandbox), refresh strategy, environment promotion sequence, hotfix branching, production freeze policies.
```

### DEV-008
```yaml
skill:       metadata-coverage-and-gaps
path:        skills/devops/metadata-coverage-and-gaps/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence
official-docs:
  - "Metadata API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm"
  - "Metadata Coverage Report: https://mdcoverage.secure.force.com/docs/metadata-coverage"
rag-source:  Check Salesforce-RAG for metadata patterns
notes:       Metadata API coverage reference, types that cannot be deployed, manual migration steps for gaps, Metadata API vs Tooling API.
```

### DEV-009
```yaml
skill:       devops-center
path:        skills/devops/devops-center/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence
official-docs:
  - "DevOps Center (Help): https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm&type=5"
  - "Metadata API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm"
rag-source:  Check Salesforce-RAG for DevOps Center patterns
notes:       DevOps Center change tracking setup, pipeline configuration, work item bundling, comparison with Copado/Gearset, limitations.
```

---

---

## DOMAIN: Experience Cloud

Experience Cloud (formerly Community Cloud) is one of the most common places practitioners get security catastrophically wrong. Guest user OWD misconfiguration is a top Salesforce security incident vector.

### EXP-001
```yaml
skill:       guest-user-security
path:        skills/experience/guest-user-security/
status:      TODO
priority:    P0
waf-pillars: Security
official-docs:
  - "Experience Cloud Guest User — Security Best Practices: https://help.salesforce.com/s/articleView?id=sf.networks_guest_access.htm&type=5"
  - "Sharing and Visibility Best Practices for Guest Users: https://help.salesforce.com/s/articleView?id=000334993&type=1"
  - "Salesforce Security Guide: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5"
  - "Org-Wide Defaults for External Users: https://help.salesforce.com/s/articleView?id=sf.security_owd_external.htm&type=5"
rag-source:  Check Salesforce-RAG for guest user patterns
notes:       P0 because misconfigured guest user access is the #1 Experience Cloud security incident. OWD for external vs internal users, what Guest User can and cannot access, CRUD/FLS in Apex called by guest sessions, Guest User profile configuration pitfalls. This is the skill that prevents data leaks.
```

### EXP-002
```yaml
skill:       experience-cloud-sharing-model
path:        skills/experience/experience-cloud-sharing-model/
status:      TODO
priority:    P0
waf-pillars: Security, Scalability
official-docs:
  - "Experience Cloud Developer Guide — Sharing: https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_sharing_overview.htm"
  - "Org-Wide Defaults for External Users: https://help.salesforce.com/s/articleView?id=sf.security_owd_external.htm&type=5"
  - "Sharing Sets for External Users: https://help.salesforce.com/s/articleView?id=sf.networks_setting_light_users_sharing.htm&type=5"
rag-source:  Check Salesforce-RAG for sharing model patterns
notes:       External OWD is separate from internal OWD. Sharing Sets vs Share Groups vs manual sharing for external users. Community User license types and their sharing limits. Role hierarchy implications for external users. Critical for portal implementations.
```

### EXP-003
```yaml
skill:       experience-cloud-setup
path:        skills/experience/experience-cloud-setup/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence, User Experience
official-docs:
  - "Experience Cloud Builder: https://help.salesforce.com/s/articleView?id=sf.community_builder_overview.htm&type=5"
  - "Experience Cloud Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_intro.htm"
  - "Experience Cloud Templates: https://help.salesforce.com/s/articleView?id=sf.networks_lightningboot_templates.htm&type=5"
rag-source:  Check Salesforce-RAG for Experience Cloud patterns
notes:       Template selection (LWR vs Aura), Network object configuration, custom domain setup, CDN, workspaces. Build decisions that are hard to reverse. NOT for theming/branding.
```

### EXP-004
```yaml
skill:       self-registration-and-user-management
path:        skills/experience/self-registration-and-user-management/
status:      TODO
priority:    P1
waf-pillars: Security, Reliability
official-docs:
  - "Experience Cloud — Self-Registration: https://help.salesforce.com/s/articleView?id=sf.networks_customize_login.htm&type=5"
  - "Experience Cloud Developer Guide — User Management: https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_user_management.htm"
  - "Apex Developer Guide — Site.createPortalUser: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_sites.htm"
rag-source:  Check Salesforce-RAG for community user patterns
notes:       Self-registration Apex handler design, duplicate person account prevention, user creation via Site.createPortalUser, person account vs contact-based accounts, email verification flows, required profile/permission set assignment on creation.
```

### EXP-005
```yaml
skill:       experience-cloud-lwc-components
path:        skills/experience/experience-cloud-lwc-components/
status:      TODO
priority:    P1
waf-pillars: User Experience, Performance
official-docs:
  - "Experience Cloud Developer Guide — LWC: https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_lwc.htm"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
  - "Lightning Web Runtime for Experience Cloud: https://developer.salesforce.com/docs/platform/lwr/guide/lwr-get-started.html"
rag-source:  Check Salesforce-RAG for Experience Cloud LWC patterns
notes:       LWC in LWR vs Aura templates, CurrentPageReference in Experience, NavigationMixin differences in community context, isGuest and user context detection, page access token patterns.
```

### EXP-006
```yaml
skill:       experience-cloud-performance
path:        skills/experience/experience-cloud-performance/
status:      TODO
priority:    P1
waf-pillars: Performance, User Experience
official-docs:
  - "Experience Cloud Builder Performance: https://help.salesforce.com/s/articleView?id=sf.community_builder_performance.htm&type=5"
  - "Experience Cloud Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_intro.htm"
  - "LWC Best Practices — Performance: https://developer.salesforce.com/docs/platform/lwc/guide/performance.html"
rag-source:  Check Salesforce-RAG for Experience Cloud performance patterns
notes:       LWR vs Aura performance comparison, CDN and caching strategy, lazy loading pages, critical CSS, avoiding SOQL on page load, image optimization. Guest user context has no server-side caching.
```

### EXP-007
```yaml
skill:       experience-cloud-headless-and-lwr
path:        skills/experience/experience-cloud-headless-and-lwr/
status:      TODO
priority:    P2
waf-pillars: Performance, Scalability
official-docs:
  - "Lightning Web Runtime for Experience Cloud: https://developer.salesforce.com/docs/platform/lwr/guide/lwr-get-started.html"
  - "Headless Experience Cloud: https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_headless.htm"
  - "Experience Cloud Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_intro.htm"
rag-source:  Check Salesforce-RAG for headless patterns
notes:       LWR vs Aura vs headless/composable decision. When headless is justified (custom storefront, mobile app backend). REST/GraphQL API serving. NOT for standard community builds.
```

---

## DOMAIN: Service Cloud

Service Cloud is the most widely deployed Salesforce product after Sales Cloud. Practitioners constantly struggle with entitlements, case routing, and knowledge integration. These are high-value skills.

### SVC-001
```yaml
skill:       case-management-patterns
path:        skills/servicecloud/case-management-patterns/
status:      TODO
priority:    P0
waf-pillars: Reliability, User Experience
official-docs:
  - "Service Cloud Overview: https://help.salesforce.com/s/articleView?id=sf.service_cloud_overview.htm&type=5"
  - "Cases (Object Reference): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_case.htm"
  - "Case Assignment Rules: https://help.salesforce.com/s/articleView?id=sf.customize_caseassign.htm&type=5"
  - "Case Auto-Response Rules: https://help.salesforce.com/s/articleView?id=sf.customize_caserespond.htm&type=5"
rag-source:  Check Salesforce-RAG for Service Cloud patterns
notes:       Case lifecycle (New→Working→Escalated→Closed), assignment rule design, auto-response templates, case team patterns, parent-child case design, custom case statuses and what they mean. Foundation skill for all Service Cloud work.
```

### SVC-002
```yaml
skill:       entitlements-and-sla
path:        skills/servicecloud/entitlements-and-sla/
status:      TODO
priority:    P0
waf-pillars: Reliability, User Experience
official-docs:
  - "Entitlements and Milestones: https://help.salesforce.com/s/articleView?id=sf.entitlements_overview.htm&type=5"
  - "Entitlement Processes: https://help.salesforce.com/s/articleView?id=sf.entitlements_setup_entitlements.htm&type=5"
  - "Milestone Actions: https://help.salesforce.com/s/articleView?id=sf.entitlements_milestones.htm&type=5"
  - "Cases (Object Reference): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_case.htm"
rag-source:  Check Salesforce-RAG for SLA patterns
notes:       Entitlement Process design (business hours vs calendar hours), Milestone types (First Response, Resolution), time-based actions, escalation via Flow/Apex, SLA breach reporting. One of the most underimplemented Service Cloud features.
```

### SVC-003
```yaml
skill:       omni-channel-routing
path:        skills/servicecloud/omni-channel-routing/
status:      TODO
priority:    P1
waf-pillars: Scalability, User Experience
official-docs:
  - "Omni-Channel Overview: https://help.salesforce.com/s/articleView?id=sf.omnichannel_intro.htm&type=5"
  - "Omni-Channel Routing Models: https://help.salesforce.com/s/articleView?id=sf.omnichannel_routing_model_overview.htm&type=5"
  - "Service Channel Configuration: https://help.salesforce.com/s/articleView?id=sf.omnichannel_creating_service_channels.htm&type=5"
rag-source:  Check Salesforce-RAG for routing patterns
notes:       Skill-based routing vs queue-based vs external routing, capacity model configuration, agent availability states, routing priority, Omni Supervisor. Decision guide for routing model selection.
```

### SVC-004
```yaml
skill:       knowledge-base-management
path:        skills/servicecloud/knowledge-base-management/
status:      TODO
priority:    P1
waf-pillars: User Experience, Operational Excellence
official-docs:
  - "Salesforce Knowledge Overview: https://help.salesforce.com/s/articleView?id=sf.knowledge_whatis.htm&type=5"
  - "Knowledge Article Types: https://help.salesforce.com/s/articleView?id=sf.knowledge_article_types.htm&type=5"
  - "Knowledge and Search: https://help.salesforce.com/s/articleView?id=sf.knowledge_setup.htm&type=5"
rag-source:  Check Salesforce-RAG for knowledge patterns
notes:       Article type design, data category hierarchy, visibility configuration (Internal/Partner/Customer/Public), versioning, translation, search optimization, Einstein Article Recommendations. Knowledge is critical for both agent productivity and customer self-service.
```

### SVC-005
```yaml
skill:       email-to-case-setup
path:        skills/servicecloud/email-to-case-setup/
status:      TODO
priority:    P1
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Email-to-Case Setup: https://help.salesforce.com/s/articleView?id=sf.setting_up_email_to_case.htm&type=5"
  - "On-Demand Email-to-Case: https://help.salesforce.com/s/articleView?id=sf.setting_up_email_on_demand.htm&type=5"
  - "Salesforce Security Guide — Email: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for email service patterns
notes:       Email-to-Case vs On-Demand Email-to-Case decision, routing address configuration, threading token handling, attachment size limits, SPF/DKIM for deliverability, handling replies on closed cases, spam prevention.
```

### SVC-006
```yaml
skill:       case-escalation-and-milestones
path:        skills/servicecloud/case-escalation-and-milestones/
status:      TODO
priority:    P1
waf-pillars: Reliability, User Experience
official-docs:
  - "Escalation Rules: https://help.salesforce.com/s/articleView?id=sf.customize_caseescalation.htm&type=5"
  - "Entitlements and Milestones: https://help.salesforce.com/s/articleView?id=sf.entitlements_overview.htm&type=5"
  - "Flow Reference — Time-Based Automation: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_schedule.htm&type=5"
rag-source:  Check Salesforce-RAG for escalation patterns
notes:       Escalation Rule chains, time-based escalation vs milestone-based escalation, who gets notified and how, Flow vs Escalation Rules decision, manager escalation chains, SLA vs Escalation Rule interaction.
```

---

## DOMAIN: Admin (additional skills)

### ADM-019 — DONE: permission-set-architecture
```yaml
skill:       permission-set-architecture
path:        skills/admin/permission-set-architecture/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Security, Operational Excellence
official-docs:
  - "Permission Sets (Help): https://help.salesforce.com/s/articleView?id=sf.perm_sets_overview.htm&type=5"
  - "Permission Set Groups: https://help.salesforce.com/s/articleView?id=sf.perm_set_groups.htm&type=5"
  - "Muting Permission Sets: https://help.salesforce.com/s/articleView?id=sf.perm_set_groups_muting_overview.htm&type=5"
  - "Profile Retirement Roadmap: https://help.salesforce.com/s/articleView?id=sf.users_profiles_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for permission patterns
notes:       Built permission-set-first architecture guidance for minimum-access profiles, capability bundles, custom-permission policy hooks, and a checker for profile-heavy or overly broad permission-set designs.
```

### ADM-020
```yaml
skill:       approval-process-design
path:        skills/admin/approval-process-design/
status:      TODO
priority:    P1
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Approval Process Setup: https://help.salesforce.com/s/articleView?id=sf.approvals_creating.htm&type=5"
  - "Approval Process — Jump To Step: https://help.salesforce.com/s/articleView?id=sf.approvals_process.htm&type=5"
  - "Apex Developer Guide — Process.SubmitRequest: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Process_ProcessWorkitemRequest.htm"
rag-source:  Check Salesforce-RAG for approval patterns
notes:       Multi-step approval design, dynamic approver assignment (role hierarchy vs manager field vs queue), delegated approver, recall/reject/reassign patterns, Apex-submitted approvals (Process.SubmitRequest), approval email template design. Common in Quote, Expense, PTO workflows.
```

### ADM-021
```yaml
skill:       formula-field-patterns
path:        skills/admin/formula-field-patterns/
status:      TODO
priority:    P1
waf-pillars: Reliability, Performance
official-docs:
  - "Formula Fields (Help): https://help.salesforce.com/s/articleView?id=sf.customize_formulas.htm&type=5"
  - "Formula Functions Reference: https://help.salesforce.com/s/articleView?id=sf.customize_formulaops.htm&type=5"
  - "Cross-Object Formulas: https://help.salesforce.com/s/articleView?id=sf.formula_using_cross_object.htm&type=5"
rag-source:  Check Salesforce-RAG for formula patterns
notes:       Cross-object formula depth limits (5 hops), compile size limit (5,000 chars), VLOOKUP, PRIORVALUE in field updates, ISCHANGED in validation rules, formula field on Report Types, performance impact of complex formulas on large data sets.
```

### ADM-022
```yaml
skill:       duplicate-management
path:        skills/admin/duplicate-management/
status:      TODO
priority:    P1
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Duplicate Management (Help): https://help.salesforce.com/s/articleView?id=sf.managing_duplicates_overview.htm&type=5"
  - "Matching Rules: https://help.salesforce.com/s/articleView?id=sf.matching_rules_overview.htm&type=5"
  - "Duplicate Rules: https://help.salesforce.com/s/articleView?id=sf.duplicate_rules_overview.htm&type=5"
  - "Apex Developer Guide — Datacloud Duplicate API: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_datacloud_DuplicateResult.htm"
rag-source:  Check Salesforce-RAG for data quality patterns
notes:       Matching Rule algorithm selection (exact vs fuzzy), Duplicate Rule action (Allow/Block/Report), Merge API via Apex, Lead deduplication before conversion, third-party dedup tools for large orgs, Person Account deduplication patterns.
```

### ADM-023
```yaml
skill:       email-deliverability-and-relay
path:        skills/admin/email-deliverability-and-relay/
status:      TODO
priority:    P1
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Email Deliverability (Help): https://help.salesforce.com/s/articleView?id=sf.emailadmin_deliverability.htm&type=5"
  - "Email Relay Setup: https://help.salesforce.com/s/articleView?id=sf.emailadmin_relay_overview.htm&type=5"
  - "SPF, DKIM, DMARC for Salesforce: https://help.salesforce.com/s/articleView?id=sf.emailadmin_email_deliverability_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for email setup patterns
notes:       SPF/DKIM/DMARC setup for outbound Salesforce email, email relay for corporate email gateway, bounce handling, mass email limits vs transactional email, Salesforce org-wide email addresses, send-through vs relay decision.
```

### ADM-024
```yaml
skill:       dynamic-forms-and-dynamic-actions
path:        skills/admin/dynamic-forms-and-dynamic-actions/
status:      TODO
priority:    P1
waf-pillars: User Experience, Operational Excellence
official-docs:
  - "Dynamic Forms (Help): https://help.salesforce.com/s/articleView?id=sf.dynamic_forms_overview.htm&type=5"
  - "Dynamic Actions (Help): https://help.salesforce.com/s/articleView?id=sf.dynamic_actions_overview.htm&type=5"
  - "Lightning App Builder: https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for UX configuration patterns
notes:       Dynamic Forms vs classic page layouts decision (supported objects, profile-based vs rule-based visibility), Field Section vs Field components, Dynamic Actions filtering rules, mobile support status, migration from classic layouts.
```

### ADM-025
```yaml
skill:       order-of-execution
path:        skills/admin/order-of-execution/
status:      TODO
priority:    P0
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Triggers and Order of Execution: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_exec.htm"
  - "Flow Reference: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5"
  - "Validation Rules: https://help.salesforce.com/s/articleView?id=sf.fields_about_field_validation.htm&type=5"
rag-source:  Check Salesforce-RAG for order of execution patterns
notes:       Foundational cross-domain skill. Full save-operation sequence: system validation → before-save flows → before triggers → system validation + duplicate rules → after triggers → assignment rules → auto-response rules → workflow rules → after-save flows → entitlement rules → criteria-based sharing → roll-up summaries → cross-object workflows → post-commit logic. Where each automation type fires relative to others. What causes re-evaluation. Common conflicts between Flows and Apex triggers. Why before-save flows are cheaper than after-save. Must include a clear visual/table of the full sequence. This is the single most referenced concept in Salesforce development and every practitioner needs it.
```

---

## DOMAIN: Apex (additional skills)

### APX-016
```yaml
skill:       platform-cache
path:        skills/apex/platform-cache/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Performance, Scalability
official-docs:
  - "Apex Developer Guide — Platform Cache: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_cache_overview.htm"
  - "Apex Reference — Cache.OrgPartition: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_cache_OrgPartition.htm"
  - "Platform Cache Considerations: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_cache_considerations.htm"
rag-source:  Check Salesforce-RAG for caching patterns
notes:       Built Platform Cache guidance for org vs session scope, cache-aside wrappers, key versioning, invalidation, and a checker for unsafe shared cache and missing miss-paths.
```

### APX-017
```yaml
skill:       apex-cpu-and-heap-optimization
path:        skills/apex/apex-cpu-and-heap-optimization/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Performance, Scalability
official-docs:
  - "Apex Developer Guide — Governor Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm"
  - "Apex Developer Guide — Performance Best Practices: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_performance_best_practices.htm"
  - "Apex Reference — Limits Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_limits.htm"
rag-source:  Check Salesforce-RAG for performance patterns
notes:       Built CPU and heap optimization guidance for nested-loop refactors, payload pressure, temporary `Limits.getCpuTime()` checkpoints, and a checker for JSON, regex, and string work inside loops.
```

### APX-018
```yaml
skill:       recursive-trigger-prevention
path:        skills/apex/recursive-trigger-prevention/
status:      DONE
agent:       Codex
started:     2026-03-13T18:25:36Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Reliability, Scalability
official-docs:
  - "Apex Developer Guide — Triggers: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers.htm"
  - "Apex Developer Guide — Trigger Patterns: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_bestpract.htm"
rag-source:  SEEDED — check Salesforce-RAG for trigger framework patterns
notes:       Built recursion-prevention guidance for self-DML, delta checks, record-aware guards, and a checker that flags blunt static booleans and missing old/new comparisons.
```

### APX-019
```yaml
skill:       custom-metadata-in-apex
path:        skills/apex/custom-metadata-in-apex/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Apex Developer Guide — Custom Metadata: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/custommetadata_apex.htm"
  - "Metadata API Developer Guide (Custom Metadata): https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custommetadata.htm"
  - "Custom Metadata Types (Help): https://help.salesforce.com/s/articleView?id=sf.custommetadata_about.htm&type=5"
rag-source:  Check Salesforce-RAG for custom metadata patterns
notes:       Built Apex guidance for reading and deploying custom metadata, testing behavior, packaging visibility, and a checker for runtime DML assumptions and weak metadata test patterns.
```

### APX-020
```yaml
skill:       governor-limits-quick-reference
path:        skills/apex/governor-limits-quick-reference/
status:      TODO
priority:    P0
waf-pillars: Reliability, Scalability
official-docs:
  - "Execution Governors and Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm"
  - "Apex Developer Guide — System.Limits: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_limits.htm"
rag-source:  Check Salesforce-RAG for governor limit patterns
notes:       Pure reference card. Every governor limit number in one place organized by context (synchronous, asynchronous, batch start, batch execute, Queueable, future, scheduled). Table format with limit name, sync value, async value, batch value. Common patterns that hit each limit. Companion to governor-limits skill (APX-003) which covers strategy — this skill covers the numbers. Include CPU time (10s sync / 60s async), heap (6MB / 12MB), SOQL (100 / 200), DML (150), DML rows (10k), callouts (100), future calls (50), Queueable enqueue (1 child per execution / 50 from non-Queueable). Must be the cheat sheet every Apex developer bookmarks.
```

---

## DOMAIN: Integration (additional skills)

### INT-011
```yaml
skill:       graphql-api-patterns
path:        skills/integration/graphql-api-patterns/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Performance, Reliability
official-docs:
  - "Salesforce GraphQL API Developer Guide: https://developer.salesforce.com/docs/platform/graphql/guide/graphql-about.html"
  - "GraphQL API — Queries and Mutations: https://developer.salesforce.com/docs/platform/graphql/guide/graphql-queries.html"
  - "GraphQL API — Aggregations: https://developer.salesforce.com/docs/platform/graphql/guide/graphql-aggregations.html"
rag-source:  Check Salesforce-RAG for GraphQL patterns
notes:       Built Salesforce GraphQL guidance for variables, adapter choice, pagination, GraphQL vs REST decisions, and a checker for interpolated query strings and weak transport patterns.
```

### INT-012
```yaml
skill:       salesforce-connect-external-objects
path:        skills/integration/salesforce-connect-external-objects/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Scalability, Reliability
official-docs:
  - "Salesforce Connect Overview: https://help.salesforce.com/s/articleView?id=sf.platform_connect_about.htm&type=5"
  - "External Objects (Help): https://help.salesforce.com/s/articleView?id=sf.external_objects_overview.htm&type=5"
  - "OData Adapter for Salesforce Connect: https://help.salesforce.com/s/articleView?id=sf.platform_connect_odata_adapter.htm&type=5"
  - "Custom Adapter (Apex): https://help.salesforce.com/s/articleView?id=sf.platform_connect_custom_adapter.htm&type=5"
rag-source:  Check Salesforce-RAG for external data patterns
notes:       Built Salesforce Connect guidance for virtualization vs replication, OData and custom adapter choice, latency and feature-fit tradeoffs, and a checker for risky `__x` query patterns.
```

### INT-013
```yaml
skill:       oauth-flows-and-connected-apps
path:        skills/integration/oauth-flows-and-connected-apps/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Security, Reliability
official-docs:
  - "OAuth Authorization Flows: https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_flows.htm&type=5"
  - "Connected Apps Overview: https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm&type=5"
  - "JWT Bearer Token Flow: https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5"
  - "REST API — OAuth: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_understanding_authentication.htm"
rag-source:  Check Salesforce-RAG for OAuth patterns
notes:       Built integration-focused OAuth guidance for client credentials, JWT bearer, auth code, scope and token lifecycle governance, and a checker for weak flows, broad scopes, and hardcoded secrets.
```

---

## DOMAIN: Data (additional skills)

### DAT-011
```yaml
skill:       roll-up-summary-alternatives
path:        skills/data/roll-up-summary-alternatives/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Performance, Reliability
official-docs:
  - "Roll-Up Summary Fields (Help): https://help.salesforce.com/s/articleView?id=sf.fields_about_roll_up_summary.htm&type=5"
  - "Apex Developer Guide — Aggregate SOQL: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_agg_fns.htm"
  - "Flow Reference — Record-Triggered Flows: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm&type=5"
rag-source:  Check Salesforce-RAG for rollup patterns
notes:       Built guidance for native roll-up fit, Flow and Apex alternatives, recalculation and locking tradeoffs, and a checker for aggregate-in-loop and approaching summary-limit signals.
```

### DAT-012
```yaml
skill:       sosl-search-patterns
path:        skills/data/sosl-search-patterns/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Performance, User Experience
official-docs:
  - "SOQL and SOSL Reference — SOSL: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl.htm"
  - "Apex Developer Guide — SOSL: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOSL.htm"
  - "Search Manager (Help): https://help.salesforce.com/s/articleView?id=sf.search_manager_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for search patterns
notes:       Built SOSL guidance for search vs filter decisions, result shaping, Search.query safety, and a checker for risky dynamic SOSL and LIKE-based pseudo-search patterns.
```

### DAT-013
```yaml
skill:       multi-currency-and-advanced-currency-management
path:        skills/data/multi-currency-and-advanced-currency-management/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Reliability, Scalability
official-docs:
  - "Multi-Currency (Help): https://help.salesforce.com/s/articleView?id=sf.admin_currency.htm&type=5"
  - "Advanced Currency Management: https://help.salesforce.com/s/articleView?id=sf.admin_currency_dated_exchange.htm&type=5"
  - "SOQL and SOSL — Currency in Queries: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_currency.htm"
rag-source:  Check Salesforce-RAG for currency patterns
notes:       Built multi-currency guidance for irreversible activation, CurrencyIsoCode handling, convertCurrency, ACM tradeoffs, and a checker for bare amount queries and hardcoded currency assumptions.
```

---

## DOMAIN: Security (additional skills)

### SEC-011
```yaml
skill:       permission-set-groups-and-muting
path:        skills/security/permission-set-groups-and-muting/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P0
waf-pillars: Security, Operational Excellence
official-docs:
  - "Permission Set Groups: https://help.salesforce.com/s/articleView?id=sf.perm_set_groups.htm&type=5"
  - "Muting Permission Sets: https://help.salesforce.com/s/articleView?id=sf.perm_set_groups_muting_overview.htm&type=5"
  - "Permission Sets (Help): https://help.salesforce.com/s/articleView?id=sf.perm_sets_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for permission patterns
notes:       Built PSG and muting guidance for access-bundle design, profile minimization, migration strategy, and a checker for profile-heavy orgs with weak PSG adoption signals.
```

### SEC-012
```yaml
skill:       org-hardening-and-baseline-config
path:        skills/security/org-hardening-and-baseline-config/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Security, Operational Excellence
official-docs:
  - "Salesforce Security Guide: https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5"
  - "Security Health Check: https://help.salesforce.com/s/articleView?id=sf.security_health_check.htm&type=5"
  - "Critical Updates and Release Settings: https://help.salesforce.com/s/articleView?id=sf.release_updates.htm&type=5"
  - "Clickjack Protection: https://help.salesforce.com/s/articleView?id=sf.security_clickjack_overview.htm&type=5"
rag-source:  Check Salesforce-RAG for org hardening patterns
notes:       Built baseline org-hardening guidance for Health Check context, trust exceptions, session and browser controls, release cadence, and a checker for missing hardening metadata signals.
```

---

## DOMAIN: LWC (additional skills)

### LWC-013
```yaml
skill:       custom-property-editor-for-flow
path:        skills/lwc/custom-property-editor-for-flow/
status:      DONE
agent:       Codex
started:     2026-03-13T19:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: User Experience, Operational Excellence
official-docs:
  - "Flow Reference — Custom Property Editor: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_cpe.htm&type=5"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
  - "Flow Reference — Screen Component: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen.htm&type=5"
rag-source:  Check Salesforce-RAG for Flow screen component patterns
notes:       Built LWC custom-property-editor guidance for metadata hookup, builder APIs, value-change events, and a checker for missing Flow editor registration and weak builder contracts.
```

### LWC-014 — DONE: lwc-offline-and-mobile
```yaml
skill:       lwc-offline-and-mobile
path:        skills/lwc/lwc-offline-and-mobile/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: User Experience, Reliability
official-docs:
  - "LWC Offline Development: https://developer.salesforce.com/docs/platform/lwc/guide/offline-intro.html"
  - "Salesforce Mobile App Customization: https://help.salesforce.com/s/articleView?id=sf.salesforce1_overview.htm&type=5"
  - "Mobile SDK Overview: https://developer.salesforce.com/docs/atlas.en-us.mobile_sdk.meta/mobile_sdk/intro.htm"
rag-source:  Check Salesforce-RAG for offline/mobile patterns
notes:       Built mobile and offline LWC guidance for task-focused mobile UX, adapter choice, container-safe navigation, and a checker for hardcoded paths, weak network handling, and online-first GraphQL on offline-oriented surfaces.
```

---

## DOMAIN: Flow (additional skills)

### FLW-011 — DONE: flow-custom-property-editors
```yaml
skill:       flow-custom-property-editors
path:        skills/flow/flow-custom-property-editors/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: User Experience, Operational Excellence
official-docs:
  - "Flow Reference — Custom Property Editor: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_cpe.htm&type=5"
  - "LWC Best Practices: https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html"
rag-source:  Check Salesforce-RAG for Flow extensibility patterns
notes:       Built Flow custom-property-editor guidance for when to introduce a design-time editor, metadata registration, builderContext validation, and a checker for weak builder contracts.
```

### FLW-012 — DONE: flow-for-experience-cloud
```yaml
skill:       flow-for-experience-cloud
path:        skills/flow/flow-for-experience-cloud/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: User Experience, Security
official-docs:
  - "Flow Reference — Availability in Experience Cloud: https://help.salesforce.com/s/articleView?id=sf.flow_distribute_expose_community.htm&type=5"
  - "Flow Reference — Running User Context: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_running_user.htm&type=5"
  - "Experience Cloud Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_intro.htm"
rag-source:  Check Salesforce-RAG for Experience Cloud flow patterns
notes:       Built Experience Cloud Flow guidance for guest and authenticated user context, lightning-flow surfacing, LWR constraints, and a checker for hardcoded Flow URLs and unsafe site-exposed Apex.
```

### FLW-013 — DONE: orchestration-flows
```yaml
skill:       orchestration-flows
path:        skills/flow/orchestration-flows/
status:      DONE
agent:       Codex
started:     2026-03-13T20:05:00Z
completed:   2026-03-13
files:       6
priority:    P1
waf-pillars: Reliability, Scalability
official-docs:
  - "Flow Orchestration Overview: https://help.salesforce.com/s/articleView?id=sf.flow_orchestration_overview.htm&type=5"
  - "Orchestration Steps and Stages: https://help.salesforce.com/s/articleView?id=sf.flow_orchestration_steps.htm&type=5"
  - "Flow Reference: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5"
rag-source:  Check Salesforce-RAG for orchestration patterns
notes:       Built Flow Orchestration guidance for stage modeling, work-item ownership, child-flow boundaries, and a checker for placeholder stages, missing ownership cues, and weak operability signals.
```

### FLW-014
```yaml
skill:       flow-debugging-and-troubleshooting
path:        skills/flow/flow-debugging-and-troubleshooting/
status:      TODO
priority:    P0
waf-pillars: Reliability, Operational Excellence
official-docs:
  - "Flow Debugging: https://help.salesforce.com/s/articleView?id=sf.flow_test_debug.htm&type=5"
  - "Flow Reference: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5"
  - "Debug Log Reference: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging_debug_log.htm"
rag-source:  Check Salesforce-RAG for flow debugging patterns
notes:       How to trace flow failures in production. Debug log reading for Flow (FLOW_START_INTERVIEWS, FLOW_VALUE_ASSIGNMENT, FLOW_ELEMENT_ERROR). $Flow.FaultMessage usage and format. Flow fault email configuration. Debug interview reading in Flow Builder. How to reproduce intermittent flow failures. Bulk vs single-record debugging. When flow errors surface as generic "unhandled fault" vs specific messages. Common failure signatures and what they mean. This is the skill admins reach for when something breaks in production and they can't figure out why.
```

### FLW-015
```yaml
skill:       flow-versioning-and-deployment
path:        skills/flow/flow-versioning-and-deployment/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence, Reliability
official-docs:
  - "Flow Reference — Versioning: https://help.salesforce.com/s/articleView?id=sf.flow_distribute_version.htm&type=5"
  - "Flow Reference: https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5"
  - "Metadata API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm"
rag-source:  Check Salesforce-RAG for flow deployment patterns
notes:       Flow version management (active vs inactive, version numbering, what happens to running interviews when a new version activates). Deploying flows via change sets vs metadata API vs DevOps Center. How flow definitions move between sandboxes. Retirement strategy for old versions. When to create a new flow vs new version. Impact of deleting old versions on debug history. Common deployment failures (missing referenced fields, missing custom objects, process type mismatches).
```

---

## DOMAIN: AgentForce (additional skills)

### AGT-013
```yaml
skill:       model-builder-and-custom-llm
path:        skills/agentforce/model-builder-and-custom-llm/
status:      TODO
priority:    P2
waf-pillars: Security, Reliability
official-docs:
  - "Einstein Model Builder: https://developer.salesforce.com/docs/einstein/genai/guide/model-builder.html"
  - "Bring Your Own Large Language Model: https://developer.salesforce.com/docs/einstein/genai/guide/byollm.html"
  - "Einstein Trust Layer: https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm&type=5"
rag-source:  Check Salesforce-RAG for custom model patterns
notes:       When to use Einstein Foundation Models vs bring-your-own LLM (Azure OpenAI, custom). Model Builder configuration, supported model providers, Trust Layer enforcement for external models, audit logging for custom model calls. Mostly for enterprise customers with specific LLM requirements.
```

### AGT-014
```yaml
skill:       agent-deployment-and-monitoring
path:        skills/agentforce/agent-deployment-and-monitoring/
status:      TODO
priority:    P1
waf-pillars: Operational Excellence, Reliability
official-docs:
  - "Agentforce Developer Guide — Deployment: https://developer.salesforce.com/docs/einstein/genai/guide/agent-deployment.html"
  - "Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html"
  - "Einstein Trust Layer: https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm&type=5"
rag-source:  Check Salesforce-RAG for agent operations patterns
notes:       Deploying agents across sandboxes and production (what deploys, what doesn't), monitoring conversation logs, agent error rates, token usage tracking, rollback when an agent misbehaves, A/B testing agent configurations. Operational concern that gets ignored during initial builds.
```

---

## Agent Handoff Log

| Timestamp | Agent | Skill IDs | Description | Commit |
|-----------|-------|-----------|-------------|--------|
| 2026-03-15 | Codex | LWC-008..012, FLW-004..008 | lwc-accessibility, lwc-forms-and-validation, lwc-data-table, static-resources-in-lwc, lwc-modal-and-overlay, subflows-and-reusability, screen-flows, flow-governance, scheduled-flows, flow-testing | n/a - workspace is not a git repository |
| 2026-03-13 | Codex | ADM-001..015 | All 15 admin skills | feat(admin): complete all 15 admin skills |
| 2026-03-13 | Codex+Claude | APX-001..003 | soql-security, trigger-framework, governor-limits | feat(apex): complete 3 apex skills |
| 2026-03-13 | Codex | APX-004..008 | exception-handling, async-apex, test-class-standards, callouts-and-http-integrations, apex-security-patterns | n/a - workspace is not a git repository |
| 2026-03-13 | Codex | APX-009..018 | platform-events-apex, apex-design-patterns, debug-and-logging, batch-apex-patterns, apex-rest-services, apex-mocking-and-stubs, invocable-methods, platform-cache, apex-cpu-and-heap-optimization, recursive-trigger-prevention | n/a - workspace is not a git repository |
| 2026-03-13 | Codex | APX-019, INT-011..013, DAT-011..013, SEC-011..012, LWC-013 | custom-metadata-in-apex, graphql-api-patterns, salesforce-connect-external-objects, oauth-flows-and-connected-apps, roll-up-summary-alternatives, sosl-search-patterns, multi-currency-and-advanced-currency-management, permission-set-groups-and-muting, org-hardening-and-baseline-config, custom-property-editor-for-flow | n/a - workspace is not a git repository |
| 2026-03-13 | Codex | ADM-019, LWC-002, LWC-004, FLW-002..003, OMS-002, LWC-014, FLW-011..013 | permission-set-architecture, wire-service-patterns, lwc-security, flow-bulkification, record-triggered-flow-patterns, omniscript-design-patterns, lwc-offline-and-mobile, flow-custom-property-editors, flow-for-experience-cloud, orchestration-flows | n/a - workspace is not a git repository |
| 2026-03-13 | Codex | ADM-017, OMS-003, OMS-009, AGT-001..002 | process-automation-selection, dataraptor-patterns, omnistudio-security, agent-topic-design, agent-actions | n/a - workspace is not a git repository |
| 2026-03-13 | Codex | LWC-006 | lwc-performance | n/a - workspace is not a git repository |
| 2026-03-13 | Codex | ADM-016, ADM-018, LWC-003, LWC-005, LWC-007 | custom-metadata-types, list-views-and-compact-layouts, component-communication, lwc-testing, navigation-and-routing | n/a - workspace is not a git repository |
| 2026-03-13 | Codex+Claude | LWC-001 | lifecycle-hooks | feat(lwc): complete lifecycle-hooks |
| 2026-03-13 | Codex+Claude | FLW-001 | fault-handling | feat(flow): complete fault-handling |
| 2026-03-13 | Codex+Claude | OMS-001 | integration-procedures | feat(omnistudio): complete integration-procedures |

---

*Version: 0.5.0 | 157 skills planned | 77 complete | Last updated: 2026-03-15*
*Maintained by: Pranav Nagrecha*
