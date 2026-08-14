# Gotchas — Guest User Security

## 1. `with sharing` Does NOT Prevent Field Exposure

**What happens:** A developer adds `with sharing` to a guest-facing Apex class and considers the security review complete. An internal audit later discovers that the class returns sensitive fields (BillingCity, AnnualRevenue) from Account records because `with sharing` only enforces which RECORDS are visible, not which FIELDS.

**Why:** `with sharing` enforces the sharing model (row visibility). It does not enforce field-level security. For a guest user the row set is whatever the guest user sharing rules grant — so on an object with a broad sharing rule, `with sharing` filters out almost nothing, and the class still returns every field on every matched record.

**How to avoid:** Combine `with sharing` with `WITH USER_MODE` in SOQL or explicit `Schema.SObjectType.Account.fields.AnnualRevenue.isAccessible()` checks. Return DTOs (data transfer objects) that explicitly whitelist returned fields.

---

## 2. Each Experience Cloud Site Has Its Own Guest User

**What happens:** An admin hardens the guest profile on Site A (removes Create/Edit permissions, tightens FLS). Six months later, Site B is launched and has a completely separate guest profile that inherited the org's default profile configuration — which still has Create, Edit, and access to sensitive fields.

**Why:** Every Experience Cloud site generates a distinct guest user and guest user profile. Changing the profile on one site does not affect other sites.

**How to avoid:** When any new Experience Cloud site is created, immediately audit its guest profile using the same hardening checklist applied to existing sites. Treat each new site as a separate security surface.

---

## 3. Permission Sets Assigned to the Guest User Are an Access Path Most Audits Miss

**What happens:** A developer needs to give guest users the ability to submit a specific type of form. Rather than modifying the guest profile, they create a permission set with Create access on a few objects and assign it to the guest user. Later, the permission set is expanded (by a different developer who doesn't realize it's on the guest user) to include access to Contact records. Guest users can now query Contact records.

**Why:** Permission sets on the guest user grant object, field and system permissions on top of the profile, and nothing about the guest user makes that union visible in one place.

Do not date this risk to Spring '22 — assigning permission sets to guest users predates that release, and the Spring '22 event was a *restriction*, not a grant. The actual timeline runs the other way:

- **Spring '21** — Edit, Delete, View All Records and Modify All Records can no longer be given to guest users at all, "even with a permission set or permission set group." Existing assignments carrying them were removed automatically.
- **Spring '22** — Salesforce began restricting assignment of guest users to permission sets and permission set groups associated with permission set *licences* that contain those restricted object permissions, and shipped a release update to prepare orgs for enforcement.
- **Winter '23** — that release update, "Remove Guest User Assignments from Permission Sets Associated with Permission Set Licenses with Restricted Object Permissions," was enforced and the affected assignments were auto-removed.

So the surviving exposure is narrower than "guests can be given anything through a permission set": read and create on standard objects is what remains reachable. That is still worth auditing — a permission set expanded by a developer who does not realise it is assigned to the guest user is exactly how read access to Contact leaks onto a public site.

**How to avoid:** Regularly audit permission set assignments to the guest user: `SELECT Id, PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = :guestUserId`. Treat the guest user's effective permission set as the union of profile + all assigned permission sets.

---

## 4. Secure Guest User Record Access Breaks Pre-Winter '21 Sharing Mechanisms

**What happens:** An org configured before Winter '21 granted guests access by adding the guest user to a public group or queue, by manual/Apex managed sharing, or by an ordinary sharing rule. After enforcement, guests can no longer see those records.

**Why:** Since Winter '21, "Secure guest user record access" is enabled in every org with Experience Cloud sites and can't be disabled. Guest org-wide defaults are Private for all objects and that access level can't be changed. Guests can't be members of public groups or queues, can't receive manual or Apex managed shares, and can't own records. The only surviving grant path is a **guest user sharing rule** — a criteria-based rule that grants Read Only.

