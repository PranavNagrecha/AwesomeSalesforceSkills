# LLM Anti-Patterns — B2B Commerce Store Setup

Common mistakes AI coding assistants make when generating or advising on B2B Commerce Store Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming All Contacts Under a BuyerAccount Automatically Get Storefront Access

**What the LLM generates:** Instructions that convert an Account to a BuyerAccount, add it to a BuyerGroup, and then tell the user "contacts associated with this account can now log in and transact." No mention of per-contact Buyer role assignment.

**Why it happens:** LLMs trained on general CRM or Community Cloud documentation associate "account contact relationship" with access inheritance. In standard Experience Cloud sites, contact-based membership does propagate access. B2B Commerce adds an extra layer — the explicit Buyer role assignment — that is specific to the Commerce data model and easy to omit when blending sources.

**Correct pattern:**

```text
After converting an Account to a BuyerAccount and assigning it to a BuyerGroup:

1. Navigate to BuyerAccount → Contacts (Commerce Admin) OR query BuyerAccountAccess.
2. For each contact that needs to transact, explicitly assign the Buyer role
   (or Buyer Manager if they need account management capabilities).
3. Do NOT assume account membership or Experience Cloud profile grants commerce access.
4. Verify: log in as the contact and confirm cart and checkout are accessible.
```

**Detection hint:** Look for any setup instruction that mentions BuyerAccount without a corresponding step for contact role assignment. If "Buyer role" or "Buyer Manager role" does not appear in the setup flow, the output is incomplete.

---

## Anti-Pattern 2: Treating Commerce Admin Catalog as Ground Truth for Buyer Visibility

**What the LLM generates:** After adding products to an entitlement policy, the LLM advises the user to "verify products are visible" by checking the Commerce admin product list or the entitlement policy's product records. It does not mention rebuilding the search index or validating via a buyer login.

**Why it happens:** LLMs generalize from standard Salesforce admin UIs where data is immediately consistent. Commerce search is an indexed search system — changes to entitlement data are not reflected in buyer-facing search until the index is explicitly rebuilt. The distinction between admin data and the search index is a Commerce-specific concept not present in most Salesforce admin workflows.

**Correct pattern:**

```text
After adding or removing products from a CommerceEntitlementPolicy:

1. Confirm the CommerceEntitlementProduct records are saved correctly (admin verification).
2. Navigate to Commerce Admin → Store → Search → Indexes.
3. Trigger a manual index rebuild.
4. Wait for index status to return to Active.
5. Log in as a buyer contact and search for the affected SKU(s) in the storefront.
6. Only mark the change complete after buyer-facing search returns correct results.
```

**Detection hint:** Any setup or update instruction that validates success only via admin-side record checks, without a buyer-login smoke test and an explicit search index rebuild step, is incomplete.

---

## Anti-Pattern 3: Recommending One BuyerGroup Per Customer Account for Granular Product Control

**What the LLM generates:** When asked how to give different customers different product catalogs, the LLM suggests creating one BuyerGroup per customer account and assigning each account a custom EntitlementPolicy.

**Why it happens:** The pattern of "one container per entity" is a common generalization from other access models (one profile per user type, one permission set per role). LLMs apply this pattern to BuyerGroups without awareness of the 200-groups-per-policy platform limit, which makes this approach non-scalable for any store with more than 200 customers.

**Correct pattern:**

```text
Design BuyerGroups around product entitlement TIERS, not individual accounts:

- Identify distinct product visibility segments (e.g., Distributor, Retail, OEM).
- Create one BuyerGroup per segment.
- Create one CommerceEntitlementPolicy per segment with the appropriate product set.
- Assign each BuyerAccount to the segment group that matches its entitlement tier.
- Hard limit: max 200 BuyerGroups per EntitlementPolicy — plan for growth.
```

**Detection hint:** If a proposed design results in the number of BuyerGroups equaling or approaching the number of customer accounts, flag it as a scalability anti-pattern. Ask: "How many accounts are expected at 12 months and 36 months?"

---

## Anti-Pattern 4: Omitting the WebStoreBuyerGroup Junction Record

