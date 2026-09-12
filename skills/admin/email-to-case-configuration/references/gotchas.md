# Gotchas — Email-to-Case Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Routing Address Verification is a Hard Blocker

**What happens:** After creating a routing address and configuring the mail server forwarding rule, inbound emails arrive at the Salesforce-generated address but no cases are created. The mail server logs show successful delivery; Salesforce shows nothing.

**When it occurs:** Any time a routing address has not been verified. Salesforce will not process inbound email for an unverified routing address even if delivery is confirmed at the network level. The verification requirement is enforced silently — there is no error in the UI or in the email headers to indicate the cause.

**How to avoid:** After creating a routing address, always click "Send Verification Email" immediately. Open the Salesforce-generated inbox (which requires the forwarding rule to be active first), click the verification link, and confirm the status shows "Verified" in the routing address record before testing case creation. Document the verification date in the org runbook.

---

## Gotcha 2: The On-Demand Size Limit Is a 35 MB Total, and MIME Encoding Eats a Third of It

**What happens:** An inbound email is silently dropped and no case is created. The support team was told the limit is 25 MB, the customer's attachment was 24 MB, and everyone concludes Email-to-Case is broken. In fact Salesforce enforces the limit on the *total* redirected message — body + attachments + HTML — at 35 MB, and MIME transfer encoding inflates the payload by up to 33% between the sender's outbox and the routing address. A 27 MB set of attachments can arrive as 36 MB and be rejected. There is no in-Salesforce error record for the rejection.

**When it occurs:** On-Demand mode, at the routing address, before any Apex or assignment logic runs. Standard Email-to-Case receives at the company's own mail server, so its first size gate is whatever that server is configured to allow.

**How to avoid:** Publish the honest figure — 35 MB total message, roughly 25 MB of usable attachment payload — rather than a per-attachment cap, because Salesforce does not document one. If large attachments are a genuine business requirement, put a Salesforce Files or portal upload link in the auto-response template rather than switching modes. Beware of stale numbers: 25 MB was the org-wide total before Winter '21 and 10 MB before Summer '14, so any source quoting those as current is out of date.

---

## Gotcha 3: Auto-Response Email Loops When From Address Matches Routing Address

**What happens:** After configuring an auto-response rule, cases begin appearing in the org at an abnormal rate. Investigation reveals that each case creates an auto-response email, the customer's inbox receives it and bounces or forwards it, and the routing address receives the bounce/forward and creates another case.

**When it occurs:** When the auto-response rule entry's sender ("From") email address is the same as or forwards to the Email-to-Case routing address. The most common cause: the admin copies the support address (`support@company.com`) into the auto-response rule "From" field, and the company mail server has a blanket forwarding rule for all mail arriving at `support@company.com`.

**How to avoid:** Always use a dedicated no-reply address (e.g., `no-reply@company.com`) as the From address for auto-response rule entries. Confirm this address does not forward to any Email-to-Case routing address. Test auto-response by sending a single inbound email and monitoring the Case count for 5 minutes to confirm it does not grow.

---

## Gotcha 4: Security Gateway Token Stripping Breaks Threading Silently

**What happens:** Threading works in sandbox or direct SMTP tests but fails in production. Customer replies consistently create new cases instead of adding Email Messages to the original case. The Lightning thread token (the `[ref:...:ref]` suffix in the subject and the reference string in the body) is present in emails sent from Salesforce but absent in the replies received.

**When it occurs:** Corporate email security gateways (Proofpoint, Mimecast, Barracuda, Microsoft Defender for Office 365) perform link rewriting and content modification on inbound and outbound email. Some configurations strip or rewrite the thread token strings as part of safe-link processing or content normalization. Because sandbox tests often bypass the production gateway, the issue only surfaces in production.

**How to avoid:** Test the full round-trip through the production mail gateway before go-live. Send an email from Salesforce to an external inbox that goes through the production gateway. Reply to that email and confirm the reply threads correctly. If tokens are being stripped, work with the IT team to add Salesforce thread token patterns to the gateway's allowlist or exclusion rules. The thread token pattern (`ref:` followed by alphanumeric characters and `:ref`) is the signature to preserve.

---

## Gotcha 5: Standard Email-to-Case Agent API Call Consumption

