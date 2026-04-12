# LLM Anti-Patterns — Data Cloud Architecture

Common mistakes AI coding assistants make when generating or advising on Data Cloud Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Mapping Email to Individual DMO Instead of ContactPointEmail DMO

**What the LLM generates:** A data stream field mapping that routes `Contact.Email` to `Individual.email` — treating the `Individual` DMO as a flat record that holds all person attributes including contact point data.

**Why it happens:** LLMs trained on general CRM data modeling patterns assume a "person record" holds all person attributes. The Data Cloud canonical model separates the person entity (`Individual`) from its contact points (`ContactPointEmail`, `ContactPointPhone`) as distinct related DMOs. This separation is non-obvious and not analogous to any standard CRM object model.

**Correct pattern:**

```
WRONG:
  Individual.email ← Contact.Email

CORRECT:
  ContactPointEmail.emailAddress ← Contact.Email
  ContactPointEmail.partyId ← Contact.Id  (link back to Individual)
```

**Detection hint:** Search the proposed field mapping for `Individual.email`, `Individual.phone`, or any email/phone field mapped to the `Individual` DMO. Any such mapping is incorrect and will prevent identity resolution participation.

---

## Anti-Pattern 2: Treating Calculated Insights as Real-Time Attributes

**What the LLM generates:** A segment configuration that uses a Calculated Insight attribute (e.g., `totalPurchaseValue30Days`) in a real-time or near-real-time activation use case, with the implicit assumption that the CI reflects current data at the moment of segment evaluation.

**Why it happens:** LLMs conflate "computed attribute" with "real-time computed attribute." In many data platforms, computed columns or materialized views refresh continuously. In Data Cloud, Calculated Insights run on a configurable batch schedule — they are closer to a scheduled SQL job than a live computed column.

**Correct pattern:**

```
For time-sensitive activation (< 1 hour freshness required):
  Use Streaming Insights derived from real-time event ingestion.
  
For historical aggregate metrics (day-old freshness acceptable):
  Use Calculated Insights with the batch schedule configured appropriately.

In segment documentation, always note:
  Segment filter: [CI attribute] — effective data age: [CI refresh interval]
```

**Detection hint:** Check any segment using a CI-based filter against a time-sensitive activation use case description. If the use case mentions "real-time," "in-session," "within the last hour," or similar, and the filter uses a CI, flag it.

---

## Anti-Pattern 3: Assuming Activation Target Authentication Is Automatic After Connection Creation

**What the LLM generates:** Architecture documentation or a go-live checklist that says "create the Activation Target in Data Cloud Setup" without including a step to complete and verify authentication before the first segment publish.

**Why it happens:** LLMs describe configuration steps at the level of "create the object" without modeling the multi-step OAuth or credential validation flow that must be completed after creation. The target appears in the UI immediately after creation, but it is not usable until the authentication handshake is completed.

**Correct pattern:**

```
Activation Target Setup Checklist:
  1. Create Activation Target in Data Cloud Setup
  2. Complete authentication:
     - File-based (SFTP/S3/GCS): enter credentials, click "Test Connection," verify green status
     - Ad platforms: complete OAuth flow, verify "Connected" status and token expiry date
     - Salesforce platforms (MC, CRM): complete connected app authorization
  3. Perform a test activation with a small segment (< 100 records) before go-live
  4. Record token expiry dates; schedule re-authentication before expiry
```

**Detection hint:** If any go-live or activation checklist omits "verify connection status" and "test with small segment" steps, flag it as incomplete.

---

## Anti-Pattern 4: Recommending a Single Global Identity Resolution Ruleset for Multi-BU or Multi-Brand Deployments

**What the LLM generates:** A single identity resolution ruleset designed to cover all data sources across multiple business units or brands, with a shared match rule configuration and shared Unified Individual output.

**Why it happens:** LLMs default to "one unified profile" as an architectural goal without modeling the operational and privacy implications of merging identities across organizational boundaries. In multi-BU or multi-brand deployments, there are often legal, privacy, or business reasons why a customer in Brand A and the same person in Brand B should not be automatically merged into a single profile accessible to both brands.

**Correct pattern:**

```
Multi-BU identity resolution design:
  - Define identity resolution rulesets at the org level with explicit source inclusion per BU
  - Evaluate whether cross-BU identity resolution is legally permissible (GDPR, CCPA consent)
  - If cross-BU resolution is required: define a shared "global" ruleset with explicit consent governance
  - If BU isolation is required: define per-BU rulesets that only include that BU's data sources
  - Document the decision and obtain legal/privacy sign-off before configuring cross-BU rules
```

**Detection hint:** Any architecture that automatically merges data from sources belonging to different business units, brands, or legal entities without a documented privacy/consent review should be flagged.

---

## Anti-Pattern 5: Proposing Fuzzy Name Matching as the Primary Identity Resolution Rule

**What the LLM generates:** An identity resolution ruleset that uses fuzzy first name + last name matching as the primary match rule, arguing that this is "more inclusive" and handles name variations.

**Why it happens:** LLMs overweight the "missing data" problem (some records have no email) and recommend fuzzy name matching to catch those cases. They underweight the false merge problem — common names create massive incorrect clusters that are impossible to resolve after the fact.

**Correct pattern:**

```
WRONG:
  Rule 1 (primary): Fuzzy match on Individual.firstName + Individual.lastName

CORRECT:
  Rule 1 (primary): Exact match on ContactPointEmail.emailAddress
  Rule 2 (secondary): Exact match on PartyIdentification.partyIdentificationNumber
                      where partyIdentificationType = [specific ID type]
  Rule 3 (tertiary, optional): Normalized match on ContactPointPhone.telephoneNumber
  
  Only add name-based matching as a last resort with compound conditions:
  Rule 4 (low-confidence): firstName + lastName + postalCode (compound exact)
                           AND only for sources with verified data quality
```

**Detection hint:** If the primary match rule is name-based (first name, last name, or full name) rather than a unique identifier (email, phone, loyalty ID), flag it as high-risk for false merges. Run a cluster size distribution check before approving.

---

## Anti-Pattern 6: Ignoring the DMO Mapping Requirement for PartyIdentification When Using Proprietary IDs

**What the LLM generates:** A data stream mapping that ingests a loyalty member number or Shopify customer ID as a custom field on the `Individual` DMO rather than mapping it to the `PartyIdentification` DMO with the correct `partyIdentificationType`.

**Why it happens:** LLMs treat proprietary IDs as "just another field" on the person record, not as a structured identity link entity. The `PartyIdentification` DMO has a specific structure: `partyIdentificationNumber` (the ID value) and `partyIdentificationType` (a string identifying which system the ID comes from). Both fields must be populated for the ID to be usable as a match key in identity resolution.

**Correct pattern:**

```
WRONG:
  Individual.loyaltyMemberNumber ← member.loyalty_id

CORRECT:
  PartyIdentification.partyIdentificationNumber ← member.loyalty_id
  PartyIdentification.partyIdentificationType  ← "LoyaltyMemberNumber"  (literal constant)
  PartyIdentification.partyId                  ← member.contact_id  (link to Individual)
  
  Then configure an identity resolution match rule:
    Exact match on PartyIdentification.partyIdentificationNumber
    WHERE partyIdentificationType = 'LoyaltyMemberNumber'
```

**Detection hint:** Search proposed field mappings for proprietary ID fields (loyalty IDs, system-specific customer IDs, member numbers) mapped to `Individual` DMO fields. Any such mapping bypasses identity resolution participation via that identifier.
