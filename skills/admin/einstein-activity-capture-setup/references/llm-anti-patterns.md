# LLM Anti-Patterns — Einstein Activity Capture Setup

Common mistakes AI coding assistants make when generating or advising on Einstein Activity Capture Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Omitting PSL Assignment as a Required Step

**What the LLM generates:** A setup guide that says "Enable EAC in Setup, create a Configuration profile, and add users to the profile." The guide skips or buries the Permission Set License assignment step, treating it as optional or self-evident.

**Why it happens:** LLMs conflate EAC user assignment (adding users to a Configuration profile) with the separate PSL entitlement step. Training data often shows only the Configuration profile UI, not the PSL assignment flow in a different area of Setup.

**Correct pattern:**

```text
REQUIRED sequence for EAC user enablement:

1. Setup > Company Information > Permission Set Licenses
   → Confirm "Einstein Activity Capture" PSL has available seats

2. For EACH user: Setup > Users > [User] > Permission Set License Assignments
   → Assign "Einstein Activity Capture" PSL
   → Bulk assignment via Data Loader INSERT on PermissionSetLicenseAssign is supported

3. ONLY after PSL is assigned:
   → Open EAC Configuration profile
   → Add user to Assigned Users list

If PSL is not assigned first, Configuration assignment appears to succeed
but sync never starts and no error is surfaced.
```

**Detection hint:** Flag any EAC setup guide that does not mention "Permission Set License" or "PSL" as a distinct step before Configuration profile assignment.

---

## Anti-Pattern 2: Recommending Org-Level OAuth for Google Workspace

**What the LLM generates:** "For large rollouts, use Org-Level OAuth to avoid per-user authorization" — applied generically without distinguishing between Microsoft 365 and Google Workspace. The guide instructs admins to configure Org-Level OAuth for Google Workspace users.

**Why it happens:** LLMs describe Org-Level OAuth as the best practice for enterprise rollouts (which is true for Microsoft 365) but fail to apply the platform constraint that Org-Level OAuth is Microsoft 365-only. Google Workspace API architecture does not support the same AAD-style tenant consent model.

**Correct pattern:**

```text
Auth type selection by email platform:

Google Workspace (Gmail / Google Calendar):
  → User-Level OAuth ONLY
  → Each user must individually connect their account in:
    Profile > Settings > Connected Accounts
  → No Org-Level OAuth option exists for Google Workspace

Microsoft 365 / Exchange Online:
  → User-Level OAuth: each user connects own account (simpler setup, more support overhead)
  → Org-Level OAuth: admin consents via Azure AD, no per-user action needed
    (preferred for rollouts >50 users)

Mixed-platform orgs: create SEPARATE Configuration profiles per email platform
```

**Detection hint:** Flag any guide that recommends Org-Level OAuth without first confirming the email platform is Microsoft 365, or that uses "Org-Level OAuth" and "Google" in the same instruction.

---

## Anti-Pattern 3: Claiming EAC Queryability Without Version Context

**What the LLM generates:** Either "EAC-synced emails are stored as EmailMessage records and you can query them with SOQL" — OR the opposite: "EAC data is in a separate Einstein data store and cannot be queried via SOQL." Either claim may be wrong depending on the org's Salesforce release version.

**Why it happens:** The storage model for EAC changed in Summer '25. Pre-Summer '25 training data shows the separate Einstein data store model (not SOQL queryable via standard objects). Post-Summer '25, synced emails are standard EmailMessage records. LLMs interpolate from whichever version dominates their training data without flagging the version dependency.

**Correct pattern:**

```text
EAC data storage — version-dependent behavior:

Pre-Summer '25:
  → Synced emails: separate Einstein data store, NOT standard EmailMessage records
  → NOT queryable via SOQL on Task, Event, or EmailMessage
  → Visible only in Activity Timeline UI component
  → Does NOT count against org file storage

Summer '25+:
  → Synced emails: standard EmailMessage records, SOQL queryable
  → SELECT Id, Subject, FromAddress, ToAddress FROM EmailMessage WHERE ...
  → DOES count against org file storage

Always confirm the org's Salesforce release version before advising on queryability.
```

**Detection hint:** Any EAC advice about SOQL queryability or storage that does not mention Salesforce release version dependency should be flagged for review.

---

