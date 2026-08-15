# LLM Anti-Patterns — Employee HR Service Agent Rollout

Common mistakes AI assistants make when an admin / architect asks for help rolling out an HR / Employee Service agent. Avoid these when generating recommendations.

---

## Anti-Pattern 1: Treating the LLM as an access-control layer

**What the LLM generates:**

> "Add an instruction to the agent: 'You may only display HR data for the user you are currently chatting with.' That will prevent cross-employee data leaks."

**Why it's wrong:**
- Prompt instructions are guidance, not controls. A sufficiently confused state, an instruction-injection attack, or even an idiosyncratic LLM response can violate them silently.
- Compliance auditors will not accept "we told the LLM not to" as a security control.
- The cost of getting this wrong (one employee sees another's pay or PTO) is materially worse than the cost of building a real control.

**What to do instead:** Enforce the visibility boundary in the **Apex action layer**. Every action binds the running user from `UserInfo.getUserId()`, queries with explicit user-scoped filters, and returns only the rows the caller is authorized to see. The LLM is a presentation layer; it can only display data the action gave it.

---

## Anti-Pattern 2: Passing the full HRIS row into agent context

**What the LLM generates:**

```apex
// Fetch the worker record from Workday and stash it on the conversation context
Map<String, Object> worker = WorkdayClient.getWorker(workerId);
session.put('worker', worker);   // The agent can now reference any field
```

**Why it's wrong:**
- The Workday worker record contains pay rate, performance scores, dependents, termination data, and SSN-derived identifiers. Exposing all of it to the LLM context means any one of those fields can leak into responses.
- The Einstein Trust Layer can mask some of this, but masking is entitlement-gated and not a substitute for not transmitting the data in the first place.

**What to do instead:** Action's return type is a tightly-scoped struct with only the fields the agent will display. Pull the worker, project the fields, return only those. The LLM cannot leak what it never received.

---

## Anti-Pattern 3: Recommending read-write HRIS integration in the pilot

**What the LLM generates:**

> "For the pilot, build the agent to submit leave requests, update benefits enrollments, and modify direct-deposit settings — all writing back to Workday."

**Why it's wrong:**
- Read-write integration roughly triples the engineering and operational cost vs read-only: idempotency, reconciliation runbooks, manager-approval round-trips, EU works-council consultation, error-message curation.
- Pilots are about producing measurable deflection within a quarter. Read-only against PTO balance and benefits FAQ does that. Read-write does not — it spends the quarter on the integration and produces a small amount of deflection at the end.
- Read-write failure modes (Workday-side rejection after the agent said "submitted") create a worse user experience than no agent at all.

**What to do instead:** Pilot read-only. Build a Salesforce-side "leave intent" record where read-write is desired, but defer the actual HRIS submission until a second phase where the operational mechanics are mature.

---

## Anti-Pattern 4: Confident claims about specific HRIS connector availability

**What the LLM generates:**

> "Salesforce has a certified Workday connector on the AppExchange — install it from this URL: ..."
> "Use the BambooHR Lightning Connector to wire the agent to BambooHR."

**Why it's wrong:**
- Specific AppExchange listings, package names, and URLs change. A confident claim about "the certified Workday connector" that resolves to a stale or partner-owned package leads the user down a wrong path.
- HRIS connector availability is org- and contract-specific. A connector that exists on AppExchange may not be entitled for a particular customer's edition.

**What to do instead:** Recommend that the rollout team **verify on the AppExchange** at planning time, evaluate against the specific HRIS deployment (cloud vs on-prem, edition), and in parallel scope a Custom Apex + Named Credentials path as a fallback. Do not name specific package names with the certainty of a fact.

---

## Anti-Pattern 5: Recommending Embedded Service on the intranet as the default surface

**What the LLM generates:**

> "Deploy the HR agent as an Embedded Service chat widget on the company intranet. Employees can click the widget any time they have a question."

**Why it's wrong:**
- Most employees are not on the intranet for sustained periods. The friction of "open intranet → find widget → ask question" is higher than the friction of "open Slack → ask in DM."
- Embedded Service on intranet has the lowest adoption of the three surface options for frontline employee use cases.
- The recommendation often comes from "this is the most Salesforce-native deployment" reasoning, which optimizes the wrong axis.

**What to do instead:** Default to where the user is. Slack-first for Slack-native orgs, Teams-first for Microsoft 365 / Teams-native orgs, Embedded Service only when neither chat platform is available or approved for HR data classes. The platform-native answer (Salesforce console) is right only for HRBPs, not for end employees.

---

## Anti-Pattern 6: Fabricating standard subagent names or SKU details

**What the LLM generates:**

> "The Employee Service license includes the following standard topics out of the box: Leave_Request_Standard, Benefits_Open_Enrollment_Walkthrough, PTO_Balance_Lookup_Standard, Onboarding_Day_One_Checklist, ..."

**Why it's wrong:**
- The names of shipped subagents (called topics before April 2026, and still called that in the metadata API), the exact SKU coverage, and the entitlement matrix change per release. Naming specific subagents in this confident way creates an expectation the org will then look for in their builder UI. When they don't find that exact name, they assume their license is wrong.
- Releases (Spring '25, Summer '25, Winter '26) shift this content; LLM training data lags real release notes.

**What to do instead:** Recommend opening Agentforce Builder → Templates → Employee Service in the actual org and reviewing the real shipped roster against the actual entitlement. Frame the rollout in terms of "configure the standard subagents your license includes" rather than naming a specific list.

---

## Anti-Pattern 7: Skipping baseline measurement before launch

**What the LLM generates:**

> "After launch, measure deflection rate by counting agent sessions and comparing to the previous month's HR ticket volume."

**Why it's wrong:**
- Without a deliberate pre-launch baseline (4 weeks of HR case volume by category, time-to-first-response distributions, post-resolution CSAT), there is no honest answer to "did the agent help?" Comparing to "the previous month" is a noisy point estimate that can swing 20% on a single PTO season or compliance update.
- Stakeholders will ask for the success number within two weeks of launch. Without instrumentation in place from day 1, that number doesn't exist and the rollout loses political credibility.

**What to do instead:** Instrument deflection rate, FRT, and CSAT — with a 4-week pre-launch baseline — before going live. Make the measurement plan a phase gate, not an afterthought. The skill's recommended workflow places measurement at step 7 deliberately: it's the last step in launching, not the first step after.
