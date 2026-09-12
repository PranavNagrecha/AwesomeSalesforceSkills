# Web-to-Case form contract — M3-S03

Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was deployed.
This file exists because the thing the website team actually needs — the form — **is not metadata,
and has no metadata type at all**. The deployable half of Web-to-Case is three lines inside
[`settings/Case.settings-meta.xml`](./settings/Case.settings-meta.xml); everything else is a
contract between this build and a repository Salesforce does not own.

## 1. What is deployable and what is not

Reproduced from `skills/admin/case-management-setup/references/metadata-examples.md` § 4, narrowed
to this build:

| Piece | Deployable? | Where it lives in this build |
|---|---|---|
| The feature switch | **Yes** — `CaseSettings.webToCase.enableWebToCase` = `true` | `artefacts/M3-S03/settings/Case.settings-meta.xml` |
| The default origin stamped on web cases | **Yes** — `CaseSettings.webToCase.caseOrigin` = `Web` | same file |
| The `Case.Origin` value that origin points at | **Yes** — `StandardValueSet:CaseOrigin` | `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml` (`Web`, and it is the `default`) |
| The fallback owner for unrouted web cases | **Yes** — `defaultCaseOwner` `Tier_1_General` + `defaultCaseOwnerType` `Queue` | `artefacts/M3-S03/settings/Case.settings-meta.xml`; the queue is `artefacts/M2-S04/queues/Tier_1_General.queue-meta.xml` |
| The record type and support process a web case gets | **Yes** in principle — `CustomObject` `recordTypes` / `businessProcesses` | `artefacts/M1-S01/objects/Case/` — but **nothing stamps one on a web case**; see § 5 |
| Which queue a web case is routed to | **Yes, but elsewhere** — `AssignmentRules` | **M3-S04** |
| The acknowledgement email | **Yes, but elsewhere** — `AutoResponseRules` | **M3-S04**, with its sender held open at the M3 gate (`decisions.md` D-M3S02-04) |
| **The generated HTML form** | **No** | Setup only — authored and hosted in the website's own repository, outside this build |
| **The daily submission allocation** | **No** | Setup / Salesforce Support |

`WebToCaseSettings` has **exactly three** children — `enableWebToCase`, `caseOrigin` and
`defaultResponseTemplate` (api_meta L112128) — and "none of them describes a form, a field list, a
return URL or an org id". The file written by this step carries two of the three; § 4 explains the
deliberate omission.

## 2. How the form posts — the question this step cannot answer

**Q66's answer does not settle it, and says so:** "The website form is the only external producer
named; **confirm whether it posts to Web-to-Case directly or through middleware**, and whether
account/entitlement data comes from a billing system." The requirement says only "a form on our
website (roughly 60 a day)". So the posting path is **UNCONFIRMED**, and both paths are specified
below rather than one being assumed.

| | Path A — direct post to Web-to-Case | Path B — post via middleware |
|---|---|---|
| What the site does | posts the HTML form straight to the Salesforce Web-to-Case endpoint | posts to the customer's own service, which then writes the Case into Salesforce over an API |
| Origin stamped on the Case | `Web`, from `CaseSettings.webToCase.caseOrigin`, unless the form sends its own `origin` input | whatever the caller writes into `Case.Origin` — **nothing defaults it**, because `webToCase.caseOrigin` applies only to the Web-to-Case endpoint |
| What must be true for routing to work | nothing extra — `Origin` = `Web` is what M3-S04's assignment rule reads | the caller **must** write `Origin` = `Web` (or another active `CaseOrigin` value) explicitly, or M3-S01's `Origin_Must_Be_Known` validation rule rejects the insert and no rule entry matches |
| Credentials / secrets | none — the endpoint is public by design | a Named Credential / External Credential on the caller's side; nothing of that shape belongs in this build directory |
| Where it sits in `standards/decision-trees/integration-pattern-selection.md` | **nowhere** — see § 3 | Direction 2, Q5 `< 1k rows/day → REST API` (60/day, Q15); Q9 `Yes, plain CRUD → Standard REST on sObject`; Q7 requires a stable External Id rather than name-matching |
| `enableWebToCase` still needed? | **yes** | **no** — but it is set `true` regardless, because Path A is the stated default until IT confirms otherwise, and the switch is inert if nothing posts to the endpoint |

**Recommended, and the reason:** Path A, direct post, unless the website team already runs
middleware for another reason. It needs no credential, no External Id strategy and no second system
to monitor; the tree's own strategic default 3 ("prefer Named Credentials … over hardcoded
endpoints") is a constraint Path B imports and Path A never incurs. Path B's only real advantage —
transforming or enriching the payload before it lands — is not something any answered clarification
asks for.

