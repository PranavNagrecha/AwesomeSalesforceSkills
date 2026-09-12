# Metadata Examples — Case Management Setup

The intake layer this skill owns is not one metadata type. It is **four files that must land in
order**: the standard picklist value sets that `Case.Origin`, `Case.Priority` and `Case.Status`
draw from, the `Case` object definition that carries the support processes and record types, the
`CaseSettings` file that turns Web-to-Case on and names the fallback owner, and the rule files that
the sibling skills own.

| What | Metadata type | File path | Since | Owned by |
|---|---|---|---|---|
| `Case.Origin` / `Priority` / `Status` values | `StandardValueSet` | `standardValueSets/CaseOrigin.standardValueSet-meta.xml` (etc.) | API 38.0 | **this skill** |
| Support processes (Status subsets) | `BusinessProcess` inside `CustomObject` | `objects/Case/Case.object-meta.xml` | API 17.0 | this skill (intake shape) / `admin/record-types-and-page-layouts` (record-type + layout mechanics) |
| Case record types + compact layout assignment | `RecordType` inside `CustomObject` | same file | API 12.0 / 29.0 | same split |
| Web-to-Case switch, origin, default owner, notification behaviour | `CaseSettings` → `webToCase` (`WebToCaseSettings`) + org-level fields | `settings/Case.settings-meta.xml` | API 27.0 | **this skill** |
| Email-to-Case switches + routing addresses | `CaseSettings` → `emailToCase` | same file | API 27.0 | `admin/email-to-case-configuration` → `references/metadata-examples.md` |
| Assignment / auto-response / escalation rules | `AssignmentRules`, `AutoResponseRules`, `EscalationRules` | `assignmentRules/Case.assignmentRules-meta.xml` etc. | — | `admin/assignment-rules`, `admin/escalation-rules` |

Every element name, type and enum value below comes from the *Metadata API Developer Guide*:
`CaseSettings` (api_meta L111632–112230; `WebToCaseSettings` L112128; sample definition L112160),
`StandardValueSet` (L130740), `StandardValue` (L47532), `BusinessProcess` (L42955),
`RecordType` (L44968), `CustomObject` field table (L41930–42240, sample L43130), and the
StandardValueSet-name table (L141974 `CaseOrigin`, L141976 `CasePriority`, L141982 `CaseStatus`).
Object behaviour comes from the *Object Reference*: `Case` (L62202 ff.), `CaseStatus` (L64145).
PDFs: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf and
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

---

## 1. `standardValueSets/*.standardValueSet-meta.xml` — the values the form and the rules depend on

The Metadata API guide's table of "StandardValueSet Names and Standard Picklist Fields" maps
`CaseOrigin` → `Case.Origin`, `CasePriority` → `Case.Priority`, `CaseStatus` → `Case.Status`
(api_meta L141974–141982). The `fullName` of the file is that enum name, not the field name.

`standardValueSets/CaseOrigin.standardValueSet-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Email</fullName>
        <default>false</default>
        <label>Email</label>
    </standardValue>
    <standardValue>
        <fullName>Web</fullName>
        <default>true</default>
        <label>Web</label>
    </standardValue>
    <standardValue>
        <fullName>Phone</fullName>
        <default>false</default>
        <label>Phone</label>
    </standardValue>
    <standardValue>
        <fullName>Billing</fullName>
        <default>false</default>
        <label>Billing</label>
        <description>Set by the billing@ Email-to-Case routing address.</description>
    </standardValue>
</StandardValueSet>
```

`standardValueSets/CasePriority.standardValueSet-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>High</fullName>
        <default>false</default>
        <label>High</label>
    </standardValue>
    <standardValue>
        <fullName>Medium</fullName>
        <default>true</default>
        <label>Medium</label>
    </standardValue>
    <standardValue>
        <fullName>Low</fullName>
        <default>false</default>
        <label>Low</label>
    </standardValue>
</StandardValueSet>
```

