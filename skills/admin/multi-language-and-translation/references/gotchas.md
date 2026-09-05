# Gotchas — Multi-Language and Translation

Nine platform behaviours that make a correct-looking translation deploy do
nothing, do the wrong thing, or quietly undo someone else's work. Every one of
them deploys without an error.

## Gotcha 1: Picklist API Values Never Change — Only Labels Do

**What happens:** An admin adds Spanish translations for picklist values and notices that existing records still show English values in some contexts — specifically in reports filtered by picklist value or in Apex conditions.

**When it occurs:** Any code or formula that references picklist values by their stored value. Since the API value (stored value) does not change, comparisons using translated labels fail.

**How to avoid:** Always use the API value (default language value) in Apex, SOQL, validation rule formulas, and report filters. Translations only affect the displayed label in the UI. Document this clearly for developers joining the project.

---

## Gotcha 2: Disabling Translation Workbench Removes All Translations

**What happens:** An admin disables Translation Workbench to troubleshoot a UI issue. All translations disappear immediately for all users. When Translation Workbench is re-enabled, the translations return — but the org experienced a translation outage.

**When it occurs:** Setup > Translation Workbench > Translation Settings > Disable.

**How to avoid:** Never disable Translation Workbench in production. Use a sandbox to troubleshoot translation issues. If a specific language is causing problems, remove just that language rather than disabling the entire workbench.

UNVERIFIED (2026-09-05): the extracted corpus (Metadata API, Object Reference,
Apex, REST, Bulk, Data Loader and LDV guides) documents
`LanguageSettings.enableTranslationWorkbench` as a boolean whose "default value
is `false`" (`api_meta.txt:120965-120967`) but states nothing about what
happens to existing translations when it is flipped back to `false`. The safer
lever *is* grounded: `Translation.IsActive` "indicates whether the translated
values for this language display to users (`true`) or not (`false`)"
(`object_reference.txt:290205-290206`), so deactivating one language is a
documented, per-language, reversible switch. Prefer it, and confirm the
workbench-disable behaviour in a scratch org before you ever need to know.

---

## Gotcha 3: Export/Import Translation Files Are Language-Specific

**What happens:** An admin exports translations for all languages at once, expecting a single file to contain all translations. The export actually creates language-specific files in the ZIP. Importing the wrong language's file overwrites translations.

**When it occurs:** Translation Workbench > Export > select all languages. Each language has its own tab-delimited file in the export ZIP.

**How to avoid:** Process one language at a time in export/import workflows. Label each file clearly with the language code before sending to a vendor or importing. Always import the file for the correct language.

The metadata layer works the same way and is grounded: local translations are
stored "in a file with a format of `localeCode.translation`… For example, the
file name for German translations is `de.translation`"
(`api_meta.txt:135574-135575`), and object translations in
`customObjectName__c-lang.objectTranslation` (`api_meta.txt:45899-45901`). One
file per language per object, never a combined one.

---

## Gotcha 4: A Blank Translation Is Silently Skipped, Not Applied

**What happens:** A translator returns a file in which some strings were
deliberately left blank — "this one should stay English", or the cell was
cleared by accident. You deploy it expecting those entries to be reset to the
source language. Nothing happens. The old translation is still there, and the
deploy reported success.

**When it occurs:** Any `Translations` or `CustomObjectTranslation` deploy that
contains an empty translated element. The Metadata API Developer Guide states
it flatly: "In Metadata Deployment of Translations, it's expected that blank
values cannot be used to delete existing translations. If a translation label
is left blank, it's skipped during deployment, and no error will be shown"
(`api_meta.txt:135789-135790`).

**How to avoid:** Treat "blank means delete" as false. To remove a translation
you must overwrite it with the value you actually want. Run
`scripts/check_multi_language_and_translation.py --manifest-dir <dir>` before
every translation deploy — it WARNs on every empty translated element rather
than letting the deploy's green tick imply the change landed. The same rule
explains why `GlobalValueSetTranslation` and `StandardValueSetTranslation`
retrieves come back with `<translation><!-- Silver --></translation>`: the
guide's own convention is that "when a value isn't translated, its translation
becomes a comment that's paired with its masterLabel"
(`api_meta.txt:79475-79476`). A comment-only element is untranslated, not
translated-to-itself.

