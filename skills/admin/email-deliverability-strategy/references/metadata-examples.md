# Metadata Examples — Email Deliverability (Salesforce Core)

Deployable shapes for the **Salesforce Core** deliverability surface: the org's email administration settings, email authorization, DKIM keys, email relay, org-wide addresses, and bounce reporting.

Field names, enum values, defaults and the skeleton XML come from the Metadata API Developer Guide (`EmailAdministrationSettings`, `EmailAuthorizationSettings`, `Settings`) and the Object Reference (`EmailDomainKey`, `EmailRelay`, `EmailDomainFilter`, `OrgWideEmailAddress`, `Contact`, `Lead`); the worked examples extend the guides' own samples to a realistic two-domain org.

Marketing Cloud sending domains, dedicated IPs, and warm-up have **no** Core metadata surface — see `SKILL.md` § Core Concepts and `references/examples.md` for that layer.

Lint everything below with:

```bash
python3 skills/admin/email-deliverability-strategy/scripts/check_email_deliverability_strategy.py \
  --manifest-dir force-app/main/default
```

---

## Where each control actually lives

| Control | Surface | Deployable? | API |
|---|---|---|---|
| Bounce handling, SPF compliance, Compliance BCC, TLS restriction, external-sender footers | `EmailAdministrationSettings` → `settings/EmailAdministration.settings-meta.xml` | Yes, Metadata API | 47.0+ (api_meta.txt L114866) |
| From-address substitution for unverified domains | `EmailAuthorizationSettings` → `settings/EmailAuthorization.settings-meta.xml` | Yes, Metadata API | 66.0+ (api_meta.txt L115069) |
| DKIM signing keys | `EmailDomainKey` **sObject** | No metadata type — API/Data Loader/Setup only | 28.0+ (object_reference.txt L103512-103514) |
| Email relay through your own SMTP server | `EmailRelay` **sObject** | No metadata type | 43.0+ (object_reference.txt L104890-104892) |
| Which domains a relay applies to | `EmailDomainFilter` **sObject** | No metadata type | 43.0+ (object_reference.txt L103422-103424) |
| Org-wide From addresses and their verification state | `OrgWideEmailAddress` **sObject** | No metadata type | `IsVerified` 58.0+ (object_reference.txt L206797-206804) |
| Deliverability **Access Level** (No access / System email only / All email) | Setup page only | **No** — absent from the `EmailAdministrationSettings` field table (api_meta.txt L114869-114996) and from the whole Metadata API guide | UNVERIFIED (2026-09-05): the three option labels are the Setup UI's, quoted from the sibling `devops/sandbox-data-isolation-gotchas` skill; help.salesforce.com is not fetchable from this repo. The *effect* is grounded — a blocked org raises `System.NoAccessException: The organization is not permitted to send email.` (apexrefguide.txt L225158). |

`EmailDomainKey`, `EmailRelay`, `EmailDomainFilter` and `OrgWideEmailAddress` all support `create() delete() describeSObjects() query() retrieve() update() upsert()` (object_reference.txt L103518, L104896, L103428, L206755-206757), which is what makes the Data Loader CSVs below legal.

---

## 1. `EmailAdministration.settings-meta.xml`

Every element here appears in the guide's field table (api_meta.txt L114869-114996). The guide's own sample is at L114998-115022; this extends it to a production org that sends externally, relays through corporate SMTP, and BCCs a compliance archive.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EmailAdministrationSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableComplianceBcc>true</enableComplianceBcc>
    <enableEmailConsentManagement>true</enableEmailConsentManagement>
    <enableEmailSenderIdCompliance>false</enableEmailSenderIdCompliance>
    <enableEmailSpfCompliance>true</enableEmailSpfCompliance>
    <enableEmailToSalesforce>false</enableEmailToSalesforce>
    <enableEmailWorkflowApproval>false</enableEmailWorkflowApproval>
    <enableEnhancedEmailEnabled>true</enableEnhancedEmailEnabled>
    <enableHandleBouncedEmails>true</enableHandleBouncedEmails>
    <enableHtmlEmail>false</enableHtmlEmail>
    <enableInternationalEmailAddresses>true</enableInternationalEmailAddresses>
    <enableListEmailLogActivities>true</enableListEmailLogActivities>
    <enableResendBouncedEmails>false</enableResendBouncedEmails>
    <enableRestrictTlsToDomains>true</enableRestrictTlsToDomains>
    <enableSendViaExchangePref>false</enableSendViaExchangePref>
    <enableSendViaGmailPref>false</enableSendViaGmailPref>
    <enableUseOrgFootersForExtTrans>false</enableUseOrgFootersForExtTrans>
    <sendMassEmailNotification>true</sendMassEmailNotification>
    <sendTextOnlySystemEmails>false</sendTextOnlySystemEmails>
