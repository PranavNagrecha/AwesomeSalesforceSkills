# Gotchas — Salesforce Support Escalation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Severity Downgrade Resets Queue Position

**What happens:** If you open a case at Sev1 but the support engineer determines it does not meet the Sev1 criteria (e.g., it is a sandbox issue or a partial impact with a workaround), they will downgrade the severity. A downgraded case does not retain its original queue position — it is re-routed to the new severity queue and treated as a fresh intake. This can add hours to response time.

**When it occurs:** Any time a case is opened at an inflated severity to "get attention faster." Common examples: sandbox blocking a developer (not Sev1), a feature broken for one user (not Sev2), or a cosmetic issue with no workaround explicitly tried (not Sev3).

**How to avoid:** Match severity to the actual Salesforce definition. If the business impact is borderline between Sev2 and Sev3, open at Sev3 and include a sentence in the description explaining why urgency is higher than the standard Sev3 response window (e.g., upcoming go-live in 48 hours). This keeps the case in the correct queue while flagging the urgency to the triage agent.

---

## Gotcha 2: The In-Case Escalate Button Is Disabled on Certain Case Statuses

**What happens:** The "Escalate to Technical Support Management" button is only available when the case is in an active status (typically "New," "In Progress," or "Assigned"). If the case status has moved to "Pending Customer Input," "Solution Provided," or "Closed," the button is grayed out or absent entirely.

**When it occurs:** A support engineer replies with a question or a proposed solution and the case auto-transitions to "Pending Customer Input." If the practitioner doesn't respond quickly, the case may be closed without resolution. When they come back to escalate, the button is gone.

**How to avoid:** Before attempting to escalate, add a case comment stating that the issue is not resolved and that you are still experiencing the problem. This moves the case status back to an active state and re-enables the escalation button. Always respond to "Pending Customer Input" cases promptly even if only to say "This is still occurring."

---

## Gotcha 3: Trust Site Instance Names Can Differ from What You See in the Org URL

**What happens:** A practitioner checks `trust.salesforce.com` for their instance but cannot find it, because the instance name in their org URL does not exactly match the Trust site entry. This is common for Hyperforce orgs, Government Cloud instances, and orgs migrated across data centers.

**When it occurs:** Hyperforce orgs may have instance names like `USA2S` or region-based identifiers rather than the classic `NA###` or `EU##` pattern. Practitioners searching for "NA135" will not find the relevant Trust entry if the org was migrated.

**How to avoid:** Find the canonical instance name under Setup > Company Information > Instance (not the URL). This field reflects the actual Salesforce infrastructure instance. Use that string to search on the Trust site. For Hyperforce orgs, note that Trust status may be aggregated at the Hyperforce region level, not the individual org instance level.

---

## Gotcha 4: Opening Multiple Cases for the Same Incident Slows Resolution

**What happens:** During a widespread incident, multiple admins or team members open separate Sev1 cases for what is the same platform-level issue. Salesforce support must triage and link all of them to the incident. This creates case queue congestion that slows response time for everyone, including the organization that filed the duplicates.

**When it occurs:** During major outages when multiple team members act independently without checking whether a case is already open or whether the Trust site shows an active incident.

**How to avoid:** Designate one person as the "case owner" during incidents. Check `trust.salesforce.com` and the org's open cases in the Help portal before filing. If an incident is already on the Trust site, one case with org-specific detail is sufficient. Post the case number in a shared internal channel so no one files a duplicate.

---

## Gotcha 5: Known Issue Votes Are Per Org, Not Per User

**What happens:** A team of five admins all click "This issue affects me" on the same Known Issue article from their individual Salesforce Help accounts. They assume this registers five votes toward prioritization. In reality, Salesforce counts unique affected org IDs, not unique users. All five clicks from the same org count as one.

**When it occurs:** Anytime a team tries to "vote up" a known issue by having multiple people register from the same org.

**How to avoid:** Designate one person per org to click "This issue affects me" and to add the most detailed comment possible (which browser, which Lightning page, which user profile, which API version). The comment quality contributes more to fix prioritization than the number of clicks. If multiple orgs are affected (e.g., an ISV with many customers), have one admin per org register — each org ID counts separately.

---

## Gotcha 6: Premier Response Time Applies to Response, Not Resolution

**What happens:** An admin expects that Premier's 1-hour Sev2 SLA means the issue will be resolved in one hour. The SLA actually covers initial response — first contact from an engineer. Resolution time is separate and not guaranteed by plan tier for most issues.

**When it occurs:** Any time a practitioner communicates a plan-tier-based SLA to a business stakeholder as a resolution commitment rather than a response commitment.

**How to avoid:** When setting stakeholder expectations, distinguish between "we will hear from a support engineer within 1 hour (Premier Sev2)" and "the issue will be resolved within X hours." Resolution depends on the complexity of the underlying defect. For Sev1 incidents, the support team works continuously toward resolution, but no plan tier guarantees a resolution time in the standard service agreement.
