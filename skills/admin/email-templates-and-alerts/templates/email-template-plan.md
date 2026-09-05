# Email Template and Alert Plan

Use this before creating a new transactional email. Every row below decides a value that
ends up in metadata; the italic text is what a filled-in answer looks like, not a suggestion
to copy. Deployable shapes for the decisions here: `references/metadata-and-sender-identity.md`.

---

## Overview

| Property | Value | Lands in |
|----------|-------|----------|
| Email purpose | _One sentence, from the recipient's side: "tell the case contact we received their web request and give them the case number."_ | `EmailTemplate.description` |
| Audience | Internal / External / Both | Recipient design, deliverability review |
| Trigger event | _The exact state transition, not the end state: "Case created with Origin = Web", "Status changes from Open to Closed"._ | Rule entry criteria / Flow entry conditions |
| Sending mechanism | Email Alert / Standard Send / Auto-Response Rule / Assignment Rule / Escalation Rule / Apex | `WorkflowAlert`, or a rule's `senderEmail`, or code |
| Sender identity | _The mailbox that owns replies: `support@acme.example`._ | `senderType` + `senderAddress` |
| Org-Wide Email Address needed? | Yes / No — Yes for anything customer-facing or reply-bearing | `OrgWideEmailAddress` (Setup only; no metadata type) |
| Address verified in **every** target org? | Yes / No, per org | `IsVerified` must be `true` before the first send |

## Content Design

| Item | Decision | Lands in |
|------|----------|----------|
| Template name | _API-safe developer name, no spaces, no trailing or doubled underscores: `Case_Web_Acknowledgement`._ | `fullName` |
| Folder | _Public folder for anything a rule sends; personal folders are invisible to other users and to folder-based inventory._ | `EmailFolder` |
| Template family | Classic (`uiType` `Aloha`) / Lightning (`uiType` `SFX`) — rules and packages require Classic | `uiType`, `type` |
| Subject line | _Specific and scannable; must stay under 230 chars for Classic, 1,000 for Lightning._ | `subject` |
| Merge-field context | _Name the firing object and its usable parents: a Case auto-response resolves `{!Case.*}` and `{!Contact.*}`; a Lead auto-response resolves `{!Lead.*}` only._ | Template body |
| Required related fields | _Each merge field, plus what the email should read like when that field is blank._ | Body + fallback copy |
| Branding / signature rules | _Letterhead name if `type` is `html`; otherwise plain text and a written-out signature._ | `letterhead`, `style` |
| Thread token required? | Yes / No — Yes when replies must land back on the Case | Subject or body |

## Trigger Design

| Check | Decision | Lands in |
|-------|----------|----------|
| Exact entry criteria | _Written as a transition, e.g. "IsChanged(Status) AND PRIORVALUE(Status) <> 'Closed' AND Status = 'Closed'"._ | Rule / Flow criteria |
| Transition-only logic needed? | Yes / No — Yes whenever the record can be re-saved in the qualifying state | Prior-value check |
| Recipient source | _Recipient rows with the companion element each type needs: `owner` and `creator` need none; `contactLookup` / `userLookup` / `email` need `field`; `group` / `role` / `user` need `recipient`._ | `recipients` |
| CC addresses | _Max 5. A sixth goes in a public group, not a sixth `ccEmails` line._ | `ccEmails` |
| Duplicate-email prevention | _Which other automation on this object can fire on the same save, and how this one stays out of its way._ | Consolidation decision |

## Validation Checklist

- [ ] Sender address exists in every target org and `IsVerified` is `true`
- [ ] At least one `recipients` or `ccEmails` entry is populated
- [ ] `senderAddress` set only where `senderType` is `OrgWideEmailAddress`
- [ ] Merge fields tested against a record whose optional lookups are empty
- [ ] Fired the real trigger and counted the emails — exactly one arrived
- [ ] `python3 scripts/check_email_templates.py --manifest-dir <email source dir>` run and every REVIEW finding answered (it exits 1 only when no template artefact matched, or a `.email-meta.xml` will not parse; use `--strict` to fail on REVIEW too)
- [ ] Business owner approved subject/body
- [ ] Deliverability/compliance requirements reviewed (sandbox deliverability is system-only after a refresh)

## Worked Example

| Property | Value |
|----------|-------|
| Email purpose | Acknowledge a web-submitted case and give the contact the case number |
| Audience | External |
| Trigger event | Case created with `Origin = Web` |
| Sending mechanism | Auto-Response Rule |
| Sender identity | `support@acme.example` (verified, `Purpose = UserSelection`) |
| Template name | `Support_Templates/Case_Web_Acknowledgement`, `uiType` `Aloha`, `type` `text` |
| Subject line | `We received your request: {!Case.Subject} [ ref:{!Case.Thread_Id} ]` |
| Merge-field context | `{!Case.*}`, `{!Contact.*}` |
| Duplicate-email prevention | Auto-response rules fire once at creation; no record-triggered Flow sends on the same event |