</EmailAdministrationSettings>
```

How to read it:

- **The filename is `EmailAdministration.settings`, not what the guide's prose says.** api_meta.txt L114855 reads verbatim: `EmailAdministrationSettings values are stored in the EmailAdminstration.settings file in the settings directory.` — "Adminstration" is missing an `i`. The general `Settings` rule (api_meta.txt L108379-108383, "The filename uses the format *Setting feature*`.settings`… the SecuritySettings file would be `Security.settings`") and the guide's own package.xml sample (`<members>EmailAdministration</members>`, api_meta.txt L115029) both give the correct spelling.
- `enableEmailSpfCompliance` **defaults to `true`** — the only field in the type whose security-ish default is on (api_meta.txt L114893-114895). Setting it `false` to "fix" a relay problem silently drops SPF compliance for the whole org.
- `enableEmailSenderIdCompliance` cannot be `true` unless `enableEmailSpfCompliance` is `true` (api_meta.txt L114884-114887). The guide adds its own caution beside it: "Evaluate the multiple standard email security protocols (SPF, DKIM, and DMARC) supported by Salesforce before you enable this setting" (L114889-114891).
- `enableResendBouncedEmails` cannot be `true` unless `enableHandleBouncedEmails` is `true` (api_meta.txt L114946-114950).
- `enableComplianceBcc` is only half the configuration: "To use this feature, you must specify an email address in **Compliance BCC Email** in Setup" (api_meta.txt L114872-114877). That address has no metadata element, so the deploy succeeds and the BCC never fires. The checker cross-checks it against `deliverability/email-policy.json`.
- `enableRestrictTlsToDomains` likewise needs two things set on the **Deliverability** Setup page: a TLS Setting other than `Preferred`, and the comma-separated domain list (api_meta.txt L114952-114965). Domains not in the list fall back to `Preferred`.
- `enableHtmlEmail` is **Email-to-Case inbound rendering**, not outbound HTML (api_meta.txt L114925-114931). Do not touch it while tuning outbound deliverability — see `admin/email-to-case-configuration`.
- **Omitted on purpose:** `enableSendThroughGmailPref`, which the guide documents as one word — `Deprecated.` (api_meta.txt L114964). The live field is `enableSendViaGmailPref` (L114969).
- The type has exactly 19 documented fields. Any other element name fails the deploy; the checker rejects them before you spend a deploy cycle finding out.

---

## 2. `EmailAuthorization.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EmailAuthorizationSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableSubstituteFromAddress>false</enableSubstituteFromAddress>
</EmailAuthorizationSettings>
```

How to read it:

- One field, `enableSubstituteFromAddress`, available in API 66.0 and later (api_meta.txt L115069, L115074).
- `false` (the default) means, verbatim: "Salesforce users and automations can send messages from Salesforce only when the email domain is verified" (api_meta.txt L115081-115082).
- `true` means Salesforce rewrites the From address to `email@UniqueId.sfcustomeremail.com`, where `UniqueId` is the org ID or Experience Cloud site ID (api_meta.txt L115076-115080).
- Leaving it `false` is the correct deliverability posture — a substituted `sfcustomeremail.com` From address is not your domain, so it carries none of your SPF/DKIM/DMARC reputation. Setting it `true` is a *fallback for unverified domains*, not a fix for one.
- The field "applies only to outbound email that requires domain-level verification" (api_meta.txt L115082-115084), so it interacts directly with `OrgWideEmailAddress.IsVerified` in § 5.

---

## 3. DKIM key inventory + the SOQL that produces it

`EmailDomainKey` is an sObject, so the inventory is a query result, not a retrieve. Keep the inventory in source control next to the settings files; it is the only durable record of which selector is live and when it is due for rotation.

```sql
SELECT Id, Domain, DomainMatch, Selector, AlternateSelector,
       TxtRecordName, AlternateTxtRecordName, TxtRecordsPublishState,
       KeySize, IsActive, CreatedDate, LastModifiedDate
