# Metadata Examples — Custom Label Management

Deployable XML for `CustomLabels`, the `Translations` companion that carries the
translated values, and the four consumer surfaces that reference a label. Shapes
are taken from the Metadata API Developer Guide's own sample definitions
(`api_meta.txt:41232-41248` for `CustomLabels`, `api_meta.txt:136655-136665` for
`Translations`) and extended to a realistic quoting feature.

---

## Where the files live

| What | MDAPI path (grounded) | Source-format path (as shipped by `sf project retrieve`) |
|---|---|---|
| Master label values | `labels/CustomLabels.labels` — one file for the whole org (`api_meta.txt:41165`) | `force-app/main/default/labels/CustomLabels.labels-meta.xml` |
| Translations | `translations/<localeCode>.translation` (`api_meta.txt:135574-135575`) | `force-app/main/default/translations/<localeCode>.translation-meta.xml` |
| Packaged translations | `translations/<pkgNamespace>__<localeCode>.translation` (`api_meta.txt:135576-135577`) | same, under the package directory |

UNVERIFIED (2026-09-04): the Metadata API Developer Guide documents only the
MDAPI file names above (`.labels`, `.translation`). The `-meta.xml` suffixes and
the `force-app/main/default/` layout are the Salesforce DX source-format
convention; the corpus available here (Metadata API, Apex, Object Reference,
REST, Bulk, Data Loader guides) contains no statement about source-format
decomposition, so **do not assume the DX tree splits labels into one file per
label** — verify against your own `sf project retrieve start --metadata CustomLabels`
output. The guide's only claim is that master values live in *one* file.

---

## `labels/CustomLabels.labels-meta.xml`

Four labels: a plain UI string, an error message with a `String.format`
placeholder, a protected label intended for a managed package, and a
categorised label used by a list-view filter.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomLabels xmlns="http://soap.sforce.com/2006/04/metadata">
    <labels>
        <fullName>Quote_Save_Button</fullName>
        <categories>UIButtons,Quote</categories>
        <language>en_US</language>
        <protected>false</protected>
        <shortDescription>Button that saves the quote draft</shortDescription>
        <value>Save Quote</value>
    </labels>
    <labels>
        <fullName>Error_Amount_Must_Be_Positive</fullName>
        <categories>Errors,Quote</categories>
        <language>en_US</language>
        <protected>false</protected>
        <shortDescription>Validation error shown when Amount is zero or negative. {0} is the field label.</shortDescription>
        <value>{0} must be greater than zero.</value>
    </labels>
    <labels>
        <fullName>Internal_Pricing_Engine_Error</fullName>
        <categories>Errors,Internal</categories>
        <language>en_US</language>
        <protected>true</protected>
        <shortDescription>Internal pricing engine failure; not referenceable by subscriber code</shortDescription>
        <value>The pricing engine is temporarily unavailable. Contact your administrator.</value>
    </labels>
    <labels>
        <fullName>Toast_Quote_Submitted</fullName>
        <categories>Toast,Quote</categories>
        <language>en_US</language>
        <protected>false</protected>
        <shortDescription>Success toast title after a quote is submitted for approval</shortDescription>
        <value>Quote submitted for approval.</value>
    </labels>
