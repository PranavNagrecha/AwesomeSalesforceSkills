# LLM Anti-Patterns — Experience Cloud Licensing Model

Common mistakes AI coding assistants make when generating or advising on Experience Cloud license selection.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Defaulting to Customer Community for All External Portals

**What the LLM generates:** "For your Experience Cloud portal, use the Customer Community license — it's the standard license for external users and covers most use cases."

**Why it happens:** Customer Community is the most frequently mentioned Experience Cloud license in training data, so it becomes the default recommendation regardless of the stated requirements. LLMs conflate "most common" with "most appropriate."

**Correct pattern:**

```
Run the license selection decision framework:
1. Check CRM object requirements — Leads/Opportunities/Contracts → Partner Community minimum.
2. Check sharing model complexity — criteria-based sharing rules → Customer Community Plus minimum.
3. Check report/dashboard requirements → any report access → Customer Community Plus minimum.
4. Only recommend Customer Community if all three gates pass.
```

**Detection hint:** Any response that recommends Customer Community without explicitly clearing the CRM object and sharing model gates should be reviewed.

---

## Anti-Pattern 2: Missing the Reports/Dashboards Constraint on Customer Community

**What the LLM generates:** "You can configure reports and dashboards for your Customer Community portal by adjusting profile permissions or adding a Reports tab to the Experience Builder navigation."

**Why it happens:** LLMs know that Salesforce reports are controlled by permissions and that tabs can be added to communities. They incorrectly infer that the same mechanism applies to Customer Community users, missing that the constraint is at the license level, not the permission level.

**Correct pattern:**

```
Customer Community license: reports and dashboards are NOT supported.
This is a hard platform constraint, not a permission setting.
No profile configuration, permission set, or Experience Builder tab will enable
native Salesforce report/dashboard viewing for a Customer Community user.
Minimum tier for report access: Customer Community Plus.
```

**Detection hint:** Any guidance suggesting reports or dashboards can be "enabled" for Customer Community users via permissions, tabs, or components is incorrect. Flag responses containing "add Reports tab" + "Customer Community" together.

---

## Anti-Pattern 3: Not Modeling Login vs Member Economics Before Recommending

**What the LLM generates:** "Use member-based licensing — it's simpler and you'll have predictable costs."

**Why it happens:** Member-based licensing is conceptually simpler (fixed seats = fixed cost) and LLMs default to simplicity. The login-based economics model requires knowing user volume and activity patterns, which LLMs often skip when that context is not explicitly provided.

**Correct pattern:**

```
Before recommending member-based vs login-based:
1. Collect: total user volume, expected daily active users (DAU) as percentage.
2. Calculate login credit consumption: total_users × DAU% × 30 days.
3. Compare: login credit pool cost vs member seat cost at that volume.
4. Rule of thumb: login-based is cheaper below ~25% DAU ratio.
5. Also consider credit exhaustion risk for high-criticality portals.
```

**Detection hint:** Any license variant recommendation that does not reference user volume and activity ratio should be treated as incomplete.

---

## Anti-Pattern 4: Recommending License Tier Upgrade Mid-Project Without Flagging Profile Migration

**What the LLM generates:** "If you later need reports, you can upgrade from Customer Community to Customer Community Plus — it's just a license change."

**Why it happens:** LLMs know that Salesforce licenses can be changed and assume the change process is trivial (similar to adding a permission set). They are not aware that Experience Cloud license type is tied to user profiles, making a tier upgrade a bulk profile migration operation.

**Correct pattern:**

```
Upgrading Experience Cloud license tier mid-project requires:
1. Creating a new profile for the target license type (e.g., Customer Community Plus profile).
2. Migrating all affected users to the new profile.
3. Auditing and re-applying all profile-level permissions on the new profile.
4. Testing all portal functionality under the new profile for all user scenarios.

For large user populations (thousands of users), this is a significant data operation.
Always evaluate the probability of tier upgrade in the roadmap BEFORE committing
to the initial tier — starting one tier higher may be cheaper than migrating later.
```

**Detection hint:** Phrases like "just upgrade the license later" or "you can switch license types if needed" without mentioning profile migration indicate this anti-pattern.

---

## Anti-Pattern 5: Assuming Partner Community Is Required for Any B2B Portal

**What the LLM generates:** "Since this is a B2B portal for your business customers, use Partner Community — that's the license designed for B2B use cases."

**Why it happens:** "B2B" and "Partner Community" are frequently co-located in training data. LLMs over-generalize the association and recommend Partner Community for any portal that has business (rather than consumer) users, even when the portal only needs cases, knowledge, and basic account data — requirements that Customer Community Plus can satisfy at lower cost.

**Correct pattern:**

```
"B2B audience" does not automatically mean "Partner Community."
Partner Community is required ONLY when:
- External users need access to Leads, Opportunities, or Contracts, OR
- The portal requires a per-account three-tier role hierarchy for visibility.

A B2B portal where business customers submit support cases, view invoices on
custom objects, and read knowledge articles is well-served by Customer Community
or Customer Community Plus depending on reporting and sharing requirements.
```

**Detection hint:** Any recommendation of Partner Community that does not explicitly cite a Leads/Opportunities/Contracts requirement or a per-account role hierarchy requirement should be reviewed.

---

## Anti-Pattern 6: Conflating Experience Cloud Licensing with Internal Salesforce User Licensing

**What the LLM generates:** "Use the Salesforce Platform license for your portal users — it's more cost-effective than full Salesforce licenses for users who only need a few objects."

**Why it happens:** LLMs know that Salesforce Platform is a reduced-cost internal user license and assume it applies to external portal users. They conflate internal license optimization with Experience Cloud external user licensing.

**Correct pattern:**

```
Experience Cloud external users (portal/community users) use a distinct license
family: Customer Community, Customer Community Plus, Partner Community, External Apps.
Internal Salesforce user licenses (Salesforce, Salesforce Platform, Identity) are
for employees and integration users — they are NOT valid license types for
Experience Cloud external (unauthenticated or low-cost portal) users.
This skill covers external Experience Cloud licensing only.
```

**Detection hint:** Any response recommending Salesforce Platform, Identity, or Salesforce (full CRM) license for portal/community users is incorrect for the external user licensing context.
