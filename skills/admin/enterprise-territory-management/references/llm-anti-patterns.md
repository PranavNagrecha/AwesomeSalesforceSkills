# LLM Anti-Patterns — Enterprise Territory Management

Common mistakes AI coding assistants make when generating or advising on Salesforce Enterprise Territory Management (ETM).
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Enterprise Territory Management with Legacy Territory Management

**What the LLM generates:** "Go to Setup → Territory Management to configure your territories."

**Why it happens:** LLMs reference Legacy (Original) Territory Management, which was the pre-ETM feature. Enterprise Territory Management (ETM) is a separate, more modern implementation with different Setup paths, different metadata, and different features. Legacy TM is no longer available for new enablements.

**Correct pattern:**

```
Enterprise Territory Management (ETM):
- Setup path: Setup → Territory Models (under Feature Settings → Sales).
- Supports multiple territory models (only one active at a time).
- Uses Territory2, Territory2Model, Territory2Type metadata types.
- Supports territory-based forecasting.

Legacy Territory Management (deprecated):
- Setup path: Setup → Territory Management (under Manage Users).
- Uses Territory metadata type (not Territory2).
- Does not support multiple models or territory types.
- Not available for new enablements.

Always verify which version is enabled before advising.
```

**Detection hint:** If the output references `Territory` metadata (without "2") or navigates to "Manage Users → Territory Management," it is describing the legacy version. Search for `Territory2` to confirm ETM.

---

## Anti-Pattern 2: Activating a territory model without understanding the reprocessing impact

**What the LLM generates:** "Create your territory model, add territories and assignment rules, then activate it."

**Why it happens:** LLMs describe activation as a simple on/off step. Activating a territory model triggers assignment rule processing across all Accounts in the org. For large orgs, this can take hours and may cause performance degradation. Reactivating after changes also reprocesses all rules.

**Correct pattern:**

```
Territory model activation considerations:
1. Build and test the model in Planning state first.
   - Add territory types, territories, and assignment rules.
   - Use "Run Assignment Rules" in preview mode to test without activating.
2. Schedule activation during off-peak hours.
3. For large orgs (100K+ Accounts):
   - Activation may take hours.
   - Monitor via Setup → Territory Models → [Model] → Assignment Status.
4. After any rule change, rules must be re-run to update assignments.
   This reprocesses ALL accounts, not just changed ones.
5. Only ONE territory model can be active at a time.
```

**Detection hint:** If the output activates the model without mentioning processing time, scheduling, or impact on large orgs, the activation step is understated. Search for `off-peak`, `processing time`, or `reprocess` in the activation instructions.

---

## Anti-Pattern 3: Assuming territory assignment rules support all field types and operators

**What the LLM generates:** "Create a territory assignment rule: State = 'California' AND Annual Revenue > 1,000,000 AND Owner.Role = 'West Sales'."

**Why it happens:** LLMs compose complex rule criteria without checking which fields and operators are available. Territory assignment rules only work with specific Account fields and support limited operators. Cross-object fields (like Owner.Role) are not available in assignment rule criteria.

**Correct pattern:**

```
Territory2Rule constraints (Metadata API Developer Guide, Territory2Rule):
1. objectType is documented as Account only.
2. A rule holds at most 10 <ruleItems>.
3. <operation> is a closed enumeration. There is no "between", and no
   "greater_than" despite the guide's own sample showing it:
     equals, notEqual, lessThan, greaterThan, lessOrEqual, greaterOrEqual,
     contains, notContain, startsWith, includes, excludes,
     within  (DISTANCE criteria only)
4. <booleanFilter> numbering starts at 1 and must be contiguous. Item order
   is derived from position in the XML, so reordering renumbers the filter.
5. For criteria the rule cannot express, surface the value in a formula field
   on Account and test that field instead.
```

**Detection hint:** If the output uses cross-object references or unsupported operators in territory assignment rules, the rule will not save. Search for dot notation (e.g., `Owner.`) in rule criteria.

---

## Anti-Pattern 4: Ignoring the relationship between territory types and the hierarchy

**What the LLM generates:** "Create territories: North America, US East, US West, New York, California. Add them all at the same level."

**Why it happens:** LLMs create flat territory lists without establishing a hierarchy or using Territory Types to classify territory levels. Territory Types define categories (Region, District, Territory) and the hierarchy defines parent-child rollup. A flat structure prevents meaningful reporting and forecast rollup.

**Correct pattern:**

