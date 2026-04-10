# LLM Anti-Patterns — B2C Commerce Store Setup

Common mistakes AI coding assistants make when generating or advising on B2C Commerce Store Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Applying B2B Commerce Data Model to SFCC Setup

**What the LLM generates:** Instructions referencing `WebStore`, `BuyerGroup`, `CommerceEntitlementPolicy`, or `IsBuyer` field on Contact records when the user is asking about SFCC / Business Manager.

**Why it happens:** Both products use the name "Salesforce Commerce" and training data conflates them. B2B Commerce on Lightning is a Salesforce platform product with standard objects; SFCC is a proprietary SaaS platform with no such objects. The LLM defaults to what it knows from Salesforce platform documentation.

**Correct pattern:**

```
# SFCC site setup uses Business Manager, not Salesforce org objects.
# No WebStore, BuyerGroup, or CommerceEntitlementPolicy.
# Site creation: Administration > Sites > Manage Sites > New in Business Manager.
# Customer segmentation uses SFCC Customer Groups, not BuyerGroups.
```

**Detection hint:** If the response contains `WebStore`, `BuyerGroup`, `CommerceEntitlementPolicy`, or `sf.com/lightning` URLs in context of a storefront setup request, the LLM has confused B2B and B2C Commerce.

---

## Anti-Pattern 2: Modifying app_storefront_base to Apply Customizations

**What the LLM generates:** Instructions telling the practitioner to edit files inside `app_storefront_base` — for example, directly patching `checkout.isml` or `productDetail.isml` in the base cartridge.

**Why it happens:** It is the most direct path to the desired change. LLMs optimize for the shortest path to a working result and may not model the upgrade-compatibility consequences. Training data may include examples of direct edits from pre-SFRA codebases where there was no base cartridge concept.

**Correct pattern:**

```
# WRONG:
# Edit: cartridges/app_storefront_base/cartridge/templates/default/checkout/checkout.isml

# CORRECT:
# 1. Create custom cartridge: app_custom_mystore
# 2. Mirror the path: cartridges/app_custom_mystore/cartridge/templates/default/checkout/checkout.isml
# 3. Place override content in the mirrored file
# 4. Set cartridge path: app_custom_mystore:app_storefront_base
```

**Detection hint:** Any instruction that includes `app_storefront_base/cartridge/` as a target for editing (not just reading) is this anti-pattern.

---

## Anti-Pattern 3: Placing Custom Cartridges to the Right of app_storefront_base

**What the LLM generates:** A cartridge path string that appends the custom cartridge after the base — e.g., `app_storefront_base:int_payment_acme`.

**Why it happens:** "Adding" something intuitively feels like putting it at the end of a list. LLMs unfamiliar with SFCC's left-to-right resolution order apply this intuition. The mistake is also visually subtle — the string looks valid.

**Correct pattern:**

```
# WRONG — int_payment_acme is never reached:
app_storefront_base:int_payment_acme

# CORRECT — custom cartridge evaluated first:
int_payment_acme:app_storefront_base

# With multiple cartridges (all custom left of base):
int_payment_acme:plugin_giftcert:app_custom_mystore:app_storefront_base
```

**Detection hint:** If the generated cartridge path contains `app_storefront_base` anywhere except the rightmost position, this anti-pattern is present.

---

## Anti-Pattern 4: Assuming Search Index Auto-Rebuilds After Catalog Changes

**What the LLM generates:** A catalog import or deployment procedure with no search index rebuild step, or a statement like "the search index will update automatically once the import completes."

**Why it happens:** Most modern data platforms do rebuild indexes automatically or use eventual-consistency models. LLMs apply this general expectation to SFCC, which deliberately decouples catalog writes from search index rebuilds for performance reasons.

**Correct pattern:**

```
# After any catalog import or structural change, ALWAYS manually trigger:
# Merchant Tools > Search > Search Indexes > [Site Index] > Full Rebuild
#
# This is a required operational step — not optional.
# Skipping it means production search serves stale data indefinitely.
```

**Detection hint:** Any deployment runbook for catalog changes that does not include a search index rebuild step is missing this requirement.

---

## Anti-Pattern 5: Treating SFCC Session as a General-Purpose Data Store

**What the LLM generates:** Code that stores serialized objects (full product records, user preference maps, complex cart state) in the SFCC session object — e.g., `session.custom.recentlyViewed = JSON.stringify(productArray)`.

**Why it happens:** Session storage is a familiar pattern from web frameworks. LLMs apply it without awareness of the 10 KB session size cap enforced by SFCC infrastructure. The limit is not in typical SFCC code examples in training data.

**Correct pattern:**

```javascript
// WRONG — risks 10 KB session cap:
session.custom.productData = JSON.stringify(fullProductObjects);

// CORRECT — store only identifiers, fetch on demand:
session.custom.recentlyViewedIds = JSON.stringify(['pid1', 'pid2', 'pid3']);
// Then fetch full product data from ProductMgr or API on render
```

**Detection hint:** Look for `session.custom` assignments that serialize arrays or objects longer than a few hundred characters — these risk exceeding the 10 KB limit.

---

## Anti-Pattern 6: Confusing Replication with Full Deployment (Missing Post-Replication Index Rebuild)

**What the LLM generates:** A staging-to-production release process that ends with "run the replication job" as the final step, without specifying a subsequent search index rebuild on the production instance.

**Why it happens:** Replication sounds like a complete synchronization. LLMs describe it as the end state without knowing that SFCC replication copies catalog objects but not the search index state.

**Correct pattern:**

```
Release checklist after staging-to-production replication:
1. Run replication job: Administration > Site Development > Site Import & Export > Replicate
2. Confirm replication job status = FINISHED
3. On the PRODUCTION instance: Merchant Tools > Search > Search Indexes > Full Rebuild
4. Confirm rebuild job status = FINISHED
5. Validate production storefront search for new/changed products
```

**Detection hint:** A production release runbook for SFCC that ends at "replication complete" without a subsequent production search index rebuild is incomplete.
