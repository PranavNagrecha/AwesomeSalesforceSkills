---
name: analytics-adoption-strategy
description: "Use this skill when driving adoption of CRM Analytics (Einstein Analytics) across an org — including setting up the Analytics Adoption App to measure who uses which dashboards, embedding analytics into Lightning pages for in-context discovery, pinning dashboards to the Analytics home page, building self-service personas, and defining analytics-specific success metrics. Triggers: analytics adoption, dashboard usage tracking, embedded analytics strategy, self-service analytics enablement, CRM Analytics rollout. NOT for general Salesforce change management (use change-management-and-training), NOT for In-App Guidance prompt mechanics (use in-app-guidance-and-walkthroughs), NOT for dashboard technical design or JSON (use analytics-dashboard-design or analytics-dashboard-json)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
triggers:
  - "how do I track who is actually using our CRM Analytics dashboards and apps"
  - "users are not opening the analytics dashboards we built — how do I drive adoption"
  - "how do I embed a CRM Analytics dashboard inside a Lightning record page so users see it in context"
  - "how do I set up the Analytics Adoption App to measure dashboard engagement"
  - "what is a self-service analytics strategy for non-technical Salesforce users"
  - "how do I make analytics dashboards discoverable on the Analytics home page"
tags:
  - crm-analytics
  - analytics-adoption
  - adoption-analytics-app
  - embedded-analytics
  - self-service-analytics
  - analytics-home
  - dashboard-discovery
  - einstein-analytics
  - analytics-adoption-strategy
inputs:
  - "List of CRM Analytics apps and dashboards already built in the org"
  - "Target user personas (executives, managers, field reps, analysts)"
  - "Current adoption pain point: low open rates, wrong users, wrong context, or no data culture"
  - "Whether the Analytics Adoption Metadata managed package is installed (required prerequisite)"
  - "Lightning Experience pages where embedded analytics is desired"
outputs:
  - "Analytics Adoption App setup guide (including managed package prerequisite)"
  - "Embedded analytics LWC strategy with js-meta.xml analytics-dashboard target guidance"
  - "Analytics home page pinning and collections plan"
  - "Self-service persona enablement plan with permission set and app sharing configuration"
  - "Analytics-specific success metrics and measurement cadence"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Analytics Adoption Strategy

This skill activates when an org has built CRM Analytics dashboards and apps but needs a strategy to drive usage — measuring who opens what, making dashboards discoverable in context, enabling self-service for non-analyst users, and defining the right success metrics. It covers the strategy and configuration layer above technical dashboard construction.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the **Analytics Adoption Metadata managed package** installed? This is a hard prerequisite for creating the Salesforce-provided Analytics Adoption App template. Without the package the template cannot be created and usage tracking will not work. Confirm in Setup > Installed Packages before advising on the Adoption App.
- Which **user personas** need analytics access? Executives, operations managers, and field reps have radically different discovery paths — executives want pinned home-page dashboards, field reps need dashboards embedded in record pages they already open, and analysts want direct Analytics Studio access.
- What is the **actual adoption problem**? Low usage usually falls into one of three categories: users cannot find dashboards (discoverability), users open dashboards but find them irrelevant or confusing (relevance/design, not a strategy problem — escalate to analytics-dashboard-design), or users do not trust the data (data quality — escalate to the appropriate data skill). Strategy interventions only fix the first category.
- Do not confuse the **Salesforce Adoption Dashboards AppExchange package** (Salesforce Labs, tracks CRM record creation and login frequency) with the **Analytics Adoption App** (tracks CRM Analytics-specific usage: app opens, dashboard opens, lens opens). They track completely different things and require different setup steps.

---

## Core Concepts

### The Analytics Adoption App

Salesforce ships a first-party template app specifically for measuring CRM Analytics usage. It tracks who opened which app, dashboard, and lens — and when. This is separate from general Salesforce adoption metrics.

**Hard prerequisite:** The **Analytics Adoption Metadata managed package** must be installed in the org before the template can be used. Navigate to Setup > Installed Packages and confirm it is present. If it is missing, the Analytics Adoption App template will not appear in the template picker in Analytics Studio.

**What it tracks:** App open events, dashboard open events, lens open events, user identity, timestamp. It does NOT track which filters a user applied, how long they spent on a dashboard, or whether a user acted on the data — those require custom instrumentation.

