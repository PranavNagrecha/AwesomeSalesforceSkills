# Gotchas — Analytics Adoption Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Analytics Adoption App Template Is Invisible Without the Managed Package

**What happens:** An admin navigates to Analytics Studio, selects Create > App > Use a Template, and the "Adoption Analytics" template does not appear in the list. There is no error message — the template is simply absent from the picker.

**When it occurs:** Any org where the Analytics Adoption Metadata managed package has not been installed from AppExchange. The managed package is a hard prerequisite for the template but this dependency is not surfaced in the UI. Practitioners who jump straight to template creation without checking Installed Packages cannot diagnose the blank template list without knowing to look for the package.

**How to avoid:** Before advising any practitioner to create the Analytics Adoption App, confirm the managed package is installed: Setup > Installed Packages > search for "Analytics Adoption Metadata." If absent, the package must be installed from AppExchange first. Only then will the template appear in the template picker.

---

## Gotcha 2: Adoption App Dataflow Runs As the Creating User and Inherits Their App Access

**What happens:** An admin creates the Analytics Adoption App as a user who has Viewer access to only 3 of the org's 12 analytics apps. The resulting Adoption App dataset silently contains usage data for only those 3 apps. The dashboards show low overall adoption numbers, but 9 apps are simply not represented in the data.

**When it occurs:** Any org where the CRM Analytics analytics admin role is not consistently assigned, or where the Adoption App is created by a team lead rather than the org-wide analytics admin. The dataflow runs using the credential of the user who created the Adoption App. If that user cannot see an app, the dataflow cannot retrieve that app's usage events.

**How to avoid:** Always create the Analytics Adoption App as the org-wide analytics admin — a user with the "Manage Analytics" permission and Viewer or higher access to all apps in the org. After creation, verify the Adoption App dataset contains events from multiple apps (not just a subset) before sharing the Adoption App with stakeholders.

---

## Gotcha 3: Embedded Dashboard Does Not Filter by Record Context Automatically

**What happens:** An admin drops the CRM Analytics Dashboard component onto an Account record page. Every user who opens an Account record sees the same unfiltered dashboard — showing all accounts' data, not just the current account. This often reveals data the viewing user is not supposed to see (accounts owned by other reps, confidential deal data).

**When it occurs:** Any time the CRM Analytics Dashboard component is added via Lightning App Builder without explicitly configuring the filter pass-through. The component renders the dashboard as-is; it does not auto-detect the record's context or apply any automatic filtering based on the page's record ID.

**How to avoid:** In the component properties pane, configure the filter attribute to map the record's field value to the corresponding dashboard filter. For an Account record page filtering by AccountId:
```
Filter Name: AccountFilter    (must match the filter API name in the dashboard)
Filter Value: {!recordId}     (the Lightning page's record ID token)
```
Test by opening several different Account records with different owning users and confirming each sees only that account's data. Always verify with a non-admin test user, not the admin — admin users may have org-wide visibility that bypasses row-level security.

---

## Gotcha 4: Editor Access Allows Overwriting Shared Dashboards

**What happens:** A self-service analyst with App Editor access opens a shared dashboard, applies several filters, and clicks Save (not "Save As"). The filter state is saved back to the canonical shared dashboard. All other users who open that dashboard now see it with the analyst's filters applied and may see no data or incorrect data if the filters exclude their relevant records.

**When it occurs:** Any org where Editor access has been granted for self-service exploration without briefing users on the difference between editing a shared dashboard and creating a personal lens. Editor access is needed for lens creation, but it also enables editing shared dashboards in the same app.

**How to avoid:** Two mitigations in combination work best:
1. Brief Editor-access users explicitly: personal exploration should use "Save As" to a personal lens, never Save on a shared dashboard.
2. For dashboards that must remain canonical, the admin or Manager can clone the dashboard and reassign it to a protected app where only Managers can edit, keeping the Explorer's app as Viewer-only for the canonical dashboards.
Also check the Adoption App for unusual save events from Editor-access users immediately after granting access.

---

## Gotcha 5: Favorites Cannot Be Pushed to Users by Admins

**What happens:** An admin wants to ensure every sales rep sees the "Top 5 Dashboards" pinned to their Analytics home page. The admin stars the dashboards in their own account, expecting the favorites to propagate. Or the admin looks for a Setup option to push pinned favorites org-wide. Neither works — the other reps' home pages are unchanged.

**When it occurs:** Any rollout where the adoption plan depends on every user's Analytics home page showing specific dashboards without requiring user action. This is a common expectation borrowed from the SharePoint/Teams world where admins can pin content to user home pages.

**How to avoid:** Set expectations early: CRM Analytics favorites are per-user personal preferences and cannot be set by an admin on behalf of users. The two admin-controlled alternatives are:
1. **Embed dashboards in Lightning pages** — The dashboard appears in the user's existing workflow without requiring the user to navigate to Analytics home or star anything.
2. **Onboarding step** — Include a mandatory 5-minute "star these 3 dashboards" exercise in the analytics onboarding session, with screenshot instructions.
Do not promise org-wide home page pinning — it does not exist in the platform as of Spring '25.
