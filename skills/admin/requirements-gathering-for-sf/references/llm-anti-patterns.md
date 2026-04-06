# LLM Anti-Patterns — Requirements Gathering for Salesforce

Common mistakes AI coding assistants make when generating or advising on Salesforce requirements gathering and business analysis.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Writing user stories without Salesforce-specific acceptance criteria

**What the LLM generates:** "As a sales rep, I want to track my deals so that I can manage my pipeline."

**Why it happens:** LLMs produce generic user stories that lack Salesforce-specific testable criteria. A Salesforce user story must reference specific objects, fields, page layouts, picklist values, and automation behavior. Without platform-specific acceptance criteria, the developer cannot validate the build against the requirement.

**Correct pattern:**

```
Salesforce-specific user story format:
As a [Sales Rep with Sales User profile],
I want to [create an Opportunity with the B2B Sales Process record type],
So that [I can track my deals through the pipeline stages].

Acceptance Criteria:
- Given a Sales Rep user with the Sales_User profile
- When they click "New Opportunity" on an Account record
- Then the record type selector shows "B2B Sales Process" as default
- And the Stage picklist shows: Prospecting, Qualification, Proposal, Closed Won, Closed Lost
- And the Amount and Close Date fields are required
- And a validation rule prevents saving without a primary Contact Role
- And the Opportunity appears in the "My Open Opportunities" list view
```

**Detection hint:** If the user story has no acceptance criteria referencing specific Salesforce objects, fields, record types, or profiles, it is too generic. Search for Salesforce-specific terms (object names, field names, profile names) in the acceptance criteria.

---

## Anti-Pattern 2: Skipping the As-Is process documentation

**What the LLM generates:** "Here is the To-Be process for your Salesforce implementation: Step 1: Lead is created via web form..."

**Why it happens:** LLMs jump to the solution (To-Be) without documenting the current state (As-Is). Without As-Is documentation, the team cannot identify what is actually changing, what pain points exist, what workarounds users have developed, or what data needs to be migrated. The gap analysis has no baseline.

**Correct pattern:**

```
Requirements gathering sequence:
1. As-Is Documentation:
   - Current process steps, tools, and handoffs.
   - Current pain points and workarounds.
   - Current data sources and volumes.
   - Current system integrations.
2. Gap Analysis:
   - As-Is pain point → Salesforce capability that addresses it.
   - As-Is workaround → Salesforce standard feature that replaces it.
   - As-Is limitation → Salesforce limitation that persists (no magic fix).
3. To-Be Documentation:
   - New process steps mapped to Salesforce features.
   - Changes per user role.
   - Data migration requirements.
```

**Detection hint:** If the output jumps directly to a To-Be process without an As-Is section, the baseline is missing. Search for `As-Is` or `current process` in the requirements document.

---

## Anti-Pattern 3: Producing a fit-gap analysis that marks everything as "Fit"

**What the LLM generates:** "Salesforce can handle all of these requirements out of the box. No gaps identified."

**Why it happens:** LLMs are optimistic about Salesforce's capabilities and mark all requirements as "Fit" without identifying the configuration effort, customization needed, or genuine platform limitations. Every Salesforce implementation has gaps -- features that require custom development, AppExchange solutions, or process changes.

**Correct pattern:**

```
Honest fit-gap classification:
| Requirement         | Classification | Effort | Notes                        |
|---------------------|---------------|--------|------------------------------|
| Lead capture form   | Fit           | Low    | Web-to-Lead standard feature |
| Approval routing    | Fit           | Medium | Approval Process config needed|
| Document generation | Gap (AppEx)   | Medium | Requires Conga or equivalent |
| Real-time sync      | Gap (Custom)  | High   | Requires Platform Events + Apex|
| Legacy report parity| Partial Fit   | Medium | 80% covered, 20% needs custom RT|

Classifications:
- Fit: standard feature, minimal configuration.
- Partial Fit: possible but requires significant configuration or workarounds.
- Gap (Config): requires custom development (Flow, Apex, LWC).
- Gap (AppExchange): requires a third-party app.
- Gap (Process Change): requirement must change to fit the platform.
```

**Detection hint:** If the fit-gap analysis has zero gaps or marks all items as "Fit," the analysis is unrealistically optimistic. Count the number of "Gap" or "Partial Fit" items -- zero gaps is a red flag.

---

## Anti-Pattern 4: Not identifying stakeholder roles for discovery interviews

**What the LLM generates:** "Interview the project sponsor about all the requirements for the Salesforce implementation."

**Why it happens:** LLMs default to a single stakeholder. Effective requirements gathering interviews multiple personas: end users (daily workflow), managers (reporting needs), IT (integration requirements), compliance (security/audit), and executives (business objectives). A single stakeholder provides only one perspective.

**Correct pattern:**

```
Stakeholder interview plan:
| Stakeholder Role    | Interview Focus                          | Key Questions                     |
|---------------------|------------------------------------------|-----------------------------------|
| Executive Sponsor   | Business objectives, success metrics     | What does success look like?      |
| Sales Rep           | Daily workflow, data entry pain points   | Walk me through your typical day  |
| Sales Manager       | Pipeline visibility, forecasting         | What reports do you check daily?  |
| Service Agent       | Case handling, SLA requirements          | What slows you down most?         |
| IT / Integration    | Systems of record, data flows            | What systems must connect?        |
| Compliance / Legal  | Data retention, PII, audit requirements  | What regulations apply?           |

Schedule 45-60 minutes per stakeholder group.
Prepare role-specific question guides before each interview.
```

**Detection hint:** If the output interviews only one stakeholder or does not distinguish between stakeholder roles, the requirements will be one-dimensional. Count the number of distinct stakeholder roles in the interview plan.

---

## Anti-Pattern 5: Mapping requirements to Salesforce features without considering limits

**What the LLM generates:** "Use a custom object for each transaction type. Create 15 custom objects to model the business."

**Why it happens:** LLMs map requirements to Salesforce features without checking edition-specific limits. Custom object limits vary by edition: Enterprise Edition allows 200 custom objects, Professional Edition allows 50. Similarly, process automation, custom fields per object, and API call limits vary. Requirements must be mapped against the org's actual limits.

**Correct pattern:**

```
Requirements must account for platform limits:
1. Custom objects: PE=50, EE=200, UE=2000.
2. Custom fields per object: varies by type (800 for standard Text).
3. Record-Triggered Flows per object: no hard limit but consolidate
   to 1 per timing (before/after) for maintainability.
4. API calls per 24 hours: varies by edition and license count.
5. Report types: 200 custom report types max.
6. Validation rules per object: limit varies.

During requirements gathering:
- Document the org's edition.
- Check current usage against limits (Setup → System Overview).
- Flag requirements that approach 80% of any limit.
```

**Detection hint:** If the output maps requirements to Salesforce features without referencing edition limits or current org usage, the implementation may hit limits. Search for `edition`, `limit`, or `System Overview` in the requirements.