---

## Gotcha 5: A Picklist Value Missing From a Deploy Is Deactivated, Not Ignored

**What happens:** You retrieve an object, spend a week on translations, and in
the meantime someone adds two picklist values in Setup. You deploy your
(now stale) object alongside the translations. The two new values disappear
from the picklist — not deleted, deactivated — and the translations that
referenced them stop resolving.

**When it occurs:** Any `CustomObject` or `GlobalValueSet` deploy built from a
stale retrieve. The guide says so twice: "If picklist values are missing from a
component definition, they get deactivated when deployed. Deactivation occurs
for picklist values of both standard and custom fields"
(`api_meta.txt:47482-47483`, `api_meta.txt:79237-79238`).

**How to avoid:** Retrieve immediately before you deploy, never at the start of
the translation cycle. A translation project runs for weeks; the metadata
underneath it does not stand still. If the payload must be old, split it:
deploy only the `objectTranslations/` and `translations/` folders and leave
`objects/` and `globalValueSets/` out entirely. The deploy order in
`references/metadata-examples.md` is written this way for exactly this reason.

---

## Gotcha 6: A Global Value Set's Values Cannot Be Translated Per Field

**What happens:** Three objects share a `Region` global value set. An admin
translates the values inside each object's `objectTranslation` file, under the
field that uses them. The deploy succeeds. None of the three fields shows a
translated value.

**When it occurs:** Whenever a custom picklist field carries
`<valueSet><valueSetName>` rather than an inline `<valueSetDefinition>`.
`PicklistValueTranslation` "contains details for translation of a picklist
value from a **local, custom** picklist field" (`api_meta.txt:46182-46183`);
values inherited from a global value set are translated once in a
`GlobalValueSetTranslation` file, and standard picklists in a
`StandardValueSetTranslation` — "In API versions 37.0 and earlier standard
picklist values could be translated with CustomFieldTranslation. In API version
38.0, use StandardValueSetTranslation instead" (`api_meta.txt:45982-45983`).

**How to avoid:** Classify each picklist before translating it — local, global
value set, or standard — because each lands in a different file with a
different name. The naming trap sits on top: "any global value set created in
API version 57.0 or later automatically has the `__gvs` suffix appended to the
developer name" (`api_meta.txt:79419-79421`), and the translation file is named
`ValueSetName-lang.globalValueSetTranslation` (`api_meta.txt:79446-79448`), so
a post-v57 value set needs `Region__gvs-de`, not `Region-de`. The checker
detects both mistakes and names the file you should have written.

---

## Gotcha 7: The 40-Character Field-Label Cap Is Half the Cap Everywhere Else

**What happens:** A German or Finnish translation of a field label deploys
cleanly in one org and fails in another, or a translator's carefully chosen
compound noun is rejected while a much longer record-type name goes through
without comment.

**When it occurs:** `CustomFieldTranslation.label` is "Translation for the
label. **Maximum of 40 characters**" (`api_meta.txt:46000`). Almost every
neighbouring element is far more generous: `LayoutSectionTranslation.label`,
`RecordTypeTranslation.label`, `QuickActionTranslation.label`,
`WebLinkTranslation.label` and `CustomLabelTranslation.label` are all "Maximum
of 765 characters" (`api_meta.txt:46069`, `api_meta.txt:46213`,
`api_meta.txt:46203`, `api_meta.txt:46256-46257`,
`api_meta.txt:135934-135935`), and `nameFieldLabel` and `relationshipLabel` are
80 (`api_meta.txt:45941`, `api_meta.txt:46024-46027`).

**How to avoid:** Give the translation vendor the per-element ceiling, not one
number for the whole job — 40 for field labels, 80 for name-field and
relationship labels, 765 for everything else on the object, 765 for custom
labels. Note the second-order trap: a source `CustomLabel.value` may be up to
1,000 characters, but `CustomLabelTranslation.label` caps at 765, so a
near-maximum English label has no legal translation at all. Run the checker; it
enforces every one of these ceilings by element type.

