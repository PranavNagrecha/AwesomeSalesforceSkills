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
Territory assignment rule constraints:
1. Rules can only reference Account fields (standard and custom).
2. Cross-object fields (Owner.Role, Parent.Name) are NOT available.
3. Supported operators vary by field type:
   - Text: equals, not equal, starts with, contains.
   - Number/Currency: equals, not equal, greater than, less than, between.
   - Picklist: equals, not equal.
4. For criteria not supported by rules (e.g., Owner's role):
   - Create a formula field on Account that surfaces the needed value.
   - Use that formula field in the assignment rule criteria.
5. Rules evaluate Account field values at the time of rule execution,
   not at the time of Account creation.
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
Opportunity territory assignment is NOT automatic by default:
1. Enable Opportunity Territory Assignment:
   Setup → Territory Settings → Enable "Opportunity Territory Assignment."
2. Choose the assignment mechanism:
   - Filter-based assignment: Opportunities are assigned to territories
     based on configurable filters (Account territory, Opportunity fields).
   - Manual assignment: users select the territory on the Opportunity.
3. If filter-based: configure the Opportunity Territory Assignment filter
   under the active territory model.
4. Existing Opportunities are NOT retroactively assigned.
   Run "Run Opportunity Territory Assignment" to process existing records.
5. For forecasting by territory: territory assignment on Opportunities
   is a prerequisite.
```

**Detection hint:** If the output assumes Opportunities inherit territory from their Account without configuring Opportunity Territory Assignment, the assignment is missing. Search for `Opportunity Territory Assignment` in the setup instructions.
