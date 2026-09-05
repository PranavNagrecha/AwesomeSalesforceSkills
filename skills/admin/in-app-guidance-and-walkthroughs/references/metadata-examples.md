# Metadata Examples — In-App Guidance and Walkthroughs

Deployable shapes for the one metadata type in-app guidance is made of: `Prompt`, which carries a list of
`promptVersions`. A single prompt and a ten-step walkthrough are the *same* type — a walkthrough is a
`Prompt` whose `promptVersions` list has more than one entry, each carrying a `stepNumber`. There is no
separate "walkthrough" metadata type and no `isWalkthrough` flag.

Shapes below are taken from the Metadata API Developer Guide (v62 PDF — `Prompt` api_meta.txt L98902–98957,
`PromptVersion` L98958–99347, `UiFormulaRule` L99349–99364, `UiFormulaCriterion` L99365–99420, sample
definition L99418–99465) and extended to one worked renewal-process example. `PromptAction` /
`PromptError` field names come from the Object Reference (object_reference.txt L234826–235013 and
L235018–235103).

Two things this file deliberately does **not** own:

- **Which guidance to build, for whom, and when.** `admin/change-management-and-training`
  `references/worked-examples.md` makes that call as part of a rollout plan; this file builds what it decided.
- **Custom-permission design.** `admin/custom-permissions` owns naming, dependency chains, and assignment
  strategy. Section 5 here carries only the two fragments needed to make a `uiFormulaRule` gate resolve.

## Where the files live

| Type | package.xml `<name>` | `<members>` syntax | Wildcard `*` | DX source file | API |
|---|---|---|---|---|---|
| `Prompt` | `Prompt` | the prompt's developer name | **Supported** (L99508–99510) | `prompts/Renewal_Checklist.prompt-meta.xml` | 46.0+ (L98921) |
| `CustomPermission` | `CustomPermission` | custom permission name | **Supported** (L46738–46740) | `customPermissions/Renewal_Pilot.customPermission-meta.xml` | 31.0+ (L46635) |
| `PermissionSet` | `PermissionSet` | permission set name | Supported | `permissionsets/Renewal_Pilot.permissionset-meta.xml` | — |

MDAPI folder name is `prompts/` with suffix `.prompt` (L98917–98918). The DX suffix adds `-meta.xml`.

## How to read it

- **`masterLabel` appears twice.** Once on `<Prompt>` (required, max 80 chars, L98944–98948) and once on
  each `<promptVersions>` entry (required, L99138–99142). They are different fields; both must be present.
- **`displayType` is what makes it floating, docked, or targeted** — `FloatingPanel`, `DockedComposer`, or
  `Targeted` (52.0+). It is required (L99037–99044).
- **`isPublished` is the active flag.** `true` = the guidance is active, `false` = inactive
  (L99133–99138). Deploying `<isPublished>true</isPublished>` deploys an *active* prompt.
- **`versionNumber` is always `1`** — "The number remains 1 since multiple versions aren't saved in the
  org" (L99326–99329). It is not a step counter and not a revision counter.
- **`stepNumber` is what makes it a walkthrough.** Required for walkthroughs only, up to 10 steps, "Numbers
  must be consecutive without repeated or skipped numbers" (L99190–99196).
- **Walkthrough-level settings live on step 1, the button lives on the last step.** `startDate`, `endDate`,
  `delayDays`, `timesToDisplay`, `publishedDate`, `themeColor`, `themeSaturation` → first step
  (L99005, L99066–99068, L99152–99153, L99177–99181, L99260, L99271, L99293). `actionButtonLabel` and
  `actionButtonLink` → last step (L98965–98966, L98983–98984).
- **`targetPageType` and `targetPageKey1` are required and opaque.** The guide says only "Used by
  Salesforce to identify the prompt's page location" (L99206–99210, L99244–99248) and publishes no value
  vocabulary. Build one prompt in Setup, retrieve it, and copy the values it produced.
