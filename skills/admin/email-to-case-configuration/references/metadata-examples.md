# Metadata Examples — Email-to-Case Configuration

Email-to-Case is not its own metadata type. It is the `emailToCase` block inside `CaseSettings`,
retrieved and deployed as the `Settings` member `Case`.

| What | Metadata type | File path | Since |
|---|---|---|---|
| Email-to-Case switches and routing addresses | `CaseSettings` → `emailToCase` (`EmailToCaseSettings`) | `settings/Case.settings-meta.xml` | API 27.0 (`CaseSettings`) |
| One routing address | `EmailToCaseRoutingAddress` (repeating `routingAddresses`) | same file | API 27.0 |
| Case assignment rule that reads the routing address's `caseOrigin` | `AssignmentRules` | `assignmentRules/Case.assignmentRules-meta.xml` | API 27.0+ |

Field names, types and enum values below come from *Metadata API Developer Guide*, `CaseSettings`
(api_meta L111632–112090: `EmailToCaseSettings` L111726, `EmailToCaseRoutingAddress` L112010,
sample definition L112160).
PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

---

## `settings/Case.settings-meta.xml` — On-Demand with two routing addresses

Shaped from the guide's own `CaseSettings` sample definition (api_meta L112160–112215) and extended
to two real support channels. The guide's sample uses an `Outlook` second address; this one uses two
`EmailToCase` addresses, which is the shape a support org actually deploys.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CaseSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <defaultCaseOwner>Tier_1_General</defaultCaseOwner>
    <defaultCaseOwnerType>Queue</defaultCaseOwnerType>
    <defaultCaseUser>integration.user@acme.example</defaultCaseUser>
    <emailToCase>
        <enableEmailToCase>true</enableEmailToCase>
        <enableOnDemandEmailToCase>true</enableOnDemandEmailToCase>
        <enableHtmlEmail>true</enableHtmlEmail>
        <enableE2CAttachmentAsFile>true</enableE2CAttachmentAsFile>
        <enableE2CDeduplicateAttachments>true</enableE2CDeduplicateAttachments>
        <enableE2CSourceTracking>true</enableE2CSourceTracking>
        <enableThreadTokenInBody>true</enableThreadTokenInBody>
        <enableThreadTokenInSubject>true</enableThreadTokenInSubject>
        <useEmailHeadersForThreading>true</useEmailHeadersForThreading>
        <notifyOwnerOnNewCaseEmail>false</notifyOwnerOnNewCaseEmail>
        <preQuoteSignature>true</preQuoteSignature>
        <overEmailLimitAction>Requeue</overEmailLimitAction>
        <unauthorizedSenderAction>Bounce</unauthorizedSenderAction>
        <routingAddresses>
            <addressType>EmailToCase</addressType>
            <routingName>ACME General Support</routingName>
            <emailAddress>support@acme.example</emailAddress>
            <caseOrigin>Email</caseOrigin>
            <casePriority>Medium</casePriority>
            <createTask>false</createTask>
            <saveEmailHeaders>true</saveEmailHeaders>
        </routingAddresses>
        <routingAddresses>
            <addressType>EmailToCase</addressType>
            <routingName>ACME Billing</routingName>
            <emailAddress>billing@acme.example</emailAddress>
            <caseOrigin>Billing</caseOrigin>
            <casePriority>Medium</casePriority>
            <createTask>false</createTask>
            <saveEmailHeaders>true</saveEmailHeaders>
        </routingAddresses>
    </emailToCase>
    <enableCaseFeed>true</enableCaseFeed>
    <enableDraftEmails>true</enableDraftEmails>
