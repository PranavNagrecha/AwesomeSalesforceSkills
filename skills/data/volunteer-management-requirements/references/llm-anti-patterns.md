# LLM Anti-Patterns — Volunteer Management Requirements

Common mistakes AI coding assistants make when generating or advising on volunteer management in Salesforce nonprofits.

---

## Anti-Pattern 1: Omitting the GW_Volunteers Namespace Prefix in V4S SOQL

**What the LLM generates:** `SELECT Id, GW_Volunteers__Status__c FROM Volunteer_Hours__c WHERE Contact__c = :contactId`

**Why it happens:** LLMs learn object names from documentation and forum posts that sometimes omit namespace prefixes for readability. The partial name `Volunteer_Hours__c` looks valid syntactically.

**Correct pattern:** `SELECT Id, GW_Volunteers__Status__c FROM GW_Volunteers__Volunteer_Hours__c WHERE GW_Volunteers__Contact__c = :contactId` — every object and field in V4S requires the `GW_Volunteers__` prefix in API references.

**Detection hint:** If V4S SOQL contains object names without the `GW_Volunteers__` prefix, it will return 0 rows without an error in most contexts. Always verify query results are non-zero in a test org with known volunteer data.

---

## Anti-Pattern 2: Conflating V4S Objects with NPC-Native Volunteer Objects

**What the LLM generates:** Code or documentation that mixes `GW_Volunteers__Volunteer_Job__c` (V4S) with `JobPositionAssignment__c` (NPC), treating them as equivalent or suggesting they can be used in the same org seamlessly.

**Why it happens:** Both platforms serve volunteer management and share conceptual vocabulary (jobs, shifts, hours). LLMs trained on general Salesforce documentation conflate the two without platform context.

**Correct pattern:** Determine the org's platform first. V4S objects exist only in NPSP orgs with the managed package installed. NPC-native objects exist only in orgs with the Nonprofit Cloud license. They are not interchangeable and should never be mixed in the same process or SOQL join.

**Detection hint:** If code references both `GW_Volunteers__` prefixed objects and unnamespaced NPC volunteer objects in the same query or flow, it is conflating two separate platforms.

---

## Anti-Pattern 3: Treating TotalVolunteerHours as a Real-Time Field in NPC

**What the LLM generates:** A Flow or Apex trigger that reads `TotalVolunteerHours__c` immediately after a volunteer hours insert to check if a recognition threshold is met.

**Why it happens:** LLMs assume calculated fields (like rollup summaries) update synchronously. They do not model the DPE batch execution gap.

**Correct pattern:** Recognize that `TotalVolunteerHours__c` in NPC is a DPE-computed field updated on a scheduled batch cycle. Any threshold check or recognition automation must execute after the DPE run, not on the hours insert event. Use a DPE completion event listener or schedule the recognition flow after the DPE window.

**Detection hint:** If a flow triggered on a volunteer hours record insert reads `Contact.TotalVolunteerHours__c` in the same transaction, it is reading a stale value.

---

## Anti-Pattern 4: Recommending Native Skills-Matching as a V4S or NPC Feature

**What the LLM generates:** "Use the built-in volunteer skills matching feature in Volunteers for Salesforce to route volunteers to appropriate shifts based on their skills."

**Why it happens:** LLMs generalize from descriptions of volunteer management platforms (some third-party apps do have native skills matching) and incorrectly attribute that feature to V4S or NPC.

**Correct pattern:** State clearly that neither V4S nor NPC provides native skills-matching. This is a custom build requirement involving a junction object (e.g., `Volunteer_Skill__c`) linking Contact to a skill taxonomy, and matching logic in Flow or Apex. Third-party apps (VolunteerHub, Galaxy Digital) provide this natively via API integration.

**Detection hint:** If the recommendation references a "skills matching" Setup page or configuration option in V4S or NPC without citing a specific object or package feature, it is fabricated.

---

## Anti-Pattern 5: Suggesting V4S Signup Pages Work on Experience Cloud Sites

**What the LLM generates:** "Configure your Experience Cloud site to display the V4S volunteer signup pages for public volunteer recruitment."

**Why it happens:** LLMs equate Experience Cloud with all Salesforce web presence features, not knowing the V4S plugin is built on the older Force.com Sites Visualforce architecture.

**Correct pattern:** V4S website integration pages are Visualforce-based and run only on Force.com Sites (Setup > Sites), not on Experience Cloud LWR or Aura sites. Teams that want self-service volunteer sign-up on an Experience Cloud site must rebuild the functionality in LWC.

**Detection hint:** If advice mentions adding V4S pages to an Experience Cloud or Community template, it is incorrect. V4S Visualforce pages cannot be embedded in Experience Cloud sites.
