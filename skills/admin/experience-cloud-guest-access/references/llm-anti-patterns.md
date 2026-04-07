# LLM Anti-Patterns — Experience Cloud Guest Access

Common mistakes AI coding assistants make when generating or advising on Experience Cloud guest access configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Granting "API Enabled" to the Guest User Profile

**What the LLM generates:** Advice to enable "API Enabled" on the guest user profile to allow the public site to call Salesforce APIs or to fix authentication errors on public pages.

**Why it happens:** LLMs associate "API Enabled" with general platform access and do not model the security implications of enabling API access on an unauthenticated system user. The training data contains many examples of enabling this permission to fix API-related errors without the guest-user context.

**Correct pattern:**

```
- Leave "API Enabled" OFF on the guest user profile.
- Leave "Allow guest users to access public APIs" OFF in Site Administration > Preferences.
- Public page components (LWC, Aura) communicate via the Experience Cloud runtime, not direct API calls.
- If a Force.com Site needs REST endpoint access, scope the API setting narrowly to that endpoint rather than enabling general API access on the guest profile.
```

**Detection hint:** Look for any advice that says "enable API Enabled on the guest profile" or "turn on Allow guest users to access public APIs". Both should be treated as a flag for review unless the use case is explicitly a public REST endpoint on a Force.com Site.

---

## Anti-Pattern 2: Setting External OWD to Public Read Only to Fix Empty Public Pages

**What the LLM generates:** A recommendation to set the external OWD of an object to Public Read Only as the solution when a public page shows no records or empty components.

**Why it happens:** LLMs recognize that OWD controls record visibility and that Public Read Only makes records visible. They do not always distinguish between internal OWD and external OWD, or between "all records visible" and "specific records visible via sharing rule". The shortcut is factually correct about the symptom but wrong about the scope.

**Correct pattern:**

```
1. Keep external OWD at Private for custom objects and any object with potentially sensitive records.
2. Create a Guest User Sharing Rule with criteria that match only the records intended for public display
   (e.g., Status = Published, IsPublic__c = true).
3. Only set external OWD to Public Read Only for objects where ALL records are genuinely intended
   for unauthenticated access (e.g., Product2 on a commerce site).
```

**Detection hint:** Look for phrases like "set external OWD to Public" as a troubleshooting step for empty public pages. Flag for review unless the object is a catalog-type object where all-records visibility is explicitly confirmed as acceptable.

---

## Anti-Pattern 3: Using Internal Sharing Rules Instead of Guest User Sharing Rules

**What the LLM generates:** Instructions to create a regular (internal) sharing rule, criteria-based or owner-based, to make records visible on a public Experience Cloud page.

**Why it happens:** LLMs are extensively trained on internal sharing rule documentation. Guest User Sharing Rules are a narrower, less common feature. When asked how to make records visible to "users", LLMs default to the familiar sharing rule model without distinguishing between authenticated users and the guest user system account.

**Correct pattern:**

```
- Navigate to Setup > Sharing Settings.
- Scroll to "Guest User Sharing Rules" — a separate section from internal sharing rules.
- Create a sharing rule that grants the site's guest user Read Only access to the target records.
- Internal sharing rules do not apply to the guest user system account.
```

**Detection hint:** If the sharing rule instructions do not explicitly mention "Guest User Sharing Rules" or the specific site's guest user, the LLM is likely generating instructions for internal sharing rules, which have no effect on guest access.

---

## Anti-Pattern 4: Conflating Guest Page Access with Authenticated Member Page Access

**What the LLM generates:** Advice that mixes configuration steps for guest (unauthenticated) users and authenticated Experience Cloud members in the same instructions — for example, suggesting that sharing sets or external user profiles control what guests can see on public pages.

**Why it happens:** Experience Cloud has multiple user types: guest (unauthenticated), external authenticated members, and internal users. LLMs frequently blur the distinction between guest users and external authenticated members because both interact with Experience Cloud sites and both use "external" sharing concepts.

**Correct pattern:**

```
- Guest user (unauthenticated): controlled by guest user profile, Page Access = Public, external OWD,
  and Guest User Sharing Rules. No login required.
- External authenticated member: controlled by member profile, sharing sets, external OWD for
  authenticated access, and standard sharing rules.
- Sharing sets apply to authenticated external members only — they do not affect guest users.
- Page Access = Requires Login applies to authenticated members — it redirects guests to login.
```

**Detection hint:** Look for any mention of "sharing sets" in the context of configuring guest user access. Sharing sets do not apply to the guest user. Flag for immediate review.

---

## Anti-Pattern 5: Not Reviewing FLS Before Adding a New Public Page

**What the LLM generates:** Instructions to set a new page to Public and grant object-level Read on the guest profile, without a step to review field-level permissions for sensitive fields on that object.

**Why it happens:** LLMs treat object-level Read access as the complete permission requirement for displaying records. Field-level security as a distinct layer is an underrepresented concept in training data relative to object permissions.

**Correct pattern:**

```
After granting Read on a new object for the guest profile:
1. Open the guest user profile > Object Settings > [Object] > Field Permissions.
2. Review every field that currently has Read access.
3. Remove Read from any field that is not displayed on the public page:
   - PII fields (email, phone, address, birthdate)
   - Internal fields (owner, created by, cost fields, notes)
   - Any field with a name suggesting sensitivity (SSN, TaxId, InternalNotes, etc.)
4. Grant Read only to the fields the page components explicitly display.
```

**Detection hint:** If the LLM response includes "grant Read on [Object]" for the guest profile without a follow-up step to review field-level permissions, the FLS layer is missing. Always flag guest profile object permission grants that lack a field-level review step.
