# Sender identity — M3-S02 (Classic case-intake email templates)

Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was
deployed, and **no artefact of this step sets a sender.** An `EmailTemplate` carries no
sender element at all — the element set in
`skills/admin/email-templates-and-alerts/references/metadata-and-sender-identity.md`
("Classic text template used by an auto-response rule") is `available`, `description`,
`encodingKey`, `name`, `style`, `subject`, `type`, `uiType`, and none of those is a From
address. This note is therefore the *record* of the sender decision, not its
implementation. The implementation is downstream:

| The sender that actually gets set | Element | Step that owns it |
|---|---|---|
| Acknowledgement From / Reply-To | `AutoResponseRules` → `ruleEntry.senderEmail`, `senderName`, `replyToEmail` | **M3-S04** |
| Inbound routing addresses | `CaseSettings` → `emailToCase.routingAddresses.emailAddress` | **M3-S03** |
| Escalation handover notice From | *none exists* — see § 3 | M4-S04 (consumer only) |

---

## 1. The org-wide address each template sends from

| Template | Org-wide address it sends from | Answer it comes from |
|---|---|---|
| `case_intake/Case_Acknowledgement` | **`support@acme.example`**, for **both** channels (Email-to-Case and Web-to-Case) | Q28, Q60, Q22 — and the answer key's "Acknowledgement" row |
| Agent replies on a general Support case | **`support@acme.example`** | Q60 "Reply identity"; answer key "Reply identity" row |
| Agent replies on a **finance** case | **`billing@acme.example`** | Q60 "Reply identity": "billing@ replies from billing@" |
| `case_intake/Case_Escalated_To_Tier2` | **no sender is set by any artefact of this build** — see § 3 | — |

Both addresses in the step's `senders` input are covered: `support@acme.example` and
`billing@acme.example`.

Q60 supersedes the clarifier's own proposed default. The clarifier proposed
"acknowledgements from a no-reply address"; the recorded answer is support@ for both
channels. That supersession is the source of the risk in § 2, and it is recorded here
rather than silently applied.

### What "org-wide address" costs, and why none of it is in this manifest

`OrgWideEmailAddress` **has no metadata type**. Both cited skills say so independently —
`admin/email-templates-and-alerts/references/metadata-and-sender-identity.md` § "Org-wide
email address (the sender)" ("they are created in Setup → Organization-Wide Addresses and
must be verified from the mailbox") and
`admin/email-deliverability-strategy/references/metadata-examples.md` § "Where each
control actually lives" (row `OrgWideEmailAddress` → "No metadata type — API/Data
Loader/Setup only"). So the two addresses above travel with **no** file, in this step or
any other. Before the first send in each target org, a human confirms:

```sql
SELECT Id, Address, DisplayName, Purpose, IsAllowAllProfiles, IsVerified
FROM OrgWideEmailAddress
WHERE Address IN ('support@acme.example', 'billing@acme.example')
```

- `IsVerified` (API 58.0+) defaults to `false` and "is only cleared by clicking a link
  mailed to the mailbox owner, which no deploy can do for you"
  (`email-templates-and-alerts/references/gotchas.md`, § `senderAddress` Is Only Legal…).
  An unverified address cannot send.
- `IsAllowAllProfiles` defaults to `false`, so "an address created by one admin is
  unusable by everyone else until profiles are listed or the flag is flipped" (same
  gotcha). Q60 answers this: both addresses are "restricted to the profiles that need
  them" — the three profiles M2-S03 built.
- `Purpose` is `DefaultNoreply`, `UserSelection`, or `UserSelectionAndDefaultNoReply`
  (`email-deliverability-strategy/references/metadata-examples.md` § 5). `UserSelection`
  is what lets an agent pick the address as From on a reply, which is what Q60's reply
  identity needs.

**Requires View Setup and Configuration** to query, per the sender-identity reference.

---

## 2. The self-addressed-loop risk, and why it exists here

**The risk.** `support@acme.example` is both the address the acknowledgement is sent
*from* (Q22/Q60) and the address inbound customer mail arrives *at* (Q22, requirement.md
line 1). An acknowledgement whose From address reaches an Email-to-Case intake path can
re-enter Email-to-Case and create another case, which fires the auto-response again.

**The cause, grounded.** `admin/email-to-case-configuration/references/gotchas.md`
Gotcha 3 — "Auto-Response Email Loops When From Address Matches Routing Address" —
describes exactly this shape, and names exactly this cause:

> "the admin copies the support address (`support@company.com`) into the auto-response
> rule 'From' field, and the company mail server has a blanket forwarding rule for all
> mail arriving at `support@company.com`."

The answer key's "Mailbox ownership" row puts that blanket forwarding rule in place: "IT
owns the forwarding rules for support@ and billing@." The mechanism is then: the
acknowledgement goes out From support@ → a recipient's mailer bounces it, auto-replies to
it, or forwards it → that mail arrives at support@ → IT's forwarding rule feeds it to the
Salesforce-generated `emailServicesAddress` → a new case → a new acknowledgement.

