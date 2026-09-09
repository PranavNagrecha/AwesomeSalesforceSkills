# Gotchas — Case Management Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Auto-Response Rules Do Not Fire Independently of Assignment Rules

**What happens:** The auto-response rule never sends an acknowledgment email to the customer, even though the rule is active and the template is valid.

**When it occurs:** The auto-response rule fires ONLY when the active case assignment rule also fires for that case. If the assignment rule is inactive, if no rule entry criteria match the incoming case, or if the case was created via an API or Data Loader integration that did not include the `Sforce-Auto-Assign: true` REST header or the SOAP `AssignmentRuleHeader` element, the assignment rule does not fire — and therefore the auto-response rule does not fire either.

**How to avoid:** Before debugging the auto-response rule itself, always verify that the case assignment rule is active, has at least one matching entry (or a catch-all), and that the creation method triggers assignment rule evaluation. Check Case history for "Rule Assignment" entries to confirm the assignment rule ran. If creating cases via API, confirm the integration is passing the correct header.

---

## Gotcha 2: Escalation Rule Reactivation Triggers Bulk Immediate Escalations

**What happens:** When a deactivated escalation rule is reactivated, the escalation engine immediately evaluates all open cases against the rule. Cases that have been open longer than the escalation threshold since the rule was deactivated will escalate at once — generating a surge of re-assignment actions, emails, and queue changes in a single engine pass.

**When it occurs:** Any time an escalation rule is deactivated for maintenance or troubleshooting and then reactivated. The longer the rule was inactive and the more open cases exist in the org, the larger the wave. In orgs with thousands of open cases and multi-hour SLA thresholds, hundreds of simultaneous escalations can occur.

**How to avoid:** Never reactivate an escalation rule in production without first testing in a sandbox with representative case volume. Before reactivation, consider temporarily closing or bulk-updating the cases that would immediately escalate. Communicate to the support team that a volume surge may follow reactivation.

---

## Gotcha 3: Email-to-Case Thread ID Misconfiguration Creates Duplicate Cases

**What happens:** Customer replies to a case email notification create new, separate cases instead of threading as Email Message records on the original case.

**When it occurs:** The Email-to-Case thread ID is a token embedded in outgoing case emails that Salesforce uses to match replies to the parent case. If the routing address is incorrectly configured, the mail server strips custom headers, the reply-to address is not set to the routing address, or a third-party email system modifies the message body before forwarding, the thread token is missing or invalid. Salesforce cannot match the reply and creates a new case.

**How to avoid:** Test thread handling end-to-end before go-live: create a case via email, reply from the Salesforce case (not manually), and confirm the customer-facing reply-to address includes the Salesforce routing address. Have the customer (or a test email account) reply and verify the reply appears as an Email Message on the original case. Enable the "Thread ID in Email Subject" option as a fallback if the mail server strips body tokens.

---

## Gotcha 4: The Web-to-Case Overflow Signal Exists, But It Stops After Five Emails

**What happens:** Web-to-Case enforces a 24-hour submission limit. Requests above it are not discarded — they land in a pending request queue that Web-to-Case and Web-to-Lead **share**, capped at 50,000 combined requests. Only when that queue is full are further requests rejected and not queued at all. The submitter sees the HTML form's success page regardless, and no case is created.

There **is** a native signal, and teams routinely build monitoring as though there weren't: when the pending limit is reached and requests start being rejected, Salesforce emails the administrator about the **first five rejected submissions**. That is the whole notification. A four-hour outage that drops 40,000 requests produces exactly five emails, all in the first few seconds — so the useful design question is not "how do we detect this at all" but "is the address receiving those five emails monitored, and do we have a second signal for the remaining 39,995?"

**When it occurs:** High-volume campaigns, product launches, or outage events that drive spike submission volume. Because the pending queue is shared, a Web-to-Lead spike from a marketing campaign can exhaust the queue and take Web-to-Case down with it — a coupling that is invisible from the Service Cloud side.