FROM EmailDomainKey
ORDER BY Domain, IsActive DESC, CreatedDate DESC
```

```bash
sf data query \
  --query "SELECT Id, Domain, DomainMatch, Selector, AlternateSelector, TxtRecordName, AlternateTxtRecordName, TxtRecordsPublishState, KeySize, IsActive FROM EmailDomainKey ORDER BY Domain" \
  --target-org prod --result-format json > deliverability/dkim-keys.raw.json
```

`deliverability/dkim-keys.json` — the reviewed inventory the checker reads:

```json
{
  "capturedOn": "2026-09-05",
  "capturedFrom": "prod",
  "rotationIntervalMonths": 12,
  "dkimKeys": [
    {
      "domain": "em.retailbrand.com",
      "domainMatch": "DomainAndSubdomains",
      "selector": "em2026a",
      "alternateSelector": "em2026b",
      "keySize": 2048,
      "isActive": true,
      "txtRecordsPublishState": "Published",
      "lastRotatedOn": "2026-03-01",
      "nextRotationDue": "2027-03-01",
      "owner": "platform-ops@retailbrand.com"
    },
    {
      "domain": "retailbrand.com",
      "domainMatch": "DomainOnly",
      "selector": "corp2026a",
      "alternateSelector": "corp2026b",
      "keySize": 2048,
      "isActive": true,
      "txtRecordsPublishState": "Published",
      "lastRotatedOn": "2026-01-15",
      "nextRotationDue": "2027-01-15",
      "owner": "platform-ops@retailbrand.com"
    },
    {
      "domain": "em.retailbrand.com",
      "domainMatch": "DomainAndSubdomains",
      "selector": "em2024a",
      "alternateSelector": "em2024b",
      "keySize": 1024,
      "isActive": false,
      "txtRecordsPublishState": "Published",
      "lastRotatedOn": "2024-02-10",
      "nextRotationDue": null,
      "retiredOn": "2026-03-01",
      "note": "Superseded. DNS CNAMEs left in place for 30 days after retirement so in-flight mail still verifies."
    }
  ]
}
```

How to read it:

- `DomainMatch` is a **restricted** picklist with exactly three values (object_reference.txt L103573-103594):
  `DomainOnly` (signs `example.com` but not `mail.example.com`), `SubdomainsOnly` (signs `mail.example.com` but not `example.com`), `DomainAndSubdomains` (both). A `DomainOnly` key on the parent domain does **not** sign mail from the marketing subdomain.
- `KeySize` is `1024` or `2048` only, available in API 45.0 and later (object_reference.txt L103603-103611). The 1024-bit key above is retired for that reason.
- `TxtRecordsPublishState` is `Published`, `Publishing in progress`, or `Publishing failed` (object_reference.txt L103665-103674). An `IsActive` key whose state is not `Published` signs mail with a key receivers cannot look up — every message fails DKIM.
- `AlternateSelector` / `AlternatePublicKey` exist so "Salesforce [can] auto-rotate domain keys" (object_reference.txt L103529-103545). `AlternatePublicKey` and both TXT-record-name fields are **read-only**; you supply the selectors, Salesforce supplies the records.
- `lastRotatedOn` / `nextRotationDue` / `owner` are **this repo's** bookkeeping fields, not platform fields. Nothing on the platform expires a DKIM key or reminds you to roll it — the checker is the reminder.

The creation order the Object Reference prescribes (object_reference.txt L103679-103698), which is not the order Setup implies:

1. Insert `Domain`, `DomainMatch`, `Selector`, and `AlternateSelector`. Salesforce publishes its TXT record to DNS.
2. Read back `TxtRecordName` and `AlternateTxtRecordName`.
3. Publish two CNAMEs in **your** DNS:
   `<selector>._domainkey.<domain> IN CNAME <txtRecordName>`
   `<alternateSelector>._domainkey.<domain> IN CNAME <alternateTxtRecordName>`
4. **Only then** set `IsActive` to `true`.

```csv
Domain,DomainMatch,Selector,AlternateSelector,IsActive
em.retailbrand.com,DomainAndSubdomains,em2026a,em2026b,false
retailbrand.com,DomainOnly,corp2026a,corp2026b,false
```

```bash
# Step 1 — insert inactive, then read back the TXT record names for DNS
sf data import bulk --sobject EmailDomainKey --file deliverability/dkim-keys-insert.csv --target-org prod
sf data query --query "SELECT Id, Domain, Selector, TxtRecordName, AlternateSelector, AlternateTxtRecordName, TxtRecordsPublishState FROM EmailDomainKey WHERE IsActive = false" --target-org prod

