# Release delta: Winter '27 (264, API 68.0) vs Summer '26 (262, API 67.0)

Cites: `file:Lnn` = `grep -n` line in the **264** file unless prefixed `262:`. Files: apexdev=salesforce_apex_developer_guide, meta=api_meta, obj=object_reference, rest=api_rest, bulk=api_asynch, pe=platform_events, stream=api_streaming, dx=sfdx_dev, pkg2=pkg2_dev, ldv=salesforce_large_data_volumes_bp, dl=salesforce_data_loader, lim=salesforce_app_limits_cheatsheet. Slug cells = `skills/*/*/SKILL.md` matching the key regex in the last table; none = no SKILL.md names it.

## 0. Header

| Item | 262 (Summer '26) | 264 (Winter '27) |
|---|---|---|
| API version | 67.0 | 68.0 (meta:L2, obj:L3, apexdev:L2) |
| Guide stamp | Last updated Aug 7 (apexdev) / Aug 21 (meta, obj), 2026 | Last updated Oct 16, 2026 (apexdev, meta, obj) |
| Corpus dir | `scratchpad/corpus/` | `scratchpad/corpus264/` |
| Release preview windows | n/a | dx:L10539 Winter '27 Aug 30 - Oct 10, 2026; dx:L10541 Spring '27 Jan 10 - Feb 20, 2027; Summer '27 May 9 - Jun 12, 2027; same table pkg2:L21170-21174 |

- **At 264 (12 files, each stamped Version 68.0 / Winter '27):** api_meta, object_reference, salesforce_apex_developer_guide, api_rest, api_asynch, api_streaming, platform_events, sfdx_dev, pkg2_dev, salesforce_data_loader, salesforce_large_data_volumes_bp (ldv:L3 says Winter '27, Last updated Sep 18, 2026), salesforce_app_limits_cheatsheet (no version stamp; lim:L43 Last updated Sep 11, 2026 vs 262:L46 Aug 7, 2026).
- **NOT at 264 yet:** `salesforce_apex_reference_guide` and `salesforce_security_impl_guide` stay at 262 (HTTP 404 at resources.docs.salesforce.com/264/latest/en-us/sfdc/pdf/<name>.pdf, 200 at /262/, checked 2026-10-19). Cite them as `262:` and do not assert 68.0 behaviour from them.

## 1. Apex Developer Guide: Versioned Behavior Changes, API 68.0 (apexdev:L45118-45129)

5 entries. Section header apexdev:L45096-45107; `Version 68.0` apexdev:L45118. Each row: old vs new, domains, SKILL.md slugs.

| # | Change (264 line) | Old (<=67.0) vs new (>=68.0) | Domain | Skills naming it |
|---|---|---|---|---|
| 1 | Test Discovery API results (apexdev:L45119-45120) | `showAllMethods` parameter -> `testLevel` replaces it; `showAllMethods` works only at 67.0 and earlier | apex testing, CI | `apex/tooling-api-patterns`, `flow/flow-invocable-from-apex`, `lwc/lwc-local-development` |
| 2 | Recompile only invalid classes/triggers (apexdev:L45121-45123) | whole-org recompile only -> compilation results for classes/triggers with validation errors via Setup or Tooling `apexCompileResults` | apex, devops deploy | `devops/deployment-error-diagnosis`, `devops/deployment-error-troubleshooting` |
| 3 | Compiler warnings for Apex saved at API 9.0-19.0 (apexdev:L45124-45125) | no warning -> compiler warns on compile/deploy; such classes/triggers "will be retired in a future release" | devops, api-version hygiene | `admin/api-contract-documentation`, `architect/technical-debt-assessment`, `devops/api-version-management`, `integration/rest-api-patterns` (judgment: no SKILL.md names 9.0-19.0 specifically; these cover API-version retirement) |
| 4 | `DebugLevel` metadata type (apexdev:L45126-45127; meta:L13259-13269) | none -> type holding log category levels assigned to a `TraceFlag` | apex debug, flow debug | `apex/debug-logs-and-developer-console`, `apex/tooling-api-patterns`, `flow/flow-debugging` |
| 5 | Symbol Table API, Tooling REST, beta (apexdev:L45128-45129) | none -> metadata for built-in/custom/dynamic Apex types (classes, interfaces, methods, triggers) | apex tooling | `apex/tooling-api-patterns` |
| 6 | **Unchanged**: 67.0 entries (apexdev:L45132-45146) | user-mode default, `with sharing` default, `WITH SECURITY_ENFORCED` removed: text identical to 262:L44493-44502; 65.0/63.0/62.0 entries also unchanged | security, apex | still valid: `apex/apex-security-patterns`, `apex/apex-stripinaccessible-and-fls-enforcement`, `apex/apex-with-without-sharing-decision`, `devops/code-review-checklist-salesforce`, `lwc/lwc-security`, `devops/api-version-management` |

### 1b. Apex Developer Guide changes outside the versioned list