**How to avoid:** Route the administrator notification address to a monitored support mailbox or ticket queue, not an individual's inbox. Monitor the pending request count in Setup, and account for Web-to-Lead volume in the same budget. Salesforce Customer Support can raise the pending request limit. For sustained high volume, supplement with On-Demand Email-to-Case, or replace the built-in endpoint with an Experience Cloud form or a custom integration that creates cases through the **REST or SOAP API**. (SOSL is a search language and cannot create records of any kind — it is not an alternative intake path.)

---

## Gotcha 5: Escalation Rule Business Hours Omission Runs Clock 24/7

**What happens:** Cases escalate outside of business hours — on weekends, evenings, and holidays — because the escalation threshold is measured in calendar time, not business time.

**When it occurs:** When creating an escalation rule entry, the business hours field is optional and defaults to none. Without a business hours record attached, Salesforce measures escalation time in elapsed wall-clock hours from case creation or last modification. A case opened on Friday at 5 PM escalates after the threshold hours even if the support team does not work weekends.

**How to avoid:** Always create a business hours record in Setup → Business Hours before configuring escalation rules. Attach the correct business hours record to every escalation rule entry that should respect work schedules. Verify the attachment is saved — the field is easy to overlook in the rule entry form.

---

## Gotcha 6: Same Subject and Body in Email-to-Case Creates Infinite Loop

**What happens:** An infinite loop of case creation occurs: an auto-response email to a customer triggers the Email-to-Case routing address again, creating a new case, which sends another auto-response, which creates another case — indefinitely.

**When it occurs:** If the "from" address or "reply-to" address on an auto-response email is set to (or accidentally matches) the Email-to-Case routing address, Salesforce receives the outgoing auto-response as a new inbound email and creates a new case. This is most common when the routing address is set up as both a send-from and receive-at address, or when a mail server misconfiguration bounces outgoing auto-responses back to the routing address.

**How to avoid:** Set the auto-response "from" address to a non-routed email address (e.g., noreply@company.com). Never use the Email-to-Case routing address as the sender for auto-response emails. In Salesforce Setup, the Email-to-Case routing address should only be used for inbound routing. Test by inspecting the "from" and "reply-to" headers on the outgoing auto-response email before go-live.

---

## Gotcha 7: A Deployed Case Status or Origin Value Is Invisible on Every Record Type Until Someone Edits It in Setup

**What happens:** `StandardValueSet:CaseStatus` (or `CaseOrigin`) deploys clean, the new value is
present in the org's value set, `sf project retrieve` returns it — and no agent can select it on any
case. Reports filtered on it return nothing. A `BusinessProcess` that lists the value still deploys,
because the value genuinely exists at the object level.

**When it occurs:** On every metadata deployment of a standard picklist value to an object that has
record types — which Case almost always does, since a Case record type is required to carry a
support process. The Metadata API guide states it directly on `StandardValueSet.standardValue`:
"When setting `standardValue` on Record Types, including person account record types, new picklist
values loaded into your organization through the Metadata API don't display in the picklist UI by
default. For users to see the new values, go to the Record Types list for the object containing the
picklist field, click Edit, and add the new value to the Selected Fields list" (*Metadata API
Developer Guide*, `StandardValueSet`, api_meta L130740 ff.). It is the record-type-level *selected
values* list, not the org-level value set, that gates the UI.

**How to avoid:** Treat a value-set deployment as two steps, not one. Deploy the `StandardValueSet`,
then deploy the `<recordTypes><picklistValues>` block that names the new value on each affected
record type (see `references/metadata-examples.md` §2) — or, if you are not deploying record types,
open Setup → Object Manager → Case → Record Types → each record type → Edit and move the value into
Selected Values. Verify from the org, not the source file: a case saved with the new Status must come
back from the `CaseStatus` query in `references/metadata-examples.md` §6, and an agent on each record
type must be able to pick it in the UI.

---

## Gotcha 8: Web-to-Case Has No Owner Setting of Its Own, So Unmatched Submissions Land Wherever `defaultCaseOwner` Points

**What happens:** Web form submissions create cases that nobody works. They are not in any queue list
view, they are not on any agent's My Cases, and the auto-response never fires for them either. The
form is working perfectly; the cases have simply been assigned to one person — often the admin who
built the org — and are sitting in an individual's record set.

