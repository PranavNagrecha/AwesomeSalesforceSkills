# LLM Anti-Patterns — Industries CPQ vs Salesforce CPQ

Common mistakes AI coding assistants make when advising on Industries CPQ vs Salesforce CPQ selection, migration, or comparison. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Industries CPQ and Revenue Cloud as the Same Product

**What the LLM generates:** "Industries CPQ is Salesforce's new Revenue Cloud product that replaces Salesforce CPQ." or "Revenue Cloud uses OmniStudio and is the successor to both Vlocity CPQ and Salesforce CPQ."

**Why it happens:** LLMs conflate Salesforce's CPQ product naming evolution. Both products fall under Salesforce's "Revenue Cloud" marketing umbrella in some contexts, and Salesforce's own marketing materials use "Revenue Cloud" loosely to refer to both the native platform product and the industries product set. Training data mixes these references.

**Correct pattern:**

```
Industries CPQ:
- OmniStudio-native
- For telco, energy, insurance, media industry verticals
- Uses Calculation Procedures, DataRaptors, OmniScripts
- Part of industry cloud licensing (Communications Cloud, etc.)

Revenue Cloud (native CPQ):
- Salesforce-native objects (no managed package, no namespace)
- Successor to Salesforce CPQ managed package for enterprise sales
- Uses LWC Product Configurator
- Licensed as Revenue Cloud; does not require OmniStudio

These are separate products with separate licenses and separate object models.
```

**Detection hint:** Look for phrases like "Revenue Cloud is built on OmniStudio" or "Industries CPQ is the new Revenue Cloud." Both are incorrect generalizations.

---

## Anti-Pattern 2: Recommending Industries CPQ Without Checking for Industry Cloud License

**What the LLM generates:** "For complex bundling, you should use Industries CPQ with Calculation Procedures — this will handle your 1,000+ product catalog much better than Salesforce CPQ." (Stated without any mention of licensing requirement.)

**Why it happens:** LLMs learn that Industries CPQ has better bundling capability and recommend it on the basis of technical fit alone, without modeling the licensing prerequisite. The licensing gate is not salient in code/configuration training data.

**Correct pattern:**

```
Before recommending Industries CPQ, verify:
1. Does the org have Communications Cloud, Energy Cloud, Media Cloud,
   Insurance Cloud, or another Industries cloud license?
2. Is Industries CPQ specifically listed as a licensed feature in
   Setup > Company Information?

If no → Industries CPQ is not available. Recommend Revenue Cloud
        for enterprise selling or advise on licensing options.
If yes → Industries CPQ is appropriate for the use case.
```

**Detection hint:** Any Industries CPQ recommendation that does not include a licensing verification step is potentially incomplete.

---

## Anti-Pattern 3: Advising Immediate Emergency Migration After Salesforce CPQ End-of-Sale Announcement

**What the LLM generates:** "Salesforce CPQ is end-of-sale. You need to migrate to Revenue Cloud immediately. Here is a migration plan to cut over in Q2." (No mention of end-of-life timeline, feature parity gaps, or managed transition options.)

**Why it happens:** LLMs pattern-match "end-of-sale" to urgency and generate migration recommendations without distinguishing end-of-sale from end-of-life or end-of-support. The nuance that existing customers can renew and that end-of-life has not been announced is not well-represented in generic migration advice.

**Correct pattern:**

```
End-of-sale (March 2025):
- No new Salesforce CPQ licenses sold
- Existing customers can continue to renew
- Salesforce support continues on defined timeline

Recommended approach:
- Do NOT initiate emergency cutover
- Assess feature parity gap: Salesforce CPQ features used vs Revenue Cloud availability
- Plan migration for a natural business window (annual renewal, org redesign)
- Monitor Salesforce's end-of-support date announcement (not yet announced as of Spring '25)
```

**Detection hint:** Migration advice that uses language like "you must migrate" or "immediately migrate" in response to end-of-sale is likely overstating urgency.

---

## Anti-Pattern 4: Assuming Vlocity CPQ DataPacks Deploy Cleanly to Native OmniStudio Orgs