- **`delayDays` is days between *recurrences*, not seconds before render** — "Required if recurrences are
  scheduled. Number of days in between occurrences" (L99001–99005). The page-load timing control is
  `shouldIgnoreGlobalDelay` (L99166–99172).
- **Audience is two independent gates.** `userProfileAccess` (`Everyone` | `SpecificProfiles`, 48.0+,
  L99317–99325) and `userAccess` (`Everyone` | `SpecificPermissions`, L99308–99316). Both are resolved by
  `uiFormulaRule` criteria; if `uiFormulaRule` is null "the in-app guidance displays by default"
  (L99299–99306).

---

## 1. Floating prompt on a record page, gated by a custom permission

`force-app/main/default/prompts/Renewal_Pilot_Notice.prompt-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Prompt xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Renewal Pilot Notice</masterLabel>
    <promptVersions>
        <body>Opportunities in the renewal pilot use the new Renewal Stage field. Set it before you move the record to Negotiation.</body>
        <description>Floating prompt, Opportunity record page. Pilot cohort only, gated on Renewal_Pilot custom permission.</description>
        <dismissButtonLabel>Got it</dismissButtonLabel>
        <displayPosition>BottomRight</displayPosition>
        <displayType>FloatingPanel</displayType>
        <isPublished>true</isPublished>
        <masterLabel>Renewal Pilot Notice</masterLabel>
        <shouldDisplayActionButton>false</shouldDisplayActionButton>
        <shouldIgnoreGlobalDelay>false</shouldIgnoreGlobalDelay>
        <startDate>2026-09-14</startDate>
        <endDate>2026-11-14</endDate>
        <targetPageKey1>Opportunity</targetPageKey1>
        <targetPageType>standard__recordPage</targetPageType>
        <timesToDisplay>3</timesToDisplay>
        <title>New: Renewal Stage</title>
        <userAccess>SpecificPermissions</userAccess>
        <userProfileAccess>Everyone</userProfileAccess>
        <versionNumber>1</versionNumber>
        <uiFormulaRule>
            <booleanFilter>1</booleanFilter>
            <criteria>
                <leftValue>{!$Permission.CustomPermission.Renewal_Pilot}</leftValue>
                <operator>EQUAL</operator>
                <rightValue>true</rightValue>
            </criteria>
        </uiFormulaRule>
    </promptVersions>
</Prompt>
```

UNVERIFIED (2026-09-04): `targetPageKey1` = `Opportunity` and `targetPageType` = `standard__recordPage`.
The Metadata API guide documents both fields as required but describes their contents only as "Used by
Salesforce to identify the prompt's page location" (L99206–99210, L99244–99248) and lists no valid values.
Treat these two lines as placeholders — retrieve a Setup-built prompt for the same page and copy its values
in before deploying. Everything else in this file is element-for-element from the field tables.

Notes on the gate:

- `operator` has exactly one valid value, `EQUAL` (L99394–99399). There is no `NOT EQUAL`, so "hide from
  users who have X" cannot be expressed; invert by gating on a second custom permission instead.
- `rightValue` is `true` for a permission and the *profile name* for a profile criterion (L99401–99410).
- `leftValue` accepts three expression forms only (L99372–99392): `{!$Permission.CustomPermission.<name>}`,
  `{!$Permission.StandardPermission.<name>}`, and `{!ENCODED:{!ID:$User.Profile.Key}}` (48.0+). No formula,
  no field reference, no record data.
- Permission expressions are "Supported for app, Home, and record pages only" (L99377–99378, L99383–99384).
- `booleanFilter` "Specifies the AND filter condition" (L99355–99359); criteria are numbered in document
  order, so `(1 AND 2) AND (3 OR 4)` refers to the first four `<criteria>` blocks.

---

## 2. Docked prompt with a video and an action button

