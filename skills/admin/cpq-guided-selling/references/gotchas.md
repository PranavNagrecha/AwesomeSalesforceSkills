# Gotchas: CPQ Guided Selling

Non-obvious CPQ guided selling behaviors that cause real production problems. Sources are listed in `well-architected.md`. Line references cite the `pdftotext -layout` extraction of the Summer '26 Salesforce CPQ Developer Guide (`cpq_developer_guide`) and Salesforce CPQ Plugins Developer Guide (`cpq_plugins`), written as `<guide> L<n>`. The CPQ object and field reference is published only on help.salesforce.com, which did not fetch; claims that rest on it carry an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: The CPQ managed package has no new feature development

**What happens:** "The Salesforce CPQ managed package continues to be available for existing customers, however, there is no longer any new feature development. We will continue to provide support and services for the duration of your contract." The guide recommends Revenue Cloud "for a more comprehensive and robust CPQ solution" (`cpq_developer_guide L32-36`).

**When it occurs:** A team plans a large guided selling build, with custom plugins and executors, on a platform that will not gain features.

**How to avoid:** Record the platform decision before designing. For existing CPQ orgs, keep guided selling configuration-first and keep custom plugin code small and tested. For new implementations, evaluate Revenue Cloud.

---

## Gotcha 2: A missing mirror field on Process Input returns the whole catalog

**What happens:** The wizard shows the question, the rep answers, and the results list shows every product. No error appears.

**When it occurs:** A question filters on a custom Product2 field, and no field with the same API name exists on `SBQQ__ProcessInput__c`. UNVERIFIED (2026-10-03): this mechanism (CPQ stores the answer on a same-name Process Input field and skips the filter when that field is absent) is documented only on help.salesforce.com. The plugin guide confirms the shape of the answers that reach the plugin: "a map of the guided selling suggestion criteria. The Key is a Product2 API name and the value is the desired suggest value" (`cpq_plugins L1445`).

**How to avoid:** Deploy the mirror field as `CustomField` metadata in the same change as the Product2 field (see `metadata-examples.md`), with compatible type and identical picklist values, and grant field-level security to the users who run the wizard. When answers stop filtering, check the mirror field first.

---

## Gotcha 3: Enhanced and Custom are plugin modes chosen at run time by `isSuggestCustom`

**What happens:** For a guided selling prompt, CPQ calls `isInputHidden` and `getInputDefaultValue` for each input, then `isSuggestCustom`. If it returns true, CPQ calls `suggest`, which "gives you full control of the search query" and returns `List<PricebookEntry>`. If it returns false, CPQ calls `getAdditionalSuggestFilters`, which "appends a WHERE clause to the existing SOQL query" (`cpq_plugins L1370-1395`, `L1414-1430`, `L1538-1580`). Earlier versions of this skill described a `search(SBQQ.ProductSearchContext ctx)` method returning `List<Id>`; that signature is not in the guide.

**When it occurs:** A developer implements only `suggest` but returns false from `isSuggestCustom` (so `suggest` never runs), or writes a method with an invented signature that does not compile against the interface.

**How to avoid:** Decide the mode first and implement both branches deliberately. In Enhanced mode, return a fragment such as `AND Product2.Inventory_Level__c > 3` or null. In Custom mode, return price book entries for the quote's price book. UNVERIFIED (2026-10-03): the guide's two example classes each show only one half of the interface (product search or guided selling); compile a full implementation in a sandbox to confirm which methods your package version requires.

---

## Gotcha 4: Plugins see only a subset of quote fields, and dates arrive as strings

**What happens:** "Product search plugins can use only a subset of CPQ quote fields by default. If you can't pass a field to your guided selling input, or if it passes as null, you must retrieve it with a SOQL query." Date fields "are returned as strings in the format yyyy-mm-dd" (`cpq_plugins L1364-1367`). The `suggest` map "contains only keys for non-null values" (`L1587-1589`).

**When it occurs:** Plugin logic branches on a custom quote field (region, segment) or parses a date field as a `Date`, and fails or silently takes the wrong branch.

**How to avoid:** Query the quote by `Id` for any field the logic needs. Parse date strings explicitly. Treat a missing map key as "not answered".

---

## Gotcha 5: The guide's sample `suggest` method concatenates strings into SOQL

**What happens:** The guide's example builds its query by concatenating `quote.get('SBQQ__Pricebook__c')` and field-set paths into a string and calling `Database.query` (`cpq_plugins L1600-1625`). The product search example concatenates rep-entered values into a `LIKE` clause (`L1305-1312`).

**When it occurs:** A developer copies the sample, and a rep-entered answer containing a quote character breaks the query or changes its meaning.

**How to avoid:** Use static SOQL with bind variables (`:pricebookId`, `:answer`), or `Database.queryWithBinds` when the field list must be dynamic, and enforce sharing and field access in the plugin class. The class in `metadata-examples.md` uses binds.

---

## Gotcha 6: The configuration initializer sets only standard product option fields

**What happens:** "The product configuration initializer uses a custom user-provided APEX page to select options and set field values based on the results of guided selling prompts. It works only for standard product option fields and not for configuration attributes or custom product option fields." An initializer on a quote process overrides the package-level one (`cpq_plugins L2703-2711`).

**When it occurs:** Requirements ask guided selling answers to set a custom field on a product option or a configuration attribute in the bundle configurator.

**How to avoid:** Limit initializer designs to standard option fields such as selection and quantity. Use product rules or configuration rules for anything else.

---

## Gotcha 7: Auto Select needs a price book entry for the single match

**What happens:** With Auto Select on and exactly one matching product, CPQ adds the product directly. If that product has no active entry in the quote's price book, the add fails and the rep sees an error. UNVERIFIED (2026-10-03): the Auto Select behavior and its failure mode are help-only claims carried from earlier versions of this skill.

**When it occurs:** Products are added to the catalog but not to every price book used with the quote process.

**How to avoid:** Before enabling Auto Select, check that every product that can be a sole match has an active `PricebookEntry` in every price book in use (`SELECT Product2Id FROM PricebookEntry WHERE Pricebook2Id = :pb AND IsActive = true`). In Custom mode, `suggest` returns price book entries filtered by the quote's price book, which avoids the gap by construction.

---

## Gotcha 8: Null classification values never match an equals filter

**What happens:** A product with a blank value on a filter field never appears for that question, whatever the rep selects. This is standard SOQL null behavior: `WHERE Field = 'Value'` never matches null.

**When it occurs:** New products are added without classification values, or a product is meant to apply to every answer and was left blank.

**How to avoid:** Make classification fields required for products in guided selling, or give cross-category products an explicit value (for example "All") and design the question to include it. UNVERIFIED (2026-10-03): whether leaving an optional question blank skips its filter entirely is help-only; test it.