| # | Change (264 line) | 262 vs 264 | Skills naming it |
|---|---|---|---|
| a | **Heap limit** (apexdev:L19780; footnote apexdev:L19854) | 262:L19577 `6 MB` sync / `12 MB` async -> `10 MB` sync / `25 MB` async; footnote adds uncatchable `System.LimitException` and heap/CPU coupling. Opt-out: `ApexSettings.enableEnforceSummer26ApexHeapLimit` pins nonproduction orgs to the lower Summer '26 limits, Winter '27 only; Spring '27 enforces the higher limits globally (meta:L113858-113862) | 36 skills state a 6/12 MB figure (full list below table) |
| b | **Elastic async Apex limits (beta)** (apexdev:L20211-20243, table apexdev:L19937-19953) | scope Queueable+future (262:L20020) -> Batch+Queueable+future, scheduled stays capped (apexdev:L20222); extra elastic capacity cap `10 million` -> `2 million` (262:L19750,L20025,L20034 -> apexdev:L19953,L20227,L20235); batch throttled to one active job (apexdev:L20243); production only, nonproduction override via `ApexSettings.asyncApexExecutionsOverride` (apexdev:L20266-20281; meta:L113751) | elastic: `architect/org-limits-monitoring`; 24-hour async limit prose: `apex/apex-batch-chaining`, `apex/async-apex`, `apex/batch-apex-patterns`, `architect/limits-and-scalability-planning`, `architect/omnistudio-scalability-patterns`, `architect/org-limits-monitoring` (+9; K-asyncdaily) |
| c | Apex cursors (apexdev:L19965, L20691-20704, L20762) | row renamed "Apex cursors per day" (262:L19753) -> "Apex cursor instances per 24-hour period", value 10,000 unchanged; new "Best Practices for Apex Cursors" (reuse one cursor across a Queueable chain; `getCursor()` in `execute()` exhausts `DailyApexCursorLimit`); new "Use Apex Cursors with Data 360 DMOs (Beta)" (consumes Data Services credits) | `apex/apex-limits-monitoring`, `apex/async-apex`, `apex/governor-limits` |
| d | Apex Integration Tests, Developer Preview, scratch orgs (apexdev:L5060, L5086, L5107, L42653) | `@BeforeClass` new (0 hits in 262); section renamed from "...for Agentforce and Data 360 Services"; still not GA | `flow/flow-invocable-from-apex` |
| e | `Database.QueryOptions` `explicitNamespace` + SOQL `SET OPTIONS` (apexdev:L43721-43760) | 0 hits in 262 -> managed-package namespace shadowing fix for dynamic SOQL | none; closest (judgment): `devops/managed-package-development`, `devops/second-generation-managed-packages` |
| f | Guide samples switched to user mode (`insert as user`, `WITH USER_MODE`; e.g. apexdev:L9549, L9598, L20515) | documentation examples only, not a behaviour change | any skill quoting the guide's samples |

Skills stating a 6 MB / 12 MB heap figure (re-ground to 10/25 MB, apexdev:L19780; heap key): `admin/email-service-inbound`, `admin/flow-for-admins`, `agentforce/mcp-tool-definition-apex`, `apex/apex-blob-and-content-version`, `apex/apex-collections-patterns`, `apex/apex-cpu-and-heap-optimization`, `apex/apex-email-services`, `apex/apex-json-serialization`, `apex/apex-limits-monitoring`, `apex/apex-queueable-patterns`, `apex/apex-rest-services`, `apex/apex-scheduled-jobs`, `apex/callouts-and-http-integrations`, `apex/change-data-capture-apex`, `apex/custom-iterators-and-iterables`, `apex/dynamic-apex`, `apex/governor-limit-recovery-patterns`, `apex/governor-limits`, `apex/long-running-process-orchestration`, `architect/limits-and-scalability-planning`, `architect/nfr-definition-for-salesforce`, `architect/omnistudio-scalability-patterns`, `architect/sales-cloud-architecture`, `data/attachment-to-files-migration`, `data/soql-query-optimization`, `flow/flow-bulkification`, `flow/flow-get-records-optimization`, `flow/flow-governor-limits-deep-dive`, `flow/flow-large-data-volume-patterns`, `flow/flow-loop-element-patterns`, `flow/flow-platform-events-integration`, `flow/flow-transaction-finalizer-patterns`, `integration/dataweave-for-apex`, `lwc/file-upload-patterns`, `omnistudio/dataraptor-transform-optimization`, `omnistudio/integration-procedure-cacheable-patterns`

## 2. Metadata API (meta) delta

Method: TOC (dot-leader) entries of `Chapter 13: Metadata Types` diffed 262 vs 264 (meta:L203-874 vs 262:L130-772), then body `available in API version` lines.

### 2a. New metadata types (14)

| Type | Min API | 264 TOC | 264 body | Skills naming it |
|---|---|---|---|---|
| `AiAgentDefinition` | 68.0 | meta:L262 | meta:L17518, L17544 | none (files `aiAgents/*.aiAgentDefinition` meta:L17540; versions `MyAgent#1` meta:L17535); related surface GenAiPlannerBundle/AiAuthoringBundle: `agentforce/agent-channel-deployment`, `agentforce/agent-deployment-checklist`, `agentforce/agent-script-dsl`, `agentforce/agent-topic-design` (+3; K-agentrel) |
| `AiAgentDefinitionVersion` | 68.0 | meta:L263 | meta:L17822, L17851 | none; related surface GenAiPlannerBundle/AiAuthoringBundle: `agentforce/agent-channel-deployment`, `agentforce/agent-deployment-checklist`, `agentforce/agent-script-dsl`, `agentforce/agent-topic-design` (+3; K-agentrel) |
| `AppFrameworkApp` | 68.0 | meta:L277 | meta:L23378, L23401 | none |
| `DataMaskPolicy` | 61.0 (Data Mask & Seed needs 68.0, meta:L51650) | meta:L399 | meta:L51618, L51658 | none |
| `DataMaskSettings` | 67.0 | meta:L400 | meta:L51855, L51884 | none |
| `DebugLevel` | 68.0 | meta:L234 | meta:L13259, L13269 | `apex/debug-logs-and-developer-console`, `apex/tooling-api-patterns`, `flow/flow-debugging` |
| `HelpSettings` | 68.0 | meta:L723 | meta:L121264, L121280 | none |
| `MarketingObject` | 68.0 | meta:L377 | meta:L46746, L46756 | none |
| `MCETransformationsSettings` | 68.0 | meta:L748 | meta:L125275, L125287 | none |
| `MktPlanningOpsSettings` | 68.0 | meta:L746 | meta:L125128, L125150 | none |
| `ScndTelephPrvdOtbdDtl` | 68.0 | meta:L641 | meta:L109673, L109684 | none |
| `SecondaryTelephonyProvider` | 68.0 | meta:L645 | meta:L110284, L110295 | none |
| `TelephonyProvider` | 68.0 | meta:L833 | meta:L136588, L136605 | none |
| `TrustedTelephonyProvider` | 68.0 | meta:L844 | meta:L140504, L140515 | none |

