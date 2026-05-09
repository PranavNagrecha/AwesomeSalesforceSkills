# Gotchas — Employee HR Service Agent Rollout

Non-obvious Salesforce platform behaviors that cause real production problems when rolling out an HR / Employee Service agent.

---

## Gotcha 1: PII flows into the LLM context whenever you put the raw HRIS row into the prompt

**What happens:** Team writes an Apex action that calls Workday, gets back a JSON row containing leave balance, pay rate, manager id, dependents, then passes the entire JSON blob to the agent as a flow variable. The LLM "knows" about pay rate even when only displaying leave balance, and sometimes leaks it into responses ("Based on your $4,500 base salary…").

**When it occurs:** Whenever the action layer passes raw HRIS rows into the agent context object instead of returning a tightly-scoped output struct.

**How to avoid:** The action's `@InvocableMethod` return type should contain only the fields the agent will display. Strip everything else server-side before the agent sees it. The LLM cannot leak what it never received.

---

## Gotcha 2: The Einstein Trust Layer's masking and zero-retention behaviors are entitlement-gated

**What happens:** Team designs the agent assuming Trust Layer masking applies automatically — passing PII through the agent and trusting that masking will redact before anything is sent to a model provider. In production they discover their license tier doesn't include the masking they expected, or masking applies to a narrower field set than they assumed.

**When it occurs:** Most often when a Service Agent license is being repurposed for an Employee Service rollout, or when the org bought into Agentforce on an entry tier and assumed feature parity with enterprise demos.

**How to avoid:** Confirm Trust Layer entitlements in writing with your AE before the rollout plan calls for masking-dependent flows. Defensive design: minimize PII in prompt context regardless of Trust Layer entitlement. Treat Trust Layer as defense-in-depth, not the only line.

---

## Gotcha 3: Manager-of-team sharing requires explicit relationship lookups, not Role Hierarchy alone

**What happens:** Team assumes Salesforce Role Hierarchy gives a manager visibility to direct reports' HR records. They build the agent to query the running manager's User record, expecting Role Hierarchy to return the team. The query returns nothing, or returns the wrong people, because Role Hierarchy reflects org chart sales territory, not always HR reporting line.

**When it occurs:** Whenever the org's Salesforce Role Hierarchy was built for sales reporting and is not synchronized with the HR reporting structure. This is most orgs.

**How to avoid:** Use the standard `User.ManagerId` field as the source of truth for HR reporting line. For the manager-of-team flow, query `WHERE ManagerId = :runningUser.Id`. Document this as the manager-team join in the visibility matrix. Synchronize `User.ManagerId` from the HRIS as part of the rollout — out-of-date manager assignments produce wrong agent behavior.

---

## Gotcha 4: Knowledge article visibility cascades through Data Categories and channel availability — both must be set

**What happens:** HR ops imports policy articles into Salesforce Knowledge for grounding. They set Data Category to "Compensation — manager-only." But the agent retrieves the article anyway when an employee asks, because the article's Channel availability included "Internal App" and the agent is treated as Internal App.

**When it occurs:** When Data Category visibility and Channel availability are configured by different people at different times. Each is necessary; neither is sufficient.

**How to avoid:** For each Knowledge article in the HR KB, audit BOTH:
1. Data Category visibility — restrict "Compensation" category to manager profiles via Setup → Data Category Visibility.
2. Channel availability — confirm "Public Knowledge Base" is unchecked on internal-only HR articles.

Run the bundled checker to flag articles where channel = Public Knowledge Base on HR-tagged Data Categories.

---

## Gotcha 5: The HRIS may return data in a different timezone or unit than the employee expects

**What happens:** Workday returns leave balance in days; the agent displays "you have 12 days of PTO." But the employee's payroll system tracks PTO in hours. Or: HRIS returns leave dates in UTC; the agent displays them un-localized; an employee in Singapore sees their leave starting on the wrong day.

**When it occurs:** Whenever HRIS data is returned with implicit unit assumptions and the agent treats the value as a printable string.

**How to avoid:** Action layer normalizes units and timezone before returning to the agent. Return a struct with explicit unit fields (`balanceUnits: 'HOURS'`) so the agent template can render the right phrase. For dates, convert to the user's `User.TimeZoneSidKey` server-side and return formatted strings.

---

## Gotcha 6: Slack-to-Salesforce user mapping breaks for SSO-provisioned shadow users

**What happens:** Slack workspace has employees whose Salesforce account was provisioned via SSO with a federation Id mismatch. The Slack-to-Salesforce mapping returns no user. The agent action calls `UserInfo.getUserId()` and gets the integration user, not the actual employee. The action then fetches the integration user's "leave balance" — which is nonsense or empty.

**When it occurs:** Mid-rollout, often the day after launch when contractor or new-hire accounts hit the agent. The pilot group did not include this case because pilots typically use full-employee FTEs with established SSO.

**How to avoid:** Action layer asserts that the running user is a real employee user (e.g., `User.Profile.Name != 'Integration User'` and `User.IsActive = true` and a populated employee identifier on the User record). On assertion failure, return a clear "your account isn't provisioned for this self-service feature" message and emit an admin alert.

---

## Gotcha 7: Read-write back to HRIS is not transactional with the Salesforce-side record

**What happens:** Agent submits a leave request. The Apex action successfully calls Workday (Workday returns 201 Created). Then the local `Leave_Submission__c` record save fails (validation rule, governor limit). The leave is in Workday but Salesforce has no record of it. Or the inverse: Salesforce save succeeds, Workday call times out, leave appears in Salesforce but not Workday.

**When it occurs:** Anywhere a write spans Salesforce and an external system. There is no two-phase commit.

**How to avoid:**
- Adopt the local-record-first pattern shown in `examples.md` — write a `PENDING` row in Salesforce first, then call the HRIS, then update the local row to `ACCEPTED` or `REJECTED` based on the HRIS response. This makes Salesforce the source of "did we attempt this" and HRIS the source of "did we succeed."
- Implement a reconciliation job: every N hours, compare PENDING rows to HRIS state and reconcile.
- Communicate truthfully to the employee: "your request is pending — we'll confirm in the bell when HR has accepted." Do not say "your request was submitted" until the HRIS round-trip confirms.