**What the LLM generates:** "Export your Vlocity CPQ DataPacks using the Vlocity Build Tool and import them into the target org using the OmniStudio CLI. The process is straightforward."

**Why it happens:** LLMs know DataPacks as the general deployment mechanism for OmniStudio and Vlocity/Industries CPQ. They do not reliably model the namespace difference between legacy Vlocity (managed package, `%vlocity_namespace%` token) and native OmniStudio (no namespace).

**Correct pattern:**

```
Migration from Vlocity CPQ to native OmniStudio Industries CPQ:
1. Export DataPacks from legacy Vlocity org using VBT or OmniStudio CLI
2. Audit all exported DataPacks for %vlocity_namespace% tokens
3. Run namespace migration to replace with native OmniStudio equivalents
4. Validate component types — Vlocity-branded types may differ from
   native OmniStudio component type names
5. Deploy to native org and validate each component
6. Follow official guide: help.salesforce.com
   id=ind.comms_download_and_migrate_industries_cpq_datapacks_to_salesforce_org
```

**Detection hint:** Any DataPacks migration advice that skips namespace migration for a legacy Vlocity org is incomplete.

---

## Anti-Pattern 5: Generating SOQL or Apex That Joins SBQQ__ Objects with Industries CPQ Cart Objects

**What the LLM generates:**

```apex
// Attempting to join Salesforce CPQ quotes with Industries CPQ orders
List<SBQQ__Quote__c> quotes = [
    SELECT Id, SBQQ__Account__c,
           (SELECT Id FROM IndustriesCPQOrders__r)
    FROM SBQQ__Quote__c
    WHERE SBQQ__Status__c = 'Presented'
];
```

**Why it happens:** LLMs see that both products live in the same Salesforce org and generate SOQL that attempts to navigate across object relationships. There is no standard relationship between `SBQQ__Quote__c` and Industries CPQ order/cart objects. This code will fail with a compile error or runtime null result.

**Correct pattern:**

```apex
// These are separate, unrelated object hierarchies.
// Query them separately and join in Apex if needed.

// Salesforce CPQ quotes
List<SBQQ__Quote__c> sfCpqQuotes = [
    SELECT Id, SBQQ__Account__c, SBQQ__TotalAmount__c
    FROM SBQQ__Quote__c
    WHERE SBQQ__Status__c = 'Presented'
];

// Industries CPQ orders — use the appropriate CPQ order object
// (varies by org — check via Schema or object metadata)
List<Order> industryCpqOrders = [
    SELECT Id, AccountId, TotalAmount
    FROM Order
    WHERE Type = 'CPQ'
    AND Status = 'Draft'
];

// Join in memory if needed, or use a custom summary object
```

**Detection hint:** Any SOQL or Apex that attempts to traverse from `SBQQ__Quote__c` to Industries CPQ objects via a relationship field is likely wrong.

---

## Anti-Pattern 6: Claiming Revenue Cloud Feature Parity with Salesforce CPQ Without Verifying Current Release

**What the LLM generates:** "Revenue Cloud is fully feature-equivalent to Salesforce CPQ. You can migrate with confidence that all your existing CPQ functionality will be available."

**Why it happens:** Salesforce's marketing messaging around Revenue Cloud launch stated "feature parity" as a goal. LLMs trained on this messaging repeat it as a current fact, without accounting for the ongoing development timeline and known gaps.

**Correct pattern:**

```
Revenue Cloud feature parity with Salesforce CPQ is a goal, not a
current fact (as of Spring '25). Known areas requiring parity verification:
- Partner community quoting
- Certain Salesforce Billing configurations
- Specific Apex plugin hook points (CPQ plugin interface replacements)
- Some legacy discount schedule configurations

Always perform a formal feature gap assessment against the current
Revenue Cloud release notes before committing to a migration timeline.
```

**Detection hint:** Unqualified "full parity" or "all features available" statements about Revenue Cloud relative to Salesforce CPQ are overstatements until confirmed against current release notes.