### 2b. Removed / folded / retired (meta)

| Item | 262 | 264 | Skills |
|---|---|---|---|
| `DashboardTranslation`, `DashboardComponentTranslation`, `ReportTranslation` as standalone types | 262:L309-310, L535 (TOC), 67.0 pages L48930-49100, L105661 | no TOC entry, no sample page; folded into `Translations` (meta:L139248-139251, L139314, L139639-139655, L140199) | `admin/multi-language-and-translation`, `lwc/lwc-internationalization` |
| `AnalyticsVisualization` field `positional` | present | "REMOVED in v68.0" meta:L22449 | none |
| `AnalyticsSettings.incrementalUpsertEnabled` | 66.0 | "Removed in API version 68.0" meta:L113620 | none |
| `LightningExperienceSettings.enableAuraSecStaticResCRUCPref` | present | removed at 68.0, release update cancelled (meta:L124706-124707) | none |
| Salesforce API versions 31.0-40.0 | 262:L1188 "31.0 through 66.0 Supported" | meta:L1289-1295 "Versions 31.0 through 40.0 Supported. Deprecated and unsupported from Summer '27. Retired from Summer '28."; 41.0-68.0 supported; 21.0-30.0 retired Summer '25 unchanged (same table rest:L1232-1238, bulk:L4274-4280, L9228-9234) | `admin/api-contract-documentation`, `architect/technical-debt-assessment`, `devops/api-version-management`, `integration/rest-api-patterns` |

### 2c. Minimum-version statements that changed

| Type | 262 | 264 | Skills |
|---|---|---|---|
| `DuplicateRule` | 262:L55842 "66.0 and later" | meta:L58362 "68.0 and later" (doc statement; verify in an org before changing a deploy claim) | `admin/data-import-and-management`, `admin/duplicate-management`, `apex/apex-record-clone-patterns`, `data/data-quality-and-governance`, `data/duplicate-rule-person-account-edge-cases` (+2; K-dupe) |
| `CleanDataService` | 262:L33374 66.0 | meta:L35533 68.0 | none |
| `AffinityScoreDefinition` | 262:L16333 66.0 | meta:L17293 68.0 | none |
| `AppointmentSchedulingPolicy` | 53.0 | meta:L24958 47.0 | none |
| `SharingReason` | custom objects 14.0+ | standard objects now supported at 68.0 (meta:L47651) | `admin/compliant-data-sharing-setup`, `admin/data-skew-and-sharing-performance`, `admin/enterprise-territory-management`, `admin/experience-cloud-guest-access`, `admin/multi-language-and-translation` (+11; K-sharingreason) |

### 2d. Fields and values marked API 68.0 (grep `68.0` in meta, 163 raw hits minus version stamps/samples)