`standardValueSets/CaseStatus.standardValueSet-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>New</fullName>
        <default>true</default>
        <label>New</label>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Working</fullName>
        <default>false</default>
        <label>Working</label>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Awaiting Customer</fullName>
        <default>false</default>
        <label>Awaiting Customer</label>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Closed</fullName>
        <default>false</default>
        <label>Closed</label>
        <closed>true</closed>
    </standardValue>
    <standardValue>
        <fullName>Closed - No Response</fullName>
        <default>false</default>
        <label>Closed - No Response</label>
        <closed>true</closed>
    </standardValue>
</StandardValueSet>
```

### How to read it

- **`fullName` of the file is the enum name, not the field.** The file is `CaseOrigin`, the field is
  `Case.Origin`. The mapping table is api_meta L141974–141982. `CaseReason` and `CaseType` are in the
  same table if the intake needs them.
- **`sorted` is documented Required** ("Indicates whether a global value set is sorted in
  alphabetical order. By default, this value is false" — api_meta L130740 ff.). `false` keeps the
  authored order, which is what a status ladder needs; `true` would show `Awaiting Customer` first.
- **At least one value or the deploy fails.** "When you deploy a StandardValueSet, this array must
  contain at least one picklist value. Otherwise, you receive an error."
- **`default` is inherited from `CustomValue` and is Required, defaulting to `true`**
  (api_meta L47500 ff.). Omitting it on every value produces several defaults, so state it on each.
- **`isActive` is how you retire a value, not deletion.** Removing a `<standardValue>` from the file
  is not the documented deactivation path; `CustomValue.isActive=false` is
  (api_meta L47480: deactivate "with the isActive field set to false").
- **`closed` marks a Status value as a closed state.** The guide's placement of this field is
  contradictory: `StandardValue.closed` says "This field is only relevant for the standard `Status`
  field in cases and tasks. This field is available in API version 16.0 and up to version 36.0. In
  version 37.0, this field is in GlobalPicklistValue" (api_meta L47545) — yet `StandardValueSet`
  itself only exists from API 38.0 (L130740). UNVERIFIED (2026-09-05): which element carries the
  closed flag in a v62 `CaseStatus.standardValueSet` retrieve is not resolvable from the Metadata
  API PDF. Retrieve `StandardValueSet:CaseStatus` from the target org first and copy the shape the
  org returns rather than trusting the block above; the `IsClosed` verification query in §6 is the
  authoritative read either way.
- **Deploying a value does not make it selectable on a record type.** The guide's note on
  `standardValue` is explicit: "new picklist values loaded into your organization through the
  Metadata API don't display in the picklist UI by default. For users to see the new values, go to
  the Record Types list for the object containing the picklist field, click Edit, and add the new
  value to the Selected Fields list" (api_meta L130740 ff.). See gotchas #7.
- **No wildcard.** "This metadata type doesn't support the wildcard character `*`". Name each value
  set in `package.xml`.

---

## 2. `objects/Case/Case.object-meta.xml` — support processes, record types, compact layout

A Case record type **must** name a support process: the `RecordType.businessProcess` field "is
required in record types for lead, opportunity, solution, and case, and not allowed otherwise"
(api_meta L44968 ff.). The process is a subset of the `CaseStatus` values deployed in §1, so §1
lands first.

Every `<fullName>` below is written in stem form (`Inbound_Intake_Process`, not
`Inbound Intake Process`), because a Salesforce DX project decomposes this one file into a
directory of files, and each decomposed file's stem has to be its own `fullName` — see § 2.1.
The files are
`objects/Case/Case.object-meta.xml`,
`objects/Case/businessProcesses/Inbound_Intake_Process.businessProcess-meta.xml`,
`objects/Case/businessProcesses/Internal_Intake_Process.businessProcess-meta.xml`,
`objects/Case/recordTypes/Inbound_Intake.recordType-meta.xml`,
`objects/Case/recordTypes/Internal_Intake.recordType-meta.xml` and
`objects/Case/compactLayouts/Case_Intake_Compact.compactLayout-meta.xml`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <businessProcesses>
        <fullName>Inbound_Intake_Process</fullName>
        <description>Status ladder for cases arriving from the web form and support mailbox.</description>
        <isActive>true</isActive>
        <values>
            <fullName>New</fullName>
            <default>true</default>
        </values>
        <values>
            <fullName>Working</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Awaiting Customer</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Closed</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Closed - No Response</fullName>
            <default>false</default>
        </values>
    </businessProcesses>
    <businessProcesses>
        <fullName>Internal_Intake_Process</fullName>
        <description>Agent-raised cases; no customer-wait state.</description>
        <isActive>true</isActive>
        <values>
            <fullName>New</fullName>
            <default>true</default>
        </values>
        <values>
            <fullName>Working</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Closed</fullName>
            <default>false</default>
        </values>
    </businessProcesses>
    <compactLayouts>
        <fullName>Case_Intake_Compact</fullName>
        <fields>CaseNumber</fields>
        <fields>Origin</fields>
        <fields>Priority</fields>
        <fields>Status</fields>
        <label>Case Intake</label>
    </compactLayouts>
    <compactLayoutAssignment>Case_Intake_Compact</compactLayoutAssignment>
    <recordTypes>
        <fullName>Inbound_Intake</fullName>
        <active>true</active>
        <businessProcess>Inbound_Intake_Process</businessProcess>
        <compactLayoutAssignment>Case_Intake_Compact</compactLayoutAssignment>
        <description>Cases created by Web-to-Case and Email-to-Case.</description>
        <label>Inbound Intake</label>
        <picklistValues>
            <picklist>Origin</picklist>
            <values>
                <fullName>Web</fullName>
                <default>true</default>
            </values>
            <values>
                <fullName>Email</fullName>
                <default>false</default>
            </values>
            <values>
                <fullName>Billing</fullName>
                <default>false</default>
            </values>
        </picklistValues>
    </recordTypes>
    <recordTypes>
        <fullName>Internal_Intake</fullName>
        <active>true</active>
        <businessProcess>Internal_Intake_Process</businessProcess>
        <description>Cases raised by agents on the phone or from an internal referral.</description>
        <label>Internal Intake</label>
        <picklistValues>
            <picklist>Origin</picklist>
            <values>
                <fullName>Phone</fullName>
                <default>true</default>
            </values>
        </picklistValues>
    </recordTypes>
</CustomObject>
```

### How to read it

- **`<businessProcess>` is the bare name inside the object; `Case.Inbound_Intake_Process` is the
  `package.xml` form.** The guide spells the split out on `BusinessProcess.fullName`: "Use the
  object-qualified form (`Opportunity.Bulk Orders`) for API addressing, such as in a `package.xml`
  member in metadata retrieve results. When creating a business process in a `CustomObject`
  definition, use the bare process name (`Bulk Orders`) … The enclosing object already supplies the
  entity context" (api_meta L42955 ff.).
- **Every value in `<businessProcesses><values>` must already be a `CaseStatus` standard value.**
  The process selects from the value set; it does not create values.
- **Two `compactLayoutAssignment` elements, two scopes.** `CustomObject.compactLayoutAssignment` is
  "The compact layout assigned to the object" (api_meta L41951); `RecordType.compactLayoutAssignment`
  is "the compact layout that is assigned to the record type" (L45016). `SYSTEM` is the reserved
  value for the platform default, used in the guide's own sample (L43152). `Internal_Intake` above
  omits its own and therefore inherits the object-level assignment.
- **Element order follows the guide's `CustomObject` sample** (L43130 ff.): `compactLayouts` before
  `compactLayoutAssignment`, `recordTypes` last. It is not alphabetical.
- **Record types are an intake convenience, not access control.** The guide is emphatic: "Don't use
  record types as an access control mechanism… a user assigned to a profile that isn't enabled for a
  particular record type can't create records with that record type, but can access records
  associated with that record type" (L44968 ff.). The same warning is repeated for `BusinessProcess`
  (L42955 ff.) — never put anything sensitive in a process or record-type name or description.
- **Nothing here makes the record type pickable.** Record type visibility is a `Profile` /
  `PermissionSet` concern, and retrieving a `RecordType` "makes the component appear in any Profile
  and PermissionSet components that are retrieved in the same package" (L44968 ff.). The layout
  assignment and profile wiring belong to `admin/record-types-and-page-layouts` — read that file for
  the `Layout` and `recordTypeVisibilities` shapes; they are not restated here.

### 2.1 File stem = fullName

**Rule: in a source-format (DX) project, a decomposed `*.businessProcess-meta.xml` or
`*.recordType-meta.xml` file's stem must be character-for-character its own `<fullName>`.** The CLI
derives the `package.xml` member from the *file stem* — `Support_Process.businessProcess-meta.xml`
becomes the member `Case.Support_Process` — and the deploy then looks for a component of that name
inside the zip. A file whose stem says `Support_Process` while its `<fullName>` says
`Support Process` declares a member nothing satisfies, and the deploy fails on the manifest
rather than on anything the org objected to:

```text
An object 'Case.Support_Process' of type BusinessProcess was named in package.xml,
but was not found in zipped directory
```

Evidence: verified by `sf project deploy start --dry-run` against a Summer '26 developer org on
2026-09-05 (`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md`). A build authored from an
earlier revision of this file wrote
`objects/Case/businessProcesses/Support_Process.businessProcess-meta.xml` carrying
`<fullName>Support Process</fullName>`. Run 5 of that report failed with the error above for both
`Case.Support_Process` and `Case.Billing_Process`; runs 6–7 renamed each `<fullName>` to its stem and
updated the record types' `<businessProcess>` references, and all 12 components validated
(`checkOnly: true`, 0 errors). The validated files are in
`examples/builds/case-onboarding/reports/mock-deploy-fixes/`.

Why the trap exists only for `BusinessProcess`:

| Type | What the guide says about `fullName` | Can it hold a space? |
|---|---|---|
| `BusinessProcess` | "the `fullName` is created combining the Entity Name and Business Process Name… for a business process called 'Bulk Orders' for opportunities, the `fullName` would be `Opportunity.Bulk Orders`" (api_meta L42993–L43007) | **Yes** — no character restriction is stated, and the guide's own worked name contains one |
| `RecordType` | "The `fullName` can contain only underscores and alphanumeric characters… begin with a letter, not include spaces" (api_meta L45022–L45024) | No |

So a spaced display name is legal inside the nested `<CustomObject>` form, deploys there, and only
breaks once the same content is decomposed into a file whose stem cannot carry the space. A record
type reaches the same failure by a different route — a file renamed away from its `<fullName>`.

The guide does not cover this. `BusinessProcess` → "Declarative Metadata File Suffix and Directory
Location" says only "Business processes are defined as part of the custom object or standard object
definition" (api_meta L42969); the per-file source-format layout under `objects/Case/` is a DX
convention the Metadata API PDF never describes, so the rule above rests on the dry run, not on the
guide.

UNVERIFIED (2026-09-09): **the rule is source-format-specific as proven.** Whether a
*metadata-format* deploy driven by an explicit `package.xml` accepts a spaced `fullName` — with
`Case.Support Process` written out as the member — is not established here, and the guide is silent.
Run 1 of the same report, against the same pre-fix tree, listed the members as `Case.Support Process`
/ `Case.Billing Process` and reported them `ok` (that deploy failed on two `Layout` components, so
nothing was committed either way), while run 5 — same tree, layouts fixed — named them
`Case.Support_Process` / `Case.Billing_Process` and failed. Why the member name differed between the
two runs was not investigated. Do not read run 1 as a licence to ship spaced `fullName` values:
making the stem equal the `fullName` satisfies both derivations, and is the only shape this skill
has watched deploy clean.

`scripts/check_case_management_setup.py` enforces both halves — **CMS-STEM-01** (stem ≠ `fullName`,
or a `fullName` containing a space) and **CMS-STEM-02** (a record type's `<businessProcess>` names a
process with no matching file stem in the tree).

---

## 3. `settings/Case.settings-meta.xml` — Web-to-Case and the org-level intake behaviour

Shaped from the guide's own `CaseSettings` sample definition (api_meta L112160–112225) and reduced
to the fields an intake build actually decides. **The `emailToCase` block is deliberately absent** —
it lives in `admin/email-to-case-configuration` → `references/metadata-examples.md`, and both blocks
go in the *same* physical file when both channels are in scope.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CaseSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <defaultCaseOwner>Tier_1_General</defaultCaseOwner>
    <defaultCaseOwnerType>Queue</defaultCaseOwnerType>
    <notifyDefaultCaseOwner>true</notifyDefaultCaseOwner>
    <useSystemUserAsDefaultCaseUser>false</useSystemUserAsDefaultCaseUser>
    <defaultCaseUser>service.automation@acme.example</defaultCaseUser>
    <caseAssignNotificationTemplate>Support_Templates/Case_Assigned_Notification</caseAssignNotificationTemplate>
    <caseCreateNotificationTemplate>Support_Templates/Case_Created_Notification</caseCreateNotificationTemplate>
    <caseCommentNotificationTemplate>Support_Templates/Case_Comment_Notification</caseCommentNotificationTemplate>
    <caseCloseNotificationTemplate>Support_Templates/Case_Closed_Notification</caseCloseNotificationTemplate>
    <closeCaseThroughStatusChange>true</closeCaseThroughStatusChange>
    <keepRecordTypeOnAssignmentRule>true</keepRecordTypeOnAssignmentRule>
    <notifyContactOnCaseComment>false</notifyContactOnCaseComment>
    <notifyOwnerOnCaseComment>true</notifyOwnerOnCaseComment>
    <notifyOwnerOnCaseOwnerChange>true</notifyOwnerOnCaseOwnerChange>
    <useSystemEmailAddress>true</useSystemEmailAddress>
    <enableCaseFeed>true</enableCaseFeed>
    <enableSuggestedSolutions>false</enableSuggestedSolutions>
    <enableSuggestedArticlesApplication>true</enableSuggestedArticlesApplication>
    <enableEarlyEscalationRuleTriggers>true</enableEarlyEscalationRuleTriggers>
    <webToCase>
        <enableWebToCase>true</enableWebToCase>
        <caseOrigin>Web</caseOrigin>
    </webToCase>
</CaseSettings>
```

### How to read it

- **`webToCase` has exactly three children.** `WebToCaseSettings` (api_meta L112128) is
  `enableWebToCase`, `caseOrigin` and `defaultResponseTemplate` — nothing else. No owner, no field
  list, no form markup, no throttle, no reCAPTCHA switch. Anything else you were expecting to
  configure is either a different metadata type or Setup-only (§4).
- **`caseOrigin` here must be a live `CaseOrigin` value.** "Specifies the default case origin for
  cases created through this web form. Applies only if `enableWebToCase` is set to `true`." §1 is
  therefore a hard prerequisite, and `Case.Origin` is the field the assignment rule reads to tell a
  web case from an email case.
- **`defaultResponseTemplate` is not the acknowledgement email.** The guide scopes it to
  "email responses to cases that are submitted through a **Self-Service portal**" (L112128 ff.), and
  the Self-Service portal has not been available for new orgs since Spring '12 (api_meta L47500 ff.
  on `cssExposed`). It is omitted above on purpose. The customer acknowledgement is an
  `AutoResponseRules` entry, which fires only when the assignment rule fires — see `SKILL.md`
  § Assignment Rules and Auto-Response Dependency and `admin/assignment-rules`.
