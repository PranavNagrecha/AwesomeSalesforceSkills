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

## Anti-Pattern 6: Assuming the Enterprise All Subscribers List Provides Automatic Cross-BU Suppression

**What the LLM generates:** Advice that an opt-out recorded in any Child BU is automatically suppressed across all other Child BUs via the Enterprise All Subscribers list, requiring no additional configuration.

**Why it happens:** The Enterprise All Subscribers list is described in documentation as tracking subscriber status "across the org," which LLMs interpret as implying automatic cross-BU suppression enforcement at send time.

**Correct pattern:**
```
The Enterprise All Subscribers list records subscriber status but does NOT
automatically suppress sends from sibling Child BUs at send time.
To enforce global suppression:
1. Create a Shared DE in the Parent BU to hold global opt-outs
2. Configure read access for all sending Child BUs via folder-level permissions
3. Reference the Shared DE as a suppression list in every Child BU's send activities
Test suppression behavior per Child BU before go-live.
```

**Detection hint:** Phrases like "automatically suppressed enterprise-wide", "all BUs respect the opt-out by default", or "the Enterprise list handles it" without mention of Shared DE configuration.