**How to avoid:** Replace each broken grant with a guest user sharing rule whose criteria match only the genuinely public records. Do **not** raise the object's OWD: guest visibility is not evaluated against it, so the change grants guests nothing while widening exposure for authenticated internal users. Also remove the guest user from any group or queue by hand — legacy memberships are not cleaned up automatically. Keep `WITH USER_MODE` in Apex for field enforcement; the sharing-rule criteria remain the row-level backstop.

---

## 5. View All Fields Is Not a Shortcut Out of Guest FLS Maintenance

**What happens:** A public site needs several fields on one object and someone is tired of adding a field permission each time that object grows. They find the object-level **View All Fields** permission added in Spring '25 — enabled on the Object Settings page of a permission set — and try to put it on the permission set assigned to the guest user, or ship a design that claims guest FLS is now maintenance-free.

**Why:** View All Fields covers "Viewing all fields and field data for a specific object," and "users are automatically granted access to any new fields created for the object." On an internal permission set that is the right answer to "read every field on this object, including future ones" — better than View All Data and better than a hand-maintained `FieldPermissions` list that goes stale the moment someone adds a field. For guests it is neither available nor desirable. Salesforce states that "View All Data, Modify All Data, and View All Records, Modify All Records, or View All Fields for a given object can't be assigned to external users," and the guest profile rule is narrower still: "The only object permissions allowed for guest users are read and create." The auto-grant is exactly why — every field a future admin adds to that object would become world-readable with no change to any guest configuration and no review.

**How to avoid:** Enumerate guest field permissions one field at a time and treat that explicit list as the audit surface. Its staleness is the feature: a newly added field stays invisible to the internet until someone justifies it. Add "does the guest profile need this?" to the checklist for creating any field on a guest-readable object. Do not let "it's only read" carry the argument — View All Fields is a read grant, and on a public site read is the entire exposure.

---

## 6. Guest Apex Runs in System Mode — Sharing Is Not the Boundary

**What happens:** The design says OWD Private plus a guest profile with no object access. Guest `@AuraEnabled` / OmniStudio remote Apex still reads and writes whatever the class queries, because guest Apex commonly runs in **system mode**. Record Id in the request is partially guessable. The only real access control is whatever the Apex method checks **before** the query.

**When it occurs:** Unauthenticated Experience Cloud intake (applications, cases, surveys) that stores a draft record and round-trips its Id from the browser.

**How to avoid:**
- Mint a high-entropy session token **in Apex** (`Crypto.generateAesKey` or equivalent). Store only an HMAC (`Crypto.generateMac('HmacSHA256', …)`). Return the raw token once.
- Keep the raw token in `sessionStorage` or a cookie — never in the URL, never in `localStorage`, never in a log.
- **Resolve the record from the token**, never from a client-supplied Id. Load children by parent traversal, not by Ids the client sent.
- Rotate the token on each section commit. Separate idle timeout (clear token) from absolute TTL (also null PII fields if the row is a draft).
- Per-section **write allowlists** — system mode has no FLS.
- Apex REST cannot set `Set-Cookie` / HttpOnly via `addHeader()`. If you need HttpOnly, use a Visualforce endpoint; otherwise the LWC sets a JS cookie (`Secure; SameSite=Strict`) and that is a platform limitation, not a security win.

---

## 7. `UserInfo.getUserId()` Is One Id for Every Guest

**What happens:** A Platform Cache or Custom Object throttle keys on `UserInfo.getUserId()`. Every anonymous visitor shares that Id. Fail-secure then 429s the **entire site**. Fail-open at least keeps applicants moving when cache is down — but a per-user design never existed.

**When it occurs:** Copying an authenticated rate-limit pattern onto the guest path (file uploads, OTP, IDV, form submit).

**How to avoid:** Key guest throttles on sanitized client IP plus a server nonce, not the guest user Id. Platform Cache keys must be alphanumeric and start with a letter. Decide fail-open vs fail-closed explicitly: cache exceptions on a public intake form should not take the form down. Write a test that two concurrent guest sessions do **not** share a counter.
