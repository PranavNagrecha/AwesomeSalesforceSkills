# LLM Anti-Patterns — Compliant Data Sharing Setup

Common mistakes AI coding assistants make when generating or advising on Compliant Data Sharing Setup. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating CDS as an Extension of Role Hierarchy Sharing

**What the LLM generates:** "Enable CDS to enhance your role hierarchy sharing. Managers will still inherit their subordinates' records, but CDS adds an additional layer of participant-based control on top."

**Why it happens:** LLMs trained on general Salesforce content learn that most sharing features extend the role hierarchy. CDS is the exception — it replaces hierarchy-based inheritance for its managed objects rather than supplementing it. The nuance is underrepresented in general Salesforce documentation relative to standard sharing content.

**Correct pattern:**

```
CDS disables role-hierarchy-based sharing on supported objects entirely.
Managers do NOT automatically see subordinate records.
Access requires explicit Participant Role assignments.
CDS is a parallel mechanism — it is NOT an extension of the role hierarchy.
```

**Detection hint:** If the output contains phrases like "in addition to role hierarchy" or "while keeping manager visibility", the output is incorrect about CDS behavior.

---

## Anti-Pattern 2: Recommending Public Read/Write OWD Alongside CDS

**What the LLM generates:** "You can enable Compliant Data Sharing with any OWD setting. If you want broad base access with targeted ethical walls, set OWD to Public Read/Write and use CDS to restrict sensitive records."

**Why it happens:** LLMs understand that some features work across OWD settings and over-generalize. CDS specifically requires Private or Public Read-Only OWD. With Public Read/Write, the CDS engine accepts participant record inserts but writes no share rows because universal access already exists — there is nothing to extend.

**Correct pattern:**

```
OWD must be Private or Public Read-Only for CDS to function.
Public Read/Write OWD causes CDS participant assignments to silently 
produce no share rows. No error is thrown, but no access is granted.
Always set OWD before enabling CDS.
```

**Detection hint:** If the output recommends Public Read/Write OWD alongside CDS, or does not mention OWD as a prerequisite, it is incorrect.

---

## Anti-Pattern 3: Skipping the Deal Management Prerequisite for Financial Deal CDS

**What the LLM generates:** "To enable CDS for Financial Deal, set `enableCompliantDataSharingForFinancialDeal = true` in IndustriesSettings and add the Financial Deal Participants related list to your page layout."

**Why it happens:** The LLM knows the IndustriesSettings flag and related list are required but does not know that Deal Management is a separate, independent feature that must be enabled first. This prerequisite is easy to miss because it is documented in a different section of the Salesforce Help than the CDS content.

**Correct pattern:**

```
Financial Deal CDS setup order:
1. Enable Deal Management: Setup > Financial Services > Financial Deal Settings
2. Enable CDS for Financial Deal: IndustriesSettings flag
3. Add Financial Deal Participants related list to page layouts

Without step 1, step 2 has no effect and step 3 is unavailable.
```

**Detection hint:** If the output for Financial Deal CDS setup does not mention Deal Management enablement as a step, it is incomplete.

---

## Anti-Pattern 4: Conflating CDS with Standard Sharing Rules

**What the LLM generates:** "Compliant Data Sharing works by creating sharing rules that restrict access between business lines. You can configure these rules in Setup > Sharing Settings under Sharing Rules."

**Why it happens:** LLMs associate the phrase "data sharing" with Salesforce sharing rules, which are the most commonly documented sharing mechanism. CDS is not a type of sharing rule — it is an entirely separate mechanism implemented via participant objects and managed by the CDS engine.

**Correct pattern:**

```
CDS is NOT a sharing rule mechanism.
CDS is enabled via IndustriesSettings metadata flags, not in Sharing Rules.
CDS grants access via Participant Role assignments on individual records.
Standard sharing rules and CDS run simultaneously and independently.
Existing sharing rules must be audited separately when enabling CDS.
```

**Detection hint:** If the output directs the user to Setup > Sharing Settings > Sharing Rules to configure CDS, it is wrong about the mechanism.

---

## Anti-Pattern 5: Not Deleting Participant Role Assignments Before Disabling CDS

**What the LLM generates:** "To disable CDS, go to IndustriesSettings and set the flag to false, then submit a Salesforce Support ticket."

**Why it happens:** The disabling step is a two-phase process (delete participant records first, then deactivate the flag), and the participant deletion prerequisite is easy to miss because it is documented in the Considerations and Limitations article rather than the main CDS setup article.

**Correct pattern:**

```
CDS deactivation sequence:
1. Delete ALL AccountParticipant (or object-equivalent) records 
   for the target object using Data Loader or Apex batch.
   Example query: SELECT Id FROM AccountParticipant (delete all)
2. Verify zero participant records remain.
3. Contact Salesforce Support to deactivate the CDS flag for the object.

Attempting deactivation with active participant records results in an 
error and Salesforce Support will not proceed until cleanup is complete.
```

**Detection hint:** If the output describes CDS deactivation without a participant record cleanup step, it is missing a required prerequisite. Look for the absence of any mention of `AccountParticipant` deletion or bulk data cleanup before deactivation.

---

## Anti-Pattern 6: Missing the CDS User Permission Assignment for Business Users

**What the LLM generates:** "Assign the CDS Manager permission set to your administrators and the setup is complete. Business users will be automatically eligible to be added as participants."

**Why it happens:** The two-permission model (CDS Manager for admins + CDS User for business users) is a detail that LLMs frequently collapse to a single permission. The CDS Manager permission for admins is more prominent in setup documentation, causing the CDS User permission for end users to be omitted.

**Correct pattern:**

```
Two distinct permission sets are required:
- CDS Manager (Configure CDS): assign to administrators who manage CDS setup
- CDS User (Use CDS): assign to EVERY business user who will be 
  assigned as a participant on any record

Without "Use CDS", a user cannot be added as a participant even by 
an admin. The assignment attempt silently fails or produces an error.
```

**Detection hint:** If the output mentions only one CDS permission set, or does not distinguish between admin and end-user CDS permissions, it is incomplete.