**Two cited skills state the prohibition in almost the same words:**

- `admin/email-templates-and-alerts/references/metadata-and-sender-identity.md`, §
  "Org-wide email address (the sender)": "The auto-response `senderEmail` must match this
  address exactly and must **not** be the Email-to-Case routing address, or the
  acknowledgement re-enters Email-to-Case and loops."
- `admin/email-to-case-configuration/references/metadata-examples.md`, § "Loop test": the
  auto-response `senderEmail` "must never equal, alias to, or forward into any
  `emailAddress` in this file."

### The divergence this step records but cannot resolve

The plan carries two readings of the same decision, and they do not agree:

| Source | What it says |
|---|---|
| `answers-key.md`, "Acknowledgement" row | "from support@acme.example (**an org-wide email address, never the Email-to-Case routing address itself**)" |
| `plan.json` clarification **Q22** (answered) | "**support@ (a live routing address) itself sends the acknowledgement.** Since support@ also receives inbound mail, confirm during the sandbox loop test (Q68) that this does not create an acknowledgement loop." |

The answers key reads support@ as *not* the routing address. **The cited skills do not
support that reading, and this note does not manufacture one.** In
`admin/email-to-case-configuration/references/metadata-examples.md` the customer-facing
address is precisely what goes in the routing address element:
`<routingAddresses><emailAddress>support@acme.example</emailAddress>…`. The
Salesforce-generated `emailServicesAddress` is a *read-only sibling field of that same
routing-address record*, not a different object — "`emailServicesAddress` and `isVerified`
are read-only… They come back on retrieve and are ignored on deploy." So support@ is the
`emailAddress` of an `EmailToCaseRoutingAddress`, which is exactly the value both cited
skills forbid as the auto-response `senderEmail`.

A human has to settle which reading stands. It is not settleable from the artefacts,
because no artefact of this step sets a sender.

**Noted for whoever settles it:** the two cited-adjacent skills' own worked examples
contradict the rule they both state. `admin/assignment-rules/references/metadata-examples.md`
writes `<senderEmail>support@acme.example</senderEmail>` on both auto-response entries,
ten lines after its own prose says `senderEmail` "must never be the Email-to-Case routing
address" — while `admin/email-to-case-configuration` puts that same literal in
`<emailAddress>`. Whichever way the human decides, one of those two worked examples wants
correcting.

### The named control, and what is actually load-bearing in it

The plan names the control as: *the auto-response rule fires once per case, and the
routing address rejects its own sender.* Both halves are recorded here, and both are
qualified, because only the first is grounded:

1. **"Fires once per case" — grounded, but it does not bound the loop.** Q63: "One
   acknowledgement per case creation: auto-response only, with no parallel Flow email
   alert on the same event", and an auto-response rule "is only evaluated when the
   assignment rule fires" (`admin/assignment-rules/references/metadata-examples.md` §
   "Case auto-response rule"). So one case yields exactly one acknowledgement. That rules
   out a *fan-out* per case. It does **not** rule out the loop in Gotcha 3, whose growth
   is one *new case* per round trip — each new case is entitled to its own single
   acknowledgement. One-per-case and unbounded-cases are compatible.
2. **"The routing address rejects its own sender" — NOT grounded as this build is
   configured.** The only rejection lever the cited skills document is
   `authorizedSenders` / `unauthorizedSenderAction` on the routing address, and
   `admin/email-to-case-configuration/references/metadata-examples.md` § "Forwarding and
   verification checklist" says to "Leave it empty for a public support address" —
   support@ is a public support address taking ~400 emails a day. With `authorizedSenders`
   empty, nothing is unauthorised, so `unauthorizedSenderAction` (M3-S03's input records
   `Bounce`, per Q21) never fires and rejects nothing, including mail from support@
   itself. As planned, this half of the control is inert. Marked, not asserted.

### What is genuinely standing between this build and the loop

| Control | Grounded in | Owner | Kind |
|---|---|---|---|
| One acknowledgement per case | Q63; `admin/assignment-rules` § Case auto-response rule | M3-S04 | prevention, partial (see above) |
| Disable "keep a copy and auto-reply" on the forwarding mailbox | `email-to-case-configuration/references/metadata-examples.md` forwarding checklist: "the mailbox auto-reply is a second sender that can loop back into the routing address" | IT (mail server, outside Salesforce) | prevention — **not a metadata artefact of this build** |
| Sandbox loop test: one email per public address, then `SELECT Origin, COUNT(Id) FROM Case WHERE CreatedDate = TODAY GROUP BY Origin` must stop at one per address | `email-to-case-configuration/references/metadata-examples.md` § "3. Loop test" | **Q68 / M5** | detection, before go-live |
| A dedicated no-reply From address instead of support@ | Q22's own `proposed_default`, and Gotcha 3's "How to avoid": "Always use a dedicated no-reply address" | a human, at the M3 gate | the prevention the plan currently declines |