- **`defaultCaseOwner` is the Web-to-Case safety net, not its owner.** It "Specifies the default
  owner of a case when assignment rules fail to locate an owner". Web-to-Case has no owner field of
  its own, so every unmatched web submission lands here. Pair it with `defaultCaseOwnerType`
  (`User` or `Queue`) and set it to a **queue** so unrouted cases are visible to a team; see
  gotchas #8.
- **`defaultCaseUser` and `useSystemUserAsDefaultCaseUser` travel together.** `defaultCaseUser` is
  "the user listed in the Case History related list for automated case changes from: Assignment
  rules / Escalation rules / On-Demand Email-to-Case / Cases logged in the Self-Service portal". If
  `useSystemUserAsDefaultCaseUser` is `false`, "then you must specify a value for the
  `defaultCaseUser` field". Naming a real automation user is what makes Case History readable when
  the assignment rule, not a person, moved the case.
- **The `true` branch has a required partner too, and the guide does not say so.** Flip the boolean
  and the file above no longer deploys: the org rejects it with `CaseSettings: Enter the system
  user's email address.` The `true` form is therefore two elements, not one:

  ```xml
      <useSystemUserAsDefaultCaseUser>true</useSystemUserAsDefaultCaseUser>
      <systemUserEmail>support.automation@acme.example</systemUserEmail>
  ```

  `systemUserEmail` is documented only as "the email address used when the default case user is the
  system user" (api_meta L111871 ff.) — no Required marker, no cross-reference to the boolean.
  UNVERIFIED (2026-09-12): the requirement is proven live (dry-run, `checkOnly`, API 67.0), not in
  the guide. The file above keeps `false` + `defaultCaseUser` on purpose — a named automation user
  is queryable in Case History and reports, where "the system user" is not — but whichever branch
  you take, set the boolean **explicitly** and its partner with it. The guide states no default for
  the boolean, so omitting it hands the behaviour to whatever the target org already had. Checker
  rule `CMS-SYSUSER-01`; gotchas #12.