`force-app/main/default/prompts/Renewal_Overview_Video.prompt-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Prompt xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Renewal Overview Video</masterLabel>
    <promptVersions>
        <actionButtonLabel>Open the runbook</actionButtonLabel>
        <actionButtonLink>https://example.my.salesforce.com/lightning/r/Knowledge__kav/ka0000000000000AAA/view</actionButtonLink>
        <body>&lt;p&gt;A three-minute tour of the renewal process: the new stage, the approval step, and where the checklist lives.&lt;/p&gt;</body>
        <description>Docked prompt with embedded video. Runs for the 30 days after go-live.</description>
        <displayType>DockedComposer</displayType>
        <header>Renewals: what changed</header>
        <isPublished>true</isPublished>
        <masterLabel>Renewal Overview Video</masterLabel>
        <shouldDisplayActionButton>true</shouldDisplayActionButton>
        <shouldIgnoreGlobalDelay>false</shouldIgnoreGlobalDelay>
        <startDate>2026-09-14</startDate>
        <endDate>2026-10-14</endDate>
        <targetPageKey1>Home</targetPageKey1>
        <targetPageType>standard__namedPage</targetPageType>
        <timesToDisplay>2</timesToDisplay>
        <title>Renewals: what changed</title>
        <userAccess>Everyone</userAccess>
        <userProfileAccess>SpecificProfiles</userProfileAccess>
        <versionNumber>1</versionNumber>
        <videoLink>https://www.youtube.com/embed/Ko-gcObzTVo</videoLink>
        <uiFormulaRule>
            <booleanFilter>1 OR 2</booleanFilter>
            <criteria>
                <leftValue>{!ENCODED:{!ID:$User.Profile.Key}}</leftValue>
                <operator>EQUAL</operator>
                <rightValue>Standard</rightValue>
            </criteria>
            <criteria>
                <leftValue>{!ENCODED:{!ID:$User.Profile.Key}}</leftValue>
                <operator>EQUAL</operator>
                <rightValue>custom_renewals_rep</rightValue>
            </criteria>
        </uiFormulaRule>
    </promptVersions>
</Prompt>
```

The same UNVERIFIED note from section 1 applies to `targetPageKey1` / `targetPageType` here.

Field constraints that bite on this shape:

| Element | Constraint | Guide line |
|---|---|---|
| `title` | Required, max 36 chars | L99295–99298 |
| `header` | Docked prompt only, max 36 chars — the label in the window's browser bar | L99069–99084 |
| `actionButtonLabel` | Max 25 chars | L98965–98966 |
| `actionButtonLink` | Max 1,000 chars; "You can't use the GROUP BY option in a SOQL query for this field" | L98968–98984 |
| `body` | Required. API 60.0+: up to 4,000 chars for **all** prompt types. Earlier: 240 for floating and targeted, 4,000 for docked. For docked prompts the maximum "include HTML markup, not just readable text" | L98986–98998 |
| `videoLink` | Embed URL, max 1,000 chars, 48.0+. "You can specify this field or the `image` field, but not both" | L99340–99347 |
| `dismissButtonLabel` | Floating or targeted prompt only, max 15 chars | L99012–99015 |
| `description` | Max 255 chars | L99007–99010 |

Because `body` is HTML for a docked prompt, `<` and `&` must be escaped (`&lt;`, `&amp;`) or the file will
not parse. A CDATA section works too.

---

## 3. Three-step walkthrough

A walkthrough is one `Prompt` with one `<promptVersions>` block per step. Step 1 carries the schedule; the
last step carries the action button.

