# Email-to-Case routing addresses — M3-S03

Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was deployed.

> **REBUILT 2026-09-12 (run `2026-09-12T04-39-20Z`).** The as-built file failed the operator's
> validate-only run against the org (`sf project deploy start --dry-run`, `checkOnly: true`; run 5 of
> `reports/MOCK-DEPLOY-M3.md`). Three elements were added and the manifest's API version was raised:
> **F-25** `systemUserEmail`, **F-26** `newEntityRecordType` on both routing addresses, **F-27**
> `casePriority` on both routing addresses, and `package.xml` `<version>` `62.0` → `67.0`. Each
> change is marked below where it lands. The F-27 consequence for `M4-S03` is the one a reader of
> this file must not miss — see § 1.
Every element named below is copied from
`skills/admin/email-to-case-configuration/references/metadata-examples.md` (the `emailToCase`
block and its `routingAddresses` children) or
`skills/admin/case-management-setup/references/metadata-examples.md` § 3 (the org-level
`CaseSettings` fields). The one deployable file is
[`settings/Case.settings-meta.xml`](./settings/Case.settings-meta.xml) — Email-to-Case is not its
own metadata type, it is the `emailToCase` block inside `CaseSettings`, deployed as the `Settings`
member `Case`.

## 1. The two addresses as deployed

| `routingName` | `emailAddress` | `caseOrigin` | `newEntityRecordType` | `casePriority` | `saveEmailHeaders` | `caseOwner` | Queue that actually owns the case |
|---|---|---|---|---|---|---|---|
| `ACME General Support` | `support@acme.example` | `Email-Support` | `Case.Support` | `Medium` | `true` | **unset** | `Tier_1_General`, via the M3-S04 assignment rule on `Case.Origin` |
| `ACME Billing` | `billing@acme.example` | `Email-Billing` | `Case.Billing` | `Medium` | `true` | **unset** | `Billing`, via the same rule |

`newEntityRecordType` (**F-26**) and `casePriority` (**F-27**) are new in the 2026-09-12 rebuild; both
were absent from the as-built file. § 9.1 carries the record-type write-up and the paragraph below
carries the priority one.

