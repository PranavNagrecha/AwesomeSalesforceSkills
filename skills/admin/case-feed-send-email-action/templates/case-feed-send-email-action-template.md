# Case Feed Send Email Action — Config Worksheet

Fill this out before touching Setup. Every row maps to a decision that is expensive to reverse
once agents are trained on the composer.

## Scope

**Skill:** `case-feed-send-email-action`

**Request summary:** (what the user asked for)

**Org / sandbox:**

---

## Gate 0 — Prerequisite

| Question | Answer | Blocking? |
|---|---|---|
| Is Email-to-Case enabled in the target org? | ☐ yes ☐ no | **Yes.** *"Email-to-Case must be enabled to use the Send Email quick action on the Cases object."* |
| Does a Send Email / Email action already exist on Case? | ☐ yes ☐ no | No, but a second one confuses agents — extend the existing action before adding another |

If Email-to-Case is off, stop here and route to `admin/email-to-case-configuration`.

---

## The action

| Field | Value | Notes |
|---|---|---|
| Label | | Per `templates/admin/naming-conventions.md` |
| API name | | `Case.<Name>` |
| Action Type | `Send Email` | Metadata: `<type>SendEmail</type>` (API 31.0+) |
| Intent | ☐ first touch ☐ reply | Drives the subject decision below |

## Action layout — the field contract

Mark editability deliberately. **A read-only field silently discards any prepopulated value.**

| Field | On layout? | Editable? | Prepopulated? |
|---|---|---|---|
| `ValidatedFromAddress` | ☐ | ☐ | ☐ |
| `ToAddress` | ☐ | ☐ | ☐ |
| `CcAddress` | ☐ | ☐ | ☐ |
| `BccAddress` | ☐ | ☐ | ☐ |
| `Subject` | ☐ | ☐ | ☐ |
| `HTMLBody` | ☐ | ☐ | ☐ |
| `RelatedToId` | ☐ | ☐ | ☐ (preselects the account on the case's contact when available) |
| Attachments | ☐ | — | — |

Not prepopulatable: `AttachmentId`, `ContentDocumentIds` — they aren't part of the action layout.

## Default content

| Setting | Value | Rule |
|---|---|---|
| Default Email Template | | Must be type **Custom**. *"Only Custom type templates are supported."* |
| Don't Apply Template Subject | ☐ selected ☐ cleared | **Select** for replies (keeps the customer's subject / thread). **Clear** for first touch. |
| Predefined field values | | ID fields (`Contact.Id`) or string fields; Contact, lead, person-account IDs supported |

> The Metadata API `QuickAction` docs do not list a template field. Re-verify Default Email
> Template after every deployment and org refresh.

---

## Defaulting mechanism — pick one

| | Declarative | Apex handler |
|---|---|---|
| Chosen | ☐ | ☐ |
| Use when | Same template + recipients every send | Template/BCC varies by case, or reply vs. first touch |
| Cost | None | Org-wide synchronous Apex, test class, deployment per change |

If Apex, the skeleton — see `references/examples.md` for the complete class:

```apex
global class <Name> implements QuickAction.QuickActionDefaultsHandler {
    global <Name>() {}   // required: empty, parameterless

    global void onInitDefaults(QuickAction.QuickActionDefaults[] defaults) {
        for (QuickAction.QuickActionDefaults qad : defaults) {
            if (qad instanceof QuickAction.SendEmailQuickActionDefaults
                && qad.getTargetSObject().getSObjectType() == EmailMessage.sObjectType
                && qad.getActionName().equals('Case.Email')
                && qad.getActionType().equals('Email')) {
                QuickAction.SendEmailQuickActionDefaults d =
                    (QuickAction.SendEmailQuickActionDefaults) qad;
                // one bounded query on d.getContextId(); branch on d.getInReplyToId()
                break;
            }
        }
    }
}
```

Constraints: one bounded SOQL per init, CRUD/FLS via `templates/apex/SecurityUtils.cls`, fail
soft and log via `templates/apex/ApplicationLogger.cls`.

---

## Layout assignment

List **every** Case page layout a support persona sees. Missing one removes the composer for
that whole team with no error.

| Case page layout | Assigned to (profile / record type) | Action added? |
|---|---|---|
| | | ☐ |
| | | ☐ |

## If the *standard* Email action is the one missing

Not a layout problem. Walk the three causes the troubleshooting article documents:

| Check | Setting | Cleared? |
|---|---|---|
| Email deliverability access level is **All email**, not **System Email Only** | Setup → Deliverability | ☐ |
| Email-to-Case is enabled (irreversible once on) | Setup → Email-to-Case | ☐ |
| **Enable Case Feed Actions and Feed Items** is selected | Setup → Support Settings | ☐ |
| Agents sending via Office 365 / Gmail have the matching permission set | | ☐ |

## Move-email capability

| Question | Answer |
|---|---|
| Should agents be able to move an email to a different case? | ☐ yes ☐ no |
| Precondition: emails were created by Email-to-Case | ☐ confirmed |
| Precondition: email threading is set to **Lightning threading** | ☐ confirmed |
| Enabled via | Salesforce Help, *"Let Agents Move Emails to a Different Case"* (an admin setting — no user permission is documented for this) |
| Move volume monitored as a routing-defect signal? | ☐ yes |

---

## Agent enablement

- [ ] Agents briefed on the attachment limits for **their UI** — Lightning Experience: 10 files, 25 MB total file size; Salesforce Classic: more than 10 files, 18 MB total
- [ ] Agents told that no per-attachment size cap is documented, so the total is the budget
- [ ] Agents shown the move-email path instead of re-sending from the correct case

---

## Validation

```bash
python3 scripts/check_case_feed_send_email_action.py --manifest-dir force-app/main/default
```

Then send a real test email, reply to it, and confirm the subject, template body, and BCC behave
as designed.

## Sign-off checklist

- [ ] Email-to-Case enabled
- [ ] Action type is `SendEmail`; label follows naming conventions
- [ ] Default Email Template is a **Custom**-type template
- [ ] Don't Apply Template Subject matches the action's intent
- [ ] No prepopulated field is read-only on the layout
- [ ] No predefined value targets `AttachmentId` / `ContentDocumentIds`
- [ ] Action present on every relevant Case page layout
- [ ] Any Apex handler: `global`, empty constructor, filters on `Case.Email`, bounded SOQL
- [ ] Checker script passes
- [ ] No GA / Beta / Pilot claim in any deliverable — the official docs make none

## Notes

(Record any deviation from the standard pattern and why.)
