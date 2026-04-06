# Gotchas — Entitlements and Milestones

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Entitlement Templates Cannot Be Attached to Products in Lightning Experience

**What happens:** Admins create entitlement templates in Setup, then navigate to a Product2 record in Lightning Experience expecting to find an "Entitlement Templates" related list. The related list is absent. There is no Lightning-compatible UI to link a template to a product. If the admin relies on this for automated entitlement creation when an opportunity closes, nothing is created.

**When it occurs:** Any org running Lightning Experience that uses Products & Price Books for support contracts and relies on entitlement templates to auto-create entitlements. This is silent — no error is thrown when the template is not attached; entitlements simply are not created.

**How to avoid:** In Lightning, build a Record-Triggered Flow on `OpportunityLineItem` insert (when `Opportunity.StageName = 'Closed Won'`) or on `Order` activation that creates an `Entitlement` record programmatically, referencing the entitlement template ID. The template controls default field values (process, business hours, duration) but the Flow must create the actual entitlement. Document this Flow as the canonical entitlement creation mechanism so future admins do not re-introduce the Classic reliance.

---

## Gotcha 2: Missing EntitlementId on Case Silently Disables All Milestone Tracking

**What happens:** Entitlement processes and milestones are fully configured and activated, but no milestone timers appear on cases. No warning or violation actions fire. The Milestone Tracker component on the case record shows nothing.

**When it occurs:** Cases created via Email-to-Case, Web-to-Case, or the API where the `EntitlementId` lookup is not explicitly set. The entitlement process only triggers when `Case.EntitlementId` is populated at case creation (or updated shortly after, within the process start window). An entitlement can exist on the Account without being stamped on the Case.

**How to avoid:** Build a Before-Save Record-Triggered Flow on Case creation that queries the active entitlement for the case's account and populates `EntitlementId`. Test by creating cases through each intake channel (Email-to-Case, Web-to-Case, API, UI) and verifying the Milestone Tracker activates on all channels. Add this check to the go-live validation checklist.

---

## Gotcha 3: Milestone Timer Pauses Do Not Cancel Already-Queued Violation Actions

**What happens:** After a violation action is scheduled (the milestone's time limit is reached), an admin updates the case's entitlement business hours or otherwise attempts to pause/extend the timer. The violation action fires at the originally scheduled time regardless. The timer state and the action scheduler are not retroactively synchronized.

**When it occurs:** Orgs that change business hours mid-flight, or that attempt to "extend" a milestone after the timer has already expired. It also occurs when a sandbox copy is taken at a certain time and then restored — the action timestamps are frozen relative to when they were scheduled.

**How to avoid:** Treat milestone violation actions as immutable once the timer expires. If SLA commitments change, update the entitlement process version and apply the new version to future cases. For in-flight exceptions, handle them manually (complete the milestone in the UI or update the case field directly) rather than relying on timer manipulation. Communicate clearly to operations teams that mid-flight SLA extensions must go through a defined exception process.

---

## Gotcha 4: Entitlement Process Versions Lock In-Flight Cases

**What happens:** An admin needs to change a milestone's time limit (e.g., from 4 hours to 2 hours for a new contract tier). They update the existing entitlement process and republish it. Cases that were already on the old process version continue using the old time limits and old action thresholds. The admin believes the change is live org-wide, but open cases are unaffected.

**When it occurs:** Any time an existing entitlement process is modified and a new version is published. Salesforce creates a new process version; existing cases retain a reference to the version that was active when their entitlement was applied.

**How to avoid:** When releasing a new entitlement process version, identify open cases on the old version using a report filtered by `Case.Entitlement.EntitlementProcess.Name` and the old version label. For critical changes, build a Flow to reassign entitlements on open cases to the new version. Communicate the cutover date and cutover scope to support leadership before publishing the new version.

---

## Gotcha 5: Independent Recurrence Milestones Can Stack and Create Alert Floods

**What happens:** An entitlement process uses Independent recurrence on a milestone with a short time limit (e.g., 1 hour). Cases go unworked for several hours. The milestone timer fires multiple violation actions in rapid succession as each independent instance expires. The support team receives a flood of email alerts for a single case.

**When it occurs:** Independent recurrence milestones that reset based on a case field update or elapsed time, combined with cases that are unworked for longer than one recurrence interval. Each unresolved instance continues running independently.

**How to avoid:** Use Independent recurrence only when each recurrence genuinely represents a distinct SLA commitment (e.g., each customer comment). For general response SLAs, prefer No Recurrence. If Independent recurrence is required, gate violation email alerts with a suppression check — for example, only send the violation email if `Case.Status != 'Waiting on Customer'`. This prevents alert storms for stalled cases that are legitimately awaiting customer input.
