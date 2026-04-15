# LLM Anti-Patterns — Data Cloud Provisioning

Common mistakes AI coding assistants make when generating or advising on Data Cloud Provisioning. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Data Cloud with CRM Analytics Setup

**What the LLM generates:** Instructions that mix Data Cloud provisioning steps with CRM Analytics (Tableau CRM) setup — for example, advising users to enable "Einstein Analytics" or configure "dataflow schedules" as part of Data Cloud setup, or treating the CRM Analytics license as a prerequisite for Data Cloud.

**Why it happens:** LLMs trained on older Salesforce content conflate "Salesforce Analytics Cloud," "Einstein Analytics," "Tableau CRM," and "Data Cloud" because these product names were used interchangeably in different eras of Salesforce marketing and documentation. The training corpus contains many articles where these terms appear near each other.

**Correct pattern:**

```
Data Cloud (Data 360) and CRM Analytics are distinct products with separate:
  - Enablement paths (Data Cloud: Setup > Data Cloud; CRM Analytics: Setup > Analytics Studio)
  - License models
  - Permission sets
  - Administrative consoles

Do NOT advise enabling CRM Analytics as part of Data Cloud provisioning.
Do NOT reference SAQL, dataflow schedules, or Analytics Studio in Data Cloud setup steps.
```

**Detection hint:** Look for mentions of "Einstein Analytics," "Tableau CRM," "Analytics Studio," "dataflow," or "SAQL" in a response to a Data Cloud provisioning question. Any of these terms in a provisioning context is likely a conflation error.

---

## Anti-Pattern 2: Stating the Org Model Can Be Changed Post-Provisioning

**What the LLM generates:** Advice implying the org model (Dedicated Home Org vs. existing org) is a configuration setting that can be changed after enablement, or suggesting a "migration" option exists within Salesforce Setup.

**Why it happens:** LLMs generalize from other Salesforce features where configuration choices are reversible (e.g., turning features on/off in Setup). The permanent, contract-level nature of the Data Cloud org model decision is a domain-specific constraint not well-represented in generic Salesforce training data.

**Correct pattern:**

```
The org model decision is PERMANENT and made at provisioning time.
There is NO migration path from existing-org to Dedicated Home Org.
Moving to Dedicated Home Org after existing-org provisioning requires:
  - Provisioning a new tenant from scratch
  - Rebuilding all data streams, mappings, segments, and activation targets
  - Re-establishing all user access

This must be documented as an architectural decision with stakeholder sign-off BEFORE enabling Data 360.
```

**Detection hint:** Watch for phrases like "you can change this later," "migrate to Dedicated Home Org," or "switch org model in Setup." All indicate the LLM has generated an incorrect claim.

---

## Anti-Pattern 3: Recommending Data Cloud Admin as the Universal Permission Set

**What the LLM generates:** Instructions to assign "Data Cloud Admin" to all Data Cloud users, or to marketing administrators who need to create Activation Targets, on the grounds that it is "the most permissive" set.

**Why it happens:** LLMs apply a pattern from standard Salesforce administration where the "System Administrator" profile or the "highest" permission set grants access to everything. In Data Cloud, the permission set model does not follow this convention — the capability split between administrative and marketing-operational features is intentional and design-documented.

**Correct pattern:**

```
Permission set → Activation Target creation capability:
  Data Cloud Admin                    → NO
  Data Cloud Marketing Admin          → YES
  Data Cloud User                     → NO
  Data Cloud Data Aware Specialist    → NO
  Data Cloud Marketing Manager        → YES
  Data Cloud Marketing Specialist     → NO

For marketing operations users who need Activation Targets:
  Assign: Data Cloud Marketing Admin OR Data Cloud Marketing Manager
  NOT: Data Cloud Admin
```

**Detection hint:** Any recommendation of "Data Cloud Admin" as the correct permission set for a user who needs to create Activation Targets is incorrect. Also flag advice to assign Data Cloud Admin to all users as a default.

---

## Anti-Pattern 4: Omitting the Connected App Prerequisite for Ingestion API

**What the LLM generates:** Ingestion API setup instructions that go directly to "Data Cloud > Data Streams > New > Ingestion API" without mentioning that a Connected App with the `cdp_ingest_api` scope must be created first.

**Why it happens:** LLMs describe the surface-level UI flow in Data Cloud Setup without knowing about the prerequisite OAuth configuration step. The Connected App requirement is a separate Setup action outside the Data Cloud menu and easy to omit when generating a procedural list.

**Correct pattern:**

```
Ingestion API setup MUST follow this order:
  Step 1: Setup > App Manager > New Connected App
            - Enable OAuth Settings
            - Add scope: cdp_ingest_api
            - Save and note Consumer Key / Consumer Secret

  Step 2: Data Cloud > Data Streams > New > Ingestion API
            - Use the Connected App credentials from Step 1 to authenticate
            - Source registration will fail if Step 1 is not complete

Do NOT describe Step 2 without Step 1.
```

**Detection hint:** Any Ingestion API setup instructions that do not mention "Connected App" or `cdp_ingest_api` as a prerequisite are incomplete.

---

## Anti-Pattern 5: Treating Data Space Membership as Automatic After Permission Set Assignment

**What the LLM generates:** User access setup instructions that stop at "assign the Data Cloud User permission set" without mentioning that users must also be explicitly added to each data space they need access to.

**Why it happens:** LLMs model Salesforce access control as a two-tier system (profile + permission sets). Data space membership is a third tier specific to Data Cloud that does not exist in standard Salesforce objects and is rarely mentioned in generic Salesforce training content.

**Correct pattern:**

```
Data Cloud user access requires TWO separate assignments:
  1. Permission set assignment (Setup > Users > Permission Set Assignments)
     → Grants platform-level Data Cloud access

  2. Data space membership (Data Cloud > Data Spaces > [name] > Manage Assignments)
     → Grants access to the specific data space's streams, segments, and objects

A user with only Step 1 will see an empty Data Cloud environment.
Both steps are required for the user to see and work with data.
```

**Detection hint:** Access setup instructions that only reference permission set assignment without mentioning data space membership are incomplete. Flag any response that does not include the data space assignment step as a required follow-up.

---

## Anti-Pattern 6: Suggesting Non-Standard (Custom) Permission Sets for Data Cloud Access

**What the LLM generates:** Instructions to create a custom permission set by cloning one of the standard Data Cloud sets and modifying it to combine capabilities (e.g., "clone Data Cloud Admin and add activation target creation").

**Why it happens:** Custom permission sets are a common pattern throughout Salesforce administration. LLMs apply this pattern without knowing that Salesforce-managed Data Cloud permission sets are designed to receive automatic capability updates with each platform release, and that cloning transfers maintenance responsibility to the org admin.

**Correct pattern:**

```
Use only the six Salesforce-managed standard Data Cloud permission sets:
  - Data Cloud Admin
  - Data Cloud Marketing Admin
  - Data Cloud User
  - Data Cloud Data Aware Specialist
  - Data Cloud Marketing Manager
  - Data Cloud Marketing Specialist

Do NOT clone and customize these sets.
If a user needs capabilities from two sets (e.g., platform admin + activation targets),
assign BOTH standard sets simultaneously — do not merge them into a custom set.
```

**Detection hint:** Any reference to "clone the Data Cloud permission set" or "create a custom Data Cloud permission set" in a provisioning response should be flagged as an anti-pattern.
