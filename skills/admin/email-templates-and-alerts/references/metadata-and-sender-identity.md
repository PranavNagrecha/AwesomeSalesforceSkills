# Metadata and Sender Identity — Email Templates and Org-Wide Addresses

The two pieces a routing solution needs from this skill: a **Classic** email template deployed by metadata (assignment, auto-response, and escalation rules can only reference Classic templates when deployed; the Metadata API guide notes Lightning templates are not packageable), and a **verified org-wide email address** for the sender. Shapes below come from the Metadata API Developer Guide and Object Reference (v62 PDFs).

## Where the files live

| Piece | package.xml `<name>` | File in a DX project |
|---|---|---|
| Email folder | `EmailFolder` | `email/Support_Templates.emailFolder-meta.xml` (the guide's naming rule is `FolderName.folderType-meta.xml`, alongside the folder directory itself) |
| Classic email template | `EmailTemplate` (no `*` wildcard; list `Folder/Developer_Name` explicitly) | `email/Support_Templates/Case_Web_Acknowledgement.email` (body) + `Case_Web_Acknowledgement.email-meta.xml` |

Rules reference the template as `Support_Templates/Case_Web_Acknowledgement`. Templates in the shared unfiled folder are referenced as `unfiled$public/<Developer_Name>`.

## Folder

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EmailFolder xmlns="http://soap.sforce.com/2006/04/metadata">
    <accessType>Public</accessType>
    <name>Support Templates</name>
    <publicFolderAccess>ReadOnly</publicFolderAccess>
</EmailFolder>
```

A template in a private folder is invisible to the rule engine for other users; keep rule templates in a public folder.

## Classic text template used by an auto-response rule

`email/Support_Templates/Case_Web_Acknowledgement.email`:

```text
Hello {!Contact.FirstName},

We received your request "{!Case.Subject}" and created case {!Case.CaseNumber}.
A support specialist will respond within one business day.

Reply to this email to add information to your case.

Acme Support
```

`email/Support_Templates/Case_Web_Acknowledgement.email-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EmailTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <available>true</available>
    <description>Acknowledgement sent by the Case auto-response rule for Web origin</description>
    <encodingKey>UTF-8</encodingKey>
    <name>Case Web Acknowledgement</name>
    <style>none</style>
    <subject>We received your request: {!Case.Subject} [ ref:{!Case.Thread_Id} ]</subject>
    <type>text</type>
    <uiType>Aloha</uiType>
</EmailTemplate>
```

- `type` is `text`, `html` (letterhead-based; `letterhead` and `style` apply), `custom` (HTML without letterhead), or `visualforce` (`apiVersion` applies). `available` and `encodingKey` are required for Classic templates.
- `uiType` `Aloha` is Classic; `SFX` is Lightning and forces `type` = `custom`. Rules deployed by metadata need `Aloha`.
- Subject limit is 230 characters for Classic templates (1,000 for Lightning).
- Merge fields resolve only for the record the rule fires on and its parents: a Case auto-response can use `{!Case.*}` and `{!Contact.*}`; a Lead auto-response can use `{!Lead.*}` only (gotchas: merge fields depend on record context).
- Email-to-Case threading depends on the thread token being present in outbound mail; if the org relies on the Thread ID rather than header-based threading, keep the token in the subject or body (`admin/email-to-case-configuration`).

## Org-wide email address (the sender)

There is no metadata type for org-wide addresses; they are created in Setup → Organization-Wide Addresses and must be verified from the mailbox. Confirm one exists in the target org before deploying a rule that uses it:

```sql
SELECT Id, Address, DisplayName, IsAllowAllProfiles, IsVerified, Purpose
FROM OrgWideEmailAddress
WHERE Address = 'support@acme.example'
```

- `IsVerified` (58.0+) must be `true`; an unverified address cannot send.
- `Purpose` is `UserSelection` (users with an allowed profile may pick it as From), `DefaultNoreply`, or `UserSelectionAndDefaultNoReply`.
- `IsAllowAllProfiles` `false` means only the listed profiles may use it; an auto-response rule or an Apex `SingleEmailMessage` that passes the address Id still needs the sending context allowed.
- Querying the object requires the View Setup and Configuration permission.
- The auto-response `senderEmail` must match this address exactly and must **not** be the Email-to-Case routing address, or the acknowledgement re-enters Email-to-Case and loops (`admin/email-to-case-configuration` gotchas).
- The deploy of any AutoResponseRule / workflow alert naming the address fails validation ("… is an invalid From email address") until it exists and is verified in the target org. `UNVERIFIED (2026-09-12): proven live in a dry-run, not stated in the guide` (`admin/assignment-rules` references/gotchas.md #7).
- After a sandbox refresh, sandbox deliverability is system-only; raise it before testing (`devops/sandbox-data-isolation-gotchas`).

## package.xml and CLI

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Support_Templates</members>
        <name>EmailFolder</name>
    </types>
    <types>
        <members>Support_Templates/Case_Web_Acknowledgement</members>
        <members>Support_Templates/Case_Email_Acknowledgement</members>
        <name>EmailTemplate</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Templates cannot be wildcarded: list them first, then retrieve by name
sf org list metadata --metadata-type EmailTemplate --target-org my-sandbox
sf project retrieve start --metadata "EmailTemplate:Support_Templates/Case_Web_Acknowledgement" --target-org my-sandbox
sf project deploy start --source-dir force-app/main/default/email --target-org my-sandbox
```