**What happens:** In a high-volume environment using Standard Email-to-Case, the org's daily API call limit is exhausted before end of day. Other integrations and automations begin failing. Investigation reveals the Email-to-Case agent is responsible for a large share of the API consumption — each inbound email consumes one or more API calls.

**When it occurs:** Standard Email-to-Case only. The local agent uses the SOAP or REST API to create cases in Salesforce. Orgs receiving hundreds or thousands of emails per day may not account for this consumption when estimating daily API usage. On-Demand Email-to-Case does not use API calls — it uses Apex Email Services, which is outside the API call governor.

**How to avoid:** If the org expects high email volume, use On-Demand Email-to-Case. If Standard is required, estimate daily email volume and add it to the org's API call budget. Monitor API usage in Setup → Company Information → API Requests, Last 24 Hours.

---

## Gotcha 6: `caseOwner` on a Routing Address Writes an Org-Level Field, So the Last Address Wins

**What happens:** Two routing addresses are each given their own default owner — `support@` to the
Tier 1 queue, `billing@` to the Billing queue. After deploy, cases from *both* addresses land with
the Billing queue, or with whichever address was processed last.

**When it occurs:** Any time more than one `routingAddresses` element sets `caseOwner`. The Metadata
API guide states it plainly in the `caseOwner` field description: "Specifying a case owner here in
the routing address sets a value of `defaultCaseOwner` in `CaseSettings`" (api_meta L112010 ff.).
`defaultCaseOwner` is a single field on `CaseSettings`, not a per-address one, so the addresses are
writing to a shared slot. There is no warning at deploy and no error — the file is valid.

**How to avoid:** Set `caseOwner` on at most one routing address, or on none. Give each address a
distinct `caseOrigin` instead and let the case assignment rule pick the queue from `Case.Origin`
(`references/metadata-examples.md`, assignment rule example). Set the org-level `defaultCaseOwner`
and `defaultCaseOwnerType` once, deliberately, as the catch-all — which is what it is. When
`caseOwner` is set at all, `caseOwnerType` must be set alongside it or the owner is ambiguous.

---

## Gotcha 7: A Partial `Case.settings` Deploy Deletes the Routing Addresses It Omits

**What happens:** An admin edits the settings file to add a third channel, or a pipeline builds the
file from a template that only knows about the channels in scope for this release. The deploy
succeeds. The channels that were not in the file have stopped creating cases, and their configuration
is gone from the org — not disabled, deleted.

**When it occurs:** On any `Settings:Case` deploy. `routingAddresses` is a full-replacement list; the
guide's field description says "Removing an address from this list deletes it from the target org"
(api_meta L111726 ff.). Two related read-only fields make the damage hard to undo: `emailServicesAddress`
and `isVerified` "can't be modified", so re-adding the element does not restore the deleted
Salesforce-generated address or its verified state. The mail server's forwarding rule now points at
an address that no longer exists.

**How to avoid:** Always `sf project retrieve start --metadata "Settings:Case"` from the target org
immediately before editing, and deploy the retrieved file with your addition — never a
hand-assembled or template-generated subset. In a pipeline, diff the routing address count between
the retrieved file and the file about to deploy and fail the build when it drops. Keep the list of
public addresses and their forwarding targets in the org runbook, because the org will not hand them
back after a deletion.

---

## Gotcha 8: There Are Two Mutually Exclusive Threading Switch Pairs, and `ThreadIdentifier` Is Not One of Them

**What happens:** Threading is broken, someone turns on all four threading booleans "to be safe", and
nothing improves. Or a monitoring query is written that asserts `EmailMessage.ThreadIdentifier` is
populated, and it alerts on every single healthy Email-to-Case message in the org.

**When it occurs:** The four booleans are conditional on which threading mode the org is in.
`enableThreadTokenInBody` and `enableThreadTokenInSubject` are, per the guide, "applicable only to
orgs using Lightning Threading"; `enableThreadIDInBody` and `enableThreadIDInSubject` are "applicable
only to orgs that do not use Lightning Threading" (api_meta L111726 ff.). Setting the pair that does
not apply to your org changes nothing. Separately, `EmailMessage.ThreadIdentifier` sounds like the
threading field and is not: "This field is used by features that sync emails directly from an inbox
into Salesforce. This field is not used by On-Demand Email-to-Case" (object_reference L104638).
UNVERIFIED (2026-09-04): the Metadata API guide contains no element that switches an org between
Lightning and legacy threading — only these conditional booleans — so the org's mode has to be read
in Setup.