**When it occurs:** `WebToCaseSettings` has exactly three fields — `enableWebToCase`, `caseOrigin`
and `defaultResponseTemplate` (*Metadata API Developer Guide*, `WebToCaseSettings`, api_meta
L112128 ff.). There is no owner, no queue and no routing element anywhere in the type. Ownership of
a web-created case is resolved entirely by the active assignment rule, and when no rule entry
matches, by the org-level `CaseSettings.defaultCaseOwner`, which the guide defines as "the default
owner of a case when assignment rules fail to locate an owner" (api_meta L111632 ff.). Its companion
`defaultCaseOwnerType` says whether that is a `User` or a `Queue`, and orgs are commonly stood up
with a `User`. Worse, the value is not exclusively yours to set: an Email-to-Case routing address
that carries `caseOwner` writes it — "Specifying a case owner here in the routing address sets a
value of `defaultCaseOwner` in `CaseSettings`" (api_meta L112010 ff.) — so a change made in the
Email-to-Case configuration silently re-points the Web-to-Case fallback.

**How to avoid:** Set `defaultCaseOwnerType` to `Queue` and `defaultCaseOwner` to a real support
queue, so an unrouted case is at least visible to a team rather than parked on a person; then make
the fallback loud with `notifyDefaultCaseOwner`. Give the assignment rule a catch-all entry so the
fallback is never the routing mechanism (`admin/assignment-rules`). Re-read the value after any
change to the Email-to-Case routing addresses, and monitor it with the owner query in
`references/metadata-examples.md` §6 — any non-zero count of web cases owned by the default owner is
a routing gap.

---

## Gotcha 9: `keepRecordTypeOnAssignmentRule` Does Not Protect a Web-to-Case or Email-to-Case Record Type

**What happens:** An admin sets `keepRecordTypeOnAssignmentRule` to `true`, expecting the record type
stamped at intake to survive assignment. Manually created cases keep their record type as intended.
Cases from the web form and the support mailbox still arrive on a different record type — usually the
receiving queue's or the automated user's default — and so pick up the wrong support process, the
wrong status ladder and the wrong compact layout.

**When it occurs:** The setting's scope is narrower than the name suggests. The Metadata API guide
defines it as: "When applying assignment rules to **manually created records**, indicates whether to
keep the existing record type (`true`) or to override the existing record type with the assignee's
default record type (`false`)" (*Metadata API Developer Guide*, `CaseSettings`, api_meta L111632
ff.). Web-to-Case and Email-to-Case cases are not manually created records. Email-to-Case has its own
per-address control instead — `EmailToCaseRoutingAddress.newEntityRecordType`, which "Sets the Case
Record Type used for new Cases that are created from emails sent to that specific routing address. If
not provided, Salesforce uses the org's default Case Record Type for the user/context handling
Email-to-Case" (api_meta L112010 ff.). Web-to-Case has no equivalent field at all: `WebToCaseSettings`
carries no record type element (api_meta L112128 ff.).

**How to avoid:** Do not rely on this setting for either inbound channel. For Email-to-Case, set
`newEntityRecordType` explicitly on every routing address (owned by
`admin/email-to-case-configuration`) rather than leaving it to the handling context's default. For
Web-to-Case, set the record type deterministically in a before-save record-triggered Flow keyed on
`Origin`, or accept the org default and make sure that default's support process is the intake one
(`references/metadata-examples.md` §2). Then verify per channel, not in aggregate: group created
cases by `Origin` and `RecordTypeId` for a day and confirm each channel lands on one record type.

---

## Gotcha 10: A Support Process Without a Closed Status Produces Cases Agents Cannot Close

**What happens:** Agents on one record type can move a case through its whole ladder and then have
nowhere to put it. "Closed" is absent from the Status picklist on that record type, the Close Case
action either fails or writes a status the agent did not choose, and open-case reports and escalation
entries keep counting work that finished days ago.