```
Design the hierarchy with Territory Types:
1. Define Territory Types (categories, not individual territories):
   - Region (top level)
   - District (mid level)
   - Territory (leaf level)
2. Build the hierarchy:
   North America (Type: Region)
   ├── US East (Type: District)
   │   ├── New York (Type: Territory)
   │   └── Boston (Type: Territory)
   └── US West (Type: District)
       ├── California (Type: Territory)
       └── Washington (Type: Territory)
3. Territory Types support priority for assignment rule ordering.
4. The hierarchy enables rollup forecasting by territory.
```

**Detection hint:** If the output creates territories without defining Territory Types or establishing a parent-child hierarchy, the model is flat. Search for `Territory Type` or `parent territory` in the configuration.

---

## Anti-Pattern 5: Forgetting to configure Opportunity territory assignment

**What the LLM generates:** "Set up territory management to assign Accounts to territories. The sales team's Opportunities will automatically inherit the territory."

**Why it happens:** LLMs assume Opportunity territory assignment is automatic. While Accounts are assigned to territories via rules, Opportunities require separate configuration for territory assignment. The default behavior and the mechanism (filter-based, or territory lookup field) depend on the org's Opportunity Territory Assignment setting.

**Correct pattern:**

```
Opportunity territory assignment is neither automatic nor declarative.
Filter-based OTA is an Apex class, wired through Territory2Settings:

  <opportunityFilterSettings>
      <apexClassName>OppTerrAssignDefaultLogicFilter</apexClassName>
      <enableFilter>true</enableFilter>
      <runOnCreate>true</runOnCreate>
      <runMultiThreaded>false</runMultiThreaded>
  </opportunityFilterSettings>

The class implements TerritoryMgmt.OpportunityTerritory2AssignmentFilter:
  public Map<Id,Id> getOpportunityTerritory2Assignments(List<Id> opportunityIds)

Contract details that decide whether it is correct:
1. Salesforce supplies only opportunities whose
   IsExcludedFromTerritory2Filter is false.
2. The return map is three-valued:
     oppId -> territoryId  assigns that territory
     oppId -> null         CLEARS any existing Territory2Id
     oppId absent          leaves Territory2Id untouched
   Returning null for everything unclassifiable strips correct territories.
3. Default logic (per the guide's reference implementation): 0 territories
   on the account -> null; 1 -> that territory; 2+ -> the one whose
   territory type Priority is numerically HIGHEST, unless two tie, in which
   case null.
4. runMultiThreaded=true only for opportunity or opportunity product splits,
   and only if the Apex is safe under multithreading.
5. Territory assignment on the Opportunity is a prerequisite for territory
   forecasting.
```

**Detection hint:** If the output assumes Opportunities inherit territory from their Account without configuring Opportunity Territory Assignment, the assignment is missing. Search for `Opportunity Territory Assignment` in the setup instructions.


---

## Anti-Pattern 6: Naming Objects and Metadata That Belong to a Different Feature

**What the LLM generates:** "Query `AccountTerritoryAssignmentRule` to audit your territory rules," "deploy `Territory2ObjSharingConfig` to set Opportunity access for territory members," or "add the territory model to your change set."

**Why it happens:** Three plausible-sounding names, each attached to something real, none of them the thing being described. `AccountTerritoryAssignmentRule` exists but belongs to the original Territory Management feature — its `TerritoryId` refers to `Territory`, and its Object Reference entry cross-references `Territory` and `UserTerritory`. `Territory2ObjSharingConfig` exists but is a `query`/`update`-only SOAP object (API 56.0+) for the objects enabled through `Territory2Settings.supportedObjects`, documented as `Lead` only. Change sets exist but cannot carry these components at all. Both objects' entries open with "Available if Sales Territories has been enabled," so the availability line does not disambiguate them.

**Correct pattern:**

```
Wrong                              Right
---------------------------------  --------------------------------------------
AccountTerritoryAssignmentRule     ObjectTerritory2AssignmentRule (SOAP)
                                   Territory2Rule (Metadata API)
AccountTerritoryAssignmentRuleItem ObjectTerritory2AssignmentRuleItem
Territory (metadata type)          Territory2
UserTerritory                      UserTerritory2Association
"Territory2ObjSharingConfig        <opportunityAccessLevel>, <contactAccessLevel>,
 controls Opp/Contact access"       <caseAccessLevel> on each Territory2;
                                   defaults in Territory2Settings
"add it to the change set"         source deploy only - every Territory2* type's
                                   Usage section says "don't support packaging or
                                   change sets and aren't supported in CRUD calls"
"rules run after the deploy"       "Rules can't be run via Metadata API" - the run
                                   is user-initiated and logged in
                                   Territory2AlignmentLog
```

**Detection hint:** Any object or metadata name in ETM output that does not contain `Territory2` is suspect — check it against the Object Reference before acting. Any deployment plan that mentions a change set for territory components is wrong regardless of how the rest of it reads.