| Type | # | Added (68.0) | 264 lines | Skills naming the type |
|---|---|---|---|---|
| `ActionableListDefinition` | 8 | `actionableListType`, `isActive`, `description`, column fields `sourceObjectName`, `sourceObjectFieldName`, `isSourceObjectField`, `sourceColumnApiName`, `actionableListDefinition` | meta:L16372-16620 | none |
| `BatchCalcJobDefinition` | 19 | `activities`, `apiVersion`, `definitionType`, `steps`, `activityName`, `processNodes`, `processNodeReferenceRecord`, `shouldExcludeParentValue`, `label`/`name` children; values `PennyPerfectPricing` L27561, `PublicSector` L27569 | meta:L27402-28501 | none |
| `BillingSettings` | 1 | `enableBillingForecast` | meta:L29534 | none |
| `Bot` | 2 | channel type values `GoogleChat`, `Slack` | meta:L29950, L29960 | `agentforce/agent-channel-deployment`, `agentforce/agent-deployment-checklist`, `agentforce/agent-script-dsl`, `agentforce/agentforce-agent-creation`, `agentforce/agentforce-persona-design` (+2; K-bot) |
| `MessagingChannel` | 1 | message type value `RerouteResponse` | meta:L90454 | `admin/messaging-and-chat-setup` |
| `ConversationMessageDefinition` | 5 | values `GuidedActions`, `VideoId` (x2), `BusinessUpdate`, `Suggestions` | meta:L39633-40230 | none |
| `FlexiPage / QuickAction (Beta)` | 5 | FlexiPage type `QuickAction`; QuickAction `actionSubtype` `Create`, `flexiPage` field, type `Flexipage` | meta:L69605, L102811-102951 | none |
| `Flow` | 18 | `runInMode` value `UserMode` (user context, no inherited sharing); `FlowNodeGroup` + `groups`/`group`; `FlowDataLookup` + `dataLookups`; 12 `actionType` values (`getNrbyScvTerritories`, `groupClaimsByFields`, `processAccessDelegationRequest`, `recalculateHouseholdNames`, `b2cGetShippingMethods`, `b2cSetShippingAddress`, `b2cSetShippingMethod`, `b2cInitiatePayment`, `b2cPreProcessPayment`, `b2cPostProcessPayment`, `bulkEnqueuePostingsToGenLeads`, `invocableCallContentSearch`) | meta:L70665 (groups), L70907-70927 (runInMode), L71312-71632, L72122-72128 (actionType), L72803, L75043 (dataLookups), L73449-73465 (group) | `admin/campaign-planning-and-attribution`, `admin/flow-for-admins`, `flow/flow-cross-object-updates`, `flow/flow-debugging`, `flow/flow-dynamic-choices` (+4; K-runinmode) |
| `RecommendationStrategy` | 12 | mirror of the 12 Flow `actionType` values | meta:L103427-104719 | `agentforce/einstein-next-best-action` |
| `Network` | 1 | `networkOptionsBit` (unverified-domain sender: site `emailSenderAddress` vs org-wide substitute address vs suppressed) | meta:L93715 | `admin/email-deliverability-strategy` |
| `Report` | 1 | `crossFilters` (ReportCrossFilter[]) | meta:L106682 | `admin/report-type-strategy`, `admin/reports-and-dashboards-fundamentals`, `admin/reports-and-dashboards` |
| `Translations` | 3 | `reportAggregates`, `reportBucketFields`, `reportCharts` | meta:L139306-139312 | `admin/multi-language-and-translation`, `lwc/lwc-internationalization` |
| `AnalyticsSettings` | 45 | `enableAiSentimentInDcr`, `enableCdpBetaConnectors`, `enableCrossCloudCsi`, `enableEasySetupAI`, `enableHeadlessBrowser`, `enableLightningDashboard`, `enableLightningReportLWR`, `enableOrgHierarchyInDcr`, `enableReportRecordPreview`, `enableReportTypeSearch`, `enableSemanticAuthoringAI`, ~34 `enableTableau*` flags | meta:L112987-113534 | none |
| `ApexSettings` | 2 | `asyncApexExecutionsOverride`, `enableEnforceSummer26ApexHeapLimit` | meta:L113751, L113862 | `admin/salesforce-release-preparation`, `devops/metadata-api-coverage-gaps` |
| `CurrencySettings` | 3 | `corporateCurrency`, `currency[]`, `enableMultiCurrency`: deploying `true` now turns multi-currency on in an org that lacks it (cannot be turned off later, dx:L9495) | meta:L116861-116950, dx:L9495 | `data/multi-currency-and-advanced-currency-management` |
| `FlowSettings` | 1 | `enableFlowsLightningApp` (Automation Lightning app) | meta:L120080 | `admin/flow-for-admins`, `admin/salesforce-release-preparation`, `flow/flow-formula-and-expression-patterns` |
| `IndustriesSettings` | 5 | `enableStoreCheck`, `enableLifeSciRecTypeRoutgPref`, `enableLSDraftOrderCapture`, `enableLSVisitAgent`, `noninterchangeable` | meta:L123134-123154 | `admin/care-coordination-requirements`, `admin/clinical-data-requirements`, `admin/compliant-data-sharing-setup`, `admin/health-cloud-consent-management`, `apex/fsc-compliant-sharing-api` (+3; K-industries) |
| `LanguageSettings` | 1 | `displayedLanguages` | meta:L124216 | `admin/multi-language-and-translation`, `admin/org-setup-and-configuration` |
| `SecuritySettings` | 1 | `enableGraphQLApiGuestUserAccess` (default false) | meta:L129423 | none |
| `SharingSettings` | 1 | `enableKeepManualSharesOnTransfer` | meta:L130599 | `admin/object-creation-and-design`, `admin/sharing-rules`, `security/apex-managed-sharing-patterns`, `security/record-access-troubleshooting` |
| `UserInterfaceSettings` | 2 | `listViewIleBypassLayout`, `listViewIleMultiRecordType` (LEX list-view inline edit) | meta:L131880, L131885 | none |
| `SharedTo` | 1 | `allRestrictedEmployeeUsers` (Unified Employee license group) | meta:L132603 | `integration/slack-salesforce-integration-setup` |
| `CodeCoverageResult` | 1 | `locationsCovered` (CodeLocation[], line/column hit counts in deploy/test results) | meta:L8011-8014 | `devops/post-deployment-validation` |
| **Total** | **139** | | | |

Also tagged 68.0 but not field additions: `DataMaskPolicy` needs API 68.0 (meta:L51650) and locale-specific masking data needs 68.0 (meta:L51831); `AddressSettings` Greenland sample (meta:L112531). `GenAiPlannerBundle`/`Bot` guidance unchanged. Metadata API Context MCP Tool (beta) chapter exists in both (meta:L3831).

## 3. Object Reference (obj) delta

Method: TOC diff (obj 264 TOC vs 262 TOC, 1818 vs 1799 entries) plus `grep -n 68.0` (74 hits, 73 after dropping one curl sample).

### 3a. New objects at API 68.0 (14)

| Object | 264 line | Skills naming it |
|---|---|---|
| `AgentQltyEvalFormCondition` | obj:L24551 | none |
| `AgentQltyEvalFormCriteria` | obj:L24642 | none |
| `ApprovalDelegation` | obj:L35878 | `admin/approval-process-apex-patterns` |
| `CampaignExt` | obj:L57692 | none |
| `ComplianceControlScope` | obj:L70500 | none |
| `CustomReportType` | obj:L88842 | none |
| `DocProcReview` | obj:L101573 | none |
| `MarketingGoal` | obj:L180976 | none |
| `MarketingProgram` | obj:L181479 | none |
| `MarketingTactic` | obj:L181825 | none |
| `MarketingTacticTemplate` | obj:L182036 | none |
| `Pricebook2History` | obj:L225044 | none |
| `Review` | obj:L253199 | none |
| `ReviewExecution` | obj:L253399 | none |

### 3b. Newly documented at older API versions, flagged, removed

| Item | Detail | 264 line | Skills |
|---|---|---|---|
| `GraphQlQueryEventLog` | documented as "available in API version **69.0** and later" inside the 68.0 guide: pre-release, do not cite as 68.0 | obj:L8628-8630 | none |
| `DataSemanticSearch`, `MsgChannelAvailability`, `VoiceCallSessionData` | in 264 TOC, absent from 262 TOC; min API 67.0 | obj:L7766, L9258, L11729 | none |
| `GenOpPlanReferenceRecord` (65.0), `ProductConsumedState` (57.0), `SerializedProductTransaction` (57.0) | newly in 264 TOC; older min API | obj:L8607, L10091, L10660 | none |
| `CalculationMatrix`, `CalculationMatrixColumn`, `CalculationMatrixRow`, `CalculationMatrixVersion` (Decision Matrix, 53.0) | 262:L7310-7327 and TOC 262:L325-328 -> no index or page in 264 (4 residual mentions) | absent | `omnistudio/calculation-procedure-design`, `omnistudio/calculation-procedures` |
| `StandardInvocableActionType` | 262:L11284 "60.0 and later" -> "API versions 60.0 to 68.0" (retired after 68.0) | obj:L11020, L276704 | none |
| Intro section "Define and Deploy Custom Big Objects" | 262:L34, L3589 | removed from 264 (obj:L3605-3607 keeps only a Big Objects Implementation Guide pointer) | `admin/data-export-service`, `admin/fit-gap-analysis-against-org`, `admin/hipaa-workflow-design` (+31; K-bigobj) |

