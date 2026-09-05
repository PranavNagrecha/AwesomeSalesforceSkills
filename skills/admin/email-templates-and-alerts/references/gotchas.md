# Gotchas: Email Templates and Alerts

---

## Duplicate Automation Causes Duplicate Email

**What happens:** A flow updates a record twice in one transaction, or two different automations react to the same business event. Users receive two or three emails and stop trusting the system.

**When it bites you:** Status changes, approval notifications, and escalation logic.

**How to avoid it:** Design send criteria around the exact transition, not the final field value alone.

**Example:**
```text
Bad trigger: Status = Closed
Better trigger: Status changed from Open to Closed
```

---

## Merge Fields Depend on Correct Record Context

**What happens:** The template references related-object fields that are not available in the email's actual context. The email arrives with blanks or broken copy.

**When it bites you:** Approval emails, custom-object notifications, and heavily related templates.

**How to avoid it:** Test templates with real records and verify every merge field from the actual sending automation.

**Example:**
```text
Template expects {!Opportunity.Account.Name}
Automation sends from a context that does not supply Opportunity
Result: blank merge value
```

---

## Sender Identity Is Operational, Not Cosmetic

**What happens:** Emails come from whichever default sender setup happened to exist. Replies go to the wrong mailbox or fail audit expectations.

**When it bites you:** Customer-facing support mail, legal/compliance notices, and branded operations emails.

**How to avoid it:** Decide the sender explicitly, configure Org-Wide Email Addresses, and test reply handling.

**Example:**
```text
Customer notification should come from support@example.org, not from an individual admin mailbox
```

---

## Transactional Email Tools Get Misused for Marketing

**What happens:** Teams try to use admin-managed templates and alerts for broad recurring outreach. Limits, unsubscribes, and content governance quickly become problems.

**When it bites you:** Newsletters, nurture campaigns, and recurring mass updates.

**How to avoid it:** Keep admin email for transactional or operational communication. Move campaign-style communication to the right platform.

**Example:**
```text
Monthly customer newsletter -> not an Email Alert use case
```

---

## An Alert With No `recipients` And No `ccEmails` Deploys Clean And Never Sends

**What happens:** `WorkflowAlert` treats both recipient fields as optional at the schema level. A `.workflow` file whose alert carries a `template`, a `description` and a `senderType` but an empty recipient set deploys successfully, appears in Setup, is selectable from Flow — and delivers nothing. There is no runtime error and no entry in the debug log to look for.

**When it bites you:** Alerts hand-authored in XML rather than clicked together in Setup; alerts whose recipient rows were dropped during a package split or a partial retrieve.

**How to avoid it:** Treat "at least one of `recipients` / `ccEmails` is populated" as a deploy gate. `ccEmails` also caps at **5 addresses** — a sixth distribution address needs a public group or a role, not another `ccEmails` entry.

```xml
<alerts>
    <fullName>Case_SLA_Breach_Warning</fullName>
    <description>SLA breach warning to case owner and support managers</description>
    <ccEmails>support-leads@acme.example</ccEmails>   <!-- max 5 of these -->
    <recipients>
        <type>owner</type>
    </recipients>
    <senderType>OrgWideEmailAddress</senderType>
    <senderAddress>support@acme.example</senderAddress>
    <template>Support_Templates/Case_SLA_Breach_Warning</template>
</alerts>
```

> Source: Metadata API Developer Guide, `WorkflowAlert` — "For the email to be sent successfully, set a value for `ccEmails` or `recipients`… The value of `ccEmails` can include up to 5 different email addresses."

---

## `senderAddress` Is Only Legal When `senderType` Is `OrgWideEmailAddress`

**What happens:** The From address is not a free-text field. `senderAddress` may carry a value **only** when `senderType` is `OrgWideEmailAddress`; set it alongside the default `CurrentUser` and the deploy is rejected. And even a correctly paired `senderAddress` sends from the record-updating user's address if the matching `OrgWideEmailAddress` row in the target org is unverified — `IsVerified` defaults to `false` and is only cleared by clicking a link mailed to the mailbox owner, which no deploy can do for you.

**When it bites you:** Every first deploy into a new sandbox or a new production org. The alert metadata travels; the verified sender does not, because org-wide addresses have no metadata type at all.

**How to avoid it:** Before deploying alerts, confirm the address exists and is verified in the *target* org, then deploy:

```sql
SELECT Id, Address, IsVerified, IsAllowAllProfiles, Purpose
FROM OrgWideEmailAddress
WHERE Address = 'support@acme.example'
```

`IsAllowAllProfiles` defaults to `false`, so an address created by one admin is unusable by everyone else until profiles are listed or the flag is flipped. Full shape in `references/metadata-and-sender-identity.md`.

> Sources: Metadata API Developer Guide, `WorkflowAlert.senderAddress` ("You can only specify a value in this field if the `senderType` is set to `OrgWideEmailAddress`"); Object Reference, `OrgWideEmailAddress.IsVerified` (API 58.0+, default `false`) and `.IsAllowAllProfiles` (default `false`).

---

## `DefaultWorkflowUser` Silently Downgrades To `CurrentUser` On Package Install

**What happens:** An alert configured to send as the default workflow user keeps that identity in the source org and in the retrieved XML — but if the alert arrives in an org through a **package install**, the platform rewrites `senderType` to `CurrentUser`. Emails that were meant to come from a single service identity start arriving from whichever user happened to save the record.

**When it bites you:** ISV packages and internal unlocked/first-generation packages used to distribute a notification bundle across business units. The XML in version control still says `DefaultWorkflowUser`, so a diff of source against source finds nothing.

**How to avoid it:** For any alert that ships inside a package, use `senderType` `OrgWideEmailAddress` with an explicit `senderAddress` rather than `DefaultWorkflowUser`, and verify the address as a post-install step. Audit installed alerts against source rather than assuming the deployed value matches.

> Source: Metadata API Developer Guide, `WorkflowAlert.senderType` — "`DefaultWorkflowUser`… If the email alert is installed from a package, this field value is changed to `CurrentUser`."

---

## `uiType`, `type`, `style` And `letterhead` Are Coupled, And Only One Combination Deploys For Rules

**What happens:** The four fields are not independent switches. `uiType` `SFX` (Lightning Experience) **forces** `type` to `custom`; `letterhead` is available only when `type` is `html`; and `style` is documented as Required even though it is "only available when `type` is set to `html`" — the guide's own sample nonetheless carries `<style>none</style>` on a `custom` template. Pick an inconsistent set and the deploy fails on a field-level error that names the field, not the coupling.

**When it bites you:** Hand-writing a template `-meta.xml`; copying a Lightning template's shape onto a Classic one during migration.

**How to avoid it:** Use one of these two shapes and nothing in between.

| Consumer | `uiType` | `type` | `style` | `letterhead` | `encodingKey` |
|---|---|---|---|---|---|
| Assignment / auto-response / escalation rule, packaged content | `Aloha` | `text` or `custom` | `none` | omit | required |
| Letterhead-branded Classic template | `Aloha` | `html` | a real style value | the letterhead name | required |

Lightning templates are excluded from this table on purpose: the guide states plainly that Lightning email templates aren't packageable and recommends a Classic template for alerts, and `encodingKey` is ignored by Lightning templates entirely (encoding comes from user settings).

> Sources: Metadata API Developer Guide, `EmailTemplate` field table (`UiType`: "If `UiType` is `SFX`, the type must be `custom`. Packaging is supported for Salesforce Classic email templates only."; `letterhead`: "Only available when `type` is set to `html`"; `style`: "Required… only available when `type` is set to `html`") and `WorkflowAlert.template` ("Lightning email templates aren't packageable. We recommend using a Classic email template.").

---

## Classic And Lightning Templates Live In Different Folder Types, In Different Directories

**What happens:** "Email folder" and "Email Template folder" are two distinct folder types. Classic templates go in the `email` directory under an `EmailFolder`; Lightning templates go in `emailTemplates` under an `EmailTemplateFolder`. Put the wrong pair together — a Lightning template filed under `EmailFolder`, or an `EmailFolder` member listed in package.xml as `EmailTemplateFolder` — and the retrieve returns nothing rather than erroring usefully. Nested folders add a second trap: a nested folder member **must** end with a trailing `/` in package.xml, or the API searches for a *component* of that name inside the parent and the operation fails.

**When it bites you:** Migrating Classic templates to Lightning (see `admin/classic-email-template-migration`); reorganising a flat template folder into a nested hierarchy.

**How to avoid it:** Keep the two families in separate manifests, and remember neither folders nor email templates support the `*` wildcard — enumerate with `sf org list metadata` first.