- **`useSystemEmailAddress` decides who the notification appears to come from** — `true` = a system
  address, `false` = "the user or contact who is updating the case". It applies to case comment,
  case attachment and case assignment notifications.
- **All four `case*NotificationTemplate` fields take `folderName/templateName`** and the guide adds
  "Lightning email templates aren't packageable. We recommend using a Classic email template" on
  each. A Lightning template name here deploys and then fails to send.
- **`enableSuggestedArticlesApplication` and `enableSuggestedSolutions` are mutually exclusive.**
  Suggested Articles "is only valid if `enableSuggestedSolutions=false`", and Suggested Solutions is
  "only valid if `enableSuggestedArticlesApplication`, `…CustomerPortal`, and `…PartnerPortal=false`".
  Set both explicitly; a file that omits `enableSuggestedSolutions` inherits whatever the org had.
- **`closeCaseThroughStatusChange`** "Indicates whether Closed is included in the Case Status field
  on case edit pages". With `false`, agents close through the Close Case action only — which is a
  problem if a support process (§2) exposes a closed status that the edit page then hides.
- **`keepRecordTypeOnAssignmentRule` is scoped to manual creation.** "When applying assignment rules
  to **manually created records**, indicates whether to keep the existing record type (`true`) or to
  override the existing record type with the assignee's default record type (`false`)." See
  gotchas #6 for why this does not protect a Web-to-Case record type.