**What the LLM generates:** Setup instructions that create a BuyerGroup, create an EntitlementPolicy, link products, and assign BuyerAccounts — but never create the `WebStoreBuyerGroup` record that links the BuyerGroup to the specific WebStore.

**Why it happens:** The `WebStoreBuyerGroup` junction is a non-obvious intermediate object. LLMs that summarize documentation may compress the access chain as "BuyerGroup → EntitlementPolicy → Products" and skip the WebStore link as implied. In reality, without this record, the BuyerGroup has no path to the storefront and buyers see an empty catalog.

**Correct pattern:**

```text
For each BuyerGroup, create a WebStoreBuyerGroup record:

  WebStoreBuyerGroup:
    WebStoreId:   <Id of the target WebStore>
    BuyerGroupId: <Id of the BuyerGroup>

Do this BEFORE assigning BuyerAccounts or testing buyer access.
Verify in SOQL: SELECT Id, WebStoreId, BuyerGroupId FROM WebStoreBuyerGroup
```

**Detection hint:** Search the generated setup steps for the string "WebStoreBuyerGroup". If it is absent, the BuyerGroup-to-store linkage step is missing.

---

## Anti-Pattern 5: Ignoring the 2,000 BuyerGroup Per-Product Search Indexing Cap

**What the LLM generates:** A multi-group Commerce architecture with a broadly available "base catalog" product set entitled across all BuyerGroups, without any mention of the 2,000-groups-per-product search indexing limit.

**Why it happens:** The 2,000-groups-per-product search indexing limit is a secondary, less-visible limit documented in the B2B Commerce Developer Guide under Entitlement Data Limits. LLMs frequently surface the more prominent 200-groups-per-policy limit but miss this related constraint. The failure mode is also unusually hard to detect (silent search exclusion with no error log), making it underrepresented in community troubleshooting discussions that LLMs are trained on.

**Correct pattern:**

```text
Before finalizing a multi-group entitlement architecture:

1. Estimate the maximum number of BuyerGroups any single product will be entitled across.
2. If that number approaches or exceeds 2,000 for any product within one WebStore:
   - Restructure using fewer, broader groups.
   - Consider whether "broadly available" products need individual group-level entitlement
     or can be made available via a catch-all group.
3. After go-live, validate buyer search results in groups that are high on the list
   (groups created last may be beyond the indexing cap for popular products).
```

**Detection hint:** If the proposed architecture includes more than ~500 BuyerGroups per store, ask how many groups any single catalog-wide product will be entitled across. If the answer is "all of them" and the total exceeds 2,000, flag the indexing cap.

---

## Anti-Pattern 6: Conflating B2B Commerce Entitlement With Standard Sharing Rules

**What the LLM generates:** When asked why a buyer cannot see a product, the LLM suggests checking OWD (org-wide defaults), sharing rules, or field-level security on `Product2`. It treats the Commerce visibility problem as a standard Salesforce record sharing problem.

**Why it happens:** LLMs default to the most common Salesforce access control framework (sharing model, profiles, permission sets) when presented with an "access denied" symptom. B2B Commerce product visibility is governed by the EntitlementPolicy data model, not by the standard Salesforce sharing model. A buyer's ability to see a product is determined entirely by the CommerceEntitlementPolicy chain, not by whether they have FLS-read on `Product2.Name`.

**Correct pattern:**

```text
For B2B Commerce product visibility issues, check in this order:
1. WebStoreBuyerGroup — is the BuyerGroup linked to the WebStore?
2. BuyerGroupMember — is the BuyerAccount in the correct group?
3. CommerceEntitlementBuyerGroup — is the policy linked to the group?
4. CommerceEntitlementProduct — is the product in the policy?
5. Contact role — does the contact have Buyer or Buyer Manager role?
6. Search index — has the index been rebuilt since the last entitlement change?

Do NOT investigate OWD, sharing rules, or FLS unless all of the above check out.
```

**Detection hint:** If the LLM output for a "buyer can't see product" scenario mentions "check sharing settings," "review OWD for Product2," or "ensure the buyer has read access via permission set," it is applying the wrong access model.