# Step 4 — after both CNAMEs resolve and TxtRecordsPublishState = 'Published'
sf data update record --sobject EmailDomainKey --record-id 0EJ...  --values "IsActive=true" --target-org prod
```

`PrivateKey` is not in any CSV above and never should be: "This field doesn't contain the actual private key, but a value that represents the key in our system… The actual private key can't be leaked. You can't use the value to do your own email signing." (object_reference.txt L103622-103626). Post-Critical-Update it is no longer visible at all (L103618).

---

## 4. Email relay + domain filter (Data Loader CSVs)

`EmailRelay` routes Salesforce's outbound mail through your own SMTP servers so it inherits your corporate IP reputation instead of Salesforce's shared pools.

`deliverability/email-relay.csv`:

```csv
Host,Port,TlsSetting,IsRequireAuth,AuthType,Username
smtp-relay.retailbrand.com,587,RequiredVerify,true,PLAIN,sfdc-relay@retailbrand.com
```

`deliverability/email-domain-filter.csv` (load **after** the relay; `EmailRelayId` comes from the relay's Id):

```csv
EmailRelayId,PriorityNumber,FromDomain,ToDomain,IsActive
0RL...,10,retailbrand.com,*.retailbrand.com,true
0RL...,20,retailbrand.com,*,true
```

How to read it:

- **Order is forced by the platform.** "You must create an email relay in Setup or through the EmailRelay object before you can use the EmailDomainFilter object" (object_reference.txt L103433). And in the other direction: "An email relay must be associated with an active email domain filter to take effect" (object_reference.txt L105018). A relay with no active filter is inert, and a filter with no relay cannot be inserted.
- `Port` is a **restricted** picklist: `25`, `587`, `10025`, `11025` (object_reference.txt L104953-104971). No other value loads.
- `TlsSetting` is a restricted picklist of five (object_reference.txt L104973-105000). Only `RequiredVerify` guarantees delivery is refused rather than downgraded: Salesforce continues "only if the remote server supports TLS, the certificate is signed by a valid certificate authority, and the common name presented in the certificate matches the domain or mail exchange to which Salesforce is connected." `Preferred` and `PreferredVerify` both silently fall back to plaintext when TLS is unavailable.
- `IsRequireAuth = true` **forces** `TlsSetting = RequiredVerify` (object_reference.txt L104935-104941), and makes `Username` and `Password` required (L104944-104949, L105001-105009). `Password` is an `encryptedstring`; keep it out of the CSV in source control and set it in a separate authenticated step.
- `AuthType` is `PLAIN` (default) or `LOGIN`, API 52.0+ (object_reference.txt L104905-104926), available only when SMTP Auth is on.
- `PriorityNumber` must be unique; "Filters are evaluated in ascending order… Processing stops after the first matching filter is applied." A blank priority "is assigned the next available number and is processed last" (object_reference.txt L103476-103493). The two rows above are ordered deliberately: internal mail first, catch-all second.
- `FromDomain` and `ToDomain` are both optional, comma-separated, and support the wildcard character (object_reference.txt L103459-103466, L103495-103502). A filter with neither matches everything.
- All three of "Email Administration", "Customize Application", and "View Setup" are required to touch either object (object_reference.txt L103432, L104899).
- The guides attach the same warning to both objects: "If you also plan to activate Bounce Management and Email Compliance Management, confirm with your email admin that your company allows relaying email sent from Salesforce" (object_reference.txt L103506-103509, L105022-105025). A relay that refuses Salesforce-origin mail turns every send into a relay rejection.

---

## 5. Org-wide address verification query

`OrgWideEmailAddress` is the From identity for email alerts and Apex sends. An unverified address is the most common cause of "the Flow ran but nobody got the email".

```sql
SELECT Id, Address, DisplayName, Purpose, IsAllowAllProfiles, IsVerified
FROM OrgWideEmailAddress
WHERE IsVerified = false
ORDER BY Address
```

```bash
sf data query --query "SELECT Id, Address, DisplayName, Purpose, IsAllowAllProfiles, IsVerified FROM OrgWideEmailAddress WHERE IsVerified = false" --target-org prod
```

How to read it:

- `IsVerified` "indicates whether the email address has been verified by its owner", defaults to `false`, and is available in API version 58.0 and later (object_reference.txt L206797-206804). Below 58.0 the field is absent and this query throws — check the org's API version before scripting it.
- `Purpose` is a restricted picklist: `DefaultNoreply`, `UserSelection`, `UserSelectionAndDefaultNoReply`. "`UserSelection` allows users with the correct profile to select the address as the From address for an email" (object_reference.txt L206817-206824).
- `IsAllowAllProfiles` defaults to `false`; when false "only specified user profiles can use this object when sending email" (object_reference.txt L206787-206794). The profile allow-list is not on this object, so a verified address can still be unusable by the running user.
- The Id is passed to `sendEmail()` for a `SingleEmailMessage` (object_reference.txt L206831-206832), and named declaratively as `WorkflowAlert.senderAddress` with `senderType` = `OrgWideEmailAddress` (api_meta.txt L140010-140030). Sender identity is `admin/email-templates-and-alerts`' subject; this skill only cares that the address is verified and its domain is DKIM-signed.

---

## 6. Bounce report SOQL

Bounce management writes to fields on Contact, Lead, and person accounts. These queries are the Core-org equivalent of a suppression-list audit.

```sql
-- Contacts with a recorded hard bounce, newest first
SELECT Id, Name, Email, EmailBouncedDate, EmailBouncedReason, IsEmailBounced, AccountId
FROM Contact
WHERE IsEmailBounced = true
ORDER BY EmailBouncedDate DESC NULLS LAST
LIMIT 200