`force-app/main/default/prompts/Renewal_Checklist.prompt-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Prompt xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Renewal Checklist Walkthrough</masterLabel>
    <promptVersions>
        <body>Start here. Renewal opportunities now need three things before they can be submitted.</body>
        <delayDays>7</delayDays>
        <description>Step 1 of 3. Floating, Opportunity record page. Carries the walkthrough schedule.</description>
        <displayPosition>TopRight</displayPosition>
        <displayType>FloatingPanel</displayType>
        <endDate>2026-12-14</endDate>
        <isPublished>true</isPublished>
        <masterLabel>Renewal Checklist Walkthrough</masterLabel>
        <shouldDisplayActionButton>false</shouldDisplayActionButton>
        <shouldIgnoreGlobalDelay>false</shouldIgnoreGlobalDelay>
        <startDate>2026-09-14</startDate>
        <stepNumber>1</stepNumber>
        <targetPageKey1>Opportunity</targetPageKey1>
        <targetPageType>standard__recordPage</targetPageType>
        <themeColor>Theme1</themeColor>
        <themeSaturation>Light</themeSaturation>
        <timesToDisplay>3</timesToDisplay>
        <title>Renewal checklist (1 of 3)</title>
        <userAccess>SpecificPermissions</userAccess>
        <userProfileAccess>Everyone</userProfileAccess>
        <versionNumber>1</versionNumber>
        <uiFormulaRule>
            <booleanFilter>1</booleanFilter>
            <criteria>
                <leftValue>{!$Permission.CustomPermission.Renewal_Pilot}</leftValue>
                <operator>EQUAL</operator>
                <rightValue>true</rightValue>
            </criteria>
        </uiFormulaRule>
    </promptVersions>
    <promptVersions>
        <body>Set Renewal Stage on the record. It drives the approval route, so an empty value stalls the submission.</body>
        <description>Step 2 of 3. Targeted at the Renewal Stage field on the Opportunity record page.</description>
        <displayType>Targeted</displayType>
        <elementRelativePosition>RightCenter</elementRelativePosition>
        <isPublished>true</isPublished>
        <masterLabel>Renewal Checklist Walkthrough</masterLabel>
        <shouldDisplayActionButton>false</shouldDisplayActionButton>
        <stepNumber>2</stepNumber>
        <targetPageKey1>Opportunity</targetPageKey1>
        <targetPageType>standard__recordPage</targetPageType>
        <title>Renewal checklist (2 of 3)</title>
        <versionNumber>1</versionNumber>
    </promptVersions>
    <promptVersions>
        <actionButtonLabel>Open the runbook</actionButtonLabel>
        <actionButtonLink>https://example.my.salesforce.com/lightning/r/Knowledge__kav/ka0000000000000AAA/view</actionButtonLink>
        <body>Attach the signed renewal quote, then submit. The full runbook is one click away.</body>
        <description>Step 3 of 3. Targeted at the Submit for Approval action. Carries the action button.</description>
        <displayType>Targeted</displayType>
        <elementRelativePosition>BottomLeft</elementRelativePosition>
        <isPublished>true</isPublished>
        <masterLabel>Renewal Checklist Walkthrough</masterLabel>
        <shouldDisplayActionButton>true</shouldDisplayActionButton>
        <stepNumber>3</stepNumber>
        <targetPageKey1>Opportunity</targetPageKey1>
        <targetPageType>standard__recordPage</targetPageType>
        <title>Renewal checklist (3 of 3)</title>
        <versionNumber>1</versionNumber>
    </promptVersions>
</Prompt>
```

The same UNVERIFIED note from section 1 applies to `targetPageKey1` / `targetPageType` on all three steps.

What the guide pins down about this shape:

- Up to 10 steps, "Numbers must be consecutive without repeated or skipped numbers" (L99193–99196). A gap
  or a repeat is a deploy-time problem, not a runtime one.
- `versionNumber` is `1` on every step. It does not increment per step (L99326–99329).
- `elementRelativePosition` positions a targeted prompt against its element (52.0+) and takes twelve
  values: `BottomCenter`, `BottomLeft`, `BottomRight`, `LeftBottom`, `LeftCenter`, `LeftTop`,
  `RightBottom`, `RightCenter`, `RightTop`, `TopCenter`, `TopLeft`, `TopRight` (L99045–99065).
- `referenceElementContext` is how Salesforce identifies the anchored element (52.0+, L99155–99160). It is
  written by targeting mode in Setup, not authored by hand — which is why targeted steps are built in the
  org and then retrieved.
- `themeColor` requires `themeSaturation` and vice versa (L99250–99275), and both go on step 1.

---

## 4. Scheduling and frequency