**Creating the app:**
1. Confirm the managed package is installed.
2. In Analytics Studio, select Create > App > Use a Template.
3. Select "Adoption Analytics" from the template list.
4. Complete the configuration wizard (select org scope or app-scoped tracking).
5. The template auto-creates a dataset (fed by a scheduled dataflow pulling usage events), a set of prebuilt dashboards showing top users, top dashboards, and usage trends, and a connected Data Sync schedule.

**Scope of data:** The Adoption App tracks usage for all apps the running user has Viewer access to. To track usage across the entire org, the Adoption App must be configured by an Analytics admin with access to all apps. Users who are scoped to only their own team's app will see only that app's usage.

### Embedded Analytics for In-Context Adoption

The highest-impact adoption intervention for field-facing users (sales reps, service agents) is embedding the relevant dashboard directly into the Lightning page the user already opens for their work. A sales rep who sees their pipeline dashboard inside the Opportunity record list view does not need to navigate to Analytics Studio — the insight arrives in context.

**Mechanism:** CRM Analytics dashboards are surfaced in Lightning Experience via the `analytics-dashboard` Lightning web component target. The component is configured by adding the `analytics:analyticsFilterBridge` target in the LWC metadata (`js-meta.xml`) or via the Lightning App Builder's CRM Analytics Dashboard standard component — no custom code required for the standard component approach.

**Standard component approach (no-code):**
1. Navigate to Setup > Lightning App Builder.
2. Open or create the relevant page (Record Page, Home Page, App Page).
3. From the component palette, drag the **CRM Analytics Dashboard** component onto the canvas.
4. In the properties pane, select the target app and dashboard.
5. Configure filter pass-through if the dashboard should pre-filter based on the record context (e.g., Account ID on an Account record page).
6. Save and activate.

**LWC custom approach (for filter pass-through or dynamic dashboards):** Declare `<target>analytics__analyticsExtension</target>` or use the `lightning-analytics-cloud-dashboard` base component. This is handled by the analytics-dashboard-design skill — reference that skill for technical implementation.

**Key rule:** Embedding only adds value when the dashboard is pre-filtered to data relevant to the record or page context. An unfiltered Sales Cloud pipeline dashboard embedded on an Opportunity record page adds noise, not insight.

### Analytics Home Page: Pinning and Collections

The Analytics home page (accessible from the App Launcher) is the primary starting point for users who do not have embedded dashboards in their workflow. Two mechanisms drive discoverability here:

- **Favorites (starring):** Any user can star a dashboard or app to pin it to their personal Analytics home page. Encourage users to favorite the 1–3 dashboards relevant to their role during onboarding. This is a per-user action and cannot be pushed org-wide by admins.
- **Collections:** Admins can group related dashboards and lenses into named Collections within an app. Collections appear in the left-nav of the Analytics home for users with app access. Use Collections to organize dashboards by role or use case (e.g., "Sales Dashboards", "Service Metrics").
- **Shared apps as home pinning:** Apps that are shared widely and placed prominently in the org's App Launcher layout act as a soft "pin" for frequent users. The Analytics Adoption App itself should be shared with admins and analytics champions.

### Self-Service Analytics Personas

Self-service analytics means enabling non-analyst users to explore data with guardrails — they can apply filters, drill into charts, and create personal explorations, but they cannot break shared dashboards or access unauthorized data.

**Persona model:**
| Persona | Access Level | What They Can Do |
|---------|-------------|-----------------|
| Viewer | App Viewer | View and filter existing dashboards only |
| Explorer | App Editor or personal dataset access | Create personal lenses from shared datasets |
| Builder | App Manager or Creator | Build new dashboards and datasets |
| Admin | Analytics Admin permission | Manage all apps, data sync, and security |

**Permission path for Viewers (most common):**
1. Assign the CRM Analytics Plus User (or Growth User) permission set to the user.
2. Share the target app with the user or their public group as Viewer.
3. Ensure the dataset has no row-level security predicate that would block all rows for this user.
4. No further access is required — Viewers cannot modify dashboards.

The most common self-service failure: giving users Editor access when they only need Viewer access. Editor access allows users to edit and save changes to shared dashboards, which corrupts the canonical dashboard for all other Viewers.

### Analytics-Specific Success Metrics

General adoption metrics (login frequency, record creation) do not measure analytics adoption. Use analytics-specific metrics:

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Dashboard open rate | Analytics Adoption App — dashboard open events by week | 70%+ of licensed users open target dashboards within 4 weeks of launch |
| Repeat usage | Adoption App — same user opens same dashboard in consecutive weeks | 50%+ of initial openers return in week 2 |
| Self-service exploration | Lens creation count by non-admin users | At least 20% of Explorers create a personal lens within 60 days |
| Embedded dashboard engagement | Adoption App filtered to embedded dashboard name | Embedded dashboards should show 2-3x higher open rates than standalone |

