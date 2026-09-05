# Worked Example — One Salesforce Programme, End to End

One programme carried through every artefact this skill produces: the **stakeholder register**, the
**RACI matrix** (markdown for humans, YAML for `scripts/check_raci.py`), the **escalation path**, the
**decision log**, and the **R-to-executor map** that connects each Responsible cell to the repo agent
or skill that actually does the work.

**Programme:** Northwind Care, a Service Cloud rollout across two regions — Service EMEA (Frankfurt,
Madrid) and Service NA (Columbus). One production org, one inbound ERP feed writing Account and
Asset, one telephony integration, EMEA personal data in scope, an EMEA delegated administrator, and a
release train that has to survive two seasonal releases before go-live.

Copy the blocks below and replace the names. The YAML is the artefact of record; the markdown table is
the view you circulate for sponsor sign-off. Keep them in sync — the YAML is what gets linted.

---

## 1. Stakeholder register

The register is not a contact list. Each row carries what the platform needs to know about that
person: which org unit they answer to, which Salesforce persona they log in as, which user licence
that persona consumes, and what they are actually allowed to decide.

| Code | Role | Org unit | Salesforce persona | User licence | Decision rights |
|---|---|---|---|---|---|
| `BSP` | Executive sponsor | Global Service Ops | Dashboard consumer, no Setup access | Salesforce (`SFDC`) | Scope, budget, go-live gate, licence tier |
| `PO_EMEA` | Process owner — EMEA | Service EMEA | Service manager | Salesforce (`SFDC`) | EMEA case process, EMEA UAT sign-off |
| `PO_NA` | Process owner — NA | Service NA | Service manager | Salesforce (`SFDC`) | NA case process, NA UAT sign-off |
| `DS` | Data steward — customer master | Enterprise Data Office | Data steward, Data Loader user | Salesforce (`SFDC`) | Field semantics, picklist values, dedupe, retention, load approval |
| `SA` | Security architect | InfoSec | Setup-only administrator | Salesforce Platform (`AUL`) | OWD, role hierarchy, sharing rules, restriction rules, FLS |
| `IA` | Integration architect | Enterprise Architecture | Integration user owner | Salesforce (`SFDC`) | Integration pattern, contract, integration-user permissions |
| `AL` | CRM admin lead (global) | Global Service Ops | System Administrator | Salesforce (`SFDC`) | Declarative build, permission set composition, Setup hygiene |
| `AD_EMEA` | Delegated administrator — EMEA | Service EMEA | Delegated admin, `EMEA_Service_Admins` | Salesforce (`SFDC`) | EMEA user creation and permission set assignment **inside the delegate group only** |
| `RM` | Release manager | Platform Engineering | Deployment user | Salesforce (`SFDC`) | Promotion path, sandbox estate, hotfix authorisation |
| `CO` | Compliance officer / EMEA DPO | Legal & Compliance | Audit reader | Salesforce Platform (`AUL`) | Retention, audit trail, EMEA personal-data processing |
| `EU` | End-user representative | Service NA | Service agent | Salesforce (`SFDC`) | UAT execution, adoption feedback |

The licence codes in brackets are `UserLicense.LicenseDefinitionKey` values: `SFDC` corresponds to the
Full CRM user license and `AUL` to the Salesforce Platform user license
([Object Reference, `UserLicense`](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_userlicense.htm)).
Recording the key rather than the marketing name is what makes the register checkable in the org —
see the verification query in §7.

---

## 2. RACI matrix — the circulated view

Ten activity rows. Exactly one **A** per row; at least one **R** per row; **C** means input is required
before the decision, **I** means notification after it.

