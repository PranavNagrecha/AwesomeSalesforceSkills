# LLM Anti-Patterns — Analytics Adoption Strategy

Common mistakes AI coding assistants make when generating or advising on Analytics Adoption Strategy.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating the Salesforce Adoption Dashboards Package with the Analytics Adoption App

**What the LLM generates:** "To track who is using your CRM Analytics dashboards, install the Salesforce Adoption Dashboards package from AppExchange and review the dashboard usage reports."

**Why it happens:** Both tools use the word "adoption" and "dashboards" and both exist in the Salesforce ecosystem. LLMs trained on generic Salesforce adoption content frequently encounter the Salesforce Adoption Dashboards AppExchange package (Salesforce Labs, very widely referenced in admin content) and conflate it with the Analytics Adoption App (an Analytics Studio template, far less commonly referenced in training data). The two products track entirely different signals.

**Correct pattern:**

```
Salesforce Adoption Dashboards (AppExchange / Salesforce Labs):
- Tracks: CRM platform usage — login frequency, Opportunity creation, Case creation, record activity
- Install from: AppExchange (search "Salesforce Adoption Dashboards" by Salesforce Labs)
- Does NOT track: CRM Analytics app opens, dashboard opens, or lens opens

Analytics Adoption App (Analytics Studio template):
- Tracks: CRM Analytics-specific usage — who opened which app, dashboard, lens, and when
- Requires: Analytics Adoption Metadata managed package installed as a prerequisite
- Create from: Analytics Studio > Create > App > Use a Template > Adoption Analytics
- Does NOT track: CRM record creation or platform login frequency
```

**Detection hint:** If the response recommends "Salesforce Adoption Dashboards" as the answer to measuring "who is using my analytics dashboards," flag it as incorrect. If it recommends installing an AppExchange package to track analytics usage without mentioning the Analytics Adoption App template, flag it.

---

## Anti-Pattern 2: Advising Analytics Adoption App Creation Without Mentioning the Managed Package Prerequisite

**What the LLM generates:** "To create the Analytics Adoption App, go to Analytics Studio, click Create > App > Use a Template, and select Adoption Analytics from the template list."

**Why it happens:** LLMs reproduce the creation steps they have seen in official documentation without surfacing the prerequisite dependency — the managed package is mentioned in a separate help article, not always in the creation steps article, and the silent UI behavior (template simply does not appear) is not documented in the steps themselves.

**Correct pattern:**

```
Step 0 (prerequisite — do this first):
Setup > Installed Packages > search "Analytics Adoption Metadata"
If absent: install from AppExchange before proceeding.
The template will not appear in the template picker without this package.

Step 1: Analytics Studio > Create > App > Use a Template
Step 2: Select "Adoption Analytics" (appears only after package is installed)
...
```

**Detection hint:** If the response describes Analytics Adoption App creation steps without a prerequisite check for the Analytics Adoption Metadata managed package, it is incomplete. Search the output for "managed package," "Installed Packages," or "Analytics Adoption Metadata" — if none of these appear, the prerequisite is missing.

---

## Anti-Pattern 3: Recommending Admin-Controlled Home Page Pinning for Analytics Dashboards

**What the LLM generates:** "To ensure users see the key dashboards when they open Analytics, pin the dashboards to the Analytics home page from Setup, or configure the org's default Analytics home layout to feature the recommended dashboards."

**Why it happens:** In some Salesforce contexts (App Launcher, Lightning Experience navigation), admins can configure what users see by default. LLMs generalize this pattern to CRM Analytics, where it does not apply. CRM Analytics favorites (the mechanism for "pinning" dashboards to the Analytics home) are per-user personal preferences — there is no admin-controlled org-wide home page pinning for Analytics as of Spring '25.

**Correct pattern:**

```
Admin-controlled alternatives to home page pinning:
1. Embed dashboards in Lightning record pages via Lightning App Builder
   → User sees the dashboard in their existing workflow without navigating to Analytics
2. Onboarding exercise: guide users to star (favorite) 2–3 key dashboards during onboarding
   → User-controlled but organizationally directed
3. Organize dashboards in Collections within the app
   → Collections appear in the app left-nav for all users with Viewer access

There is no Setup option to push favorites or pin dashboards to all users' Analytics home pages.
```