-- Bounce volume by reason over the last 90 days (Leads have no IsEmailBounced field)
SELECT EmailBouncedReason, COUNT(Id) bounces
FROM Lead
WHERE EmailBouncedDate = LAST_N_DAYS:90
GROUP BY EmailBouncedReason
ORDER BY COUNT(Id) DESC

-- Person accounts
SELECT Id, Name, PersonEmail, PersonEmailBouncedDate, PersonEmailBouncedReason
FROM Account
WHERE PersonEmailBouncedDate != NULL
ORDER BY PersonEmailBouncedDate DESC
```

How to read it:

- All three field sets are documented as populated only "if bounce management is activated" (object_reference.txt L71679, L71690, L163389, L13777) — which is `enableHandleBouncedEmails` in § 1. With it off, the queries return zero rows in an org that is bouncing heavily.
- `Contact.IsEmailBounced` is boolean, read-only (`Defaulted on create, Filter, Group, Sort` — no Create or Update) and indicates "whether the email results in a **soft or hard** bounce" (object_reference.txt L71802-71809), while `Contact.EmailBouncedDate` is documented for a **hard** bounce only (L71679-71681). The two do not answer the same question; a `true` flag with a null date is a soft bounce.
- **Lead has no `IsEmailBounced` field at all** — only `EmailBouncedDate` and `EmailBouncedReason` (object_reference.txt L163384-163401). A report that unions Contact and Lead on `IsEmailBounced` silently drops every bounced Lead.
- Lead's bounce fields are **not createable** (`Filter, Nillable, Sort, Update` — object_reference.txt L163384-163387), while Contact's are (`Create, Filter, Nillable, Sort, Update` — L71663-71666). A migration CSV carrying bounce history inserts fine on Contact and fails on Lead.
- Both objects carry the same note: "Email bounce functionality isn't triggered by record updates, including updates to this field" (object_reference.txt L71682-71684, L163390-163392). Blanking `EmailBouncedDate` through the Data Loader clears the flag without re-testing the address.

---

## 7. package.xml and deploy

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>EmailAdministration</members>
        <members>EmailAuthorization</members>
        <name>Settings</name>
    </types>
    <version>66.0</version>
</Package>
```

The member name is "the component metadata type name without the 'Settings' suffix" (api_meta.txt L108368-108370). `EmailAuthorization` requires API 66.0 or later; drop that member and lower `<version>` for an older org.

The `*` wildcard does **not** work for an individual feature setting: "The wildcard character `*` in the package.xml manifest file doesn't apply to metadata types for feature settings. The wildcard applies only when retrieving all settings, not for an individual setting" (api_meta.txt L115113-115116).

```bash
# 1. Pull the org's current email settings into source before editing anything
sf project retrieve start --manifest manifest/email-deliverability-package.xml --target-org prod

# 2. Lint the settings XML, the DKIM inventory, and the policy file
python3 skills/admin/email-deliverability-strategy/scripts/check_email_deliverability_strategy.py \
  --manifest-dir force-app/main/default

# 3. Validate without deploying (settings are org-wide; there is no partial rollback)
sf project deploy validate --manifest manifest/email-deliverability-package.xml --target-org prod

# 4. Deploy
sf project deploy start --manifest manifest/email-deliverability-package.xml --target-org prod
```