### 3c. Fields marked 68.0 on existing objects

| Object | Fields / values | 264 lines | Skills |
|---|---|---|---|
| `ArchivePolicyDefinition` (65.0) | 14 fields (`ArchivePolicyRelObjSelection`, `ContentDocumentObject`, `FilterConditions`, `IsAnalyzed`, `IsArchiveRelatedFiles`, `IsBoostEnabled`, `IsLogFailuresAndContinue`, `NamespacePrefix`, `PreviewFields`, `RelatedObjects`, `RetentionMonths`, `RetentionSource`, `RetentionYears`, `Schedule*`); at 68.0 API writes do not affect policy execution, pre-68.0 policies show incomplete values | obj:L38449-38746 | none |
| `AgentWorkConversationalData`, `VoiceCall` | `AverageJitter`, `AveragePacketLoss`, `MaximumJitter`, `MaximumPacketLoss` (Salesforce Voice Native Telephony only) | obj:L25510-25569; L309673-310181 | `admin/service-cloud-voice-setup`, `architect/multi-channel-service-architecture`, `data/omni-channel-reporting-data` |
| `AssetActionSource`, `AssetStatePeriod` | `BillingTerm`; `ApplUnitPriceUpliftPct`, `RampUpliftType` | obj:L40180, L41669, L41831 | `admin/contract-and-renewal-management`, `architect/revenue-cloud-architecture` |
| `FlowTestResult` | `Error`, `FailedAssertions` | obj:L145245, L145253 | none |
| `GenOpPlanReferenceRecord` | `DisplayName`, `Url` | obj:L154083, L154138 | none |
| `MessagingSessionMetrics` | `MessagingSessionMetricType` value `ServiceRepAcceptToFirstResponseTime` | obj:L184625 | none |
| `Network` | `OptionsEmailDomainSubstitutionEnabled` | obj:L189193 | `admin/email-deliverability-strategy` |
| `Organization` | `PreferencesPublicSectorTaxRevEnabled` | obj:L207930 | none |
| `Refund` | `ReasonCode`, `ReferenceRecordId` | obj:L247878, L247886 | `admin/commerce-order-management`, `admin/custom-permissions`, `admin/permission-set-architecture`, `agentforce/agent-topic-design` (+2; K-refund) |
| `WebCart` | `TotalProductItemAdjTaxAmount`; null for carts created before Winter '27 | obj:L314277-314278 | `admin/commerce-checkout-configuration`, `admin/commerce-checkout-flow-design`, `architect/b2b-vs-b2c-architecture`, `data/commerce-analytics-data` |

Object-reference deprecations/removals flagged "removed/deprecated" that are new in 264: none beyond 3b (the other `deprecated`/`removed` strings, e.g. obj:L59879 CartDeliveryGroup 64.0/66.0, exist in 262).

## 4. Other guides

| Guide | `68.0` / `Winter` grep in 264 | Change vs 262 | Skills |
|---|---|---|---|
| api_rest | 15 hits, all samples + version table (rest:L1232) | API 31.0-40.0 deprecation/retirement rows (rest:L1234-1238); "View Relevant Items" renamed "Get Relevant Items" (rest:L78, L3775); 300 TOC entries both sides, no new resources | none; `integration/api-governance-and-rate-limits` |
| api_asynch (Bulk API 2.0) | 22 hits, samples + version table (bulk:L4274, L9228) | only the 31.0-40.0 rows (bulk:L4276-4280, L9230-9234); TOC identical (84/84); one sample still shows `v67.0` (bulk:L775) | `admin/acceptance-criteria-given-when-then`, `admin/api-contract-documentation`, `admin/data-export-service`, `admin/data-import-and-management` (+70; K-bulk) |
| platform_events | 12 hits | 3 new standard events at 68.0: `AgentQltyEvalEvent` (pe:L7656, L8107), `ObjectMilestoneCreatedDtlEvent` (pe:L7873, L13559), `ObjectMilestoneCreatedEvent` (pe:L7884, L13599); `AsyncThirdPartyPaymentGatewayEvent` newly documented at 64.0 (pe:L7733, L9654); allocation tables numerically identical (262:L6878 vs pe:L6878; section split "Platform Event Definition Allocation" / "Concurrent CometD Client Allocation"); per-event pages gained Fields/Usage subsections (PDF outline 240 -> 411) | none |
| api_streaming | 8 hits | from API 68.0 the server also emits an updated replay ID per channel on every successful `/meta/connect` (`ext.replay[<channel>]`) (stream:L434-436); version table 37.0-68.0 (stream:L823); TOC unchanged (65/65) | `admin/approval-process-apex-patterns`, `admin/change-data-capture-admin`, `apex/apex-event-bus-subscriber`, `apex/error-handling-framework`, `apex/platform-events-apex`, `architect/embedded-analytics-architecture` (+20; K-replay) |
| sfdx_dev | 1 (dx:L9495) + 2 Winter (dx:L10539, L16113) | new "Salesforce AI Skill for Dev Hub" (dx:L939; `dx-org-devhub-configure`) and "Salesforce AI Skills for Scratch Orgs" (dx:L3806; `dx-org-analyze`...) sourced from `forcedotcom/sf-skills`; `CurrencySettings` scratch-def example (dx:L9495); Winter '27 preview dates (dx:L10539) | `admin/change-advisory-board-process`, `admin/change-management-and-training`, `admin/salesforce-release-preparation`, `devops/automated-regression-testing`, `devops/environment-strategy` (+4; K-scratchpreview) |
| pkg2_dev | 0 + 2 Winter (pkg2:L21170, L21172) | "AppExchange" mentions 63 -> 3 and "AgentExchange" 106 -> 156; new "Editable Properties After Package Promotion or Installation" (pkg2:L16858); new "Sample Post Install Script for a Push Upgrade" (pkg2:L19890); "Publishing Your App on AgentExchange" (pkg2:L19776); removed "Set Up a Platform Cache Partition with Provider Free Capacity" (262:L13903, L17394) | `admin/managed-package-installation-and-upgrade`, `devops/managed-package-development`, `devops/release-notes-automation`, `devops/second-generation-managed-packages`, `devops/unlocked-package-development`; cache: `apex/ai-model-integration-apex`, `integration/platform-events-integration`, `omnistudio/omnistudio-cache-strategies` |
| salesforce_large_data_volumes_bp | stamp only (ldv:L3) | no content change (sentence diff: 1 changed line, the stamp) | `architect/large-data-volume-architecture` |
| salesforce_data_loader | 0 | no content change (sentence diff = reflow and dropped `on page N` refs; process-conf parameters, batch sizes (dl:L1467 max 2,000; recommended 50-100 dl:L1756) unchanged) | `data/data-loader-picklist-validation-pre-load` |
| salesforce_app_limits_cheatsheet | 0 | Apex tables (per-transaction, certified-package, static, size-specific, push) removed from the cheatsheet: lim:L21-29 now only points to "Execution Governors and Limits" (apexdev:L19711); file 814 lines vs 1,259; Platform Event / CDC / Pub-Sub allocation sub-sections collapsed into one pointer list (lim:L802-808); all remaining numeric tables identical | see 4b |