**How to avoid:** Establish which threading mode the org is in first, then set only that pair. Turn
on `useEmailHeadersForThreading`, described as using "metadata from incoming emails ... to match
replies with cases if token-based threading doesn't produce a match" — it is the second chance when a
gateway strips the token (Gotcha 4). Verify threading on `EmailMessage.ParentId`, never on
`ThreadIdentifier`; the query is in `references/metadata-examples.md`.

---

## Gotcha 9: `Discard` Means Discard — Rejected Mail Leaves No Record Anywhere in Salesforce

**What happens:** A customer insists they emailed support days ago. There is no case, no
EmailMessage, no error log, and no bounce in their sent folder. Nothing in Salesforce shows the
message ever arrived.

**When it occurs:** Two settings decide the fate of mail Salesforce declines to process, and both
accept a `Discard` value. `unauthorizedSenderAction` handles "email messages received from invalid
senders" — anything outside a populated `authorizedSenders` list — and accepts only `Bounce` or
`Discard`. `overEmailLimitAction` handles "email messages that are received after an organization
exceeds its daily Email-to-Case limits" and accepts `Bounce`, `Discard` or `Requeue` (api_meta
L111726 ff.). `Discard` is silent by design. The trap with `authorizedSenders` is that it is
populated at all: it is meant for a fixed internal sender list, and on a public support address it
turns every unknown customer into an invalid sender.
UNVERIFIED (2026-09-04): the numeric daily Email-to-Case limit is not in the Salesforce App Limits
Cheat Sheet (no Email-to-Case entry exists in it; the only adjacent figure is "Email services heap
size is 50 MB", salesforce_app_limits_cheatsheet L161) and is not in the Metadata API guide. Read it
from the org's own limits page rather than quoting a number.

**How to avoid:** On a public support address, leave `authorizedSenders` empty — the guide's
`EmailServicesAddress.AuthorizedSenders` equivalent says to "leave this field blank if you want the
email service address to receive email from any email address" (object_reference L105032 ff.). Use
`Requeue` for `overEmailLimitAction` so a limit spike delays mail rather than destroying it, and
`Bounce` for `unauthorizedSenderAction` so a rejected sender at least learns their message did not
arrive. Reserve `Discard` for an address under active spam attack, and write down when it was set.

---

## Gotcha 10: `enableE2CAttachmentAsFile` Moves Attachments to a Different Object

**What happens:** After the setting is flipped, inbound attachments stop appearing where the
existing report, list view, or Apex expected them. Automation querying `Attachment` returns nothing;
the case looks empty to a process that was working yesterday.

**When it occurs:** `enableE2CAttachmentAsFile` "Indicates whether to save attachments sent using
Email-to-Case as Salesforce Files (`true`) or not (`false`)" (api_meta L111726 ff.). Files are
ContentDocument/ContentVersion records linked through ContentDocumentLink — a different object from
`Attachment`, with different sharing, a different related list, and a different query. A second
setting controls whether email attachments even show in the case Attachments related list:
`showEmailAttachmentsInCaseAttachmentsRL`, which when true "displays an email icon next to each
attachment from an email in the Attachments related list for cases" and adds a Source column
(api_meta, CaseSettings fields). A third, `enableE2CDeduplicateAttachments`, links an already-present
attachment to the new email instead of storing a second copy when a reply threads onto a case.

**How to avoid:** Decide Files vs Attachments before go-live, not after, and inventory what reads
attachments — reports, list views, Apex, integrations, the agent's page layout — before flipping the
switch. The Files direction is the one to pick for a new org; the migration cost is paid by orgs that
switch later. `admin/case-feed-send-email-action` covers the outbound side's own file limits.

---

## Gotcha 11: `notifyOwnerOnNewCaseEmail` With a Queue Owner Emails a Team, on Every Reply

**What happens:** A support team asks why they each get several near-identical emails per case, and
starts filtering Salesforce mail to a folder nobody opens — including the escalation notices that
matter.

**When it occurs:** `notifyOwnerOnNewCaseEmail` "Indicates whether the owner of a case receives a
notification when a new email related to the case is received" (api_meta L111726 ff.). It fires per
inbound email, not per case, so a chatty thread notifies repeatedly. When cases are routed to a queue
— the normal design — the "owner" is the queue, and queue notification has its own two independent
switches: `email` (a shared address) and `doesSendEmailToMembers` (each member individually), mapped
in `admin/queues-and-public-groups` → `references/queue-behaviour-matrix.md`. On top of those sit the
assignment rule entry's own notification template and any Flow email alert on case create.
UNVERIFIED (2026-09-04): whether `notifyOwnerOnNewCaseEmail` fans out to individual queue members or
only to the queue address is not stated in the Metadata API guide; test in a sandbox before enabling
it on a queue-owned channel.

**How to avoid:** Pick one notification channel per team and switch the rest off. For queue-owned
Email-to-Case, that is usually the queue's shared address with `doesSendEmailToMembers` false and
`notifyOwnerOnNewCaseEmail` false, with agents working the queue list view or Omni-Channel instead of
their inbox. Count the emails a single new case generates during the sandbox test — three is common
and nobody designed it.

---

## Gotcha 12: `saveEmailHeaders` Cannot Be Turned On Retroactively

**What happens:** A phishing or spoofing incident arrives through the support address. The security
team asks for the originating IP, the SPF/DKIM result and the delivery path of the offending message.
The EmailMessage record has a From address and a body, and nothing else — the evidence was never
stored, and no setting change now recovers it.

**When it occurs:** `saveEmailHeaders` is a per-routing-address boolean: "Indicates whether email
routing and envelope information are saved (`true`) or not (`false`)" (api_meta L112010 ff.). It
governs what is captured at the moment the message is processed. The receiving field,
`EmailMessage.Headers`, is "The Internet message headers of the incoming email. Used for debugging
and tracing purposes. Doesn't apply to outgoing emails" (object_reference L104260) — inbound only, so
an outbound-side investigation has no equivalent.

**How to avoid:** Set `saveEmailHeaders` true on every Email-to-Case routing address at creation
time; the storage cost is trivial against one unanswerable security question. It is in the deployable
file, so it is reviewable in a pull request rather than being an unowned Setup checkbox. Note that
headers may carry personal data — include `EmailMessage.Headers` in the org's retention and data
subject request handling rather than leaving it out of scope.

---

## Gotcha 13: `isPermsetControlled` Locks the Address Behind Grants That Are a Separate Metadata Type

**What happens:** Permission-set control is enabled on a routing address to stop agents sending as
`billing@`. Every agent, including the billing team, loses that From address in the email composer.

**When it occurs:** `isPermsetControlled`, available in API version 61.0 and later, "Indicates
whether users' access to the email routing address is controlled by a permission set. If `true`, only
users with access via a permission set can use the routing address to send emails" (api_meta L112010
ff.). It is deny-by-default: flipping it grants nobody. The grant lives in a different type — the
Object Reference lists `EmailRoutingAddress` as a valid `SetupEntityAccess.SetupEntityType` "In API
version 62.0 and later" (object_reference L261687), so the permission set entries and the setting are
two separate pieces of metadata that must deploy together.