</CustomLabels>
```

### How to read it

- **`<fullName>` is the API handle.** It is what `System.Label.X`,
  `@salesforce/label/c.X` and `$Label.X` bind to. The guide marks it Required
  and states it "must be specified when creating, updating, or deleting"
  (`api_meta.txt:41195-41199`). There is no rename operation — a changed
  `fullName` is a delete plus a create.
- **All five other Required fields are present on every label.** `value`,
  `language`, `protected` and `shortDescription` are each marked Required in the
  `CustomLabel` field table (`api_meta.txt:41190-41221`). Omit one and the
  deploy fails; the file is not a place for terse entries.
- **`<value>` caps at 1000 characters** ("Required. The translated custom label.
  Maximum of 1000 characters", `api_meta.txt:41219-41220`). `{0}` is a
  `String.format` placeholder, not platform syntax — the platform stores it
  literally and Apex substitutes it; put the placeholder's meaning in
  `shortDescription` or the translator will reorder or drop it.
- **`<categories>` is comma-separated, max 255 characters**, and "can be used in
  filter criteria when creating custom label list views"
  (`api_meta.txt:41191-41193`). Semicolons are not the documented separator.
- **`<protected>true</protected>` is a packaging decision, not a security
  control.** Protected components "can't be linked to or referenced by
  components created in the installing organization"
  (`api_meta.txt:41203-41206`), and the Apex `Label` class states "You can't
  access labels that are protected in a different namespace"
  (`apexrefguide.txt:220009`). In an unpackaged org the flag changes nothing
  visible, which is exactly why it gets copy-pasted as `false` and then bites on
  the first package upload.
- **`<language>` is the source language of `value`**, not a list of targets. One
  `CustomLabels` file, one source language per label; every other locale lives in
  a `Translations` file.

---

## `translations/es.translation-meta.xml`

The translated value for one label in one locale. `CustomLabelTranslation` has
exactly two fields — `name` (the label's `fullName`) and `label` (the translated
text, "Maximum of 765 characters", `api_meta.txt:135933-135937`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Translations xmlns="http://soap.sforce.com/2006/04/metadata">
    <customLabels>
        <label>Guardar oferta</label>
        <name>Quote_Save_Button</name>
    </customLabels>
    <customLabels>
        <label>{0} debe ser mayor que cero.</label>
        <name>Error_Amount_Must_Be_Positive</name>
    </customLabels>
</Translations>
```

- The file name is the locale code: `de.translation` for German
  (`api_meta.txt:135574-135575`). Supported codes are listed in the guide's
  *Language* section (`api_meta.txt:135350-135405`) — `es` is Spanish, `es_MX` is
  Spanish (Mexico) and "defaults to Spanish for customer-defined translations"
  (`api_meta.txt:135379`), so translating `es` covers `es_MX` label lookups.
- The `{0}` placeholder must survive translation. Translators who reflow the
  sentence will move it; Apex `String.format` still substitutes positionally, so
  a moved placeholder is correct and a deleted one silently produces a sentence
  with no value in it.

---

## Consumer surfaces

### Apex — static reference

Grounded: "You can only access the value of a custom label using
`system.label.label_name`" (`apexdev.txt:7246-7250`), and "In Apex code, you can
refer to or instantiate a Label like this: `System.Label.myLabelName`"
(`apexrefguide.txt:220035-220037`).

```apex
public with sharing class QuoteValidator {
    public static void validate(List<Opportunity> opps) {
        for (Opportunity o : opps) {
            if (o.Amount == null || o.Amount <= 0) {
                o.Amount.addError(String.format(
                    System.Label.Error_Amount_Must_Be_Positive,
                    new List<String>{ Schema.Opportunity.Amount.getDescribe().getLabel() }
                ));
            }
        }
    }
}
```

Custom labels "aren't standard sObjects. You can't create a new instance of a
custom label" (`apexdev.txt:7246-7247`) — there is no `new Label()` and no DML
against one.

### Apex — dynamic reference

`Label.get` and `Label.translationExists` are documented methods on the
`System.Label` class (`apexrefguide.txt:220031-220034`, signatures at
`apexrefguide.txt:220067-220123`).

```apex
// Fetch a label in an explicit language, bypassing the running user's locale.
// namespace: null defaults to the package namespace; '' means the org namespace.
String frenchValue = Label.get('', 'Quote_Save_Button', 'fr');

// Guard first — a missing translation falls back silently.
if (!Label.translationExists('', 'Quote_Save_Button', 'fr')) {
    System.debug(LoggingLevel.WARN, 'No fr translation for Quote_Save_Button');
}
```

Two behaviours the guide states explicitly: label names in this API "are
dynamically resolved at run time, overriding the user's current language if a
translation exists for the requested language" (`apexrefguide.txt:220008-220009`),
and the `language` parameter "must be a valid language ISO code"
(`apexrefguide.txt:220110-220112`). The `label` parameter "cannot be null or an
empty string" (`apexrefguide.txt:220107-220109`). Because resolution is at run
time, the compiler cannot tell you the label is missing — see
`gotchas.md` Gotcha 2 for the tradeoff against the static form.

### LWC — import