| # | Activity | BSP | PO_EMEA | PO_NA | DS | SA | IA | AL | AD_EMEA | RM | CO | EU |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ACT-01 | Data model change | I | C | C | **A** | C | C | R | I | I | C | I |
| ACT-02 | Sharing model change | I | C | C | C | **A** | C | R | I | I | C | I |
| ACT-03 | Permission set change | I | C | C | I | C | I | **A** | R | I | I | I |
| ACT-04 | Integration change | I | I | I | C | C | **A** | R | I | C | C | I |
| ACT-05 | Release go / no-go | **A** | C | C | C | C | C | R | I | R | C | C |
| ACT-06 | Sandbox refresh approval | I | C | C | **A** | C | C | C | I | R | C | I |
| ACT-07 | Production hotfix | I | C | C | I | C | I | R | I | **A** | I | I |
| ACT-08 | Data load approval | I | C | C | **A** | I | C | R | I | C | C | I |
| ACT-09 | Release Update activation | I | I | I | C | C | C | R | I | **A** | I | I |
| ACT-10 | Seasonal release preview | I | C | C | I | C | C | R | I | **A** | I | C |

Three assignments in that table are the ones people argue about, and each is deliberate:

- **ACT-06 sandbox refresh is A = data steward, not A = release manager.** The release manager runs
  the refresh; the steward is the one who loses data when it happens. See `gotchas.md` Gotcha 9.
- **ACT-08 data load approval is A = data steward, not A = CRM admin lead.** The admin owns the tool;
  the steward owns the records. See `gotchas.md` Gotcha 13.
- **ACT-09 Release Update activation is A = release manager, with an explicit row.** Left off the
  matrix entirely, Release Updates get activated by whoever notices the banner, or by Salesforce on
  the auto-enforcement date. See `gotchas.md` Gotcha 12.

---

## 3. RACI matrix — the linted artefact

Save as `raci.yaml` next to the project docs and run:

```bash
python3 skills/admin/stakeholder-raci-for-sf-projects/scripts/check_raci.py \
  --file docs/governance/raci.yaml --repo-root . --strict
```