</CaseSettings>
```

### How to read it

- **`enableEmailToCase`, not `enable`.** The child of `emailToCase` is `enableEmailToCase`
  (api_meta L111726). A file written with `<enable>true</enable>` deploys without turning the
  feature on. The guide adds: "After Email-to-Case is enabled, it can't be disabled."
- **`enableOnDemandEmailToCase` is the mode switch.** `true` = On-Demand (Salesforce-hosted);
  omitted or `false` = Standard, which needs the local agent.
- **The queue owner is set once, at org level, not per address.** Both routing addresses above
  deliberately omit `caseOwner`. The guide's `caseOwner` description states: "Specifying a case
  owner here in the routing address sets a value of `defaultCaseOwner` in `CaseSettings`"
  (api_meta L112010 ff.). `defaultCaseOwner` is a single org-level field, so a second routing
  address that also sets `caseOwner` overwrites the first one's value. Per-channel ownership
  belongs in the assignment rule below, not in `caseOwner`.
- **`caseOwner` and `caseOwnerType` travel together.** `caseOwnerType` says whether the owner is a
  user or a queue; `caseOwner` without it is ambiguous and the checker script errors on it.
- **`caseOrigin` is the only per-address value an assignment rule can read.** See "Which Case field
  the routing address populates" below.
- **`emailServicesAddress` and `isVerified` are read-only** (api_meta L112010 ff.: "This field
  value is read-only and can't be modified"). They come back on retrieve and are ignored on deploy,
  so a fresh org's addresses arrive unverified no matter what the source file says.
- **`overEmailLimitAction`** (`EmailToCaseOnFailureActionType`) accepts `Bounce`, `Discard`,
  `Requeue` — what happens to mail received after the org exceeds its daily Email-to-Case limits.
  `unauthorizedSenderAction` accepts `Bounce` or `Discard` only (no `Requeue`).
- **Threading switches are two mutually exclusive pairs.** `enableThreadTokenInBody` /
  `enableThreadTokenInSubject` are "applicable only to orgs using Lightning Threading";
  `enableThreadIDInBody` / `enableThreadIDInSubject` are "applicable only to orgs that do not use
  Lightning Threading" (api_meta L111726 ff.). `useEmailHeadersForThreading` is the fallback:
  "metadata from incoming emails is used to match replies with cases if token-based threading
  doesn't produce a match".
  UNVERIFIED (2026-09-04): the Metadata API guide has no field that *switches* the org between
  Lightning Threading and legacy threading — only the four token/ID booleans that are conditional on
  it. There is no `enableEmailToCaseThreading` element in `EmailToCaseSettings`. Which mode the org
  is in must be read in Setup, not from this file.
- **`enableE2CAttachmentAsFile`** saves inbound attachments as Salesforce Files rather than
  Attachments; `enableE2CDeduplicateAttachments` links an already-present attachment to the new
  email instead of re-storing it when a reply threads onto an existing case.
- **`enableE2CSourceTracking`** — "the Case Source field is updated to Email for all cases that
  originate from Email-to-Case. Associated emails are marked as Read when the agent opens the case."

---

## Which Case field the routing address populates

| Routing address field | Lands on | Grounding |
|---|---|---|
| `caseOrigin` | `Case.Origin` (picklist; "The source of the case, such as Email, Phone, or Web. Label is Case Origin") | object_reference L62568 |
| `casePriority` | `Case.Priority` | object_reference, Case section L62202 ff. |
| `caseOwner` + `caseOwnerType` | `Case.OwnerId`, via the org-level `defaultCaseOwner` it writes | api_meta L112010 ff. |
| the routing address itself | **not a Case field** — `EmailMessage.EmailRoutingAddressId` | object_reference L104154 |

**There is no routing-address field on Case.** The Case field list in the Object Reference
(L62202–62900) contains none, and `Case.SourceId` — the field whose name invites the assumption —
is "The ID of the social post source" (object_reference L62668), nothing to do with Email-to-Case.
The routing address is recorded one object over, on the EmailMessage:
`EmailMessage.EmailRoutingAddressId` is a lookup to `EmailRoutingAddress` that "Stores the ID of the
email routing address used to create the email. This value is set when the email is processed by
Email-to-Case service. When this field is set, `EmailMessage.Incoming` cannot be false"
(object_reference L104154).

This is the answer to the open question in `admin/case-management-setup`
(`references/worked-example-case-intake.md`, "Routing-address to queue mapping"): assignment rule
criteria are Case fields, so **`Case.Origin` is the hand-off**. Give each routing address a distinct
`caseOrigin` value, add it to the `Case.Origin` picklist first, and route on it.
UNVERIFIED (2026-09-04): whether `EmailMessage.EmailRoutingAddressId` is populated early enough to
be readable by anything running at Case insert is not stated in the Object Reference; treat it as a
reporting field, not a routing input, until tested in a sandbox.

---

## `assignmentRules/Case.assignmentRules-meta.xml` — routing on those addresses

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignmentRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <assignmentRule>
        <fullName>Case_Intake</fullName>
        <active>true</active>
        <ruleEntry>
            <criteriaItems>
                <field>Case.Origin</field>
                <operation>equals</operation>
                <value>Billing</value>
            </criteriaItems>
            <assignedTo>Billing_Queue</assignedTo>
            <assignedToType>Queue</assignedToType>
        </ruleEntry>
        <ruleEntry>
            <criteriaItems>
                <field>Case.Origin</field>
                <operation>equals</operation>
                <value>Email</value>
            </criteriaItems>
            <assignedTo>Tier_1_General</assignedTo>
            <assignedToType>Queue</assignedToType>
        </ruleEntry>
        <ruleEntry>
            <assignedTo>Tier_1_General</assignedTo>
            <assignedToType>Queue</assignedToType>
        </ruleEntry>
    </assignmentRule>
</AssignmentRules>
```

Entries are first-match-wins and the last entry is the catch-all; the criteria grammar, the
`assignedToType` values and the deploy order for rules live in `admin/assignment-rules`
(`references/metadata-examples.md`). The auto-response rule file that pairs with this is in that
same skill — do not restate it here; only the sender constraint below is this skill's business.

---

## Forwarding and verification checklist

Order matters. Verification email can only be read once forwarding works, and inbound mail is only
accepted once the address is verified.