- **`enableEarlyEscalationRuleTriggers`** turns on early triggers for escalation rules; the org also
  carries a separate `escalateCaseBefore` boolean ("early triggers are enabled to escalate a case").
  Escalation entry design lives in `admin/escalation-rules`.

---

## 4. Web-to-Case: what is metadata and what is not

| Piece | Deployable? | Where it lives |
|---|---|---|
| The feature switch | **Yes** — `CaseSettings.webToCase.enableWebToCase` | `settings/Case.settings-meta.xml` |
| The default origin stamped on web cases | **Yes** — `CaseSettings.webToCase.caseOrigin` | same file |
| The `Case.Origin` value that origin points at | **Yes** — `StandardValueSet:CaseOrigin` | §1 |
| The fallback owner for unrouted web cases | **Yes** — `CaseSettings.defaultCaseOwner` + `defaultCaseOwnerType` | §3 |
| The record type and support process a web case gets | **Yes** — `CustomObject` `recordTypes` / `businessProcesses` | §2 |
| Which queue a web case is routed to | **Yes**, but elsewhere — `AssignmentRules` | `admin/assignment-rules` |
| The acknowledgement email | **Yes**, but elsewhere — `AutoResponseRules` | `admin/assignment-rules` |
| **The generated HTML form** | **No** | Setup only |
| **The daily submission allocation** | **No** | Setup / Salesforce Support |