---

## Common Patterns

### Pattern: New Analytics App Rollout with Adoption Tracking

**When to use:** Launching a new CRM Analytics app to a team and needing to measure whether they actually use it.

**How it works:**
1. Build and share the target app to the intended audience (Viewer access).
2. Confirm the Analytics Adoption Metadata managed package is installed.
3. Create the Analytics Adoption App from the template in Analytics Studio.
4. Configure Adoption App scope to include the new app.
5. Establish a baseline open-rate metric target with stakeholders (e.g., 60% of licensed users open the dashboard within the first month).
6. Schedule a weekly review of the Adoption App dashboards for the first 6 weeks post-launch.
7. Use Chatter or email to remind low-engagement users, referencing specific dashboards by name.

**Why this order matters:** Configuring the Adoption App before the target app goes live ensures no usage data is lost in the first week, which is typically the highest-engagement period.

### Pattern: Embedded Analytics for Record-Context Insight

**When to use:** Field users (sales reps, service agents) are not opening standalone Analytics apps because they do not navigate to Analytics Studio as part of their workflow.

**How it works:**
1. Identify the Lightning page the target users open most (Opportunity record page, Case list view, Account record page).
2. Identify the most relevant pre-built dashboard for that context.
3. In Lightning App Builder, add the CRM Analytics Dashboard component to the page.
4. Configure the dashboard filter to pass the record's relevant ID field (AccountId, OwnerId, etc.) as a filter context to the dashboard.
5. Activate the page for the relevant profiles.
6. Track adoption using the Analytics Adoption App, filtered to the embedded dashboard name, comparing open rates before and after embedding.

**Why not point users to Analytics Studio:** Field users have a mental model of their record-based workflow. Adding a navigation step to Analytics Studio creates friction that most users do not overcome. Embedding eliminates the navigation gap.

### Pattern: Self-Service Enablement for Operations Managers

**When to use:** An operations team wants to build their own exploratory views on top of shared datasets without needing a developer or analyst.

**How it works:**
1. Identify the 1–3 datasets relevant to the operations team's use cases. Ensure they are registered and scheduled to refresh.
2. Assign the team lead(s) as App Editors on the app containing the datasets.
3. Run a 60-minute enablement session: how to open a dataset, create a lens (group by, measure, chart type), and save it as a personal lens.
4. Share a documentation link (Trailhead: Explore Data with CRM Analytics) as reference.
5. Create a Chatter group for the team to share lens screenshots and ask questions.
6. Revisit in 30 days: check Adoption App lens creation metrics to see if self-service exploration is happening.

**Why Editor instead of Manager:** Managers can delete shared assets and change app sharing. Editors can create and edit — sufficient for self-service exploration. Grant Manager only to analytics leads.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|-----------|---------------------|--------|
| Need to measure who uses analytics | Analytics Adoption App (requires managed package) | First-party template tracks app/dashboard/lens opens per user |
| Field users not opening dashboards | Embed dashboard in Lightning record page via App Builder | Eliminates navigation friction; analytics arrives in existing workflow |
| Users cannot find dashboards | Configure app Collections; advise users to favorite key dashboards | Collections organize by role; favorites provide personal home-page pinning |
| Leadership wants to see adoption numbers | Adoption App + scheduled report/Chatter snapshot | Quantitative signal preferred by stakeholders over anecdote |
| Non-analysts want to explore data | Assign Editor access to app; run lens training session | Editor enables exploration without data access risk |
| Adoption Dashboards (AppExchange) vs Analytics Adoption App | Separate tools — use both for different signals | Adoption Dashboards = CRM record/login metrics; Adoption App = analytics usage metrics |
| Low repeat usage despite high initial opens | Investigate dashboard relevance and data freshness | Strategy cannot fix design or data quality problems |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Identify the adoption problem type** — Confirm whether the issue is discoverability (users cannot find dashboards), relevance (users open but do not use), or trust (users do not trust the data). This skill addresses discoverability only; escalate the other two.
2. **Verify the Analytics Adoption App prerequisite** — Check Setup > Installed Packages for the Analytics Adoption Metadata managed package. If missing, document the installation step before advising on adoption tracking.
3. **Map user personas to discovery paths** — Classify each target user type as executive, manager, field user, or analyst. Select the appropriate intervention: home-page pinning and sharing for executives, embedded analytics for field users, self-service Editor access for analysts.
4. **Implement the highest-priority intervention** — For field users: configure embedded dashboard via Lightning App Builder. For all others: share the app, configure Collections, and advise on favoriting key dashboards during onboarding.
5. **Set up adoption measurement** — Create the Analytics Adoption App from the template. Define 2–3 measurable targets (open rate, repeat usage, lens creation) with specific numeric goals agreed with stakeholders.
6. **Schedule a 30-day and 60-day adoption review** — Use the Adoption App dashboards to measure against the numeric targets. For users below target, use Chatter or manager escalation as reinforcement — re-training alone rarely moves the needle after the first 30 days.