```yaml
project: "Northwind Care — Service Cloud rollout (EMEA + NA)"
phase: build
version: "2.1.0"
sponsor_signoff: "2026-09-02"
next_review: "2026-11-14"

stakeholders:
  - code: BSP
    role: Executive sponsor
    named: "R. Adeyemi"
    org_unit: "Global Service Ops"
    sf_persona: "Dashboard consumer — no Setup access"
    license: "Salesforce (LicenseDefinitionKey SFDC)"
    decision_rights: "Scope, budget, go-live gate, licence tier"
  - code: PO_EMEA
    role: Process owner — EMEA
    named: "L. Brandt"
    org_unit: "Service EMEA (Frankfurt, Madrid)"
    sf_persona: "Service manager"
    license: "Salesforce (SFDC)"
    decision_rights: "EMEA case process, EMEA UAT sign-off"
  - code: PO_NA
    role: Process owner — NA
    named: "T. Okafor"
    org_unit: "Service NA (Columbus)"
    sf_persona: "Service manager"
    license: "Salesforce (SFDC)"
    decision_rights: "NA case process, NA UAT sign-off"
  - code: DS
    role: Data steward — customer master
    named: "M. Iqbal"
    org_unit: "Enterprise Data Office"
    sf_persona: "Data steward — Data Loader user"
    license: "Salesforce (SFDC)"
    decision_rights: "Object/field semantics, picklist values, dedupe, retention, load approval"
  - code: SA
    role: Security architect
    named: "P. Nowak"
    org_unit: "InfoSec"
    sf_persona: "Setup-only administrator"
    license: "Salesforce Platform (LicenseDefinitionKey AUL)"
    decision_rights: "OWD, role hierarchy, sharing rules, restriction rules, FLS"
  - code: IA
    role: Integration architect
    named: "S. Verhoeven"
    org_unit: "Enterprise Architecture"
    sf_persona: "Integration user owner"
    license: "Salesforce (SFDC)"
    decision_rights: "Integration pattern, contract, integration-user permissions"
  - code: AL
    role: CRM admin lead (global)
    named: "K. Duarte"
    org_unit: "Global Service Ops"
    sf_persona: "System Administrator"
    license: "Salesforce (SFDC)"
    decision_rights: "Declarative build, permission set composition, Setup hygiene"
  - code: AD_EMEA
    role: Delegated administrator — EMEA
    named: "J. Ferreira"
    org_unit: "Service EMEA"
    sf_persona: "Delegated admin (DelegateGroup EMEA_Service_Admins)"
    license: "Salesforce (SFDC)"
    decision_rights: "EMEA user creation and permission set assignment inside the delegate group only"
  - code: RM
    role: Release manager
    named: "A. Sokolova"
    org_unit: "Platform Engineering"
    sf_persona: "Deployment user"
    license: "Salesforce (SFDC)"
    decision_rights: "Promotion path, sandbox estate, hotfix authorisation"
  - code: CO
    role: Compliance officer / EMEA data protection
    named: "H. Lindqvist"
    org_unit: "Legal & Compliance"
    sf_persona: "Audit reader"
    license: "Salesforce Platform (AUL)"
    decision_rights: "Retention, audit trail, EMEA personal-data processing"
  - code: EU
    role: End-user representative
    named: "C. Mensah"
    org_unit: "Service NA"
    sf_persona: "Service agent"
    license: "Salesforce (SFDC)"
    decision_rights: "UAT execution, adoption feedback"

activities:
  - id: ACT-01
    activity: data-model-change
    label: "Add or change objects, fields, relationships, record types"
    cells:
      BSP: I
      PO_EMEA: C
      PO_NA: C
      DS: A
      SA: C
      IA: C
      AL: R
      AD_EMEA: I
      RM: I
      CO: C
      EU: I
    escalation:
      trigger: "DS and either process owner disagree, or the change alters a field the ERP feed writes"
      target: BSP
      time_box_business_days: 5
    executed_by:
      - agents/object-designer/AGENT.md
      - agents/field-impact-analyzer/AGENT.md
  - id: ACT-02
    activity: sharing-model-change
    label: "OWD, role hierarchy, sharing rules, restriction rules, FLS"
    cells:
      BSP: I
      PO_EMEA: C
      PO_NA: C
      DS: C
      SA: A
      IA: C
      AL: R
      AD_EMEA: I
      RM: I
      CO: C
      EU: I
    escalation:
      trigger: "Requested visibility would let NA agents read EMEA personal data"
      target: CO
      time_box_business_days: 3
    executed_by:
      - agents/access-path-explainer/AGENT.md
      - standards/decision-trees/sharing-selection.md
  - id: ACT-03
    activity: permission-set-change
    label: "Permission set / permission set group composition and assignment"
    cells:
      BSP: I
      PO_EMEA: C
      PO_NA: C
      DS: I
      SA: C
      IA: I
      AL: A
      AD_EMEA: R
      RM: I
      CO: I
      EU: I
    escalation:
      trigger: "Requested permission set carries Modify All Data, View All Data, or Manage Users"
      target: SA
      time_box_business_days: 2
    executed_by:
      - agents/permission-set-architect/AGENT.md
  - id: ACT-04
    activity: integration-change
    label: "Inbound ERP feed and outbound telephony events"
    cells:
      BSP: I
      PO_EMEA: I
      PO_NA: I
      DS: C
      SA: C
      IA: A
      AL: R
      AD_EMEA: I
      RM: C
      CO: C
      EU: I
    escalation:
      trigger: "Pattern change alters the contract with the ERP or needs a new licence entitlement"
      target: BSP
      time_box_business_days: 5
    executed_by:
      - agents/integration-catalog-builder/AGENT.md
      - standards/decision-trees/integration-pattern-selection.md
  - id: ACT-05
    activity: release-go-no-go
    label: "Go / no-go for a scheduled release into production"
    cells:
      BSP: A
      PO_EMEA: C
      PO_NA: C
      DS: C
      SA: C
      IA: C
      AL: R
      AD_EMEA: I
      RM: R
      CO: C
      EU: C
    escalation:
      trigger: "Any C votes no-go, or open P1 defects remain at the gate"
      target: "Steering committee"
      time_box_business_days: 1
    executed_by:
      - agents/release-readiness-reviewer/AGENT.md
  - id: ACT-06
    activity: sandbox-refresh-approval
    label: "Refresh of the Full sandbox used for UAT and load rehearsal"
    cells:
      BSP: I
      PO_EMEA: C
      PO_NA: C
      DS: A
      SA: C
      IA: C
      AL: C
      AD_EMEA: I
      RM: R
      CO: C
      EU: I
    escalation:
      trigger: "Unmerged work or unfinished UAT evidence exists in the sandbox at the requested refresh date"
      target: RM
      time_box_business_days: 3
    executed_by:
      - agents/sandbox-strategy-designer/AGENT.md
  - id: ACT-07
    activity: production-hotfix
    label: "Out-of-band change to production between scheduled releases"
    cells:
      BSP: I
      PO_EMEA: C
      PO_NA: C
      DS: I
      SA: C
      IA: I
      AL: R
      AD_EMEA: I
      RM: A
      CO: I
      EU: I
    escalation:
      trigger: "Hotfix touches sharing, an integration user, or a field the ERP feed writes"
      target: SA
      time_box_business_days: 1
    executed_by:
      - agents/deployment-risk-scorer/AGENT.md
      - agents/changeset-builder/AGENT.md
  - id: ACT-08
    activity: data-load-approval
    label: "Bulk insert, update, upsert, delete, or hard delete of customer records"
    cells:
      BSP: I
      PO_EMEA: C
      PO_NA: C
      DS: A
      SA: I
      IA: C
      AL: R
      AD_EMEA: I
      RM: C
      CO: C
      EU: I
    escalation:
      trigger: "Load is a hard delete, or exceeds the rehearsed row count by more than 20 percent"
      target: BSP
      time_box_business_days: 2
    executed_by:
      - agents/data-loader-pre-flight/AGENT.md
      - agents/data-migration-reconciler/AGENT.md
  - id: ACT-09
    activity: release-update-activation
    label: "Activating a Salesforce Release Update before its auto-enforcement release"
    cells:
      BSP: I
      PO_EMEA: I
      PO_NA: I
      DS: C
      SA: C
      IA: C
      AL: R
      AD_EMEA: I
      RM: A
      CO: I
      EU: I
    escalation:
      trigger: "Sandbox testing shows a regression, or the enforcement release is two releases away or nearer"
      target: BSP
      time_box_business_days: 10
    executed_by:
      - agents/change-impact-planner/AGENT.md
      - agents/org-health-assessor-v2/AGENT.md
  - id: ACT-10
    activity: seasonal-release-preview
    label: "Preview-window testing of the next seasonal release"
    cells:
      BSP: I
      PO_EMEA: C
      PO_NA: C
      DS: I
      SA: C
      IA: C
      AL: R
      AD_EMEA: I
      RM: A
      CO: I
      EU: C
    escalation:
      trigger: "Preview testing finds a break in a business-critical flow, integration, or report"
      target: BSP
      time_box_business_days: 5
    executed_by:
      - agents/release-train-planner/AGENT.md

escalation_path:
  - level: 1
    forum: "Weekly design authority (AL chairs)"
    chair: AL
    time_box_business_days: 3
    resolves: "Disagreement between an A and a C on a single activity row"
  - level: 2
    forum: "Fortnightly steering committee (BSP chairs)"
    chair: BSP
    time_box_business_days: 10
    resolves: "Cross-region conflict, licence spend, scope change"
  - level: 3
    forum: "CIO arbitration"
    chair: "CIO"
    time_box_business_days: 20
    resolves: "Steering committee deadlock, or a compliance veto the business contests"

refusal_code_map:
  REFUSAL_SECURITY_GUARD:
    row: ACT-02
    ping: SA
    loop: [CO]
  REFUSAL_DATA_QUALITY_UNSAFE:
    row: ACT-08
    ping: DS
    loop: [PO_EMEA, PO_NA]
  REFUSAL_MANAGED_PACKAGE:
    row: ACT-04
    ping: IA
    loop: [AL]
  REFUSAL_FEATURE_DISABLED:
    row: ACT-09
    ping: RM
    loop: [BSP]
  REFUSAL_FIELD_NOT_FOUND:
    row: ACT-01
    ping: DS
    loop: [AL]
  REFUSAL_NEEDS_HUMAN_REVIEW:
    row: "(named in the refusal message)"
    ping: "(the A on the matching row)"
    loop: ["(the C on that row)"]

decision_log:
  - id: DEC-014
    date: "2026-08-19"
    activity: ACT-02
    decision: "EMEA case records stay Private with a criteria-based sharing rule to the EMEA queue"
    decided_by: SA
    consulted: [CO, PO_EMEA]
    alternatives_rejected: "Public Read/Write with a restriction rule — rejected, EMEA personal data"
    reversal_cost: "High — re-parenting recalculates sharing across both regions"
    evidence: "standards/decision-trees/sharing-selection.md step 3"
```