**The form is not metadata and there is no metadata type for it.** `WebToCaseSettings` has three
fields and none of them describes a form, a field list, a return URL or an org id. Nothing in the
Metadata API guide generates, stores or versions the HTML. Treat the form as an artefact of your
website's repository, not of the Salesforce package, and re-derive it from Setup whenever the field
set changes.

UNVERIFIED (2026-09-05): the Setup path that generates the snippet, the hidden field names it emits
(`orgid`/`oid`, `retURL`, `recordType`, `debug`), the endpoint it posts to, and the reCAPTCHA option
are documented only on help.salesforce.com, which cannot be fetched. The skeleton below is shaped by
analogy with the Web-to-Lead form in `admin/lead-management-and-conversion`
(`references/examples.md`) and must be replaced by the snippet the target org's Setup page actually
generates before it is used. Do not hand-write the endpoint or the org id.

```html
<!-- SKELETON ONLY - replace with the snippet Setup generates for YOUR org. -->
<form action="[ENDPOINT FROM SETUP]" method="POST">
  <input type="hidden" name="orgid"  value="[ORG ID FROM SETUP]">
  <input type="hidden" name="retURL" value="https://www.acme.example/support/thank-you">
  <!-- origin: omit to accept CaseSettings.webToCase.caseOrigin ("Web"); -->
  <!-- send a value only if it is an active CaseOrigin standard value (see section 1). -->
  <input type="hidden" name="origin" value="Web">
  <!-- priority: a hidden constant, or a visible <select> whose options are exactly the -->
  <!-- CasePriority values from section 1. A value not in that set silently fails to stamp. -->
  <input type="hidden" name="priority" value="Medium">
  <label for="name">Name</label>      <input id="name"     name="name"     type="text"  required>
  <label for="email">Email</label>    <input id="email"    name="email"    type="email" required>
  <label for="subject">Subject</label><input id="subject"  name="subject"  type="text"  required>
  <label for="description">Details</label><textarea id="description" name="description" required></textarea>
  <input type="submit" value="Submit">
</form>
```