```javascript
// quoteForm.js
import { LightningElement } from 'lwc';
import SAVE_BUTTON from '@salesforce/label/c.Quote_Save_Button';
import AMOUNT_ERROR from '@salesforce/label/c.Error_Amount_Must_Be_Positive';

export default class QuoteForm extends LightningElement {
    labels = { saveButton: SAVE_BUTTON, amountError: AMOUNT_ERROR };
}
```

UNVERIFIED (2026-09-04): the Lightning Web Components Developer Guide is not in
the extracted corpus used for this skill, so the exact spelling of the
`@salesforce/label/<namespace>.<labelName>` import specifier — in particular
whether the local namespace prefix is `c` in every context — is not grounded
here. The Apex Reference Guide confirms only that custom labels "can be accessed
from Apex classes, Visualforce pages, Lightning pages, or Lightning components"
(`apexrefguide.txt:220025-220026`). Confirm the specifier against the LWC guide
before shipping.

### Flow, formula and validation rule — `$Label`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt from an object's validationRules, wrapped in its CustomObject
     root so the fragment is well-formed on its own. -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <validationRules>
        <fullName>Amount_Must_Be_Positive</fullName>
        <active>true</active>
        <errorConditionFormula>AND(NOT(ISBLANK(Amount)), Amount &lt;= 0)</errorConditionFormula>
        <errorDisplayField>Amount</errorDisplayField>
        <errorMessage>$Label.Error_Amount_Must_Be_Positive</errorMessage>
    </validationRules>
</CustomObject>
```

`errorMessage` is "Required. The message that appears if the validation rule
fails. The message must be 255 characters or less"
(`api_meta.txt:45402-45403`) — note that ceiling is lower than the label
`value` ceiling of 1000.

UNVERIFIED (2026-09-04): the corpus grounds the `$Label` merge-field form only
as `$Label.<namespace>.<name>` inside a Gift Entry template configuration
(`api_meta.txt:78590`, `api_meta.txt:78595`). It contains no statement that
`ValidationRule.errorMessage` accepts a `$Label` reference rather than a literal
string, nor the exact unnamespaced spelling for formula contexts. Validate the
rule in a scratch org before relying on it.

---

## `package.xml`

Two manifests, because the type name changes with the intent. The guide is
explicit: "Use `CustomLabels` with the wildcard character (\*) for members in the
package.xml manifest file to retrieve all custom labels that are defined in your
organization. `CustomLabels` doesn't support retrieving one or more custom labels
by name. To retrieve specific labels by name, use `CustomLabel` and specify the
label names as members." (`api_meta.txt:41224-41227`).

**All labels — plural type, wildcard only** (shape from `api_meta.txt:41250-41259`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>CustomLabels</name>
    </types>
    <version>62.0</version>
</Package>
```

