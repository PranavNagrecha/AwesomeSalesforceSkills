# Examples: Einstein Analytics Basics

---

## Example: Standard Reports Are Still Enough

**Scenario:** Sales leadership wants a weekly pipeline dashboard by owner, stage, and close month. The data is entirely in Opportunities and needs to reflect today's numbers.

**Decision:** Use Salesforce Reports and Dashboards.

**Why:**
- real-time data matters
- no complex transformation is required
- business users may want to tweak filters themselves
- no extra CRM Analytics licenses are needed

**What would be wasteful:** creating a CRM Analytics dataset just to show pipeline by rep.

---

## Example: CRM Analytics Is the Better Fit

**Scenario:** A support organization needs a service dashboard that blends Cases, Entitlements, milestone timing, reopen behavior, and trend calculations over a large history window.

**Decision:** Use CRM Analytics.

**Why:**
- multiple transformed metrics are needed
- historical analysis is heavier than standard reports handle well
- executives want mobile-friendly dashboards with richer visual design

**Non-negotiables:**
- define refresh cadence
- confirm license coverage
- design dataset security explicitly

---

## Example: Tableau, Not CRM Analytics

**Scenario:** Operations wants a dashboard combining Salesforce pipeline, ERP backlog, product usage telemetry, and finance forecasts.

**Decision:** Evaluate Tableau or the enterprise BI platform.

**Why:** This is a cross-system analytics problem, not just a Salesforce dashboard problem.

**Admin takeaway:** Do not use CRM Analytics as a political compromise when the real need is enterprise BI.