**How to read the YAML:**

- `activity:` is a slug from the checker's required list, not free text — a missing slug is an error,
  because a required decision with no row is a decision with no owner. Two rows may share a slug when
  a category needs splitting (EMEA personal data vs. everything else, for instance); the checker only
  insists each slug appears at least once.
- `cells:` keys are stakeholder `code` values. A code that appears in a cell but not in the roster is
  a warning — usually a role that was renamed in one place only.
- `escalation:` is per row and is where the clock lives. `escalation_path:` is programme-level and is
  where the forums live. A matrix with one but not the other stalls: either you know who decides next
  but not when, or when but not who.
- `executed_by:` is the repo path of the agent or standard that carries out the row. The checker warns
  when a path does not resolve, which catches an agent that was renamed or retired under you.
- `decision_log:` entries record *why*, not just *what*. `reversal_cost` is the field people skip and
  the field that matters at the next steering committee.

---

## 4. Escalation path

| Level | Forum | Chair | Time-box | Resolves |
|---|---|---|---|---|
| 1 | Weekly design authority | `AL` | 3 business days | A and C disagree on one activity row |
| 2 | Fortnightly steering committee | `BSP` | 10 business days | Cross-region conflict, licence spend, scope change |
| 3 | CIO arbitration | CIO | 20 business days | Steering deadlock, or a contested compliance veto |