**To confirm before UAT (Q66):** ask the website owner (a) which of the two paths the form uses
today, (b) if Path B, which system and whether it writes `Origin`, and (c) whether account or
entitlement data arrives from a billing system, which is the other half of Q66 and bears on
`M4-S02`'s entitlement design rather than on this step.

## 3. The decision tree has no Web-to-Case branch — recorded, not worked around

`plan.json` `steps[M3-S03].decision_trees[]` declares
`standards/decision-trees/integration-pattern-selection.md`. Read in full, that tree routes between
REST, REST Composite, Bulk API 2.0, custom `@RestResource`, Platform Events, CDC, Pub/Sub,
Salesforce Connect and MuleSoft. `grep -i "web-to\|webtocase\|html form\|web form"` over it returns
**nothing**. There is no branch for a native HTML form posting to a Salesforce-hosted intake
endpoint, which is what Path A is.

This step therefore cites the tree for **Path B only** — Direction 2 ("External writes into
Salesforce"), Q5 `< 1k rows/day → REST API`, and Q9 `Yes, plain CRUD → Standard REST on sObject` —
and records that Path A was **not** routed by the tree, because the tree cannot route it. Path A's
grounding is `case-management-setup/references/metadata-examples.md` § 4, which documents the
direct-post form as the native path. Per `AGENT_RULES.md`, a technology recommendation without a
tree branch is a gap to record rather than a branch to invent: this is that record, and closing it
means adding a "native platform intake endpoint (Web-to-Case / Web-to-Lead / Email-to-Case)" leaf to
Direction 2 of the tree.

## 4. `defaultResponseTemplate` is deliberately unset

The third child of `webToCase` is absent on purpose. The guide scopes it to "email responses to cases
that are submitted through a **Self-Service portal**" (api_meta L112128 ff.), and the Self-Service
portal has not been available to new orgs since Spring '12. It is **not** the customer
acknowledgement. The acknowledgement is an `AutoResponseRules` entry that fires only when the
assignment rule fires (`case-management-setup/references/gotchas.md` #1) — M3-S04's element, using
M3-S02's `case_intake/Case_Acknowledgement` template, with its sender held open as an M3 gate
decision (`decisions.md` D-M3S02-04). Setting `defaultResponseTemplate` here would make this step
look like it had answered the acknowledgement question, and it has not.

`check_case_management_setup.py` agrees: setting it prints a NOTE saying the guide scopes it to
Self-Service portal responses, not the acknowledgement.

## 5. The record type a web case lands on — an open gap, not a configured value

`WebToCaseSettings` carries no record-type element, and `keepRecordTypeOnAssignmentRule` (set `true`
in this file for Q24's ~20 manual cases a day) explicitly does **not** cover Web-to-Case: its scope
is "manually created records" (`case-management-setup/references/gotchas.md` #9). The gotcha's
remedy for the web channel is "set the record type deterministically in a before-save
record-triggered Flow keyed on `Origin`, or accept the org default and make sure that default's
support process is the intake one".

Neither is in place: `M4-S03`'s before-save flow stamps `EntitlementId`, `BusinessHoursId` and
`Priority`, not `RecordTypeId`, and this build sets no org default record type. So a web case lands
on whatever the submitting context's default Case record type is — possibly `Billing`, whose
`Billing_Process` has no `Escalated` state, which would silently break the 8-business-hour
escalation for that case. Recorded in `deploy-order.md` § "Ungrounded and open" and in
`email-to-case-routing-addresses.md` § 9.1, which is the same gap on the email side.

## 6. The form itself — skeleton only, and where the real one comes from

**Do not hand-write the endpoint or the org id.** `case-management-setup/references/metadata-examples.md`
§ 4 marks the whole shape UNVERIFIED (2026-09-05): the Setup path that generates the snippet, the
hidden field names it emits (`orgid`/`oid`, `retURL`, `recordType`, `debug`), the endpoint it posts
to and the reCAPTCHA option "are documented only on help.salesforce.com, which cannot be fetched",
and the skeleton there "is shaped by analogy with the Web-to-Lead form" and "must be replaced by the
snippet the target org's Setup page actually generates before it is used".

The skeleton below is reproduced from that reference with this build's values substituted into the
two inputs whose values this build does own. It is a **contract for the website team**, not a
deliverable of this build, and it is not a file in `artefacts/` for exactly that reason.

```html
<!-- SKELETON ONLY - replace with the snippet Setup generates for YOUR org. -->
<form action="[ENDPOINT FROM SETUP]" method="POST">
  <input type="hidden" name="orgid"  value="[ORG ID FROM SETUP]">
  <input type="hidden" name="retURL" value="https://www.acme.example/support/thank-you">
  <!-- origin: OMIT this input and let CaseSettings.webToCase.caseOrigin stamp "Web". -->
  <!-- If it is sent, the only legal value in this org is an active CaseOrigin value: -->
  <!-- Web, Email-Support or Email-Billing (artefacts/M1-S01/standardValueSets/CaseOrigin...). -->
  <!-- Sending Email-Support or Email-Billing from the web form would make a web case -->
  <!-- indistinguishable from an email case to M3-S04's assignment rule. Send "Web" or nothing. -->
  <input type="hidden" name="origin" value="Web">
  <!-- priority: DO NOT send one. See section 7. -->
  <label for="name">Name</label>      <input id="name"     name="name"     type="text"  required>
  <label for="email">Email</label>    <input id="email"    name="email"    type="email" required>
  <label for="subject">Subject</label><input id="subject"  name="subject"  type="text"  required>
  <label for="description">Details</label><textarea id="description" name="description" required></textarea>
  <input type="submit" value="Submit">
</form>
```

Field-level notes the website team needs:

- **`retURL`** is the page the submitter is returned to. It is the only success signal they get —
  see § 8 on why that matters.
- **Required-on-layout does not apply here.** Q5's answer: "Priority and Origin enforced at field or
  validation-rule level, because Web-to-Case and Email-to-Case create Cases through the API, not
  through a layout." The form's own `required` attributes are the only client-side enforcement, and
  `M3-S01`'s validation rules are the server-side one.
- **Anything the form collects that is not a Case field is dropped silently.** There is no mapping
  layer in Web-to-Case; the input name has to be the Case field.

## 7. Priority — the form must not send one

The reference skeleton offers a `priority` input. **This build's answer is not to send it.** The
requirement says "priority must be set from what the form or email tells us" (Q16), and `M4-S03`'s
before-save flow owns the Priority default, "guarded so it writes only into a null value" — a
`priority` input on the form makes the field non-null at insert and the guard never fires. Neither
this step's `settings/Case.settings-meta.xml` nor the two Email-to-Case routing addresses set a
priority either, for the same reason
(`email-to-case-routing-addresses.md` § 1).

**Open, and a real gap:** no answered clarification states which `CasePriority` value each channel
should end up with, and no `CasePriority` standard value set exists anywhere under `artefacts/`, so
a value sent by the form could not be validated against the org's picklist by any checker in this
build. If the business does want the submitter to choose a priority, that is a change to `M4-S03`'s
flow design and a `CasePriority` value set this build does not yet carry — not a hidden input added
to the form. Recorded in `deploy-order.md` § "Ungrounded and open".

## 8. The two failure modes the website team cannot see

**A dropped submission still shows the success page.** `case-management-setup/references/gotchas.md`
#4 — the Web-to-Case overflow signal exists but "it stops after five emails", so a sustained
overflow is silent after the fifth notification while the form keeps returning `retURL`. The cheap
detection is a **missing day** on the web row of the per-origin count query in
`case-management-setup/references/metadata-examples.md` § 6:

```sql
SELECT DAY_ONLY(CreatedDate) day, Origin, COUNT(Id) cases
FROM Case
WHERE CreatedDate = LAST_N_DAYS:14
GROUP BY DAY_ONLY(CreatedDate), Origin
ORDER BY DAY_ONLY(CreatedDate) DESC
```

A `null` Origin row means the default is not being applied — check `webToCase.caseOrigin`. At
~60 submissions a day (Q15) a missing day is unambiguous.

**A deployed `Case.Origin` value is invisible on a record type until someone edits it in Setup.**
`case-management-setup/references/gotchas.md` #7 and the guide's own note on `standardValue`: "new
picklist values loaded into your organization through the Metadata API don't display in the picklist
UI by default. For users to see the new values, go to the Record Types list for the object
containing the picklist field, click Edit, and add the new value to the Selected Fields list."
`artefacts/M1-S01/objects/Case/recordTypes/Support.recordType-meta.xml` already lists `Web` under
its `Origin` `picklistValues`, which covers the `Support` record type; confirm the same for any
record type a web case can land on once § 5 is settled.

## 9. Sandbox and refresh — Q74

"The Email-to-Case routing addresses and **the website form endpoint** must be re-pointed on every
refresh, or the sandbox will answer real customer mail." The form endpoint carries the org id, so a
production form posts into production whatever the sandbox is configured to do. The website
repository therefore needs its endpoint and org id as **configuration, not as a literal** in the
page, so a sandbox build of the site can point at the sandbox. That is a requirement on the
website's repository, and this file is where this build states it. `M5-S02`, the sandbox proof plan,
is `blocked`, so nothing else currently owns it.
