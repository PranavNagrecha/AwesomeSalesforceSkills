# Email Service Inbound — Work Template

Fill this in while working an inbound-email request. Every heading below
maps to a decision the `EmailServicesFunction` / `EmailServicesAddress`
metadata records, so an incomplete section here becomes a guessed XML
element later.

## Scope

**Skill:** `email-service-inbound`

**Request summary:** _(what the user asked for, in their words)_

## Context Gathered

Answers to `## Questions to Ask Before Configuring` in SKILL.md.

| Decision | Answer | Metadata element it sets |
|---|---|---|
| Record(s) the email must produce | | `apexClass` |
| Running user (username) and its permission set | | `emailServicesAddresses/runAsUser` |
| Sender population (named senders / domains / anonymous) | | `authorizedSenders`, `authorizationFailureAction` |
| SPF/DKIM/DMARC enforcement required? | | `isAuthenticationRequired`, `authenticationFailureAction` |
| Attachment policy (discard / metadata only / text / binary / all) | | `attachmentOption`, `isTextAttachmentsAsBinary` |
| Who is paged when processing fails | | `isErrorRoutingEnabled`, `errorRoutingAddress` |
| Behaviour at the daily org email-processing limit | | `overLimitAction` |
| Behaviour while the service is inactive (cutover, incident) | | `functionInactiveAction` |
| Threading source (`messageId` / `inReplyTo` / subject token / none) | | handler logic |
| Expected volume (emails/day) vs org limit (user licences x 1,000, max 1,000,000) | | capacity note |

## Approach

- Pattern selected from SKILL.md `## Common Patterns`: _(A / B / C, and why)_
- Rejected alternative and reason (usually: why not Email-to-Case):
- Async boundary: does the handler publish a Platform Event instead of
  doing callouts inline? _(yes/no + event name)_

## Artifacts Produced

- [ ] `force-app/main/default/classes/<Handler>.cls`
- [ ] `force-app/main/default/classes/<Handler>Test.cls`
- [ ] `force-app/main/default/emailservices/<Function_Name>.emailservices-meta.xml`
- [ ] `manifest/package.xml` entries for `ApexClass` and `EmailServicesFunction`
- [ ] Documented permission set for the running user

## Checklist

Copy `## Review Checklist` from SKILL.md and tick each line. Then run:

```bash
python3 skills/admin/email-service-inbound/scripts/check_email_service_inbound.py \
    --manifest-dir force-app/main/default
```

## Notes

Record deviations from the patterns in SKILL.md and the reason, plus the
production routing address once it exists (it is generated per org and
cannot be moved from sandbox — see `references/gotchas.md` § 12).