The answer key's position is that "Loop risk is covered by the sandbox loop test" — that
is the detection row, not a prevention row. If the loop test fails, the fix is a change to
**M3-S04's `senderEmail`**, not to anything in this step.

---

## 3. `Case_Escalated_To_Tier2` has no sender, and that is not an omission

This template is consumed as an escalation action's template, not by an auto-response
rule. `admin/escalation-rules/references/metadata-examples.md` names this exact developer
name in its own worked example — `<assignedToTemplate>unfiled$public/Case_Escalated_To_Tier2</assignedToTemplate>`
on a reassigning action whose `<assignedTo>` is the Tier 2 queue — and the same file notes
that "a reassigning action writes `OwnerId`". The recipient is therefore the **new owner**,
the Tier 2 Engineering queue: this template is internal, not customer-facing.

`EscalationAction` carries no sender element in that reference's element set
(`assignedTo`, `assignedToType`, `assignedToTemplate`, `minutesToEscalation`,
`notifyCaseOwner`, `notifyEmail`, `notifyTo`, `notifyToTemplate`). So there is no From
address to record for it, in this step or in M4-S04, and none was invented. Its body
carries no address either.

Because it is internal, Q64 and assumption A3 — which bind "every **customer-facing**
Case template" — do not reach it, and it deliberately carries no visible thread token.
`Case_Acknowledgement` does carry one, in its subject.

---

## 4. Deliverability posture this step declares, and the gaps it does not

`admin/email-deliverability-strategy` is cited on this step, and its checker runs against
`artefacts/M3-S02`. This step declares **none** of the three files that checker reads
(`settings/EmailAdministration.settings-meta.xml`,
`deliverability/email-policy.json`, `deliverability/dkim-keys.json`), so it exits 0 on
three WARNs and asserts nothing. The posture questions its
`## Questions to Ask Before Configuring` table asks are answered here where the plan
answers them, and recorded as open where it does not:

| Question | Status |
|---|---|
| Which layer — Marketing Cloud or Salesforce Core? | **Core.** Nothing in `requirement.md` names Marketing Cloud; every send in scope is an auto-response or escalation action from the Core org. `references/metadata-examples.md` is the runbook, not `references/examples.md`. |
| Not arriving, or arriving in spam? | **Neither — greenfield.** Not a diagnosis; recorded as not applicable rather than defaulted. |
| Daily external send volume? | **~480 acknowledgements a day minimum** (`requirement.md`: 400 email + 60 web + 20 manual cases a day), against the documented 5,000-external-addresses-a-day cap. Headroom today; it is a number that grows with the channel. |
| `enableSubstituteFromAddress` touched? | **No answer on file.** The skill's documented default stands: `false`, which it calls "the correct deliverability posture" — a substituted `…sfcustomeremail.com` From address "carries none of your SPF/DKIM/DMARC reputation". Recorded as a skill default, not a decision. |
| DKIM key per sending domain, with a rotation date? | **OPEN.** No clarification asks it and the skill documents no default ("Nothing on the platform expires a DKIM key or reminds you to roll it — the checker is the reminder"). `acme.example` has no DKIM inventory in this build. |
| SMTP relay, and bounce management on? | **OPEN.** No answer, no documented default. With `enableHandleBouncedEmails` off, "the Contact/Lead bounce fields stay empty forever" — which matters here, because an undetected bounce back to support@ is the first link in § 2's loop. |
| Who owns DNS, and what is the change lead time? | **HALF-ANSWERED.** The answer key names IT as owner of the **mail-server forwarding rules** for support@ and billing@. That is not DNS ownership, and no lead time is recorded. |

None of these blocks this step: none of them changes an element in this step's declared
`outputs[]`. All four open rows belong to a human, and the last three would be discharged
by a deliverability step this plan does not currently contain.

Sandbox-specific, from both skills: after a refresh "sandbox deliverability is
system-only; raise it before testing", which Q78 already commits to along with scrubbing
Contact emails first.

---

## 5. What a human should tick at the M3 gate (test B06)

- [ ] The acknowledgement's sender is `support@acme.example` for both channels, and the
      finance reply identity is `billing@acme.example` — § 1.
- [ ] The self-addressed-loop risk is understood, with its cause: support@ is both the
      acknowledgement's From address and an Email-to-Case intake path — § 2.
- [ ] The named control is understood **with both of its qualifications**: one-per-case is
      real but does not bound a loop that grows by new cases; "the routing address rejects
      its own sender" is inert while `authorizedSenders` is empty — § 2.
- [ ] Neither `.email` body hardcodes a recipient address. Both bodies contain no email
      address at all; the only addresses in this step are in this note and in
      `deploy-order.md`, neither of which is a template artefact.
- [ ] The Q22-vs-answers-key divergence is decided by a human, or explicitly carried into
      M3-S04 as an open risk — § 2.