- [ ] `Case.Origin` picklist contains every `caseOrigin` value the routing addresses will stamp
      (`Email`, `Billing` above). A `caseOrigin` value that is not an active picklist entry stamps
      a value nobody can filter on in reports.
- [ ] Deploy `Settings:Case`, then open Setup → Email-to-Case and copy each address's
      Salesforce-generated `emailServicesAddress` (read-only; it is not in your source file).
- [ ] Mail server: one forwarding rule per channel, `support@acme.example` →
      *its own* `emailServicesAddress`, `billing@acme.example` → *its own*. One forwarder feeding
      both Salesforce addresses duplicates every case.
- [ ] Disable any "keep a copy in the mailbox and auto-reply" rule on the forwarding mailbox — the
      mailbox auto-reply is a second sender that can loop back into the routing address.
- [ ] Setup → Email-to-Case → the routing address → **Send Verification Email**. The mail arrives at
      the forwarding mailbox because the forward is now live. Click the link.
- [ ] Re-open the routing address and confirm it reads Verified. `isVerified` is read-only, so this
      cannot be asserted from the source file — only from the org.
- [ ] `authorizedSenders`, if set, is a comma-separated list of addresses or domains; everything else
      hits `unauthorizedSenderAction`. Leave it empty for a public support address.
- [ ] Send one real email to each public address; confirm one Case per email with the expected
      `Origin`, `Priority` and owning queue.

---

## `package.xml` and the commands

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Case</members>
        <name>AssignmentRules</name>
    </types>
    <version>62.0</version>
</Package>
```

The wildcard `*` does not work for an individual settings type — the guide states it "applies only
when retrieving all settings, not for an individual setting" (api_meta, CaseSettings, Wildcard
Support in the Manifest File). Name `Case` explicitly.

```bash
# Retrieve what production actually has, before changing anything
sf project retrieve start --metadata "Settings:Case" --target-org prod

# Check it before deploying
python3 skills/admin/email-to-case-configuration/scripts/check_email_to_case_configuration.py \
    --manifest-dir force-app/main/default --verbose

# Validate against production without committing the change
sf project deploy validate --metadata "Settings:Case" "AssignmentRules:Case" --target-org prod

# Deploy
sf project deploy start --metadata "Settings:Case" "AssignmentRules:Case" --target-org prod
```

---

## Verification

**1. Threading — did the reply land on the original case or make a new one?**

```sql
SELECT Id, ParentId, Parent.CaseNumber, Incoming, MessageDate,
       FromAddress, ToAddress, EmailRoutingAddressId, ThreadIdentifier
FROM EmailMessage
WHERE ParentId != null
  AND MessageDate = TODAY
ORDER BY ParentId, MessageDate
```

Read it this way: the inbound original and the customer's reply must share one `ParentId`, both with
`Incoming = true`, with the outbound agent reply (`Incoming = false`) between them. Two different
`ParentId` values for one conversation is a threading failure — go to `references/gotchas.md`.

`ThreadIdentifier` will be blank, and that is correct, not a fault: the Object Reference says of it
"This field is used by features that sync emails directly from an inbox into Salesforce. **This field
is not used by On-Demand Email-to-Case**" (object_reference L104638). Do not write a monitoring query
that asserts `ThreadIdentifier != null` — it will alert on every healthy case. Use `ParentId`.

**2. Did the right routing address create the case, with the right origin?**

```sql
SELECT Parent.CaseNumber, Parent.Origin, Parent.Priority, Parent.Owner.Name,
       EmailRoutingAddress.PersonalName, EmailRoutingAddress.Address
FROM EmailMessage
WHERE Incoming = true AND ParentId != null AND CreatedDate = TODAY
```

The `Parent` relationship on `ParentId` is the Case (object_reference L104467).
`EmailRoutingAddress` exposes `PersonalName` (display name, max 300 chars), `Address` (the customer-
facing address mail is forwarded *from*) and `EmailServicesAddress` (Salesforce-generated, forwarded
*to*) — object_reference L105032. Only admin users can query it: "To access this object,
Email-to-Case must be enabled. Only admin users can access this object."

**3. Loop test — the one that costs money if skipped.**

Send exactly one email to each public address, then watch for five minutes:

```sql
SELECT Origin, COUNT(Id) FROM Case WHERE CreatedDate = TODAY GROUP BY Origin
```

The count must stop at one per address. If it climbs, the auto-response sender is reaching a routing
address. The auto-response `senderEmail` (in `Case.autoResponseRules`, owned by
`admin/assignment-rules`) must never equal, alias to, or forward into any `emailAddress` in this
file. The checker script cross-references the two files and errors on a match.

**4. Setup check.** Setup → Email-to-Case: every routing address reads Verified, and the count of
addresses matches the count of `routingAddresses` elements in the deployed file. A removed element
is not inert — the guide warns "Removing an address from this list deletes it from the target org"
(api_meta L111726 ff.), so a partial file silently deletes the addresses it omits.