**Named labels plus their translations and consumers — singular type**
(shape from `api_meta.txt:41261-41280`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Quote_Save_Button</members>
        <members>Error_Amount_Must_Be_Positive</members>
        <members>Internal_Pricing_Engine_Error</members>
        <members>Toast_Quote_Submitted</members>
        <name>CustomLabel</name>
    </types>
    <types>
        <members>es</members>
        <members>fr</members>
        <name>Translations</name>
    </types>
    <types>
        <members>QuoteValidator</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>quoteForm</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>62.0</version>
</Package>
```

Both `CustomLabels` and `Translations` support the wildcard in the manifest
(`api_meta.txt:41284-41286`, `api_meta.txt:136718-136720`).

Two manifest rules that are easy to get wrong:

- **Retrieving `Translations` alone returns almost nothing.** "When you use the
  `retrieve()` call to get translations, the files returned in the
  `.translations` folder only include translations for the other metadata types
  referenced in package.xml" (`api_meta.txt:136670-136673`). The label
  translations come back only because `CustomLabels` (or `CustomLabel`) is also
  listed — that is why the guide's own example manifest lists six types
  alongside `Translations` (`api_meta.txt:136674-136712`).
- **You can't retrieve `CustomLabels` with a namespace.** The guide's
  *CustomLabels Limitation* section says so in one sentence
  (`api_meta.txt:41289-41291`). Retrieving a managed package's labels through
  this type does not work; plan around it rather than debugging an empty file.

---

## Retrieve, lint, deploy

```bash
# 1. ALWAYS retrieve first. CustomLabels is a single file for the whole org.
sf project retrieve start \
  --metadata CustomLabels \
  --target-org devhub-sandbox

# 2. Edit force-app/main/default/labels/CustomLabels.labels-meta.xml,
#    then lint before you push anything.
python3 skills/admin/custom-label-management/scripts/check_custom_label_management.py \
  --manifest-dir force-app/main/default

# 3. Validate-only against the target org (no changes committed).
sf project deploy start \
  --source-dir force-app/main/default/labels \
  --source-dir force-app/main/default/translations \
  --source-dir force-app/main/default/classes \
  --source-dir force-app/main/default/lwc \
  --dry-run \
  --target-org devhub-sandbox

# 4. Deploy labels and every consumer in ONE payload.
sf project deploy start \
  --source-dir force-app/main/default/labels \
  --source-dir force-app/main/default/translations \
  --source-dir force-app/main/default/classes \
  --source-dir force-app/main/default/lwc \
  --target-org devhub-sandbox

# 5. Retrieve two labels by name (singular type) without pulling the org's whole set.
sf project retrieve start \
  --metadata CustomLabel:Quote_Save_Button \
  --metadata CustomLabel:Error_Amount_Must_Be_Positive \
  --target-org devhub-sandbox
```

### The whole-file replacement caution

`CustomLabels.labels` is one file holding every label in the org
(`api_meta.txt:41165`), and the plural type only ever retrieves *all* of them —
"`CustomLabels` doesn't support retrieving one or more custom labels by name"
(`api_meta.txt:41224-41227`). So the artifact your pipeline deploys is always the
whole set, never a diff. If your working copy was retrieved a week ago and
someone has since changed a label's `value` in Setup or through another pipeline,
your deploy silently reverts it — no conflict, no warning, because from the
platform's point of view you deployed a complete and valid `CustomLabels`
component and it took the values you gave it.

UNVERIFIED (2026-09-04): whether labels *absent* from your file are additionally
**deleted** by that deploy is not stated anywhere in the Metadata API Developer
Guide's `CustomLabels` section (`api_meta.txt:41147-41291`). Do not assume either
way. Test it once in a scratch org — deploy a two-label file over a three-label
org and count what survives — and write the answer into your team's runbook,
because the two possible behaviours have very different blast radii.

Two ways out, pick one and enforce it in review:

1. **Source of truth is git.** Nobody creates labels in Setup. Every change is a
   pull request against `CustomLabels.labels-meta.xml`, so git's merge resolves
   collisions the way it resolves any other file.
2. **Retrieve immediately before every edit** (step 1 above), and never leave a
   working copy of the file overnight.

Step 5's singular-type retrieve narrows what you *pull*; it does not narrow what
a `--source-dir force-app/main/default/labels` deploy *pushes*, because that
directory still contains the one whole file.

---

## Verification

**Setup check (grounded).** "To define custom labels, from Setup, in the Quick
Find box, enter `Custom Labels`, and then select Custom Labels"
(`apexrefguide.txt:220029`). After the deploy, filter that list view by
the `categories` value you set — `Quote` for the four labels above — and confirm
the count, the `value`, and that `shortDescription` is populated on each.

**Per-locale check.** Log in as (or use Setup > Users > Login As) a user whose
`LanguageLocaleKey` is `es`, and open each consumer surface: the Apex validation
error, the LWC toast, the validation rule message. A label with no `es`
translation renders its source-language `value` with no error and no log entry,
so a surface still showing English means the `Translations` deploy did not land —
re-check that `CustomLabels` was in the same manifest
(`api_meta.txt:136670-136673`).

**Apex check.** In anonymous Apex, assert the translation exists rather than
eyeballing it:

```apex
System.assertEquals(
    true,
    Label.translationExists('', 'Quote_Save_Button', 'es'),
    'Spanish translation for Quote_Save_Button did not deploy'
);
System.debug(Label.get('', 'Quote_Save_Button', 'es'));
```

UNVERIFIED (2026-09-04): a SOQL verification of the form
`SELECT Name, Value, Language FROM CustomLabel` is **not** supported by the
sources available here — the Object Reference contains no `CustomLabel` (or
`ExternalString`) entry, so there is no grounded evidence that custom labels are
queryable as an object in the enterprise SOQL surface. Use the Setup check or the
`Label.translationExists` assertion above instead of a SOQL query, unless you can
confirm the Tooling API object against the Tooling API guide.