**Detection hint:** If the output references "admin pin," "org-wide Analytics home configuration," or "push dashboard to all users' home pages," it is incorrect. Search for these phrases and challenge them.

---

## Anti-Pattern 4: Advising Editor Access for All Self-Service Users Without Governance Warning

**What the LLM generates:** "Grant all analytics users Editor access to the app so they can create their own explorations and get the most out of self-service analytics."

**Why it happens:** LLMs optimize for enabling self-service and may not model the governance risk of Editor access in a shared app. The ability to save over shared dashboards is a consequence of Editor access that is not always explained in introductory CRM Analytics content.

**Correct pattern:**

```
Access level guidance:
- Viewer: Can view and filter existing dashboards. Cannot save changes or create lenses.
  → Use for: executives, passive consumers, field reps with embedded dashboards
- Editor: Can create personal lenses and save changes to existing dashboards.
  → Use for: designated self-service users (analysts) only
  → Risk: Editor-access users can overwrite shared dashboards. Brief them: use Save As to personal lens, never Save on a shared dashboard.
- Manager: Can manage app membership, delete assets, change app name.
  → Use for: analytics leads only, not general self-service users

Do NOT grant Editor access to all users for convenience. Apply least privilege.
```

**Detection hint:** If the response recommends Editor access for all users without distinguishing Viewer from Editor responsibilities, or without warning about shared dashboard corruption risk, flag it as incomplete.

---

## Anti-Pattern 5: Assuming Embedded Dashboard Auto-Filters by Record Context

**What the LLM generates:** "Add the CRM Analytics Dashboard component to the Account record page. The dashboard will automatically filter to show data for the current account record."

**Why it happens:** In Lightning Experience, some components do receive record context automatically (the standard record detail form, related lists, etc.). LLMs apply this pattern to the CRM Analytics Dashboard component, which does not behave the same way. The component renders the dashboard as-is unless the filter attribute is explicitly configured.

**Correct pattern:**

```
Step 1: Add the CRM Analytics Dashboard component to the record page in Lightning App Builder
Step 2: In component properties, configure the filter attribute explicitly:
  Filter Name: [API name of the filter in the dashboard, e.g., "AccountFilter"]
  Filter Value: {!recordId}   ← Lightning page token for the current record's ID

Step 3: Test with a non-admin user on several different records to confirm:
  - Each record shows only that record's data
  - The filter is working (no unfiltered all-data view)

Without Step 2, the dashboard shows all data to all users.
```

**Detection hint:** If the response describes adding the CRM Analytics Dashboard component to a record page without mentioning filter pass-through configuration, it is incomplete. Search for "filter," "recordId," or "{!recordId}" in the response — if absent when embedding on a record page, the auto-filter assumption is being made.

---

## Anti-Pattern 6: Treating Analytics Adoption Strategy as Identical to General Salesforce Change Management

**What the LLM generates:** A generic Salesforce change management plan — role-based training, go-live communications, and Adoption Dashboards (AppExchange) — when asked how to drive analytics adoption.

**Why it happens:** General Salesforce adoption content vastly outnumbers analytics-specific adoption content in training data. LLMs default to the more common change management pattern without distinguishing analytics-specific interventions (embedded dashboards, Analytics Adoption App, lens training, favoriting workflows).

**Correct pattern:**

```
Analytics adoption strategy has its own distinct interventions:
1. Measurement: Analytics Adoption App (not Salesforce Adoption Dashboards)
2. Discoverability: Embedded dashboards in Lightning pages + Collections in app nav
3. Self-service: Editor access + lens creation training (not general Trailhead trails)
4. Metrics: Dashboard open rate + repeat usage + lens creation count
   (not login frequency or record creation counts)

General change management (training, communications, pilot groups) may supplement
analytics adoption but does not replace it. Escalate to change-management-and-training
skill for the general layer; use this skill for the analytics-specific layer.
```

**Detection hint:** If the response's primary recommendations are "create role-based training," "send go-live communication," and "install Salesforce Adoption Dashboards" without any analytics-specific interventions (Adoption App, embedded dashboards, lens training), it has conflated the two skill domains.
