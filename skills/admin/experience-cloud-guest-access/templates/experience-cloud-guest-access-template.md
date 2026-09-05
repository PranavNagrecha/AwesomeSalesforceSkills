# Experience Cloud Guest Access — Public Page Access Checklist

Use this template when configuring or reviewing guest user access on an Experience Cloud site.
Complete one copy per site.

---

## Site Information

**Site Name:**
**Site URL:**
**Site Template (LWR / Aura / Microsite):**
**Guest User Profile Name:**
**Date of Review:**
**Reviewed By:**

---

## Section 1: Page-Level Access Configuration

For each page in Experience Builder, record the access setting and whether it matches the intended audience.

| Page Name | Page Access Setting | Intended Audience | Correct? |
|---|---|---|---|
| (e.g., Home) | Public / Requires Login | Guest / Members Only | Yes / No |
| | | | |
| | | | |

**Action items from this section:**
- [ ] All public pages confirmed as intentionally public
- [ ] All members-only pages set to Requires Login

---

## Section 2: Guest User Profile — Object Permissions

For each object accessed by public pages, record the permissions granted and whether they are appropriate.

| Object | Read | Create | Edit | Delete | View All | Modify All | Appropriate? |
|---|---|---|---|---|---|---|---|
| (e.g., Knowledge) | Yes | No | No | No | No | No | Yes |
| | | | | | | | |
| | | | | | | | |

**Rules:**
- Read is the maximum appropriate permission for display-only objects.
- Create is allowed only for form-submission objects (case deflection, contact forms).
- Edit, Delete, View All, and Modify All must be OFF for all objects on the guest profile.

**Action items from this section:**
- [ ] No Edit, Delete, View All, or Modify All granted on guest profile

---

## Section 3: Guest User Profile — Field-Level Permissions

For each object with Read access on the guest profile, list the fields with Read access and verify each is needed for a public page.

| Object | Field | Read Granted? | Used on Public Page? | Action |
|---|---|---|---|---|
| (e.g., Knowledge) | Title | Yes | Yes | Keep |
| (e.g., Knowledge) | InternalNotes__c | Yes | No | Remove |
| | | | | |

**Action items from this section:**
- [ ] All fields with guest Read access are displayed on a public page component
- [ ] PII fields (email, phone, address, birthdate, SSN, TaxId) are OFF on guest profile
- [ ] Internal/cost/supplier fields are OFF on guest profile

---

## Section 4: External OWD and Sharing Rules

| Object | Internal OWD | External OWD | Guest User Sharing Rule Exists? | Rule Criteria | Appropriate? |
|---|---|---|---|---|---|
| (e.g., Knowledge) | Private | Private | Yes | Publication Status = Online | Yes |
| (e.g., Product2) | Public Read Only | Public Read Only | N/A | N/A | Yes |
| | | | | | |

**Rules:**
- External OWD = Private is the recommended default for custom objects.
- If External OWD = Private, a Guest User Sharing Rule must exist to make records visible on public pages.
- External OWD = Public Read Only is acceptable only for objects where all records are safe for unauthenticated global access.
- Do not set External OWD = Public Read/Write.

**Action items from this section:**
- [ ] No object has External OWD = Public Read/Write
- [ ] All Private OWD objects that appear on public pages have a Guest User Sharing Rule
- [ ] Sharing rules are site-specific (confirm under Guest User Sharing Rules for this site)

---

## Section 5: API Settings

| Setting | Location | Current Value | Required Value | Compliant? |
|---|---|---|---|---|
| API Enabled | Guest User Profile > System Permissions | | OFF | |
| Allow guest users to access public APIs | Site Administration > Preferences | | OFF | |

**Action items from this section:**
- [ ] API Enabled = OFF on guest user profile
- [ ] Allow guest users to access public APIs = OFF in Site Preferences

---

## Section 5b: Site and Network Settings

Values are in the deployed metadata, not only in Setup. Re-check the `Network` row **after** publishing — `enableGuestFileAccess` is enabled automatically when public access is turned on at the page or site level.

| Setting | File | Value | Decision / Reason |
|---|---|---|---|
| `siteGuestRecordDefaultOwner` | `sites/<Site>.site-meta.xml` | | Required whenever the guest profile grants create on anything |
| `clickjackProtectionLevel` | `sites/<Site>.site-meta.xml` | | `SameOriginOnly` recommended; `NoFraming` for most protection |
| `enableGuestChatter` | `networks/<Site>.network-meta.xml` | | |
| `enableGuestFileAccess` (pre-publish) | `networks/<Site>.network-meta.xml` | | |
| `enableGuestFileAccess` (**post-publish re-retrieve**) | `networks/<Site>.network-meta.xml` | | |
| `enableGuestMemberVisibility` | `networks/<Site>.network-meta.xml` | | |
| `robotsTxtPage` | `sites/<Site>.site-meta.xml` | | Public and indexed are separate decisions — see `admin/experience-cloud-seo-settings` |

**Objects the guest profile can create, and who owns the resulting records:**

| Object | Why a guest must create it | Owner after insert |
|---|---|---|
| | | |

**Action items from this section:**
- [ ] `siteGuestRecordDefaultOwner` names a maintained integration user, set in the same deploy as any `allowCreate`
- [ ] Network guest flags recorded pre-publish **and** re-checked post-publish
- [ ] Indexing decision made and recorded before the first Public route ships
- [ ] `scripts/check_experience_cloud_guest_access.py` run against the source tree: errors resolved, warnings decided

---

## Section 6: Guest Access Test Results

Test all public pages in an incognito browser (no active Salesforce session).

| Page | Expected Content Visible? | Unexpected Records Visible? | Login Redirect Works (if applicable)? | Pass/Fail |
|---|---|---|---|---|
| | | | | |
| | | | | |

**Action items from this section:**
- [ ] All public pages load expected content in incognito browser
- [ ] No unexpected records or fields visible to unauthenticated visitors
- [ ] Members-only pages redirect to login when accessed without a session

---

## Section 7: Handoff Notes

**Custom Apex classes reachable from public pages (pass to security/guest-user-security for FLS review):**

- (list class names here)

**Known deviations from least-privilege configuration and business justification:**

- (document any exceptions and owner)

**Date of next scheduled review:**

---

## Sign-Off

- [ ] All action items in Sections 1–6 are resolved or have documented exceptions.
- [ ] Site tested in incognito browser with no unresolved findings.
- [ ] Custom Apex review handed off if applicable.

**Completed by:**
**Date:**