Deploy order across the whole surface, because only step 3 is metadata:

1. DKIM keys inserted inactive → CNAMEs published → keys activated (§ 3).
2. Org-wide addresses created and verified by their owners (§ 5).
3. `EmailAdministration.settings` and `EmailAuthorization.settings` deployed (§ 1, § 2).
4. Relay and its domain filter loaded, relay first (§ 4).
5. Deliverability **Access Level** set by hand in Setup on any sandbox that must not send.

---

## 8. Verification

| # | Check | How |
|---|---|---|
| 1 | Settings landed | `sf data query --query "SELECT Id FROM OrgWideEmailAddress LIMIT 1"` succeeds and the deploy result reports `EmailAdministration.settings` as `Changed`. There is no queryable sObject for the settings themselves — re-retrieve with the manifest in § 7 and diff against source. |
| 2 | DKIM is live | `SELECT Domain, Selector, IsActive, TxtRecordsPublishState FROM EmailDomainKey WHERE IsActive = true` returns one row per sending domain, all `Published`. |
| 3 | DNS agrees with the platform | For each active key, `dig CNAME <selector>._domainkey.<domain>` resolves to the `TxtRecordName` value from check 2. A `Published` state with an unresolvable CNAME means Salesforce published its half and DNS never got yours. |
| 4 | From addresses are usable | `SELECT Address, IsVerified FROM OrgWideEmailAddress WHERE IsVerified = false` returns no row that any live alert or Apex send references. |
| 5 | Relay is actually in the path | `SELECT Id, Host, TlsSetting FROM EmailRelay` and `SELECT EmailRelayId, PriorityNumber, IsActive FROM EmailDomainFilter WHERE IsActive = true` — at least one active filter must point at the relay, or the relay is inert (object_reference.txt L105018). |
| 6 | Bounce handling is on | Setup → Deliverability shows Bounce Administration enabled, and `SELECT COUNT(Id) FROM Contact WHERE IsEmailBounced = true` is non-zero in an org with any sending history. Zero in a mature org means the setting is off, not that nothing bounces. |
| 7 | Compliance BCC actually fires | Send one test email and confirm arrival at the Compliance BCC address. `enableComplianceBcc` deploys clean whether or not the address is set in Setup (api_meta.txt L114872-114877). |

---

## 9. DNS record checklist (SPF / DKIM / DMARC)

> **Not Salesforce-guide-grounded.** The three records below are internet-standard mail authentication (RFC 7208 SPF, RFC 6376 DKIM, RFC 7489 DMARC) plus receiver policy set by Google and Yahoo. Nothing in the Metadata API guide, Object Reference, or Apex guides specifies SPF or DMARC record syntax. The only DNS shape Salesforce's own documentation prescribes is the DKIM CNAME pair in § 3.
>
> UNVERIFIED (2026-09-05): every include-host literal, threshold, and receiver requirement in this section. Take the exact `include:` value from Setup or from Marketing Cloud Setup → Private Domains for the org in hand; help.salesforce.com is not fetchable from this repo, and vendor include-hosts change.

| Record | Name | Value shape | Who supplies the literal |
|---|---|---|---|
| SPF | `<sending-domain>` TXT | `v=spf1 include:<salesforce-or-mc-include> include:<corporate-mta> ~all` | Salesforce/MC Setup. Exactly one SPF TXT per domain (RFC 7208); ≤ 10 DNS lookups. |
| DKIM | `<selector>._domainkey.<sending-domain>` CNAME | `<TxtRecordName from EmailDomainKey>` | **Salesforce** — grounded, § 3, object_reference.txt L103693-103698 |
| DKIM (alternate) | `<alternateSelector>._domainkey.<sending-domain>` CNAME | `<AlternateTxtRecordName>` | **Salesforce** — grounded, § 3 |
| DMARC | `_dmarc.<sending-domain>` TXT | `v=DMARC1; p=none; rua=mailto:<monitored-box>; fo=1` | You (RFC 7489) |

Sequence that avoids a self-inflicted outage: publish SPF and both DKIM CNAMEs first, activate the keys, let a week of mail flow, read the DMARC aggregate reports at `p=none`, and only then tighten the policy. Advancing to `p=quarantine` or `p=reject` while any legitimate sender is missing from SPF and unsigned by DKIM blocks that sender's mail, not a spoofer's.