---

## Gotcha 8: Enabling a Platform-Only Language Silently Enables End-User Languages

**What happens:** An admin enables one platform-only language — Welsh, say, or
Hindi — for a single app. The org's language picker suddenly offers seventeen
more languages nobody asked for, and users start selecting them.

**When it occurs:** `LanguageSettings.enablePlatformLanguages`: "Indicates
whether platform-only languages are enabled (`true`) or not (`false`). This
field has a default value of `false`. **Setting this field to `true` also sets
`enableEndUserLanguages` `true`**" (`api_meta.txt:120961-120964`). It is one
switch presented as two.

**How to avoid:** Treat "add a platform-only language" as an org-wide decision
about *all three* language tiers, not a per-language one. Know which tier each
code sits in before enabling anything: fully supported languages get Salesforce
translations for the whole UI, end-user languages get standard objects and
pages "except admin pages, Setup, and Help" and "aren't translated… appear in
English" for the rest, and platform-only languages leave "all standard
Salesforce labels default to English or, in select cases, to an end-user or
fully supported language" (`api_meta.txt:135382-135384`,
`api_meta.txt:135412-135413`). The guide's own advice on the middle tier is
blunt: "End-user languages are intended only for personal use by end users.
Don't use end-user languages as corporate languages"
(`api_meta.txt:135385-135387`). Arabic (`ar`) and Hebrew (`iw`) are end-user
languages, not fully supported ones.

---

## Gotcha 9: A List View Filtered With `startsWith` or `contains` Is Bound to One Language

**What happens:** A list view that filters on a text field with "starts with"
or "contains" returns rows for some users and nothing for others, with no
pattern anyone can see until you notice it tracks the user's language.

**When it occurs:** `ListView.language` is "the language used for filtering if
your organization uses the Translation Workbench and you're using the
`startsWith` or `contains` operator. **The values entered as search terms must
be in the same language as the filter language**" (`api_meta.txt:44352-44355`).
The field exists only because Translation Workbench makes filtering
language-sensitive; in an untranslated org it never matters, so nobody sets it,
and enabling the Workbench turns every such list view into a latent bug.

**How to avoid:** Audit list views with `startsWith`/`contains` filters as part
of the Workbench rollout, not after. Set `<language>` explicitly on each, and
prefer `equals`/`in` on picklist API values where the filter is really a
category test. If you need filtering that ignores the running user's language
entirely, `LanguageSettings.enableLocaleInsensitiveFiltering` (default `false`,
API 56.0+) "indicates whether users can filter query results, regardless of the
locale or language associated with the user"
(`api_meta.txt:120952-120956`) — an org-wide switch, so decide it once with the
reporting owner rather than per list view.

---

## Gotcha 10: Data Translation Is a Different Feature, and It Goes Stale

**What happens:** Every label on the Product page is translated and the product
names are still English. Someone concludes the translation "half worked".

**When it occurs:** Translation Workbench translates *metadata* — labels, help
text, picklist values, error messages. Record data is a separate feature gated
by `LanguageSettings.enableDataTranslation` (default `false`, API 49.0+,
`api_meta.txt:120918-120920`) and surfaced through per-object sObjects:
`Product2DataTranslation`, `ProductCategoryDataTranslation`,
`ServiceResourceDataTranslation` and `ServiceTerritoryDataTranslation`, each of
which requires "Translation Workbench **and data translation** must be enabled
in your org" (`object_reference.txt:227889`, `object_reference.txt:228633`,
`object_reference.txt:259996`, `object_reference.txt:260827`).

**How to avoid:** Split the requirement in two at intake — "translate the UI"
and "translate the catalogue" are different projects with different metadata,
different objects and different owners. And plan for drift: each data
translation record carries `IsOutOfDate`, which "indicates whether the
translation is out-of-date (`true`) or current (`false`). A translation is
out-of-date if the parent Product2 record is updated after the last translation
was filed" (`object_reference.txt:227916-227917`). Metadata translations have
no such flag — nothing tells you a field label was reworded in English and its
German translation now says something else. That is a review process you have
to build, not a platform feature you can enable.