Every scheduling element lives on the same `<promptVersions>` entry (step 1 for a walkthrough). This
fragment is the schedule block from section 3, isolated:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Prompt xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Schedule Fragment</masterLabel>
    <promptVersions>
        <body>Body is required on every version.</body>
        <delayDays>7</delayDays>
        <displayType>FloatingPanel</displayType>
        <endDate>2026-12-14</endDate>
        <isPublished>true</isPublished>
        <masterLabel>Schedule Fragment</masterLabel>
        <publishedDate>2026-09-14</publishedDate>
        <shouldIgnoreGlobalDelay>true</shouldIgnoreGlobalDelay>
        <startDate>2026-09-14</startDate>
        <targetPageKey1>Home</targetPageKey1>
        <targetPageType>standard__namedPage</targetPageType>
        <timesToDisplay>4</timesToDisplay>
        <title>Schedule Fragment</title>
        <versionNumber>1</versionNumber>
    </promptVersions>
</Prompt>
```

| Element | What it actually controls | Guide line |
|---|---|---|
| `startDate` | Date to start showing. Required in API 48.0 and earlier; optional after | L99172–99181 |
| `endDate` | Date to stop showing | L99066–99070 |
| `delayDays` | **Days between occurrences.** Required if recurrences are scheduled | L99001–99005 |
| `timesToDisplay` | Maximum number of times to show it. **Maximum value 30.** Required if recurrences are scheduled. "Salesforce detects whether the user interacts with the in-app guidance, then determines whether to show the in-app guidance again or cancel scheduled recurrences" | L99276–99294 |
| `shouldIgnoreGlobalDelay` | `true` = ignore the org's global time delay and show on page load (48.0+) | L99166–99172 |
| `publishedDate` | Date it was activated. "If installed from a package, this value is the date when the package was installed" | L99148–99154 |

`timesToDisplay` of `4` with `delayDays` of `7` is "up to four showings, a week apart, unless the user
interacts with it first". There is no `Once` / `Daily` / `Weekly` enum in the metadata — the Setup UI's
frequency choices resolve to this pair.

---

## 5. The custom permission the gate depends on

Two files. Neither is optional: a `uiFormulaRule` that names a custom permission nobody holds resolves
false for everyone, and the prompt simply never shows.

`force-app/main/default/customPermissions/Renewal_Pilot.customPermission-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Marks a user as part of the renewal-process pilot cohort. Read by in-app guidance uiFormulaRule gates and by the Renewal Stage validation rule.</description>
    <isLicensed>false</isLicensed>
    <label>Renewal Pilot</label>
</CustomPermission>
```

`force-app/main/default/permissionsets/Renewal_Pilot.permissionset-meta.xml` — fragment, the two elements
that matter here:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Renewal pilot cohort. Assign for the duration of the pilot, then remove.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Renewal Pilot</label>
    <customPermissions>
        <enabled>true</enabled>
        <name>Renewal_Pilot</name>
    </customPermissions>
</PermissionSet>
```

`PermissionSetCustomPermissions` takes exactly `enabled` and `name`, both required, and "Only enabled
custom permissions are retrieved" (L94943–94951) — a `<customPermissions>` block with
`<enabled>false</enabled>` will not come back on the next retrieve, so it cannot be used to record intent.
See `admin/custom-permissions` for the naming and dependency rules.

---

## 6. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Renewal_Pilot_Notice</members>
        <members>Renewal_Overview_Video</members>
        <members>Renewal_Checklist</members>
        <name>Prompt</name>
    </types>
    <types>
        <members>Renewal_Pilot</members>
        <name>CustomPermission</name>
    </types>
    <types>
        <members>Renewal_Pilot</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

`Prompt` supports the `*` wildcard (L99508–99510), and so does `CustomPermission` (L46738–46740). The
guide's own sample manifest for `Prompt` uses `<members>*</members>` with `<version>46.0</version>`
(L99490–99497) — wildcard it to audit what an inherited org already has, name members explicitly to deploy.

Order inside one package, resolved automatically by a single `sf project deploy start`:

1. `CustomPermission` — the `uiFormulaRule` `leftValue` is a reference, not a definition.
2. `PermissionSet` — cannot enable a custom permission that does not exist yet.
3. `Prompt`.

---

## 7. Retrieve and deploy

```bash
# Harvest the opaque page keys and referenceElementContext: build one prompt of each
# shape in a sandbox with Setup > In-App Guidance, then pull it.
sf project retrieve start --metadata Prompt --target-org my-sandbox
sf project retrieve start --metadata Prompt:Renewal_Checklist --target-org my-sandbox

python3 skills/admin/in-app-guidance-and-walkthroughs/scripts/check_in_app_guidance_and_walkthroughs.py \
  --manifest-dir force-app/main/default

sf project deploy start --manifest manifest/package.xml --target-org my-sandbox --dry-run
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

Targeted prompts are the reason step one is not optional. `referenceElementContext` is "Used by Salesforce
to identify the element that the targeted prompt is associated with" (L99155–99160) and there is no
documented syntax for writing one by hand. Author targeted steps in targeting mode, retrieve, then treat
the retrieved file as source.

Deploying a file with `<isPublished>true</isPublished>` deploys an **active** prompt (L99133–99138). If a
release must land dark, deploy with `false` and flip it in Setup, or hold the activation until the
`startDate` you shipped.

---

## 8. Verify after deploy

Setup check first, then the objects.

1. **Setup → User Interface → In-App Guidance** — all three prompts are listed; the walkthrough shows three
   steps; the active flag matches the `isPublished` you deployed.
2. **Log in as a pilot user, not as the admin.** The admin almost certainly does not hold `Renewal_Pilot`,
   so the gated prompt is *supposed* to be invisible to you. Assign the permission set to a test user first.

Then query engagement. `PromptAction` is one row per user per prompt version, and it is the only record of
what users did (object_reference.txt L234826–235013):

```sql
-- Engagement for one prompt version: views, action clicks, dismissals, snoozes.
SELECT PromptVersionId, COUNT(Id) users,
       SUM(TimesDisplayed) displays,
       SUM(TimesActionTaken) actions,
       SUM(TimesDismissed) dismissals,
       SUM(TimesSnoozed) snoozes
FROM PromptAction
WHERE LastDisplayDate >= 2026-09-14T00:00:00Z
GROUP BY PromptVersionId
```

```sql
-- Where a walkthrough is being abandoned: last step reached, per outcome.
-- LastResult values: CustomAction, Dismiss, Error, Finish (walkthroughs only),
-- NoAction, NotSeen, Snooze (object_reference.txt L234848-234875).
SELECT StepNumber, StepCount, LastResult, COUNT(Id) users
FROM PromptAction
WHERE Name = 'Renewal Checklist Walkthrough'
GROUP BY StepNumber, StepCount, LastResult
ORDER BY StepNumber
```

```sql
-- Individual users who never finished, for a targeted follow-up.
SELECT UserId, User.Name, StepNumber, LastResult, LastResultDate, SnoozeUntil
FROM PromptAction
WHERE Name = 'Renewal Checklist Walkthrough'
  AND LastResult != 'Finish'
ORDER BY LastResultDate DESC
```

`PromptError` is the diagnostic table and the reason "the prompt broke silently" is not the whole story
(object_reference.txt L235018–235103):

```sql
-- Broken prompts. ReferenceElementNotFound means the anchored element moved or is gone
-- and the targeted prompt has fallen back to a floating prompt.
SELECT Type, StepNumber, IsError, COUNT(Id) occurrences
FROM PromptError
GROUP BY Type, StepNumber, IsError
ORDER BY COUNT(Id) DESC
```

`Type` takes four values, each naming a distinct failure (L235086–235100): `NoAccessToApp`,
`NoAccessToPage`, `ReferenceElementNotFound`, and `Unavailable` (users opened a walkthrough by URL while it
was inactive or they were unlicensed). `IsError` distinguishes an error (`true`) from a warning (`false`).
Run this query after every page-layout or Lightning-page deploy — it is the anchor audit.
