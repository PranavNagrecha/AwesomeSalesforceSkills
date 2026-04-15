# Well-Architected Notes — Analytics Adoption Strategy

## Relevant Pillars

- **Operational Excellence** — The primary pillar for this skill. Analytics adoption strategy produces the measurement and feedback loops (Adoption App metrics, weekly review cadence, defined numeric targets) that give teams visibility into whether analytics investment is delivering value. Without adoption measurement, analytics programs operate blind. The Adoption App + success metrics framework directly supports the Operational Excellence mandate to measure outcomes, not just outputs.

- **User Experience** — Embedded analytics (dashboard-in-record-page) and role-appropriate access levels (Viewer vs. Editor vs. Explorer) are UX interventions. Delivering the right insight at the right moment in the user's existing workflow is a core UX principle. Forcing field users to navigate to Analytics Studio to see relevant data is a UX failure that strategy must correct.

- **Security** — Access model decisions (Viewer vs. Editor, row-level security verification before embedded deployment) have direct security implications. An embedded dashboard without filter pass-through may expose cross-record data. Editor access granted too broadly allows dashboard corruption. Security review of the access model is a required step before any embedded or self-service deployment.

- **Reliability** — The Adoption App depends on the analytics dataflow running successfully on schedule. If the dataflow fails silently (misscheduled, insufficient data sync window, creating-user credential issues), adoption metrics disappear without warning. Monitoring the Adoption App dataflow schedule is a reliability concern.

---

## Architectural Tradeoffs

**Embedded analytics vs. Analytics Studio navigation:**
Embedded dashboards (Lightning App Builder) deliver higher field-user adoption but require filter pass-through configuration and increase the maintenance surface (each embedded dashboard is a separate Lightning page component to maintain when dashboards are renamed or deleted). Analytics Studio navigation requires zero maintenance overhead but has significantly lower field-user adoption. For field-facing personas, embedded analytics wins on adoption impact; for analyst personas, direct Analytics Studio access is appropriate.

**Viewer vs. Editor access for self-service users:**
Editor access unlocks self-service lens creation but introduces the risk of shared dashboard corruption. The tradeoff is between self-service agility and governance risk. The mitigation is clear norms and onboarding, not restricting access — Viewer-only access defeats the purpose of self-service analytics.

**Analytics Adoption App (template) vs. custom adoption reporting:**
The template app is faster to stand up and tracks the right events (app/dashboard/lens opens) out of the box. Custom adoption reporting using the WaveAutoInstallRequest or querying analytics event logs requires developer effort and produces equivalent signal. Unless the template's pre-built dashboards are insufficient for the stakeholder's questions, the template is the right choice.

---

## Anti-Patterns

1. **Measuring analytics adoption with CRM login metrics** — Using login frequency or record creation counts (from the Salesforce Adoption Dashboards AppExchange package) as a proxy for analytics adoption produces false positives. A user who logs in daily to create Opportunities but never opens a CRM Analytics dashboard appears as "fully adopted" in CRM metrics. Analytics adoption requires analytics-specific measurement via the Analytics Adoption App.

2. **Deploying embedded analytics without filter pass-through** — Embedding a dashboard on a record page without configuring the filter pass-through attribute produces a dashboard that shows all data to all users. This is both a UX failure (irrelevant data for the record context) and a potential security issue (data the user should not see may be visible). Always configure and test filter pass-through before activating embedded dashboards for non-admin profiles.

3. **Granting Editor access org-wide for convenience** — Assigning Editor access to all analytics users to avoid having to manage Viewer vs. Editor grants is a governance anti-pattern. Editor access allows saving over shared dashboards and creating assets in the shared app namespace. Corrupted canonical dashboards erode user trust and require developer intervention to restore. Apply the principle of least privilege: Viewers get Viewer; only designated self-service users get Editor.

---

## Official Sources Used

- Adoption Analytics Template (Salesforce Help) — prerequisite, creation steps, and scope configuration for the Analytics Adoption App
  URL: https://help.salesforce.com/s/articleView?id=sf.bi_template_adoption.htm

- Use the Adoption Analytics App (Salesforce Help) — how to navigate and interpret the Adoption App dashboards
  URL: https://help.salesforce.com/s/articleView?id=sf.bi_template_adoption_use.htm

- Create the Adoption Analytics App (Salesforce Help / Analytics docs) — creation wizard steps and managed package prerequisite
  URL: https://help.salesforce.com/s/articleView?id=analytics.bi_template_adoption_create.htm

- Embed a CRM Analytics Dashboard in Lightning Experience (Trailhead) — embedded analytics component configuration in Lightning App Builder
  URL: https://trailhead.salesforce.com/content/learn/modules/wave_enable_crm_analytics/wave_enable_crm_analytics_lightning

- App Structuring and Design Concepts (Trailhead — Analytics App Design module) — app collections, sharing, and access level guidance
  URL: https://trailhead.salesforce.com/content/learn/modules/analytics-app-design/structure-your-app

- Salesforce Well-Architected Overview — Operational Excellence and User Experience pillar framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
