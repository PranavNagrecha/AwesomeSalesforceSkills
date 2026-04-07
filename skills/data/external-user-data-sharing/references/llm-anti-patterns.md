# LLM Anti-Patterns — External User Data Sharing

Common mistakes AI coding assistants make when generating or advising on External User Data Sharing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Criteria-Based Sharing Rules for Customer Community (HVP) Users

**What the LLM generates:** When asked how to give High-Volume Portal (Customer Community) users access to Cases, the LLM generates a criteria-based sharing rule configuration: "Create a sharing rule on Case, based on criteria, and share with Customer Portal Users."

**Why it happens:** LLMs conflate all external user types into a single "portal users" category. Criteria-based sharing rules work for CC Plus and Partner Community and are a common result in training data. The HVP exception is a Salesforce-specific carve-out not present in general sharing model documentation.

**Correct pattern:**

```
Customer Community (HVP) users require a Sharing Set.
Setup > Digital Experiences > Settings > Sharing Sets
- Select HVP profile
- Add object (e.g., Case)
- Set relationship path: User.AccountId → Case.AccountId
- Set access level: Read/Write
Criteria-based sharing rules do NOT fire for HVP users.
```

**Detection hint:** Any response that configures a sharing rule targeting a Customer Community (not Community Plus) profile without also configuring a Sharing Set.

---

## Anti-Pattern 2: Treating External OWD as Identical to Internal OWD

**What the LLM generates:** "Set the OWD on Case to Private to restrict portal users from seeing Cases." Or: "Change the Case OWD to Public Read Only so portal users can see all cases."

**Why it happens:** LLMs frequently omit the distinction between internal OWD and External OWD. Many training examples reference OWD without specifying the external column. The LLM assumes a single OWD controls both internal and external access.

**Correct pattern:**

```
Internal OWD and External OWD are separate settings on the same object.
Setup > Security > Sharing Settings
- "Default Internal Access" column controls internal users
- "Default External Access" column controls external/portal users
Changing internal OWD does NOT change external OWD (it cannot be set more
permissive than internal OWD, but the two are managed independently).
Always set External OWD explicitly — do not assume it mirrors internal OWD.
```

**Detection hint:** Any response that says "set the OWD to X to control portal user access" without referencing the External OWD column specifically.

---

## Anti-Pattern 3: Confusing Sharing Sets with Sharing Rules

**What the LLM generates:** "Add a sharing rule to the Sharing Set for this object." Or: "Sharing Sets and sharing rules are the same mechanism, just configured in different places."

**Why it happens:** Both "Sharing Set" and "sharing rule" contain the word "sharing." LLMs frequently treat them as synonyms or variants of the same feature.

**Correct pattern:**

```
Sharing Sets and sharing rules are distinct mechanisms:
- Sharing Sets: HVP-only, relationship-based, configured in Digital Experiences > Settings > Sharing Sets
- Sharing Rules: apply to internal + CC Plus + Partner Community users, can be criteria- or owner-based,
  configured in Security > Sharing Settings > [Object] Sharing Rules
Sharing Sets do not "contain" sharing rules. They are separate configuration areas.
A single Sharing Set can reference multiple objects and relationship paths.
A sharing rule is a standalone record in the sharing settings area.
```

**Detection hint:** Any response that references "adding a sharing rule inside a Sharing Set" or treats them as the same configuration.

---

## Anti-Pattern 4: Omitting the External OWD Review When Configuring Sharing

**What the LLM generates:** A complete Sharing Set or sharing rule configuration with no mention of External OWD. The assumption is that External OWD is already correct, so only the sharing grant needs to be configured.

**Why it happens:** LLMs focus on the explicit action requested (configure a Sharing Set) and skip the prerequisite state audit. External OWD is the baseline that determines what a sharing grant is opening up from.

**Correct pattern:**

```
Before configuring any sharing mechanism for external users:
1. Check current External OWD: Setup > Security > Sharing Settings > [Object] > Default External Access
2. If External OWD is Public Read Only or Public Read/Write, all external users already have that access —
   a Sharing Set or sharing rule adds nothing meaningful for read access.
3. Set External OWD to Private to establish a deny-by-default baseline.
4. Then grant access selectively via Sharing Set (HVP) or sharing rule (CC Plus / Partner).
Skipping the External OWD check risks either over-sharing (OWD is too permissive) or
misconfiguring against an unexpected baseline.
```

**Detection hint:** Any sharing configuration response that does not include a step to review or confirm the External OWD setting.

---

## Anti-Pattern 5: Recommending Sharing Sets for Customer Community Plus or Partner Community Users

**What the LLM generates:** When asked how to share records with Partner Community users, the LLM recommends creating a Sharing Set: "Go to Sharing Sets and add the Partner Community profile to grant access to Opportunity records."

**Why it happens:** Sharing Sets appear to support any portal profile in the UI. The HVP-only restriction is enforced at runtime, not enforced with an explicit UI error. LLMs trained on UI descriptions do not capture this runtime-only restriction.

**Correct pattern:**

```
Sharing Sets apply ONLY to High-Volume Portal (Customer Community / HVP) users.
- Customer Community Plus: use criteria-based sharing rules or manual sharing
- Partner Community: use criteria-based sharing rules, role hierarchy, or manual sharing
For Partner Community Opportunity access:
Setup > Security > Sharing Settings > Opportunity Sharing Rules > New
  Rule type: Based on criteria or Based on record owner
  Share with: Partner Community users (role or role and subordinates)
  Access level: Read Only or Read/Write
```

**Detection hint:** Any response that configures a Sharing Set targeting a Partner Community or Customer Community Plus profile.

---

## Anti-Pattern 6: Assuming Portal Users Inherit Internal User Record Visibility

**What the LLM generates:** "Since the Account OWD is Public Read Only, portal users associated with that account can see all records owned by internal users in that account."

**Why it happens:** LLMs apply general OWD logic (Public Read Only = all users can see all records) without accounting for the external OWD distinction or the portal account boundary.

**Correct pattern:**

```
External users have a separate External OWD that controls what they see.
Even if internal OWD is Public Read Only, External OWD may be Private —
meaning external users see only records explicitly shared with them.
Additionally, portal users are scoped to their Account by default.
Records owned by internal users are not automatically visible to portal users
unless the External OWD grants public access OR a Sharing Set / sharing rule
explicitly grants the portal user access to those specific records.
```

**Detection hint:** Any response that equates internal OWD Public Read Only access with portal user visibility without separately confirming External OWD.