The per-row time-box in the YAML is the clock that promotes an item to level 1. The level time-box is
the clock that promotes it to the next level. Both are needed; a row time-box without a forum is a
complaint, and a forum without a row time-box is a meeting.

---

## 5. Who actually executes the R

Each Responsible cell resolves to something in this repo. Cite the path when you hand work over; the
checker's `executed_by` warning is what keeps this map honest as agents get renamed.

| Activity | R executes with | Read first |
|---|---|---|
| ACT-01 Data model change | `agents/object-designer/AGENT.md`, `agents/field-impact-analyzer/AGENT.md` | `skills/admin/requirements-gathering-for-sf/SKILL.md` |
| ACT-02 Sharing model change | `agents/access-path-explainer/AGENT.md` | `standards/decision-trees/sharing-selection.md` |
| ACT-03 Permission set change | `agents/permission-set-architect/AGENT.md` | `skills/admin/permission-set-architecture/SKILL.md`, `skills/admin/delegated-administration/SKILL.md` |
| ACT-04 Integration change | `agents/integration-catalog-builder/AGENT.md` | `standards/decision-trees/integration-pattern-selection.md` |
| ACT-05 Release go / no-go | `agents/release-readiness-reviewer/AGENT.md` | `skills/admin/change-management-and-deployment/SKILL.md` |
| ACT-06 Sandbox refresh approval | `agents/sandbox-strategy-designer/AGENT.md` | `skills/admin/sandbox-strategy/SKILL.md` |
| ACT-07 Production hotfix | `agents/deployment-risk-scorer/AGENT.md`, `agents/changeset-builder/AGENT.md` | `skills/devops/release-management/SKILL.md` |
| ACT-08 Data load approval | `agents/data-loader-pre-flight/AGENT.md`, `agents/data-migration-reconciler/AGENT.md` | `skills/admin/change-management-and-training/SKILL.md` for the comms that follow a load |
| ACT-09 Release Update activation | `agents/change-impact-planner/AGENT.md`, `agents/org-health-assessor-v2/AGENT.md` | `skills/devops/release-management/SKILL.md` |
| ACT-10 Seasonal release preview | `agents/release-train-planner/AGENT.md` | `skills/admin/sandbox-strategy/SKILL.md` |