**How to avoid:** Deploy the permission set grants first, or in the same deploy, and only then set
`isPermsetControlled` true. Because the type is API 62.0+, the manifest must be on API 62.0 or later
or the grants will not deploy at all. Verify by having a member of the intended group open the case
email composer and confirm the address is in the From picklist — `EmailMessage.ValidatedFromAddress`
is the picklist of "the sender's address, org-wide email addresses, or Email-to-Case routing address"
and "the email address must be verified" (object_reference L104682). Permission set design itself is
`admin/permission-set-architecture`.

---

## Gotcha 14: `newEntityRecordType` Is Version-Gated and Object-Qualified, and the Guide Says Neither

**What happens:** A routing address is given the intake record type the design calls for —
`<newEntityRecordType>Support</newEntityRecordType>` — and the deploy fails twice, for two different
reasons, neither of which is written down in the field's guide entry. First the API version:
`Property 'newEntityRecordType' not valid in version 63.0`. Raise the manifest and the second one
lands: `In field: newEntityRecordType - no RecordType named Support found` — with a record type
named `Support`, active on Case, sitting in the same deployment.

**When it occurs:** The Metadata API Developer Guide entry for
`EmailToCaseRoutingAddress.newEntityRecordType` (api_meta L112078) is three sentences long: it
"Sets the Case Record Type used for new Cases that are created from emails sent to that specific
routing address", falls back to "the org's default Case Record Type for the user/context handling
Email-to-Case" when absent, and asks you to "Ensure the record type exists and is active on Case".
It carries no "Available in API version N and later" line, even though `fallbackQueue` (56.0) and
`isPermsetControlled` (61.0) — two fields away in the same table — both do, and it states no value
format. Two dry-run deploys (`checkOnly`, 2026-09-12) settle both:

- **Version gate.** The identical file is rejected at API 62.0 *and* 63.0 with
  `Property 'newEntityRecordType' not valid in version 63.0`, and accepted at 64.0. The error is a
  property-validation error, so it fires before anything looks at the record type at all — which is
  why the second failure only surfaces once the version is right.
- **Value format.** The bare developer name never resolves. `Case.Support` does. The guide's
  instruction to "ensure the record type exists and is active" is true and insufficient: existing
  and active is exactly the state in which the bare form still fails.

UNVERIFIED (2026-09-12): both behaviours are observed live, not documented. The guide edition read
here is v62 (`api_meta.pdf`, Spring '25 / API 63.0 era); a later edition may add the version note.
Re-read the field entry before quoting the gate as permanent.

**How to avoid:** Write the value as `Case.<DeveloperName>` and pin the `package.xml`
`<version>` to 64.0 or later in the same change — the version that travels with the deploy is the
one the property check reads, not the project's `sourceApiVersion`. `E2C-RT-01` and `E2C-RT-02` in
`scripts/check_email_to_case_configuration.py` catch both before the org does; `E2C-RT-02`
deliberately reads every `package.xml` under the manifest tree, because the failing manifest is
usually not the one being edited. If the org must stay below 64.0, drop the element and set the
record type in a before-save record-triggered Flow keyed on `Origin` instead — but do not expect
`keepRecordTypeOnAssignmentRule` to hold it, which is a different trap
(`admin/case-management-setup` → `references/gotchas.md` #9).

---

## Gotcha 15: `casePriority` Is Required by the Org and Optional in the Guide, and It Pre-empts Your Priority Automation

**What happens:** A routing address is authored from the field list with everything the design
needs — origin, owner strategy, threading, headers — and the deploy fails on a field nobody thought
was mandatory: `EmailToCaseRoutingAddress[support@acme.example]: Missing casePriority`. It is
supplied to clear the error, and a second, quieter problem starts: the before-save Flow that was
supposed to derive `Priority` from the account's support tier never runs its logic, because its
entry condition is `Priority` is null and `Priority` is never null on this channel again.

**When it occurs:** The guide's entry is one sentence — `casePriority` "Specifies the default case
priority for cases created through this routing address" (api_meta L112039) — with no Required
marker and nothing about deploy-time validation. The org disagrees: a `checkOnly` deploy of a
routing address with no `casePriority` is rejected (dry-run, API 67.0, 2026-09-12). Supporting but
not conclusive: the guide's own `CaseSettings` sample sets `casePriority` on **both** of its routing
addresses, `Medium` and `High` (api_meta L112187, L112200) — every field in a sample is a choice,
not a requirement, so the sample is consistent with the requirement rather than evidence of it.
UNVERIFIED (2026-09-12): required-ness proven live, absent from the guide.

The design consequence outlives the deploy error. Because the address always stamps a priority,
every Email-to-Case case is created with `Priority` populated, at the value on the address, before
any assignment rule or record-triggered automation sees it. Three patterns break on that:

- a null-guarded stamp (`Priority` is blank → set it) that silently never fires on email cases;
- an SLA or entitlement milestone keyed to `Priority`, which now starts on the address's default
  tier rather than the derived one;
- a report that reads `Priority` distribution as customer-reported urgency, when for this channel
  it is a constant.

**How to avoid:** Set `casePriority` deliberately per channel — it is the channel's declared
starting tier, not a placeholder — and pick the value the business would accept if nothing else ran.
Then decide explicitly whether anything downstream is allowed to change it: if priority is derived,
derive it unconditionally (from account tier, keyword, or entitlement) rather than on a null guard,
and document which source wins. `E2C-PRI-01` in `scripts/check_email_to_case_configuration.py`
errors on a missing `casePriority`. Verify with the origin/priority query in
`references/metadata-examples.md` § Verification 2: group a day of cases by `Origin` and `Priority`
and confirm the email channels show the distribution the design intended, not a single constant you
did not choose.
