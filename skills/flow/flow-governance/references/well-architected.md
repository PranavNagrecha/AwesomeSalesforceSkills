# Well-Architected Notes - Flow Governance

## Relevant Pillars

### Operational Excellence

Governance is operational excellence applied to declarative automation. Names, owners, descriptions, and lifecycle rules make the flow estate operable under change.

The platform's own division of labour makes the point: `FlowDefinitionView` and `FlowVersionView` exist as query-only objects with no builder behind them (`object_reference.txt` L139267, L144970). They are there so that the portfolio can be inspected as data. A governance standard that cannot be expressed as a query over those objects is a standard nobody will check twice.

### Security

Three `FlowSettings` booleans are access-control decisions that live under a Process Automation heading rather than a Security one: `doesFormulaEnforceDataAccess`, `enableFlowViaRestUsesUserCtxt`, and `isFlowBlockAccessToSessionIDEnabled` (`api_meta.txt` L116855, L116968, L117035). `runInMode` is a fourth, per flow (L68374). Governance is where they get reviewed together, because no single flow's design review sees more than one of them.

## Architectural Tradeoffs

- **Fast local changes vs portfolio consistency:** local speed feels good until the automation inventory becomes unreadable.
- **Many versions retained vs active retirement:** keeping everything feels safer, but ambiguity has a real operational cost — and a version with paused interviews cannot be deleted at all (`api_meta.txt` L68041), so "retire later" can become "cannot retire".
- **Flexible naming vs enforced naming:** free-form names reduce friction initially, but they weaken incident response and maintenance later.
- **`activation_control: flow_status` vs `flow_definition`:** driving `<status>` from the Flow matches the guide's post-44.0 recommendation and keeps the diff honest; `FlowDefinition` gives you an explicit, versioned "which number is live" artifact at the cost of silently overriding every `<status>` in the deploy (L73929–73932). Pick one and say so in the policy file. Carrying both is the only genuinely wrong answer.
- **`enableFlowDeployAsActiveEnabled` on vs off in production:** on makes deploy-and-activate one reviewable event and puts Apex tests in the path; off makes every production activation a manual Setup click that no pipeline records.

## Anti-Patterns

1. **`Copy of ...` in production** - the portfolio signals implementation history instead of business purpose.
2. **Activation with no owner or rollback note** - support and release teams lose operational clarity.
3. **Descriptions treated as optional** - future maintainers have no concise operational context, and `FlowDefinitionView.Description` is the only field the inventory query can read.
4. **A governance standard that lives only in a wiki** - it cannot fail a build, so it degrades at exactly the rate the team is busy. The policy file plus `scripts/check_flow_governance.py` is the same standard in a form that blocks a merge.
5. **Auditing only the flows in your repo** - managed-package flows run in the same save context and are unreachable through Metadata API unless they are templates (`api_meta.txt` L68035). A tie-detection pass that ignores them measures the wrong portfolio.

## Official Sources Used

- Metadata API Developer Guide — `FlowSettings` fields and the `Flow.settings` sample definition, `api_meta.txt` L116817–117096 (supports the §1 settings switchboard, the `enableFlowDeployAsActiveEnabled` / `enableFlowFieldFilterEnabled` / `enableFlowInterviewSharingEnabled` gotchas, and the deprecated-fields gotcha). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `Flow`: limitations, `apiVersion`, `status`, `runInMode`, `triggerOrder`, `interviewLabel`, `isAdditionalPermissionRequiredToRun`, and the API 44.0 upgrade checklist, `api_meta.txt` L68020–68450 and L73178–73206 (supports the version-drift, no-`<status>`, paused-interview, spaces-in-file-name and Process Builder gotchas, and every checker rule). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `FlowDefinition` (`activeVersionNumber`, `masterLabel`, the override rule) and `FlowTest`, `api_meta.txt` L73919–74400 (supports §3 activation control and the `require_flow_test_for_active` policy gate). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `PermissionSet`, `PermissionSetFlowAccess` and `PermissionSetApexClassAccess`, `api_meta.txt` L94750–95233 (supports the §2 permission-set artifact and the flow-plus-Apex-class half-grant it prevents). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference — `FlowDefinitionView`, `FlowVersionView`, `FlowInterview` and `FlowRecordRelation`, `object_reference.txt` L139267–140050, L143526–143570, L144970–145296 (supports every inventory query in §5, the `FlowVersionView` filter requirement, and the interview-sharing and retirement-blocker gotchas). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Apex Developer Guide — Triggers and Order of Execution, `apexdev.txt` L15402–15478 (supports the claim that steps 3 and 14 do not rank flows within themselves, which is what makes `triggerOrder` a governance requirement rather than a preference). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (supports the Operational Excellence and Security pillar framing above).
