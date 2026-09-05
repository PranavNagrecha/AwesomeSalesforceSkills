# Custom Label Management — Work Template

Fill this in during workflow step 1, before any `<labels>` element exists. It is
the artifact `references/examples.md` argues an eighteen-month-late i18n audit
has to reconstruct from scratch.

## Scope

**Skill:** `custom-label-management`

**Request summary:** _(what was asked for, in one sentence)_

**Target org / package:** _(org alias, and unlocked / managed / unpackaged)_

## Answers to the pre-configuration questions

Copy from SKILL.md's *Questions to Ask Before Configuring*. Every row here maps
to a `CustomLabel` field the Metadata API marks Required, so a blank is a deploy
failure waiting to happen.

| Question | Answer | Consequence for the file |
|---|---|---|
| Shown to a user verbatim, or branched on by code? | | Label vs `admin/custom-metadata-types` |
| Org default language / enabled locales? | | `<language>` value; which `<locale>.translation` files to author |
| Managed package? May the installing org reference these? | | `<protected>` per label |
| Retrieve via wildcard `CustomLabels` or named `CustomLabel`? | | Manifest shape in `package.xml` |
| Longest value, and will it be translated? | | Split plan if over ~765 chars (`gotchas.md` Gotcha 9) |
| Categories already in use in this org? | | `<categories>`, comma-separated, ≤255 chars |
| Which surfaces consume each label? | | What ships in the same deployment payload |

## String inventory and disposition

One row per hard-coded string found in `.cls`, `.trigger`, LWC `.html`/`.js`,
`.flow-meta.xml` and validation rules. Disposition is decided once, here.

| Source (file:line) | String | Disposition (Label / CMDT / stays inline) | `fullName` | `categories` | `protected` | Consumers | Owner |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
| | | | | | | | |

Rules for filling it:

- **Disposition** — a value code branches on (endpoint, toggle, threshold) is
  never a label. Internal logging and developer-facing error codes stay inline;
  write down where that boundary sits so it survives team turnover.
- **`fullName`** — there is no rename operation. Treat it as permanent from the
  moment it is written here.
- **Owner** — who answers the translator's disambiguation question ("does *Save*
  mean the button or the verb?") in twelve months.

## Locale plan

| Locale code | Enabled in Translation Workbench? | Translation file | Vendor / translator | Due |
|---|---|---|---|---|
| | | `translations/<code>.translation-meta.xml` | | |

Locale codes come from the Metadata API Developer Guide's *Language* section
(`api_meta.txt:135350-135405`). Note `es_MX` defaults to `es` for
customer-defined translations (`api_meta.txt:135379`), so translating `es` may
already cover it.

## Deployment payload

Everything below ships in **one** deploy, because Apex resolves
`System.Label.X` at compile time (`gotchas.md` Gotcha 2).

- [ ] `labels/CustomLabels.labels-meta.xml`
- [ ] `translations/<locale>.translation-meta.xml` (one per locale above)
- [ ] Apex classes / triggers referencing the labels
- [ ] LWC bundles importing the labels
- [ ] Flows and validation rules referencing `$Label.X`

Retrieved the current label file immediately before editing? _(yes / no — if no,
stop and read `gotchas.md` Gotcha 6)_

## Review checklist

From SKILL.md's *Review Checklist*, plus the checker.

- [ ] `python3 scripts/check_custom_label_management.py --manifest-dir <dir>` exits 0, or every remaining finding is a triaged INFO
- [ ] `shortDescription` populated on every new label, with placeholder meanings spelled out
- [ ] `categories` comma-separated and drawn from the existing vocabulary
- [ ] `protected` deliberately set per label, not copy-pasted
- [ ] No user-facing hard-coded strings left in the files listed in the inventory
- [ ] Translation file exists for every enabled locale
- [ ] Verified per locale by logging in as a user with that `LanguageLocaleKey`

## Deviations and decisions

Record anything that departs from the standard pattern and why — a label
deliberately left over 765 characters, a string kept inline, a `protected`
value that will change at the next package version.

- 