**The daily limit is not in any fetchable source we hold.** UNVERIFIED (2026-09-05): the widely
quoted 5,000-per-24-hour Web-to-Case allocation and the 50,000 combined Web-to-Case + Web-to-Lead
pending-request cap appear only on help.salesforce.com (cited in `references/well-architected.md`).
`grep -ci "web-to-case" salesforce_app_limits_cheatsheet.txt` returns **0**, and so does
`web-to-lead` — the Salesforce App Limits Cheat Sheet carries no Web-to-Case row at all. `grep -ni
"Web-to-Case" api_meta.txt` returns **3** hits, all inside the `CaseSettings` section (L111888,
L112128, L112142), none of them a limit. Read the allocation from Setup in the target org before
quoting it to a customer, and do not build a monitor around the number without confirming it.

---

## 5. `package.xml`, deploy order and the commands

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CaseOrigin</members>
        <members>CasePriority</members>
        <members>CaseStatus</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Case</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Case.Inbound_Intake_Process</members>
        <members>Case.Internal_Intake_Process</members>
        <name>BusinessProcess</name>
    </types>
    <types>
        <members>Case.Inbound_Intake</members>
        <members>Case.Internal_Intake</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Case</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

Wildcards: `StandardValueSet` does not support `*`; `BusinessProcess` supports it "only when a
`RecordType` is specified"; settings do not — "The wildcard character `*` … doesn't apply to
metadata types for feature settings. The wildcard applies only when retrieving all settings, not for
an individual setting" (api_meta, `CaseSettings` → Wildcard Support in the Manifest File). Name
`Case` explicitly under `Settings`.

The two `BusinessProcess` members above are the object-qualified `fullName`s from §2, which
in a source-format tree are also the file stems (`Support_Process`-style, no spaces). If a
member here and a decomposed file's stem disagree, the deploy fails with "was not found in
zipped directory" — § 2.1.

### Deploy order

| # | Deploy | Because |
|---|---|---|
| 1 | `CustomObject:Case` custom fields (if the intake adds any) | a `picklistValues` block or a rule criterion on a field that does not exist fails the deploy |
| 2 | `StandardValueSet:CaseOrigin`, `CasePriority`, `CaseStatus` | `businessProcesses` values and `webToCase.caseOrigin` both reference values that must already exist |
| 3 | `CustomObject:Case` record types + business processes (+ compact layouts) | a record type is rejected without its support process, and the process is rejected without its Status values |
| 4 | Queues, public groups, Classic email templates | `defaultCaseOwner` and the four `case*NotificationTemplate` fields resolve by name at deploy time |
| 5 | `Settings:Case` (`webToCase` here, `emailToCase` from the sibling) | turning the channel on after its origin, owner and templates exist means no case is ever created into a half-built org |
| 6 | `AssignmentRules:Case`, then `AutoResponseRules:Case`, then `EscalationRules:Case` | the auto-response fires only when the assignment rule fires; escalation entries reference the queues from step 4 |

