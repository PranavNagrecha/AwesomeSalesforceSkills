# Examples — Change Management and Training

## Example 1: Service Cloud Go-Live with 200 Agents

**Context:** A company is rolling out Salesforce Service Cloud to 200 customer service agents across three contact centers. The agents currently use a legacy ticketing system. This is not a Salesforce-to-Salesforce migration — most agents have never used Salesforce before.

**Problem:** Without structured change management, agents will receive a login URL, attend a 2-hour generic demo, and then be expected to handle live cases. Within the first week, handle time spikes, agents revert to email, and management loses confidence in the project.

**Solution:**

1. Run change impact assessment 6 weeks before go-live. Output:
   - Agents: entirely new UI, new case workflow, required Reason field
   - Supervisors: new dashboards, omni-channel queue management
   - QA team: new case scoring in Salesforce vs. legacy system export
2. Build role-specific training:
   - Agents: 4-hour hands-on session in sandbox with realistic case scenarios; Trailhead trail "Service Cloud for Agents" as pre-work
   - Supervisors: 2-hour session on queue management and dashboards
3. Configure In-App Guidance walkthroughs for the top 3 case-handling steps (create case, set status, add resolution note)
4. Run a 2-week pilot with 15 volunteer agents from one contact center
5. Use pilot feedback to rewrite 3 training modules that were unclear
6. Send go-live announcement 5 business days before, including Chatter group link and named floor support contacts
7. Install Salesforce Adoption Dashboards; set target: 95% of agents logging in within 5 business days of go-live

**Why it works:** Role-specific training anchored to real scenarios reduces cognitive load. The pilot catches gaps before they affect 200 people. In-app guidance provides just-in-time help without agents needing to remember the training session.

---

## Example 2: Sales Process Change — New Required Stage Fields

**Context:** The Revenue Operations team is adding 3 required fields to the Opportunity object for the Proposal stage: Competitor, Decision Criteria, and Budget Confirmed. This affects 50 Sales Reps and 10 Sales Managers globally.

**Problem:** The admin deploys the required fields without communication. Sales Reps encounter validation errors when saving Opportunities at stage Proposal. They call IT, frustrated that "Salesforce is broken." Handle time on IT support spikes for 3 days.

**Solution:**

1. Change impact assessment identifies:
   - Sales Reps: 3 new required fields at Proposal stage (medium disruption)
   - Sales Managers: no UI change; downstream impact on forecast quality (low disruption)
   - Integration team: field mapping for CRM-to-ERP sync needs update (separate technical track)
2. Draft a What Changed Guide for Sales Reps:
   - "When you move an Opportunity to Proposal, you will now need to fill in Competitor, Decision Criteria, and Budget Confirmed before saving."
   - "These fields help Revenue Ops forecast accurately. If you are unsure, enter your best estimate — you can update it later."
3. Update Path coaching text at the Proposal stage to remind reps of the 3 fields and why they matter
4. Send announcement to Sales Reps and Managers 5 business days before deployment:
   - Subject: "Salesforce Update on [Date]: 3 New Fields for Proposal Stage"
   - Body: what changes, why, who to contact with questions
5. Deploy the validation rules and Path coaching text together
6. Monitor Chatter group for questions in the first week

**Why it works:** Communicating before deployment turns a surprise error into an expected behavior. Path coaching text provides persistent guidance without requiring IT support. Framing the change around business benefit ("help Revenue Ops forecast") gives reps a reason to comply.

---

## Anti-Pattern: Training Delivered on Go-Live Day

**What practitioners do:** Schedule a "training session" as a 30-minute Zoom call on the morning of go-live. The demo covers every feature rather than what specific roles actually do.

**What goes wrong:** Users are overwhelmed with platform features they will not use for months. They have no time to practice before live cases or opportunities arrive. The first live interaction is stressful. Adoption drops. Management blames the tool, not the training approach.

**Correct approach:** Deliver hands-on, role-specific training in a sandbox at least one week before go-live. Use the go-live day for a brief reminder communication (5 minutes, not 30), not for primary training. Reserve the launch day for excitement and support — not instruction.
