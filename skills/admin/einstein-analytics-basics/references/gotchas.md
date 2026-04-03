# Gotchas: Einstein Analytics Basics

---

## Mistaking "Fancy Dashboard" for a CRM Analytics Requirement

**What happens:** Stakeholders ask for CRM Analytics because the dashboard should "look executive." The actual requirement is a summary chart on standard Salesforce data.

**When it bites you:** Sales ops, service ops, and leadership dashboards that are visually ambitious but analytically simple.

**How to avoid it:** Force the team to state what standard reports cannot do. If the answer is unclear, stay in reports.

---

## Ignoring Refresh Lag

**What happens:** Users assume analytics data is live. A dashboard shows yesterday's dataset refresh, and trust drops immediately.

**When it bites you:** Daily standups, support queue management, and any scenario where users compare dashboards to live records.

**How to avoid it:** Document refresh cadence on every dashboard and confirm that latency is acceptable for the use case.

---

## License Planning Happens Too Late

**What happens:** The pilot works for admins and analysts, but rollout stalls because the intended users do not have CRM Analytics access.

**When it bites you:** Executive dashboards, regional rollouts, and mobile analytics initiatives.

**How to avoid it:** Count actual consumers before building, not after demos succeed.

---

## Dataset Security Is Hand-Waved

**What happens:** Teams assume ordinary Salesforce visibility automatically governs all analytics behavior. A dashboard is shared too broadly or hides too much.

**When it bites you:** Territory-based analytics, partner views, and sensitive service metrics.

**How to avoid it:** Treat analytics security as its own design decision and test with real personas.