### 4b. Limits cheatsheet and Apex limits: every number that moved

Method: numeric-token multiset of the retained cheatsheet sections 262 (from L469) vs 264 (from L31) = no change except `150 MB` mention count (layout); Apex rows compared 262 apexdev:L19508-20480 vs 264 apexdev:L19711-20720.

| Limit | 262 | 264 | 264 line |
|---|---|---|---|
| Total heap size, synchronous | 6 MB (262:L19577; lim 262:L89) | **10 MB** | apexdev:L19780 |
| Total heap size, asynchronous | 12 MB | **25 MB** | apexdev:L19780 |
| Elastic async capacity cap (extra executions above licensed) | 10 million | **2 million** (worked example: 12 million + 10 million = 22 million -> 12 million + 2 million = 14 million) | apexdev:L19953, L20227, L20233-20235 |
| Elastic scope | Queueable + future only | + Batch Apex | apexdev:L19937-19944, L20222 |
| Cursor limit row | "Apex cursors per day" 10,000 | "Apex cursor instances per 24-hour period" 10,000 (value unchanged) | apexdev:L19965 |
| Every other cheatsheet and Apex governor number (SOQL 100/200, DML 150, rows 50,000, CPU 10,000/60,000 ms, callouts 100, 120 s, cursors 50 million rows, API 15,000/100,000+ allocations, 25/5 concurrent, 10 min timeout, Bulk API limits, Metadata limits) | | unchanged | lim:L48-L814; apexdev:L19732-20000 |

Numbers moved: 3 limits (heap sync, heap async, elastic cap) plus 2 scope/label changes.

## 5. Contradiction scan: 60 skills whose SKILL.md changed since 2026-10-19

Set: `git log --after="2026-10-18 23:59" --name-only -- skills | grep SKILL.md | cut -d/ -f2-3 | sort -u` = 60 skills (the brief assumed 40; `git log --since=2026-10-19` returns 0 because every commit is dated 2026-10-19 local). Scanned SKILL.md and all references/templates/scripts under each. A row is a claim now changed or incomplete at 264.

