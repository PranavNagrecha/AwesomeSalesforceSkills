# Examples — Volunteer Management Requirements

## Example 1: NPSP Org with V4S — Shift-Based Volunteer Scheduling

**Scenario:** A food bank using NPSP needs to schedule 200 volunteers across 30 weekly shifts. Staff asked whether to use Data Loader to insert Contact records directly into volunteer shifts.

**Problem:** The practitioner planned to insert records directly into a custom `Volunteer_Shift_Signup__c` object without using V4S, assuming it was equivalent to the managed package.

**Solution:**
1. Confirm V4S is installed (Setup > Installed Packages, look for Volunteers for Salesforce)
2. Use the V4S object hierarchy: `GW_Volunteers__Volunteer_Campaign__c` > `GW_Volunteers__Volunteer_Job__c` > `GW_Volunteers__Volunteer_Shift__c` > `GW_Volunteers__Volunteer_Hours__c`
3. Load shifts via Data Loader using fully qualified API names including the `GW_Volunteers__` prefix
4. Set `GW_Volunteers__Status__c = 'Confirmed'` on Hours records for scheduled volunteers
5. After shifts complete, update Status to `Completed` — the V4S rollup trigger will aggregate hours to the Contact's `GW_Volunteers__Total_Volunteer_Hours__c` field

**Why this works:** V4S is a managed package with its own object model and namespace. Bypassing it with custom objects loses the shift capacity tracking, website plugin integration, and built-in hours rollup automation. Using the correct namespace API names is mandatory — any omission of `GW_Volunteers__` causes silent SOQL failures.

---

## Example 2: NPC Org — Recognition Automation Timing Issue

**Scenario:** A national nonprofit on Nonprofit Cloud built a Flow to send a recognition badge email when a volunteer's `TotalVolunteerHours__c` exceeded 100. The Flow was triggered by a new `VolunteerHoursLog__c` record insert. Volunteers were not receiving emails despite hours being logged correctly.

**Problem:** The Flow read `TotalVolunteerHours__c` immediately after the hours log insert. Because this field is populated by a DPE scheduled batch job (not a real-time trigger), the value was always stale at trigger time. The DPE had not yet run, so the field still showed the pre-insert total.

**Solution:**
1. Remove the trigger from `VolunteerHoursLog__c` insert
2. Identify the DPE definition name in Setup > Data Processing Engine
3. Use a Scheduled Flow or DPE completion platform event to fire the recognition check after DPE runs
4. Alternatively, maintain a separate running counter using a trigger-based rollup on the hours log object that does not depend on DPE — use this counter for real-time threshold checks

**Why this works:** DPE is a batch computation layer, not an event-driven trigger. All processes that depend on DPE-computed fields must execute after the DPE run completes, not at the moment the source data is written.

---

## Example 3: Skills Matching — Scoping as a Custom Build

**Scenario:** An environmental nonprofit wanted to match volunteers with specific certifications (chainsaw certified, first aid, Spanish speaker) to volunteer shifts that required those skills.

**Problem:** An AI assistant told the team to use "the native Salesforce volunteer skills matching feature." No such native feature exists in V4S or NPC.

**Solution:**
1. Create a custom `Volunteer_Skill__c` junction object with lookup to Contact and a `Skill_Type__c` picklist
2. Add a `Required_Skills__c` multi-select picklist or related list to `GW_Volunteers__Volunteer_Job__c`
3. Build a Screen Flow that queries available shifts, filters by skill match, and surfaces options to staff schedulers
4. Document this as a custom build with ongoing maintenance responsibility — it is not a standard feature

**Why this works:** Setting accurate scope expectations early prevents scope creep and architectural surprises. Neither V4S nor NPC has a native skills-matching engine — treating it as a custom build ensures it is properly estimated, tested, and maintained.