Every one of those agents follows `agents/_shared/AGENT_CONTRACT.md`, which requires a Citations block
and a confidence score — that is what makes an agent's output attachable to a decision-log entry as
evidence rather than as an opinion.

---

## 6. Making the RACI concrete: the delegated-admin row deploys

`AD_EMEA` holding **R** on ACT-03 is not a statement of intent — it is a `DelegateGroup` in the org, and
it either matches the matrix or it does not. `DelegateGroup` components use the suffix
`.delegateGroup`, live in the `delegateGroups` folder, and the file prefix must match the group's
developer name; the type is available in API version 36.0 and later, and only users with the "View
Setup and Configuration" permission can be delegated administrators
([Metadata API Developer Guide, `DelegateGroup`](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)).

`delegateGroups/EMEA_Service_Admins.delegateGroup` (the folder and suffix the guide specifies; in a source-format project the same content sits under your package directory):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DelegateGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>EMEA Service Admins</label>
    <name>EMEA_Service_Admins</name>
    <loginAccess>false</loginAccess>
    <permissionSets>Service_Agent_EMEA</permissionSets>
    <permissionSets>Service_Manager_EMEA</permissionSets>
    <permissionSetGroups>Service_Agent_EMEA_PSG</permissionSetGroups>
    <roles>Service_EMEA_Manager</roles>
    <customObjects>Service_Region_Preference__c</customObjects>
</DelegateGroup>
```

**How to read it:**

- `<roles>` names the roles *and their subordinates* whose users this group may create and edit. It is
  the scope boundary that keeps `AD_EMEA` out of NA users.
- `<permissionSets>` / `<permissionSetGroups>` are the only permission sets this group may assign.
  Anything not listed stays with `AL`, who holds **A** on ACT-03 — the metadata and the matrix agree.
- `<profiles>` is deliberately absent. Granting profile assignment to a regional admin would hand them
  a lever the RACI never gave them; leave the element out rather than list a profile "temporarily".
- `<loginAccess>false</loginAccess>` denies login-as. Set to `true`, users in this group can log in as
  users in the role hierarchy they administer, subject to org settings that may require individual
  users to grant login access. That is an ACT-02 decision (`SA` is **A**), not an ACT-03 one — which is
  exactly the kind of cell that gets quietly flipped during a support push.
- Delegated administrators can customise nearly every aspect of the custom objects listed in
  `<customObjects>`, but they cannot create or modify relationships on them and cannot set org-wide
  sharing defaults. The platform will not let a delegated admin overrule `SA` on ACT-02 even if
  someone puts them in the wrong cell — one of the few places the matrix is enforced for you.

`manifest/package.xml` for the governance artefacts:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>EMEA_Service_Admins</members>
        <name>DelegateGroup</name>
    </types>
    <types>
        <members>RACI_Decision__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>RACI_Decision.DEC_014</members>
        <name>CustomMetadata</name>
    </types>
    <version>62.0</version>
</Package>
```

---

## 7. Optional: the decision log as deployable metadata

Teams that keep the decision log in a wiki lose it at the first re-org. Keeping it as custom metadata
puts it in source control, moves it between sandboxes with the rest of the release, and makes it
queryable from the org that the decisions describe. `CustomMetadata` components use the suffix `.md`,
live in the `customMetadata` folder, are available in API version 31.0 and later, and creating records
requires the "Customize Application" permission
([Metadata API Developer Guide, `CustomMetadata`](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)).