Steps 5 and 6 are reversible in either order only if the channel is left off until the rules land.
The failure mode of getting it wrong is not a deploy error — it is live traffic into an org with no
active assignment rule, which is exactly the state that produces the "auto-response never sends"
report in `references/gotchas.md` #1.

```bash
# Read what the org actually has before changing anything.
sf project retrieve start --target-org prod \
  --metadata "StandardValueSet:CaseOrigin" "StandardValueSet:CasePriority" \
             "StandardValueSet:CaseStatus" "Settings:Case" "CustomObject:Case"

# Check the retrieved / authored tree before deploying.
python3 skills/admin/case-management-setup/scripts/check_case_management_setup.py \
    --manifest-dir force-app/main/default --verbose

# Validate against production without committing the change.
sf project deploy validate --target-org prod --manifest manifest/package.xml

# Deploy in the order above; the manifest preserves it within one deployment.
sf project deploy start --target-org prod --manifest manifest/package.xml
```

---

## 6. Verification

**1. Is each channel producing cases, day by day, with the origin you expect?**

```sql
SELECT DAY_ONLY(CreatedDate) day, Origin, COUNT(Id) cases
FROM Case
WHERE CreatedDate = LAST_N_DAYS:14
GROUP BY DAY_ONLY(CreatedDate), Origin
ORDER BY DAY_ONLY(CreatedDate) DESC
```

`Case.Origin` is "The source of the case, such as Email, Phone, or Web. Label is Case Origin"
(object_reference L62566 ff.). A `null` Origin row means submissions are arriving without the
default being applied — check `webToCase.caseOrigin` in §3. A **missing day** on the web row is the
only cheap signal that submissions were dropped, because the submitter still sees the form's success
page; see `references/gotchas.md` #4.

**2. Did the assignment rule actually route, or did the default owner catch it?**

```sql
SELECT OwnerId, Owner.Name, COUNT(Id) cases
FROM Case
WHERE Origin = 'Web' AND CreatedDate = LAST_N_DAYS:7
GROUP BY OwnerId, Owner.Name
ORDER BY COUNT(Id) DESC
```

`Case.OwnerId` refers to `Group` or `User` (object_reference L62576 ff.), so both queues and people
appear. Any row whose owner is the `defaultCaseOwner` deployed in §3 is a case the assignment rule
**failed to place** — that field is defined as the owner used "when assignment rules fail to locate
an owner", so a non-zero count there is a routing gap, not a routing outcome. A healthy web intake
shows zero.

**3. Are the closed statuses the ones the support process thinks they are?**

```sql
SELECT ApiName, MasterLabel, IsClosed, IsDefault, SortOrder
FROM CaseStatus
ORDER BY SortOrder
```

`CaseStatus` is a queryable object, one row per Status picklist value, with `IsClosed`
("Indicates whether this case status value represents a closed Case… **Multiple case status values
can represent a closed Case**") and `IsDefault` (object_reference L64145 ff.). This is the
authoritative read of the `closed` flag whose metadata placement is marked UNVERIFIED in §1. Check
that every value your `Inbound_Intake_Process` exposes appears here, that exactly one row is
`IsDefault = true`, and that `Closed - No Response` really carries `IsClosed = true` — a
closed-looking status with `IsClosed = false` leaves every "open cases" report and every escalation
entry counting it forever.

**4. Setup check.** Setup → Web-to-Case: **Web-to-Case Enabled** is checked and the **Default Case
Origin** matches the `caseOrigin` in §3. Setup → Case Record Types: both record types from §2 are
listed and each shows its support process. Setup → Support Settings: the Default Case Owner shown is
the queue from §3 — the deploy sets it, but a `caseOwner` on an Email-to-Case routing address
overwrites it (api_meta L112010 ff.), so read it back after any change to the sibling's file.