| Skill | Claim (file:line in skill) | 264 evidence | Type |
|---|---|---|---|
| `data/soql-query-optimization` | "6 MB synchronous or 12 MB asynchronous heap" SKILL.md:187; references/llm-anti-patterns.md:54; references/well-architected.md:36 cites cheatsheet L89 | apexdev:L19780 = 10 MB / 25 MB; cheatsheet no longer holds the row (lim:L21-29) | CONTRADICTED |
| `flow/flow-bulkification` | "Heap size 6 MB / 12 MB" SKILL.md:100; "6 MB synchronous heap" SKILL.md:335 | apexdev:L19780 | CONTRADICTED |
| `flow/flow-governance` | `runInMode` allow-list built on "SystemModeWithoutSharing" (`api_meta.txt` L68382) SKILL.md:76, :220; references/gotchas.md:108-110 | meta:L70907-70927 adds value `UserMode` (68.0); line cites are 262 numbering | INCOMPLETE |
| `flow/flow-testing` | `runInMode` DefaultMode explanation (L68374-68380) SKILL.md:68; references/llm-anti-patterns.md:176 | meta:L70907-70927 | INCOMPLETE |
| `flow/subflows-and-reusability` | "`runInMode` is declared per flow" cites L68374-68390 SKILL.md:71, :110; references/gotchas.md:161 | meta:L70907-70927 (`UserMode` explicitly enforces the user's context without inheriting sharing) | INCOMPLETE |
| `flow/record-triggered-flow-patterns` | "The alternatives are `SystemModeWithSharing` and `SystemModeWithoutSharing`" references/metadata-examples.md:167-172 | meta:L70927 third alternative `UserMode` | CONTRADICTED |
| `devops/api-version-management` | anchors end "Summer '26 = 67.0" SKILL.md:52; "two distinct waves" table SKILL.md:85-100; "minimum safe version (currently 31.0)" SKILL.md:137, :162, :188, :201 | meta:L1289-1295: 31.0-40.0 deprecated and unsupported from Summer '27, retired from Summer '28; Winter '27 = 68.0 | CONTRADICTED |
| `devops/devops-center-pipeline` (also `devops/devops-center-advanced`, outside the 60) | "next-generation DevOps Center" vocabulary | meta:L117302-117337 renamed "Lifecycle Center" (0 -> 5 mentions; 262 "next-generation DevOps Center" 4 -> 0); `enableDevopsCenterMigrationPref` still developer preview | RENAMED |
| `data/batch-data-cleanup-patterns` | "10,000 DML rows per transaction (L66)" references/well-architected.md:31 | cheatsheet row removed; now apexdev:L19759 | STALE CITE |
| `flow/subflows-and-reusability` | per-transaction budget "cheatsheet L53-65", "L69" references/gotchas.md:20, :214 | rows now apexdev:L19747-19780 | STALE CITE |
| `data/bulk-api-patterns`, `data/data-model-design-patterns`, `data/sosl-search-result-limits`, `integration/api-governance-and-rate-limits` | cheatsheet line cites (e.g. L729-740, L1131-1134, L469-495) in references/well-architected.md | values unchanged; lines moved (Batch Allocations lim:L300, Metadata Limits lim:L577, API Request Limits lim:L31-190) | STALE CITE |
| `integration/api-governance-and-rate-limits` | table "Value (Summer '26 cheat sheet)" SKILL.md:67 | all values identical at 264 | OK (label only) |
| `integration/graphql-api-patterns` | guest access "v67.0 in one place and v68.0 in another" references/gotchas.md:83 | meta:L129423 `SecuritySettings.enableGraphQLApiGuestUserAccess` (68.0, default false) | EXTEND |
| `data/cdc-data-sync-patterns` | replay ID management SKILL.md:55-57 | stream:L434-436 per-channel replay ID on each `/meta/connect` from 68.0 | EXTEND |
| `agentforce/agent-script-dsl` | agent metadata surface "Vocabulary as of Summer '26", GenAiPlannerBundle SKILL.md:50, :128-136 | meta:L17518-17544, L17822-17851 `AiAgentDefinition` / `AiAgentDefinitionVersion` (68.0, `aiAgents/`) | EXTEND |
| `apex/apex-security-patterns`, `apex/apex-stripinaccessible-and-fls-enforcement`, `apex/apex-with-without-sharing-decision`, `devops/code-review-checklist-salesforce`, `lwc/lwc-security` | every 67.0 gate (user-mode default, `with sharing` default, `WITH SECURITY_ENFORCED` removed) | apexdev:L45132-45146 identical to 262:L44493-44502 | OK (no change) |
| 33 of the 60 skills | 338 line cites `api_meta.txt Lnnn` (286), `object_reference.txt` (36), apexdev (9), cheatsheet (4), rest (2), ldv (1) | all are 262 numbering; re-resolve with `grep -n` on the 264 file before reuse | STALE CITE |
| `devops/sfdx-monorepo-patterns`, `data/bulk-api-patterns`, `data/custom-index-requests`, `data/soql-query-optimization` | `sourceApiVersion` / `/services/data/v67.0/` literals | 264 samples use v68.0 (rest:L1488) | COSMETIC |

Counts: 8 skills with a changed or incomplete claim (4 CONTRADICTED rows, 3 INCOMPLETE, 1 RENAMED row; +1 outside the 60), 7 skills with stale cheatsheet cites, 33 skills with 262-numbered cites, 3 EXTEND; the 67.0 gates in 5 skills are confirmed unchanged.

## 6. Slug search keys (reproduce with `grep -rlE -i '<regex>' skills/*/*/SKILL.md`)

| Key | Regex | SKILL.md hits |
|---|---|---|
| K-affinity | `AffinityScoreDefinition` | 0 |
| K-agentmeta | `AiAgentDefinition` | 0 |
| K-agentqlty | `AgentQltyEval` | 0 |
| K-agentrel | `GenAiPlannerBundle\|AiAuthoringBundle` | 7 |
| K-analyticsset | `AnalyticsSettings\|enableTableau\|incrementalUpsert` | 0 |
| K-apexsettings | `ApexSettings\|enableEnforceSummer26ApexHeapLimit\|asyncApexExecutionsOverride` | 2 |
| K-apiretire | `API (version )?retirement\|retired API\|31\.0 through 40\.0\|End-of-Life Policy\|API End-of-Life` (i) | 4 |
| K-appfw | `AppFrameworkApp` | 0 |
| K-approvaldeleg | `ApprovalDelegation\|approval delegation\|delegated approver` (i) | 1 |
| K-archive | `ArchivePolicyDefinition\|archive polic` (i) | 0 |
| K-asset | `AssetStatePeriod\|AssetActionSource` | 2 |
| K-asyncdaily | `250,000\|rolling 24-hour[^\n]{0,30}async\|DailyAsyncApexExecutions\|AsyncApexExecutions` (i) | 15 |
| K-batchcalc | `BatchCalcJobDefinition` | 0 |
| K-bigobj | `Define and Deploy Custom Big Objects\|big object` (i) | 34 |
| K-billing | `BillingSettings\|enableBillingForecast\|billing forecast` (i) | 0 |
| K-bot | `BotVersion\|<Bot\b\|\.bot-meta\|bots/` | 7 |
| K-bulk | `Bulk API 2\.0` | 74 |
| K-calcmatrix | `CalculationMatrix` | 2 |
| K-ccr | `CodeCoverageResult\|locationsCovered` | 1 |
| K-cleandata | `CleanDataService\|cleanDataServices` | 0 |
| K-compile | `apexCompileResults\|compile results\|invalid[^\n]{0,40}recompil\|needs recompilation` (i) | 2 |
| K-conversation | `ConversationMessageDefinition` | 0 |
| K-crossfilter | `crossFilters\|cross filter` (i) | 3 |
| K-currency | `CurrencySettings\|enableMultiCurrency\|corporateCurrency` | 1 |
| K-cursor | `Database\.getCursor\|Database\.Cursor\|getPaginationCursor\|DailyApexCursor\|Apex cursor` (i) | 3 |
| K-custreporttype | `CustomReportType` | 0 |
| K-datamask | `Data Mask (&\|and) Seed\|DataMaskPolicy\|DataMaskSettings` | 0 |
| K-debug | `DebugLevel\|TraceFlag` | 3 |
| K-dupe | `DuplicateRule\|duplicateRules/` | 7 |
| K-elastic | `elastic (limit\|async\|executions)\|DailyAsyncApexElastic\|asyncApexExecutionsOverride` (i) | 1 |
| K-emaildom | `OptionsEmailDomainSubstitution\|networkOptionsBit\|unverified (email )?domain\|domain substitution` (i) | 1 |
| K-flowsettings | `enableFlowsLightningApp\|FlowSettings\|Automation Lightning app` | 3 |
| K-flowtestres | `FlowTestResult\|FailedAssertions` | 0 |
| K-graphqlguest | `enableGraphQLApiGuestUserAccess\|GraphQL[^\n]{0,60}guest\|guest[^\n]{0,60}GraphQL` (i) | 0 |
| K-graphqllog | `GraphQlQueryEventLog` | 0 |
| K-helpsettings | `HelpSettings` | 0 |
| K-ile | `listViewIle\|UserInterfaceSettings` | 0 |
| K-industries | `IndustriesSettings\|enableLifeSciRecTypeRoutgPref\|enableLSDraftOrderCapture` | 8 |
| K-integtest | `@IntegrationTest\|@BeforeClass\|@TearDown\|Apex Integration Test` (i) | 1 |
| K-lang | `LanguageSettings\|displayedLanguages\|enableLocaleInsensitive` | 2 |
| K-manualshare | `enableKeepManualSharesOnTransfer\|keep manual shares\|manual shares?[^\n]{0,60}(transfer\|owner)\|(transfer\|owner)[^\n]{0,60}manual shares?` (i) | 4 |
| K-marketingh | `MarketingProgram\|MarketingTactic\|MarketingGoal\|CampaignExt\|ComplianceControlScope` | 0 |
| K-marketingobj | `MarketingObject` | 0 |
| K-messaging | `MessagingChannel\|RerouteResponse` | 1 |
| K-mkt | `MktPlanningOpsSettings\|MCETransformationsSettings` | 0 |
| K-msgmetrics | `MessagingSessionMetrics\|ServiceRepFirstResponseTime` | 0 |
| K-orgpref | `PreferencesPublicSectorTaxRevEnabled\|Public Sector Tax` | 0 |
| K-pe | `ObjectMilestoneCreated\|AgentQltyEvalEvent\|AsyncThirdPartyPaymentGatewayEvent` | 0 |
| K-pkgcache | `Platform Cache Partition\|Provider Free Capacity` (i) | 3 |
| K-pkgpromo | `Editable Properties After\|push upgrade` (i) | 5 |
| K-pricebookhist | `Pricebook2History` | 0 |
| K-queryopts | `Database\.QueryOptions\|explicitNamespace\|namespace shadowing` (i) | 0 |
| K-quickaction | `actionSubtype\|Quick Action Page\|QuickAction[^\n]{0,40}FlexiPage\|FlexiPage[^\n]{0,40}QuickAction` (i) | 0 |
| K-recoact | `RecommendationStrategy` | 1 |
| K-refund | `\bRefund\b` | 6 |
| K-relevant | `Relevant Items` | 0 |
| K-replay | `replay ?Id` (i) | 26 |
| K-review | `ReviewExecution\|DocProcReview` | 0 |
| K-runinmode | `runInMode\|SystemModeWithoutSharing\|SystemModeWithSharing\|DefaultMode` | 9 |
| K-scratchpreview | `preview scratch\|Preview Start Date\|sandbox preview\|release preview` (i) | 9 |
| K-sharedto | `allRestrictedEmployeeUsers\|Unified Employee` | 1 |
| K-sharingreason | `SharingReason\|sharing reason\|rowCause` (i) | 16 |
| K-stdinvocable | `StandardInvocableActionType` | 0 |
| K-symbols | `SymbolTable\|Symbol Table\|symbols? resource` (i) | 1 |
| K-telephony | `TelephonyProvider\|SecondaryTelephonyProvider\|ScndTelephPrvdOtbdDtl` | 0 |
| K-testlevel | `showAllMethods\|Test Discovery\|tests/discover\|runTestsAsynchronous` (i) | 3 |
| K-translation | `ReportTranslation\|DashboardTranslation\|DashboardComponentTranslation\|<translations>\|Translations? metadata` (i) | 2 |
| K-voicecall | `AgentWorkConversationalData\|\bVoiceCall\b` | 3 |
| K-webcart | `WebCart` | 4 |
| heap | line contains `heap` and `6 MB`/`12 MB` (or `6 MB ... 12 MB`) | 36 |

## 7. How writers use this

Cite 264 lines (`grep -n` on `corpus264/`) for every API 68.0 fact; mark behaviour that exists only at API 68.0 with `salesforce-version: "Winter '27+"` in frontmatter and state the gate inline ("at API 68.0 and later"); keep 262 cites, prefixed `262:`, for `salesforce_apex_reference_guide` and `salesforce_security_impl_guide` until they appear at 264; before asserting any version gate, limit, or retirement date, check the matching row here, and when 262 and 264 disagree (heap, elastic cap, API 31.0-40.0 retirement, `UserMode`, Lifecycle Center), the 264 value wins for 68.0 and the 262 value is correct only for classes and orgs pinned to 67.0 or earlier.