Both `caseOrigin` values are live entries in
`artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml`
(`Email-Support`, `Email-Billing`, `Web`) — answer **Q19**. `caseOrigin` is the only per-address
value an assignment rule can read: there is no routing-address field on `Case` at all, the routing
address is recorded one object over on `EmailMessage.EmailRoutingAddressId`
(`email-to-case-configuration/references/metadata-examples.md`, "Which Case field the routing
address populates"). So `Case.Origin` is the hand-off to M3-S04, and the two queue names above are
M3-S04's to write, not this step's.

**`caseOwner` is deliberately unset on both** — answer **Q18**, and gotcha 6 of the same skill:
"Specifying a case owner here in the routing address sets a value of `defaultCaseOwner` in
`CaseSettings`" (api_meta L112010 ff.), and `defaultCaseOwner` is a single org-level field, so a
second address setting `caseOwner` silently overwrites the first. Ownership is expressed once, per
channel, in the assignment rule. `caseOwnerType` is therefore also absent (the two travel together
or the owner is ambiguous).

**`casePriority` is `Medium` on both — and this is the rebuild's one behavioural change (F-27).**

It was deliberately unset in the as-built file, for the reason set out below. The org refused that
file: the validate-only run returned `EmailToCaseRoutingAddress[support@acme.example]: Missing
casePriority` (and the same for `billing@`), so the element is **required in practice** on this org's
API version. The Metadata API guide does not say so — `casePriority` is described only as
"Specifies the default case priority for cases created through this routing address" (api_meta
L112039), with no required marker. **UNVERIFIED-in-guide / proven-live (2026-09-12):** the
requirement is an observed org behaviour on the validate-only path, not a documented one; a future
org or API version may not enforce it. The value `Medium` is the one the skill's own worked example
carries (`email-to-case-configuration/references/metadata-examples.md` lines 50 and 59), so nothing
was invented — but the *choice* of `Medium` is a skill default, not an answered clarification.

**Consequence for `M4-S03`, and it is not a footnote.** Every email-originated Case now arrives with
`Priority` already populated (`Medium`). `M4-S03`'s before-save flow is specified to stamp
`Case.EntitlementId`, `Case.BusinessHoursId` and `Case.Priority` "each guarded so it writes only into
a null value" — **that guard will never fire for an email-originated case**, because the field is no
longer null at insert. Three ways forward, and the M3 gate should pick one rather than let M4-S03
discover it:

1. **Derive and overwrite** (recommended by this note): M4-S03 derives Priority from `Severity__c` /
   `Support_Tier__c` and **overwrites** the intake default instead of guarding on null. The guard
   moves from "is Priority null" to "did the derivation produce a value".
2. **Accept `Medium`** as the intake priority for the email channel and let M4-S03 leave a populated
   Priority alone. Q16 ("priority must be set from what the form or email tells us") is then only
   partly met on the email channel.
3. **Split the two channels' defaults** — a different `casePriority` per address — which this build
   has no answered clarification to choose values for.

**Web-to-Case has no such setting.** `WebToCaseSettings` carries no priority element (three children,
api_meta L112128 ff.), so a web-originated Case still arrives with `Priority` blank and M4-S03's
null guard still fires for it. The two intake channels therefore no longer behave the same way, and
`M3-S01`'s `Priority_Required_On_Agent_Save` + `Bypass_Case_Intake_Validation` is now load-bearing
for the **web** channel only. **Open:** no clarification states which `CasePriority` value each
channel should end up with, and no `CasePriority` standard value set exists under `artefacts/` to
validate `Medium` against — the org accepted it at validate time, which is evidence the value exists
in that org's picklist and nothing more. See `deploy-order.md` § "Ungrounded and open".

## 2. The org-level fields these addresses depend on

| Element | Value | Where it comes from |
|---|---|---|
| `defaultCaseOwner` | `Tier_1_General` | the queue at `artefacts/M2-S04/queues/Tier_1_General.queue-meta.xml` (file stem = `fullName` = the member name); required by the checker, and by gotcha 8 — Web-to-Case has no owner field of its own |
| `defaultCaseOwnerType` | `Queue` | `defaultCaseOwner` without it is ambiguous; a `User` here would hide unrouted cases on one person's record set |
| `notifyDefaultCaseOwner` | `true` | gotcha 8 of `case-management-setup`, verbatim: set the queue fallback "then make the fallback loud with `notifyDefaultCaseOwner`". This fires on a **routing failure** — a case no assignment-rule entry matched — not on routine queue work, which is why it does not contradict Q88 ("Tier 1 uses Omni-Channel push, so no queue email"). See § 9 for the tension and the two UNVERIFIED parts |
| `useSystemUserAsDefaultCaseUser` | `true`, with `defaultCaseUser` omitted | the guide requires `defaultCaseUser` only when this is `false`. This build creates no `User` metadata, so any username written here would have to resolve by name in the target org against a user nobody in this build provisioned. Consequence: Case History attributes automated changes to the system user rather than a named automation user, which is the readability the skill recommends — revisit once an automation user exists |
| `systemUserEmail` | `support-noreply@acme.example` | **F-25, new in the 2026-09-12 rebuild.** The org rejected the as-built file with `CaseSettings: Enter the system user's email address` — `useSystemUserAsDefaultCaseUser` `true` and no `systemUserEmail` is not a deployable pair on this org. The guide's own description: "Specifies the email address used when the default case user is the system user" (api_meta L111871). **Not carried by either cited skill's element inventory** — neither `email-to-case-configuration` nor `case-management-setup` names it anywhere, which is why the as-built file omitted it; it reached this build from the org's error plus the operator's api_meta quote. Skill-deepening signal, recorded in `deploy-order.md` § 5 |

## 3. What no artefact of this step sets: the acknowledgement sender

`decisions.md` **D-M3S02-04** holds the acknowledgement-sender question open as an **M3
milestone-gate decision**: `plan.json` Q22 says `support@acme.example` itself sends the
acknowledgement, `answers-key.md` says the sender is "never the Email-to-Case routing address
itself", and both cited skills' prohibitions bite only under Q22's reading.

**This step does not pre-empt it, and cannot.** `EmailToCaseRoutingAddress`'s element set carries
no sender, From, reply-to or sender-name field. The fullest enumeration the two cited skills carry
is `email-to-case-configuration/references/well-architected.md` line 39, which lists the per-address
fields as `caseOwner`, `emailServicesAddress` and `isVerified` (both read-only), `saveEmailHeaders`,
`authorizedSenders`, `createTask` / `taskStatus`, `addressType` (`EmailToCase` / `Outlook`),
`isPermsetControlled` (API 61.0+), `routingFlow` and `fallbackQueue` (API 56.0+) and
`newEntityRecordType` — plus `routingName`, `emailAddress`, `caseOrigin`, `casePriority` and
`caseOwnerType` from the worked example. Not one of them is a sender, so nothing written above
expresses one. `emailAddress` here is the **inbound** address customer
mail arrives at, which is precisely the row `artefacts/M3-S02/sender-identity-note.md`'s opening table assigns
to this step ("Inbound routing addresses → `CaseSettings` → `emailToCase.routingAddresses.emailAddress`
→ **M3-S03**"). The sender is `AutoResponseRules` → `ruleEntry.senderEmail`, and that is M3-S04's
element and the M3 gate's decision.

**`systemUserEmail` (F-25) does not change that, and must not be read as the acknowledgement
sender.** It is not a routing address and not a From address: the guide scopes it to "the email
address used when the default case user is the system user" (api_meta L111871) — the identity
attached to the *default case user* when `useSystemUserAsDefaultCaseUser` is `true`, which is an
ownership/attribution field, not a channel sender. `EmailToCaseRoutingAddress` still carries no
sender element of any kind, and `AutoResponseRules` → `ruleEntry.senderEmail` is still the only place
a customer-facing sender is expressed — M3-S04's element, and D-M3S02-04's decision at the M3 gate.
**So this rebuild does not pre-empt D-M3S02-04.** The value written,
`support-noreply@acme.example`, was chosen to be visibly *not* one of the two inbound routing
addresses precisely so no later reader mistakes it for the acknowledgement sender, and so it cannot
be an inbound-loop source (gotcha 3). It is an unprovisioned address in this build: confirm it exists
and is monitored, or replace it, before deploying to any org where it matters.

The two sender-adjacent switches that *do* exist stay unset for exactly the same reason as before —
the rebuild changed neither of them:

- **`useSystemEmailAddress`** (org-level) decides whether case comment / attachment / assignment
  notifications appear to come from a system address or from "the user or contact who is updating
  the case". It is omitted, so the org's existing value stands. Per D-M3S02-04 this build's
  recommended reading is the non-routing sender, and `useSystemEmailAddress` is the one org-level
  lever in this file that reads on that axis — it belongs in the same gate decision, not in a
  routing step.
- **`isPermsetControlled`** (per address, API 61.0+) restricts which users may *send from* a
  routing address. The requirement's "replies to customers go from support@ for general cases and
  from billing@ for finance cases" is an agent send-as rule, and gotcha 13 records that the switch
  is deny-by-default and that the grant lives in a different metadata type
  (`SetupEntityAccess`, entity type `EmailRoutingAddress`). Enabling it here would remove both
  addresses from every agent's composer until grants no step in this build declares are deployed.
  Left unset; the send-as design belongs with the M3 sender decision.

## 4. Refused mail, and why `Bounce` is currently inert

| Element | Value | Grounding |
|---|---|---|
| `unauthorizedSenderAction` | `Bounce` | Q21. Accepts `Bounce` or `Discard` only — no `Requeue` |
| `overEmailLimitAction` | `Requeue` | Q21. A limit spike delays mail rather than destroying it |
| `authorizedSenders` | **omitted (empty)** on both addresses | a per-address field (`well-architected.md` line 39; the checker reads it off the routing address at `check_email_to_case_configuration.py:305`). gotcha 9: on a public support address the list "turns every unknown customer into an invalid sender", and the guide's `EmailServicesAddress.AuthorizedSenders` equivalent says to "leave this field blank if you want the email service address to receive email from any email address" |

`unauthorizedSenderAction` only ever fires against a sender outside `authorizedSenders`, and that
list is empty on both addresses, so the `Bounce` value is a **recorded intent that nothing
currently triggers**. It is set anyway so that populating `authorizedSenders` later cannot
silently inherit `Discard`. Q21's answer ("so refused mail leaves a trace") is satisfied on the
over-limit path, which is the one that can actually fire.

UNVERIFIED (2026-09-12, inherited from the skill): the numeric daily Email-to-Case limit is in
neither the Metadata API guide nor the Salesforce App Limits Cheat Sheet. At ~400 messages/day
(Q15) the over-limit path is unlikely to fire, but the number has to be read from the target org's
own limits page before anyone quotes it.

## 5. Threading — assumption A3, not a decided fact

Q20 ("Lightning Threading or legacy threading?") is **deferred**; assumption **A3** is "the org is
on Lightning Threading … and every customer-facing template still carries the visible thread token
as a belt-and-braces fallback", risk `medium`, and it lists `M3-S03` among its steps.

What that assumption bought this file:

- `enableThreadTokenInBody` `true` and `enableThreadTokenInSubject` `true` — the Lightning
  Threading pair.
- `enableThreadIDInBody` / `enableThreadIDInSubject` **absent** — the legacy pair. Gotcha 8: the
  two pairs are mutually exclusive and "setting the pair that does not apply to your org changes
  nothing", so turning all four on "to be safe" is the documented anti-pattern, not the safe play.
- `useEmailHeadersForThreading` `true` — the gateway fallback: "metadata from incoming emails is
  used to match replies with cases if token-based threading doesn't produce a match" (gotcha 4 is
  the case it covers, a security gateway stripping the token).

**If A3 is wrong, this file is wrong and only this file changes**: swap the token pair for the ID
pair, leave `useEmailHeadersForThreading` as it is, and rebuild M3-S03. There is no element in
`EmailToCaseSettings` that switches the org between the two modes — UNVERIFIED, per gotcha 8 — so
the mode must be read in Setup before the first deploy. Verify threading on
`EmailMessage.ParentId`, never on `EmailMessage.ThreadIdentifier`, which "is not used by On-Demand
Email-to-Case".

`M3-S02`'s `Case_Acknowledgement` template already carries the visible token
(`[ ref:{!Case.Thread_Id} ]` in its subject), which is the second half of A3 and answer Q64.

## 6. Mode and attachment handling

| Element | Value | Grounding |
|---|---|---|
| `enableEmailToCase` | `true` | the child of `emailToCase` is `enableEmailToCase`, not `enable`; a file written with `<enable>` deploys without turning the feature on. The guide adds: once enabled, Email-to-Case "can't be disabled" |
| `enableOnDemandEmailToCase` | `true` (On-Demand) | no clarification decides the mode. `skills/admin/case-management-setup/templates/case-management-setup-template.md` marks "On-Demand (recommended)", and Standard needs a locally hosted agent that nothing in `requirement.md` or the 97 clarifications mentions. Recorded as a **skill-documented default**, not an answered question |
| `enableE2CAttachmentAsFile` | `true` | gotcha 10: "The Files direction is the one to pick for a new org; the migration cost is paid by orgs that switch later." Greenfield per Q4 (no existing Cases). Consequence: inbound attachments are ContentDocument/ContentVersion, not `Attachment` — anything later written to read attachments must query Files |
| `enableE2CDeduplicateAttachments` | `true` | links an already-present attachment to the new email instead of storing a second copy when a reply threads onto an existing case |
| `notifyOwnerOnNewCaseEmail` | `false` | gotcha 11: it fires per inbound email, not per case, and on a queue-owned channel that is the whole team, repeatedly. Q88 has Tier 1 on Omni-Channel push and the queues at `artefacts/M2-S04/queues/` carry `doesSendEmailToMembers` `false` |

## 7. Forwarding and verification — the human runbook

Order matters: verification mail can only be read once forwarding works, and inbound mail is only
accepted once the address is verified. From
`email-to-case-configuration/references/metadata-examples.md`, "Forwarding and verification
checklist", narrowed to this build:

- [ ] `Case.Origin` contains `Email-Support`, `Email-Billing` and `Web` — deploy
      `StandardValueSet:CaseOrigin` (M1-S01) **before** this file.
- [ ] After deploying `Settings:Case`, open Setup → Email-to-Case and copy each address's
      Salesforce-generated `emailServicesAddress`. It is **read-only** and is not in the source
      file, so it cannot be predicted from this build.
- [ ] Mail server: **one** forwarding rule per channel — `support@acme.example` → *its own*
      `emailServicesAddress`, `billing@acme.example` → *its own*. One forwarder feeding both
      Salesforce addresses duplicates every case. Q17's answer accepted the one-rule-each default
      as an assumption and says to confirm with IT before go-live that neither mailbox has a
      second forwarding rule; IT owns both mailboxes.
- [ ] Disable any "keep a copy and auto-reply" rule on either forwarding mailbox — a mailbox
      auto-reply is a second sender that can loop back into the routing address (the same
      mechanism as gotcha 3, and the risk D-M3S02-04 is about).
- [ ] Setup → the routing address → **Send Verification Email**, then click the link in the
      forwarded mail. Re-open the address and confirm it reads Verified.
- [ ] Send one real email to each public address; confirm one Case per email with the expected
      `Origin` and owning queue.
- [ ] Confirm `EmailMessage.Headers` is inside the org's retention and data-subject-request scope
      (Q23, gotcha 12) — `saveEmailHeaders` captures at processing time and cannot be backfilled.

**`isVerified` and `emailServicesAddress` are read-only** (api_meta L112010 ff.: "This field value
is read-only and can't be modified"). They come back on retrieve and are ignored on deploy, so a
fresh org's addresses arrive **unverified no matter what this file says**, and no checker in this
build can assert otherwise. That is also why
`skills/admin/email-to-case-configuration/scripts/check_email_to_case_configuration.py` is not one
of this step's declared tests — see `plan.json` `steps[M3-S03].inputs.note`.

## 8. Two standing hazards for whoever deploys or refreshes this

**Gotcha 7 — a partial `Case.settings` deploy deletes the routing addresses it omits.**
`routingAddresses` is a full-replacement list: "Removing an address from this list deletes it from
the target org." Because `emailServicesAddress` and `isVerified` cannot be modified, re-adding the
element does **not** restore the deleted Salesforce-generated address or its verified state, and
the mail server's forwarding rule is then pointing at an address that no longer exists. This file
contains **exactly the two addresses in scope for this build**. Before deploying it to any org that
already has Email-to-Case configured, `sf project retrieve start --metadata "Settings:Case"` and
merge — never deploy this file as-is over a populated org.

**Q74 — sandbox refresh re-points nothing on its own.** "The Email-to-Case routing addresses and
the website form endpoint must be re-pointed on every refresh, or the sandbox will answer real
customer mail." A sandbox copy carries the addresses forward; the *forwarding rules on the real
mailboxes* are what decides where customer mail lands. After every refresh: confirm no production
forwarding rule points at a sandbox `emailServicesAddress`, and re-point the sandbox's own test
mailboxes deliberately. `M5-S02` (the sandbox proof plan) is `blocked`, so this hazard currently
has no owning step other than this note.

## 9. The two per-address fields the cited skills name but do not show a value for

One of them is now written (`newEntityRecordType`, F-26 — the value shape came from the org, not from
the skills) and one is still not (`fallbackQueue`). `agents/metadata-builder/AGENT.md` Step 5 rule 1
forbids writing a value this agent cannot copy from an inventory; § 9.1 records where the value that
was finally written came from, and § 9.2 records why the other one still cannot be.

### 9.1 `newEntityRecordType` — written in the rebuild (F-26), on an operator-proven value shape

`case-management-setup/references/gotchas.md` gotcha 9 is explicit: "For Email-to-Case, set
`newEntityRecordType` explicitly on every routing address (owned by
`admin/email-to-case-configuration`) rather than leaving it to the handling context's default." The
guide's own field description is quoted there: it "Sets the Case Record Type used for new Cases that
are created from emails sent to that specific routing address. If not provided, Salesforce uses the
org's default Case Record Type for the user/context handling Email-to-Case" (api_meta L112010 ff.).

What was missing until the rebuild was the **value format**. Neither cited skill shows
`newEntityRecordType` in an XML block, and a Case record type is referenced as a bare name
(`Support`) in some elements and as an object-qualified name (`Case.Support`) in others —
`artefacts/M1-S01/objects/Case/recordTypes/Support.recordType-meta.xml` carries
`<fullName>Support</fullName>` while `artefacts/M1-S01/package.xml` names the member `Case.Support`.
Writing the wrong one is a deploy failure, and the as-built run had no example to copy, so it wrote
nothing.

**The org settled it, and both candidate forms were actually tried** (operator, validate-only,
scratchpad copy — run 5 of `reports/MOCK-DEPLOY-M3.md`):

| Form written | Result against the org |
|---|---|
| `<newEntityRecordType>Support</newEntityRecordType>` | **fails** — `no RecordType named Support found` |
| `<newEntityRecordType>Case.Support</newEntityRecordType>` | **resolves** — 0 errors |

So the object-qualified form is what this file now carries: `Case.Support` on `support@` and
`Case.Billing` on `billing@`, placed immediately after `<caseOrigin>` on each address.

**There is a version gate on the element itself, and it is the reason `package.xml` moved.** The same
probe rejected the property at API **62.0** and **63.0** — `Property 'newEntityRecordType' not valid
in version 63.0` — and accepted it from **64.0**. The manifest is now `67.0` (the org's API version,
and the version `M4`'s Apex steps already target). **Any deploy of this build at below 64.0 fails on
this element**, which is a whole-build constraint, not a step-local one; `deploy-order.md` § 8 states
it for the human.

This closes ungrounded item 2 of the as-built `deploy-order.md` § 5 and delivers the mapping the
build wanted: `support@acme.example` → the `Support` record type (support process `Support_Process`,
the only ladder exposing `Escalated`) and `billing@acme.example` → the `Billing` record type
(`Billing_Process`, no `Escalated` state, "Tier 2 engineering is not the escalation target for a
finance query").

**What is still not covered, unchanged by this rebuild:**

- `keepRecordTypeOnAssignmentRule` `true` does **not** cover either inbound channel — gotcha 9's
  whole point is that its scope is "manually created records".
- `WebToCaseSettings` has no record-type element at all (three children, api_meta L112128 ff.).
- `newEntityRecordType` is absent from `plan.json` entirely — zero occurrences across all 22 steps.
- `M4-S03`'s before-save flow, which gotcha 9 names as the Web-to-Case remedy, stamps
  `EntitlementId`, `BusinessHoursId` and `Priority` — not `RecordTypeId`.

So **email** cases now land deterministically on `Support` / `Billing`, and **web** cases still land
on whatever the handling context's default Case record type is — possibly the wrong support process
and status ladder. **Recommended, and now narrowed to one channel:** a `RecordTypeId` assignment
keyed on `Origin` in `M4-S03`'s before-save flow for the web channel. That is the second thing this
rebuild hands M4-S03, alongside the Priority consequence in § 1. Verify per channel, never in
aggregate: group a day of created cases by `Origin` and `RecordTypeId` and confirm each channel lands
on exactly one record type.

**Skill-deepening signal (unchanged in kind, now with an answer attached).**
`case-management-setup` gotcha 9 instructs setting `newEntityRecordType` and neither cited skill shows
its value shape or its 64.0 version floor. Both facts are now known — object-qualified
`<Object>.<RecordType>`, API ≥ 64.0 — and both were learned from an org rather than from the library.
That is the clearest deepen-a-skill output of this step.

### 9.2 `fallbackQueue` — a possibly better mechanism than the shared org-level fallback

`well-architected.md` line 39 names `routingFlow` and `fallbackQueue` as per-address fields from API
56.0+, with no description, no example and no mention anywhere else in either skill. If
`fallbackQueue` is what its name suggests, it would give each channel its own unrouted-case
destination and remove this build's reliance on the single org-level `defaultCaseOwner` that gotcha 6
warns two addresses can fight over. Unverifiable from the files at hand; worth a skill-deepening pass
before the next org-connected build.

### 9.3 The `notifyDefaultCaseOwner` tension, stated plainly

Two UNVERIFIED parts sit behind the `true` in § 2:

1. `Tier_1_General.queue-meta.xml` carries no `<email>` element and `doesSendEmailToMembers` is
   `false`. Whether `notifyDefaultCaseOwner` then reaches individual queue members, the queue
   address, or nobody is not stated in the Metadata API guide — the same open question gotcha 11
   records for `notifyOwnerOnNewCaseEmail`. The setting may be inert in this org's configuration.
2. If it is **not** inert, Tier 1 receives email that Q88 says Tier 1 should not receive. The
   distinction this step relied on — routing-failure signal versus routine queue work — is this
   build's reading, not a documented one.

Either way the fallback should be rare: `M3-S04` owes the assignment rule a catch-all entry (gotcha 8:
"Give the assignment rule a catch-all entry so the fallback is never the routing mechanism"), and the
real monitor is the owner query in `case-management-setup/references/metadata-examples.md` § 6 — any
non-zero count of cases owned by the default owner is a routing gap. Tick or overturn this at the M3
gate.
