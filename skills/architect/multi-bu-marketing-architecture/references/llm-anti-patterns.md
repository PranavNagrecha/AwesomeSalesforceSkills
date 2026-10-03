# LLM Anti-Patterns — Multi-BU Marketing Architecture

Common mistakes AI coding assistants make when generating or advising on Multi-BU Marketing Architecture. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Role Assignments Cascade from Parent BU to Child BUs

**What the LLM generates:** Advice like "once you provision the admin in the Parent BU they will automatically have access to all Child BUs" or configuration steps that only include provisioning users in the Parent BU and assume child access follows.

**Why it happens:** LLMs trained on general IAM concepts expect role inheritance to be a default behavior (as it is in many platforms, including Salesforce CRM permission sets with group hierarchies). Marketing Cloud's per-BU provisioning model is a documented exception that is underrepresented in general training data.

**Correct pattern:**
```
Each Business Unit maintains its own independent user roster.
A user must be explicitly provisioned in each BU they need to access,
and a role must be assigned at each BU level independently.
There is no "inherit from parent" toggle in Marketing Cloud Engagement.
```

**Detection hint:** Look for phrases like "automatically have access", "inherits permissions", or "cascades to child BUs" in any user provisioning guidance.

---

## Anti-Pattern 2: Recommending Deeply Nested BU Hierarchies to Mirror Org Charts

**What the LLM generates:** A hierarchy design with three or more tiers — e.g., Parent → Continent Child BU → Country Grandchild BU → Brand Great-Grandchild BU — justified by "matching your organizational structure for easier management."

**Why it happens:** LLMs generalize from organizational hierarchy design principles (e.g., Active Directory OU structures, SharePoint site hierarchies) where deep nesting is common and reporting often rolls up automatically. Marketing Cloud's reporting layer does not perform automatic rollups across hierarchy tiers.

**Correct pattern:**
```
Keep BU hierarchies flat: one Parent BU and one tier of Child BUs.
If regional grouping is needed, use naming conventions (e.g., "EMEA-Germany-ConsumerBrand")
rather than structural nesting.
A second tier of Child BUs is appropriate only when there is a documented,
unavoidable operational requirement — not to reflect the org chart.
```

**Detection hint:** Any hierarchy diagram or recommendation showing three or more levels of BU nesting warrants scrutiny.

---

## Anti-Pattern 3: Claiming Data Extensions Are Automatically Shared Across Child BUs When Created in the Parent BU

**What the LLM generates:** Instructions like "create the suppression list in the Parent BU and all Child BUs will be able to use it" or "shared DEs are available to all BUs in your Enterprise account by default."

**Why it happens:** The term "Enterprise" account implies to LLMs that enterprise-wide resources are automatically enterprise-wide in scope. In reality, the sharing mechanism requires explicit folder-level permission configuration per Child BU.

**Correct pattern:**
```
Creating a Data Extension in the Parent BU does NOT make it visible to Child BUs.
Cross-BU access requires:
1. Placing the DE in a designated folder in the Parent BU
2. Configuring Shared Data Extension Permissions on that folder
3. Explicitly selecting which Child BUs receive Read or Read/Write access
Verify by logging into a Child BU and confirming the DE appears under the "Shared" folder.
```

**Detection hint:** Look for phrases like "automatically available", "shared by default", or "Enterprise-wide access" applied to Data Extensions.

---

## Anti-Pattern 4: Treating Marketing Cloud Account Engagement (Pardot) BUs as Equivalent to MC Engagement BUs

**What the LLM generates:** Architecture advice that conflates Marketing Cloud Account Engagement's Business Unit concept with Marketing Cloud Engagement's Business Unit concept — e.g., recommending Shared DE configurations for a Pardot multi-BU setup, or describing Pardot user provisioning in terms of MC Engagement's BU model.

**Why it happens:** Both products use the term "Business Unit" and both are branded under the Marketing Cloud umbrella. LLMs frequently merge their documentation in training. The two products have distinct architectures, user models, data models, and sharing mechanisms.