**When it occurs:** Two independent switches have to agree, and neither warns about the other. First,
a `BusinessProcess` is a *subset* of the `CaseStatus` value set — "A list of picklist values
associated with this business process" (*Metadata API Developer Guide*, `BusinessProcess`, api_meta
L42955 ff.) — and a support process authored from the happy path omits closed values as easily as it
omits any other. It deploys without complaint, and `businessProcess` is *required* on every Case
record type (api_meta L44968 ff.), so every record type inherits whichever subset it names. Second,
`CaseSettings.closeCaseThroughStatusChange` "Indicates whether Closed is included in the Case Status
field on case edit pages" (api_meta L111632 ff.); with `false`, the closed value is hidden on the
edit page even when the process does expose it. The reason the reporting damage outlives the
configuration mistake is that `Case.IsClosed` "is controlled by the `Status` field; it can't be set
directly" (*Object Reference*, `Case`, object_reference L62434 ff.), and multiple statuses can carry
the flag — "Multiple case status values can represent a closed Case" (*Object Reference*,
`CaseStatus`, object_reference L64145 ff.).

**How to avoid:** Author every support process against the deployed `CaseStatus` value set, not from
memory, and require at least one value whose `IsClosed` is `true` in each. Run the `CaseStatus` query
in `references/metadata-examples.md` §6 after deploying and reconcile its `IsClosed` column against
each `<businessProcesses>` block. Set `closeCaseThroughStatusChange` explicitly rather than
inheriting it. The checker script flags a support process with no closed-looking status and a record
type whose support process is missing.

---

## Gotcha 11: A Business Process File Whose Stem Does Not Match Its `fullName` Is Unreachable in Source Format

**What happens:** `sf project deploy start` fails before the org validates anything, with a member
the CLI itself put in the manifest:

```text
An object 'Case.Support_Process' of type BusinessProcess was named in package.xml,
but was not found in zipped directory
```

Nothing is missing from the tree. The file is there; it just answers to a different name.

**When it occurs:** In a source-format (DX) project, the Case object is decomposed into
`objects/Case/businessProcesses/<stem>.businessProcess-meta.xml` and
`objects/Case/recordTypes/<stem>.recordType-meta.xml`. The CLI builds each package member from the
**file stem** (`Support_Process` → `Case.Support_Process`) and resolves it against the component's
`<fullName>`. Write the process's display name — `<fullName>Support Process</fullName>` — into a
file the filesystem forced to be `Support_Process.businessProcess-meta.xml`, and the member points
at nothing. `BusinessProcess.fullName` invites the mistake: the Metadata API guide's own worked
example is `Opportunity.Bulk Orders`, spaces included, and it states no character restriction
(api_meta L42993–L43007) — whereas `RecordType.fullName` "can contain only underscores and
alphanumeric characters… not include spaces" (api_meta L45022–L45024), so a record type can only
reach this failure by being renamed away from its `fullName`. The guide describes business processes
only as part of the object definition (api_meta L42969) and never covers the decomposed layout, so
nothing in the official docs warns about it.

Verified by `sf project deploy start --dry-run` against a Summer '26 developer org on 2026-09-05
(`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md`): run 5 failed on
`Case.Support_Process` and `Case.Billing_Process`; runs 6–7, with each `<fullName>` renamed to its
stem and the record types' `<businessProcess>` references updated, validated 12/12 components
(`checkOnly: true`, 0 errors).

UNVERIFIED (2026-09-09): the rule as proven is source-format-specific. Whether a metadata-format
deploy with a hand-written `package.xml` accepts a spaced `fullName` is untested — run 1 of that
same report listed the members as `Case.Support Process` / `Case.Billing Process` and reported them
`ok` (that run failed on two `Layout` components instead), so treat the metadata-format behaviour as
unknown rather than safe.

**How to avoid:** Make the stem equal the `fullName`, in both formats — it satisfies either
derivation. Name support processes the way record types are already forced to be named
(`Inbound_Intake_Process`), put the human-readable wording in `<description>`, and update every
`<businessProcess>` reference when you rename. `scripts/check_case_management_setup.py` fails the
tree on this: **CMS-STEM-01** for a stem/`fullName` divergence or a `fullName` containing a space,
**CMS-STEM-02** for a `<businessProcess>` naming a process with no matching file stem. Run it before
the deploy — it is the cheapest place to catch a failure whose message points at the manifest rather
than at the file.
