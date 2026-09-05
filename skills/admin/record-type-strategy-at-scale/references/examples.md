# Examples — Record Type Strategy At Scale

## Example 1: Reducing Opportunity Layout Explosion with Dynamic Forms

**Context:** A financial services company has 12 record types on Opportunity (one per product line) and 65 profiles. This creates 780 layout assignment cells. Most record types differ only in which fields are visible — the underlying Sales Process is shared across 9 of the 12 record types.

**Problem:** Every new hire profile requires 12 layout assignments. A recent profile cleanup project stalled because administrators could not confidently map layouts across the matrix. Several record types had drifted to show identical fields, but no one could confirm which were safe to merge.

**Solution:**

```text
Step 1: Export RecordType metadata for Opportunity.
        Confirm 9 of 12 share the same Sales Process (BusinessProcess reference).

Step 2: Catalog field differences across the 9 shared-process record types.
        Result: 6 differ only in which custom fields are visible.

Step 3: Consolidate the 6 field-visibility-only record types into 2
        (one for Retail products, one for Wholesale products).

Step 4: Build Dynamic Forms pages in Lightning App Builder.
        Add field sections with visibility rules:
        - "Retail Detail" section visible when RecordType.DeveloperName = 'Retail'
        - "Wholesale Detail" section visible when RecordType.DeveloperName = 'Wholesale'

Step 5: Migrate records via Bulk API:
        UPDATE Opportunity SET RecordTypeId = '<Retail_RT_Id>'
        WHERE RecordTypeId IN ('<Old_RT_1>', '<Old_RT_2>', '<Old_RT_3>')

Step 6: Delete retired record types. Update profile layout assignments.
        New matrix: 8 record types x 65 profiles = 520 assignments (down from 780).
```

**Why it works:** The consolidation removed 4 record types that existed solely for field layout differences. Dynamic Forms absorbed that variation into component visibility rules on a single page, eliminating 260 layout assignments and making future profile additions cheaper.

---

## Example 2: Fixing Hardcoded Record Type IDs Across Sandboxes

**Context:** A healthcare ISV builds a managed package that creates Case record types during installation. Their Apex code retrieves the record type by hardcoded ID to set defaults on new Cases. The package works in their dev org but fails in customer sandboxes and production orgs.

**Problem:** Record Type IDs are org-specific. The hardcoded ID `'0124x000000AAAA'` exists only in the dev org. In customer orgs, the same record type has a different ID, causing a `System.SObjectException: Record Type not found` error.

**Solution:**

```apex
// WRONG: Hardcoded ID
// Id rtId = '0124x000000AAAA';

// CORRECT: Resolve by DeveloperName at runtime
Id rtId = Schema.SObjectType.Case
    .getRecordTypeInfosByDeveloperName()
    .get('Patient_Inquiry')
    .getRecordTypeId();

Case newCase = new Case(
    RecordTypeId = rtId,
    Subject = 'New Patient Inquiry',
    Origin = 'Web'
);
insert newCase;
```

**Why it works:** `getRecordTypeInfosByDeveloperName()` resolves the DeveloperName (which is stable across orgs since it travels with metadata deployments) to the org-local ID at runtime. This works in managed packages, scratch orgs, sandboxes, and production without any ID translation.

---

## Anti-Pattern: Creating a Record Type for Every Team

**What practitioners do:** An org creates a separate record type on Account for each sales team (East, West, Central, International, Enterprise, SMB) so each team sees "their" page layout. The record types share the same Industry picklist values and have no distinct business process.

**What goes wrong:** With 6 record types and 40 profiles, the org has 240 layout assignments. When a new region launches, adding one record type creates 40 more assignments. The layouts are nearly identical — the only difference is the section header text. Administrators spend hours maintaining assignment matrices instead of delivering business value.

**Correct approach:** Use a single record type (or two if picklist values genuinely differ) and control field visibility with Dynamic Forms. Use a custom field like `Team__c` to drive component visibility rules. If teams need different default field values, use a Flow on record creation instead of separate record types.

**Proving the six are interchangeable before you merge them.** The argument "they are all the same"
has to be evidence, not a hunch. Retrieve the record types (named members — `RecordType` takes no
wildcard) and diff the blocks pairwise; if the only difference is `<label>`, there is no picklist or
business process reason for the type to exist:

```bash
sf project retrieve start --metadata \
  "RecordType:Account.East,RecordType:Account.West,RecordType:Account.Central,RecordType:Account.International,RecordType:Account.Enterprise,RecordType:Account.SMB" \
  --target-org my-sandbox

# Record types live inside the object file; split out one block per type, then compare.
for rt in East West Central International Enterprise SMB; do
  python3 - "$rt" <<'PY' > "/tmp/rt_$rt.xml"
import re, sys
src = open('force-app/main/default/objects/Account/Account.object-meta.xml', encoding='utf-8').read()
name = sys.argv[1]
m = re.search(r'<recordTypes>\s*<fullName>' + name + r'</fullName>.*?</recordTypes>', src, re.S)
print(re.sub(r'<label>.*?</label>', '<label>NORMALISED</label>', m.group(0)) if m else '')
PY
done
diff /tmp/rt_East.xml /tmp/rt_West.xml   # empty output = nothing but the label differs
```

Then size the replacement before building it. The `Team__c` field carries what the six record types
were carrying, and the record type column collapses to one row:

| | Before | After |
|---|---|---|
| Account record types | 6 | 1 (`Standard`) |
| Profiles | 40 | 40 |
| `recordTypeVisibilities` entries to maintain | 240 | 40 |
| `layoutAssignments` entries to maintain | 240 + 40 fallback | 40 fallback only |
| Cost of the next new region | +40 entries | +1 picklist value on `Team__c` |
| Field visibility mechanism | 6 near-identical layouts | one FlexiPage, visibility filters on `Team__c` |

The last row is the trade being made, not a free win: field visibility moves from a layout to a
FlexiPage component filter, which is a UI control and not field-level security (gotchas #4). Design
the FlexiPage in `admin/dynamic-forms-and-actions`; enforce anything sensitive with FLS regardless.