```xml
<!-- nested folder: the trailing slash is load-bearing -->
<types>
    <members>Support_Templates/Escalations/</members>
    <name>EmailFolder</name>
</types>
```

> Source: Metadata API Developer Guide, `Folder` — the five folder types ("Email folder (available for Salesforce Classic email templates only)"), the `documents`/`email`/`emailTemplates` directory list, "If you omit the trailing slash… the operation fails", "For Lightning Email Template folders, use the `EmailTemplateFolder` type", and "This metadata type doesn't support the wildcard character `*`".

---

## Half The Recipient Types Are Inert Without A Companion `field` Or `recipient` Value

**What happens:** `WorkflowEmailRecipient` has three elements — `type`, `field`, `recipient` — and which of the last two is mandatory depends entirely on the `type` you chose. `contactLookup`, `userLookup` and `email` resolve through `field` and need it to point at a Contact lookup, a User foreign key, and an email field respectively. `group`, `role`, `roleSubordinates`, `user`, `partnerUser` and `customerPortalOwner` resolve through `recipient` and need a group name, role name, or username. Supply the wrong one of the pair, or leave the referenced field null on the firing record, and that recipient simply contributes nobody to the send.

**When it bites you:** `email` recipients pointed at an optional email field; `contactLookup` on an object where the Contact lookup is only populated later in the process; `role` recipients in an org where the role has no active users.

**How to avoid it:** For every recipient row, write down which of `field` / `recipient` the type requires, and what happens on a record where that field is blank. If blank is possible and the email still has to go out, add a second recipient row as a floor — `owner` and `creator` need neither companion element.

> Source: Metadata API Developer Guide, `WorkflowEmailRecipient` — per-value requirements in the `type` enumeration (`contactLookup`, `customerPortalOwner`, `email`, `group`, `partnerUser`, `role`, `roleSubordinates`, `user`, `userLookup`).

---

## Delete The Alert Before The Template, Never The Other Way Round

**What happens:** `WorkflowAlert.template` is a required named reference that "isn't required to exist in the zip file, but it must exist in Metadata API" — the reference is validated against the *target org*, not against the deployment payload. A destructive change that removes an `EmailTemplate` while an alert still points at it fails validation; a change that removes both in one `destructiveChanges.xml` can fail on ordering.

**When it bites you:** Template cleanup after an alert-consolidation exercise, which is exactly what this skill's Mode 2 produces.

**How to avoid it:** Two deployments. First remove or re-point the alerts (and any assignment / auto-response / escalation rule entry). Then, in a second deployment, delete the templates. The same ordering applies to the folder: the folder goes last.

> Source: Metadata API Developer Guide, `WorkflowAlert.template` — "Required. Named reference to an `EmailTemplate`. This email template isn't required to exist in the zip file, but it must exist in Metadata API."

---

## A Folder-Based Template Inventory Misses Every Personal-Folder Template

**What happens:** `EmailTemplate.FolderId` is a polymorphic lookup that refers to **Folder, Organization, or User**. Templates in the shared unfiled public folder hang off the Organization Id; templates in a user's personal folder hang off that User's Id. An inventory query that joins to `Folder` — or a retrieve that enumerates `EmailFolder` members — sees neither. Those templates still send, still hold merge fields against live objects, and still show up in users' send dialogs.

**When it bites you:** Alert-sprawl audits, org migrations, and "we retrieved all the templates" claims before a cutover.

**How to avoid it:** Inventory from the object, not from the folder tree, and read `IsActive` and `TimesUsed` rather than assuming an unfiled template is dead. Note `TimesUsed` is a Classic-era counter and is "not typically used with Lightning Experience templates", so a zero there is not proof of disuse for an `SFX` template.

```sql
SELECT Id, DeveloperName, FolderId, FolderName, TemplateType, UiType,
       IsActive, TimesUsed, LastUsedDate
FROM EmailTemplate
ORDER BY FolderName NULLS FIRST, DeveloperName
```

Body size is also a real ceiling on this object: `HtmlValue` is limited to 384 KB, which an inlined-image HTML template can reach.

> Sources: Object Reference, `EmailTemplate` — `FolderId` ("Refers To: Folder, Organization, User"), `TimesUsed` ("Used with Salesforce Classic templates. Not typically used with Lightning Experience templates"), `HtmlValue` ("Limit: 384 KB"), `IsActive`, `TemplateType`, `UIType`.