`objects/RACI_Decision__mdt.object` — the custom metadata *type* definition:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>RACI Decision</label>
    <pluralLabel>RACI Decisions</pluralLabel>
    <visibility>Public</visibility>
    <fields>
        <fullName>Activity_Id__c</fullName>
        <label>Activity Id</label>
        <length>20</length>
        <required>true</required>
        <type>Text</type>
        <unique>false</unique>
        <externalId>false</externalId>
    </fields>
    <fields>
        <fullName>Accountable_Code__c</fullName>
        <label>Accountable Code</label>
        <length>10</length>
        <required>true</required>
        <type>Text</type>
        <unique>false</unique>
        <externalId>false</externalId>
    </fields>
    <fields>
        <fullName>Decision_Date__c</fullName>
        <label>Decision Date</label>
        <required>true</required>
        <type>Date</type>
    </fields>
    <fields>
        <fullName>Decision__c</fullName>
        <label>Decision</label>
        <length>32000</length>
        <type>LongTextArea</type>
        <visibleLines>10</visibleLines>
    </fields>
    <fields>
        <fullName>Reversal_Cost__c</fullName>
        <label>Reversal Cost</label>
        <length>20</length>
        <required>false</required>
        <type>Text</type>
        <unique>false</unique>
        <externalId>false</externalId>
    </fields>
</CustomObject>
```

`customMetadata/RACI_Decision.DEC_014.md` — one *record* of that type:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>DEC-014 EMEA case sharing</label>
    <protected>false</protected>
    <values>
        <field>Activity_Id__c</field>
        <value xsi:type="xsd:string">ACT-02</value>
    </values>
    <values>
        <field>Accountable_Code__c</field>
        <value xsi:type="xsd:string">SA</value>
    </values>
    <values>
        <field>Decision_Date__c</field>
        <value xsi:type="xsd:date">2026-08-19</value>
    </values>
    <values>
        <field>Decision__c</field>
        <value xsi:type="xsd:string">EMEA case records stay Private with a criteria-based sharing rule to the EMEA queue.</value>
    </values>
    <values>
        <field>Reversal_Cost__c</field>
        <value xsi:type="xsd:string">High</value>
    </values>
</CustomMetadata>
```

**How to read it:**

- The record file name is the type name without `__mdt`, then the record's developer name:
  `RACI_Decision.DEC_014.md`, in the `customMetadata` folder. That naming rule is what the
  `package.xml` member `RACI_Decision.DEC_014` mirrors. The type itself is a `CustomObject` named
  `RACI_Decision__mdt.object` in the `objects` folder — two metadata types, one concept.
- `xsi:type` on `<value>` must match the field's type: `xsd:string` for Text and LongTextArea,
  `xsd:date` for Date, `xsd:int` for a Number with scale 0.
- Leaving a `<values>` block out is not the same as setting it null: an omitted field keeps its
  previous value on an update and is null on a first deploy. Use `<value xsi:nil="true"/>` when you
  mean "cleared".
- `<protected>false</protected>` keeps the records readable outside a managed package. Protected
  records are unavailable to REST, SOAP, SOQL, and Setup for subscribers — the opposite of what a
  decision log is for.

**Deploy and verify:**

```bash
# retrieve what production already has, so you diff rather than overwrite
sf project retrieve start --manifest manifest/package.xml --target-org prod

# validate-only against production before the real deploy
sf project deploy validate --manifest manifest/package.xml --target-org prod

# deploy to the UAT sandbox first
sf project deploy start --manifest manifest/package.xml --target-org uat
```

Verification after deploy — three checks, one per artefact:

```sql
-- 1. the register's licence column matches the org (UserLicense fields are API v32.0+;
--    UsedLicenses is not filterable in a WHERE clause from API v64.0, so filter client-side)
SELECT MasterLabel, LicenseDefinitionKey, TotalLicenses, UsedLicenses
FROM UserLicense
ORDER BY MasterLabel

-- 2. the decision log arrived
SELECT DeveloperName, Activity_Id__c, Accountable_Code__c, Decision_Date__c, Reversal_Cost__c
FROM RACI_Decision__mdt
ORDER BY Decision_Date__c DESC
```

3. For the delegate group, check Setup → Delegated Administration → *EMEA Service Admins* and confirm
   the roles, permission sets, and login-access flag match the matrix — then re-retrieve the component
   and diff it against the file above. A drift here means someone changed decision rights in Setup
   without changing the RACI, which is the failure mode `gotchas.md` Gotcha 14 describes.