## Anti-Pattern 4: Treating Exclusion Rules as Post-Launch Configuration

**What the LLM generates:** A rollout guide that says: "Enable EAC, assign users, and then add exclusion rules for any domains you don't want to sync." Or an incident response guide that says: "Now that sensitive emails have synced, add the domain to the exclusion list to stop future syncs and the existing records will be cleaned up."

**Why it happens:** LLMs present exclusion rules as a configuration detail rather than a pre-launch gate. They also incorrectly imply that adding an exclusion rule retroactively cleans up already-synced data — mirroring how blocklist systems work in other contexts.

**Correct pattern:**

```text
Exclusion rule behavior:
  → Exclusions are NOT retroactive
  → Adding an exclusion prevents FUTURE syncs from the excluded domain/address
  → Previously synced emails from that domain REMAIN on Salesforce records
  → Manual deletion required if retroactive removal is needed:
    SELECT Id FROM EmailMessage WHERE FromAddress LIKE '%excluded-domain.com%'
    → Hard-delete via Data Loader

Pre-launch gate requirement:
  → Obtain signed-off exclusion list from Legal and Compliance BEFORE any users
    are added to a Configuration profile
  → Exclusion configuration must be complete and reviewed before first user sync
```

**Detection hint:** Flag any setup guide that describes exclusion rule configuration as a step that comes AFTER user assignment or as a post-launch cleanup mechanism.

---

## Anti-Pattern 5: Ignoring Storage Growth for High-Volume Orgs on Summer '25+

**What the LLM generates:** A capacity plan or storage estimate for EAC that either states EAC does not consume org storage (pre-Summer '25 behavior), or omits any mention of storage growth calculations for high-volume deployments.

**Why it happens:** Until Summer '25, EAC lived outside org storage. Most LLM training data reflects this model. Even for post-Summer '25 knowledge, LLMs often omit volume-based storage calculations because they require combining EAC email volume estimates with per-message storage — a multi-step calculation that LLMs frequently skip.

**Correct pattern:**

```text
EAC storage planning for Summer '25+ orgs:

Estimate monthly storage growth:
  (Users) x (avg emails/day) x (avg email size KB) x 30 days / 1,024 = GB/month

Example: 500 reps x 40 emails/day x 20 KB x 30 / 1,024 ≈ 11.7 GB/month

Planning steps:
1. Check current org storage: Setup > Storage Usage
2. Calculate EAC-driven monthly storage growth using the formula above
3. If growth will exceed 80% of storage capacity within 6 months:
   a. Purchase additional storage, OR
   b. Configure email retention/archival policy, OR
   c. Limit EAC sync to high-value users only
4. Set a storage alert at 80% capacity
5. Reassess storage quarterly after go-live

Do NOT enable EAC for all users on Summer '25+ without a storage plan.
```

**Detection hint:** Flag any EAC enablement guide for Summer '25+ orgs that does not include a storage growth calculation or storage planning step for deployments with more than 50 active users.

---

## Anti-Pattern 6: Assuming All Synced Emails Appear on Related Records

**What the LLM generates:** "Once EAC is configured, all synced emails will automatically appear on the Activity Timeline of the related Contact, Lead, Opportunity, and Account records."

**Why it happens:** This is the intended behavior, and LLMs state the ideal outcome without surfacing the matching failure modes. EAC matching depends on email address data quality — a prerequisite that LLMs commonly omit.

**Correct pattern:**

```text
EAC email matching behavior:
  → EAC matches emails to records by comparing sender/recipient email addresses
    against Contact and Lead records in the org
  → If NO matching Contact or Lead is found: email goes to Unresolved Items queue
  → If MULTIPLE Contacts share the same email address: match is ambiguous,
    email may go to Unresolved Items or match to the first found
  → Matched email appears on Activity Timeline of the matching Contact AND
    any related Opportunity/Account/Case via the Contact relationship

Pre-launch data quality steps:
  1. Confirm key Contacts have Email field populated
  2. Run duplicate Contact report filtered by Email address
  3. Resolve duplicate emails before go-live
  4. After go-live: monitor Setup > Einstein Activity Capture > Unresolved Items weekly

Never claim "all emails will appear on records" without verifying Contact email data quality.
```

**Detection hint:** Flag any EAC setup guide that does not mention the Unresolved Items queue or Contact email address matching requirements.