**Correct pattern:**
```
Marketing Cloud Engagement (Email Studio, Journey Builder, etc.) and
Marketing Cloud Account Engagement (Pardot) are separate products with
separate BU models. Shared Data Extensions, BU-scoped provisioning,
and Enterprise 2.0 hierarchy apply to MC Engagement only.
This skill covers MC Engagement multi-BU architecture exclusively.
Pardot BU setup is a separate concern.
```

**Detection hint:** If advice for an MC Engagement multi-BU question mentions "Pardot connectors", "prospects", or "engagement history syncing" without explicitly noting a product boundary, it likely conflates the two.

---

## Anti-Pattern 5: Recommending Folder-Level Restrictions Within a Single BU as a Brand Data Segregation Strategy

**What the LLM generates:** Guidance suggesting that two brands can be safely segregated within a single Child BU by giving each brand's team access only to their own DE folders via Marketing Cloud's folder-level role restrictions.

**Why it happens:** LLMs generalize from file-system ACL or SharePoint folder permission models where folder-level restrictions are reliable security boundaries. In Marketing Cloud, folder-level restrictions are not consistently enforced across all tools and are not a substitute for BU-level isolation.

**Correct pattern:**
```
Do not use folder-level restrictions within a single BU as the primary
data segregation mechanism between brands.
Marketing Cloud Administrator roles and some API access paths bypass
folder restrictions.
For genuine brand data segregation, use separate Child BUs.
BU-level scoping is the platform-enforced boundary.
Folder restrictions within a BU are organizational aids, not security controls.
```

**Detection hint:** Look for advice that proposes keeping multiple brands in a single BU and managing separation through "folder permissions", "user role restrictions", or "profile-based access."

---

## Anti-Pattern 6: Answering "Is An Opt-Out Global?" Without Checking `MasterUnsubscribeBehavior`

**What the LLM generates:** Either "an opt-out in any Child BU is automatically suppressed across all BUs" or, the reverse, "an opt-out never crosses BUs unless you build a shared suppression data extension". Both skip the setting that decides it.

**Why it happens:** Training material describes the Enterprise All Subscribers list loosely. The API documents a per-BU property, `BusinessUnit.MasterUnsubscribeBehavior`, with values `ENTIRE_ENTERPRISE` and `BUSINESS_UNIT_ONLY`, which "defines how master unsubscription requests are handled for a business unit."

**Correct pattern:**
```
1. Retrieve MasterUnsubscribeBehavior for every BU (audit script in examples.md).
2. Agree the intended scope per brand with legal.
3. Set ENTIRE_ENTERPRISE where a master unsubscribe must stop all sends;
   BUSINESS_UNIT_ONLY where brands are legally separate.
4. Add a Shared DE suppression list only for rules the setting cannot express
   (imported suppressions, brand-level lists), shared to each sending BU.
5. Test with a send from every Child BU before go-live.
```

**Detection hint:** Any statement about cross-BU opt-out behavior that never names `MasterUnsubscribeBehavior` or the BU-level unsubscribe setting.

---

## Anti-Pattern 7: Using One API Token Across Business Units

**What the LLM generates:** Integration code that requests a token once from the Parent BU and reuses it for calls meant for several Child BUs, or a design that assumes a Parent BU token "covers children".

**Why it happens:** Most OAuth integrations elsewhere use one token per tenant. In Marketing Cloud Engagement, "Access tokens and refresh tokens act in the context of a single business unit", and a SOAP access token "doesn't flow down through child accounts."

**Correct pattern:** Request a token per target BU with `account_id` set to that BU's MID, enable the server-to-server integration for each BU on the Installed Packages Access tab, cache each token for its 20-minute life, and handle 401 and 403 for BUs the integration cannot reach.

**Detection hint:** A `v2/token` request with no `account_id` in code that writes to more than one BU.