---

## Review Checklist

Run through these before marking analytics adoption work complete:

- [ ] Analytics Adoption Metadata managed package confirmed as installed (prerequisite for Adoption App)
- [ ] Analytics Adoption App created and scoped to include target apps
- [ ] Adoption success metrics defined with numeric targets agreed with stakeholders
- [ ] User personas mapped to discovery paths (embedded, home page, Analytics Studio)
- [ ] Embedded dashboard configured with filter pass-through for record-context pages (if applicable)
- [ ] App sharing confirmed: target users have at least Viewer access on the correct app
- [ ] Row-level security verified: target users see their own data, not all data
- [ ] Editor access restricted to users who need self-service exploration (not all Viewers)
- [ ] Collections configured in the app to organize dashboards by role or use case
- [ ] 30-day and 60-day adoption review meetings scheduled

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Analytics Adoption Metadata managed package is a silent hard prerequisite** — The Analytics Adoption App template will not appear in the template picker if the managed package is not installed. There is no error message — the template is simply absent. Practitioners who skip the package installation step waste hours trying to find a template that does not exist in their org.

2. **Adoption App tracks the running user's accessible apps only** — If the Adoption App is created by a user who does not have Viewer access to all apps in the org, the Adoption App dataset will silently exclude usage data for apps outside that user's access. Always create the Adoption App as an Analytics admin with org-wide app access, and schedule the Adoption App dataflow to run as the same admin user.

3. **Giving Viewers Editor access corrupts shared dashboards** — Editor-access users can save changes to dashboards inside the shared app. An operations manager who accidentally saves a filter selection overwrites the canonical dashboard for all Viewers. Establish a pattern of using personal lenses for exploration and reserving the shared app's dashboards as read-only canonical views. Assign Editor only to designated self-service users.

4. **Embedded dashboard filter pass-through requires explicit configuration — it is not automatic** — Dropping a CRM Analytics Dashboard component onto an Account record page does not automatically filter the dashboard by the current Account. The `filter` attribute on the component must be explicitly configured to pass the record's Id field to the matching dashboard filter. Without this, every embedded dashboard shows all data to all users, which is usually wrong and often exposes data visibility issues.

5. **Favoriting is per-user and cannot be pushed org-wide** — Admins frequently want to "pin" a dashboard to every user's Analytics home page. There is no admin-controlled mechanism to push favorites to all users. The workaround is to run a short onboarding step where each user stars the recommended dashboards, or to embed dashboards in Lightning pages (which does not require user action). Do not promise an admin-pushable home-page pinning mechanism — it does not exist as of Spring '25.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Adoption App setup guide | Step-by-step: confirm managed package, create template app, scope to target apps, schedule dataflow |
| Embedded analytics plan | Mapping of Lightning pages to dashboards with filter pass-through configuration for each |
| Persona-to-access matrix | Table mapping each user type to permission set, app access level, and discovery path |
| Success metrics framework | 2–3 measurable analytics-specific targets with numeric goals and measurement method |
| Self-service enablement plan | Editor access list, dataset sharing configuration, and 60-minute onboarding session outline |

---

## Related Skills

- admin/change-management-and-training — Use for general Salesforce user adoption and training planning; not analytics-specific
- admin/in-app-guidance-and-walkthroughs — Use when the adoption mechanism is In-App Guidance prompt steps; not analytics embedding
- admin/analytics-dashboard-design — Use for dashboard design, SAQL, bindings, and filter configuration; not adoption strategy
- admin/crm-analytics-app-creation — Use for initial app, dataset, and lens creation; not for post-creation adoption
- admin/einstein-analytics-basics — Use for license provisioning, access troubleshooting, and CRM Analytics orientation
