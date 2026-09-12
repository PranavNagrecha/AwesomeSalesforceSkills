# Well-Architected Notes — Case Management Setup

## Relevant Pillars

- **Operational Excellence** — Case management setup directly determines how efficiently a support team can triage, route, and resolve customer issues. Misconfigured escalation rules, missing auto-response rules, or broken thread handling create manual work, missed SLAs, and degraded customer experience. Operational Excellence requires that every case reach the correct owner via the correct channel, with appropriate notifications, without human intervention.
- **Reliability** — Email-to-Case and Web-to-Case are customer-facing inbound channels. Silent failure modes (truncated email bodies, dropped Web-to-Case submissions at the 50,000 limit, orphaned cases from deleted queues) are reliability risks that are invisible until a customer escalates. Reliability requires monitoring these limits and testing failure paths explicitly.
- **Security** — Web-to-Case forms are publicly accessible. Without validation, they are an open vector for spam, garbage data, and potential injection of malicious content into the case body. Case team access grants record visibility independent of org sharing — this access channel must be managed deliberately.

## Architectural Tradeoffs

**Escalation rules vs. Flow/Apex for time-based re-routing:** Native escalation rules are declarative and zero-code but have a one-hour engine cadence and support only one active rule. Flow or Apex time-based actions can achieve sub-hour precision and more complex logic but require development and maintenance overhead. For SLA requirements where 30-minute precision matters, native escalation rules are insufficient.

**Web-to-Case vs. API-based form submission:** The built-in Web-to-Case endpoint is simple but has a 50,000 pending-request hard limit and no native validation. An Experience Cloud site or a custom form that POSTs directly to the REST API (creating cases via the sObject API) bypasses the Web-to-Case queue, allows server-side validation, and scales without the pending-request constraint. For high-volume scenarios (product launches, public forms), API-based submission is architecturally superior.

**Entitlements via automation vs. manual application:** Entitlement templates on products require Classic. In Lightning, automation (Flow triggered on case creation) is necessary to apply entitlements at scale. Relying on agents to manually attach entitlements introduces SLA gaps — cases without entitlements have no milestone tracking.

## Anti-Patterns

1. **Configuring auto-response rules without verifying the assignment rule layer** — Auto-response rules have no independent trigger. Treating them as standalone causes repeated misconfiguration, because every "why isn't the auto-response firing" investigation must start at the assignment rule layer. Design documentation and team onboarding should explicitly call out this dependency.

2. **Escalation rule maintenance in production without reactivation impact analysis** — Deactivating an escalation rule for any maintenance reason, then reactivating it, can generate a bulk escalation wave for all open cases that aged past threshold during the inactive period. Performing this operation in production without sandbox testing first is an operational risk that has caused unintended manager notifications and case re-assignments at scale.

3. **Relying on Web-to-Case without monitoring the pending request count** — The 50,000 limit is a silent drop ceiling. Orgs that add public-facing forms (support pages, product registration, warranty claims) without establishing operational monitoring for this counter eventually experience submission loss during traffic spikes. This is a reliability gap, not just a configuration detail.

## Official Sources Used

- Salesforce Help: Set Up Email-to-Case — https://help.salesforce.com/s/articleView?id=sf.setting_up_email_to_case.htm
- Salesforce Help: Email-to-Case Limits — https://help.salesforce.com/s/articleView?id=sf.cases_email_limitations.htm
- Salesforce Help: Set Up Web-to-Case — https://help.salesforce.com/s/articleView?id=sf.setting_up_web-to-case.htm
- Salesforce Help: Web Request Limits — https://help.salesforce.com/s/articleView?id=sf.admin_web_limits.htm&type=5 — over the 24-hour limit, requests enter a pending queue shared by Web-to-Case and Web-to-Lead capped at 50,000 combined; "additional requests are rejected and not queued, and your administrator receives email notifications for the first five rejected submissions"; Support can raise the pending limit
- SOQL and SOSL Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl.htm — SOSL is a text-search language with no create/update/delete capability; record creation from an external form requires the REST or SOAP API
- Salesforce Help: Assignment Rule Limits — https://help.salesforce.com/s/articleView?id=sf.creating_assignment_rules.htm
- Salesforce Help: Auto-Response Rules — https://help.salesforce.com/s/articleView?id=sf.creating_auto-response_rules.htm
- Salesforce Help: Escalation Rules — https://help.salesforce.com/s/articleView?id=sf.creating_escalation_rules.htm
- Salesforce Help: Set Up Entitlements and Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_setup.htm
- Salesforce Help: Case Teams Overview — https://help.salesforce.com/s/articleView?id=sf.caseteam_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide, `CaseSettings` / `WebToCaseSettings` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (api_meta L111632–112230; supplies every field in `references/metadata-examples.md` §3, the three-field shape of `WebToCaseSettings` at L112128, the `defaultCaseOwner` fallback definition, the `keepRecordTypeOnAssignmentRule` "manually created records" scope behind gotchas #8 and #9, and the `useSystemUserAsDefaultCaseUser` entry at L111880 whose documented requirement runs in one direction only — "If `false`, then you must specify a value for the `defaultCaseUser` field" — against `systemUserEmail` at L111871, which carries no Required marker; that asymmetry is the grounding for the UNVERIFIED marker in gotcha #12)
- Metadata API Developer Guide, `StandardValueSet` and `StandardValue` — same PDF (L130740 and L47532; supplies the `CaseOrigin`/`CasePriority`/`CaseStatus` XML in §1, the `sorted` and `isActive` semantics, and the record-type-visibility note behind gotcha #7)
- Metadata API Developer Guide, `BusinessProcess` and `RecordType` — same PDF (L42955 and L44968; supplies the bare-vs-object-qualified `businessProcess` naming rule, the "required … for lead, opportunity, solution, and case" constraint, and `compactLayoutAssignment` at both object and record-type scope in §2)
- Metadata API Developer Guide, StandardValueSet Names and Standard Picklist Fields — same PDF (L141974–141982; the `CaseOrigin` → `Case.Origin`, `CasePriority` → `Case.Priority`, `CaseStatus` → `Case.Status` mapping that names the files in §1)
- Object Reference, `Case` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (L62202 ff.; `Origin`, `Priority`, `Status`, `OwnerId` polymorphism, and `IsClosed` "controlled by the Status field; it can't be set directly" behind gotcha #10 and the §6 verification queries)
- Object Reference, `CaseStatus` — same PDF (L64145 ff.; the queryable `ApiName` / `IsClosed` / `IsDefault` / `SortOrder` shape used as the authoritative closed-status read in §6, and "Multiple case status values can represent a closed Case")
- Live org validation (dry-run `sf project deploy validate`, `checkOnly`, API 67.0, 2026-09-12) — the source for gotcha #12 and checker rule `CMS-SYSUSER-01`: `<useSystemUserAsDefaultCaseUser>true</useSystemUserAsDefaultCaseUser>` with no `<systemUserEmail>` is rejected with "CaseSettings: Enter the system user's email address." Org behaviour is not an official source; it is recorded here as the evidence for a claim the guide does not make, and the claim stays marked UNVERIFIED until the guide carries it
- Salesforce App Limits Cheat Sheet — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf (checked and found to contain **no** Web-to-Case or Web-to-Lead row; this is why the 5,000/day and 50,000-pending figures are marked UNVERIFIED in `references/metadata-examples.md` §4 rather than restated as grounded)
