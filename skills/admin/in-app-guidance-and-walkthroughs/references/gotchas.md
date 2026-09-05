# Gotchas — In-App Guidance and Walkthroughs

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Line citations are into the Summer '26 / v62 PDFs: `api_meta` = Metadata API Developer Guide
(https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf), `object_reference` =
Object Reference (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf).

## Gotcha 1: A Targeted Prompt Whose Anchor Disappears Turns Into a Floating Prompt

**What happens:** The prompt does not vanish and it does not error to the user. Salesforce degrades it:
"The target element has moved or is no longer on your page. Targeted prompts attached to unavailable
elements convert to floating prompts" (`object_reference` L235092–235095). What the user sees is a
context-free card floating on the page, still telling them to "click this field" with nothing pointed at.
That reads as a broken org rather than a missing prompt, which is why nobody reports it as a guidance bug.

The platform *does* record it. A `PromptError` row is written with `Type = ReferenceElementNotFound`
(`object_reference` L235018–235103). Nothing surfaces it to the admin — there is no Setup warning, no
email, no notification — but the row exists and is queryable, so this is a monitoring gap, not an
invisible failure.

**When it occurs:** After any change that moves or removes the anchored element — a page-layout edit, a
Lightning page rebuild, a Dynamic Forms migration that replaces the layout section the field sat in, or a
managed-package upgrade that swaps a component. The binding lives in `referenceElementContext`, which the
guide describes only as "Used by Salesforce to identify the element that the targeted prompt is associated
with" (`api_meta` L99155–99160); it is written by targeting mode and is opaque to review.

**How to avoid:** Query `PromptError` grouped by `Type` after every layout or FlexiPage deploy — the query
is in `references/metadata-examples.md` section 8. Add it to the post-deploy check, not to a quarterly
audit, because the degraded prompt is live from the moment the layout lands. Record the anchor element in
each targeted step's `description` (max 255 chars, `api_meta` L99007–99010) so the fix is possible without
re-deriving what the prompt was pointing at.

---

## Gotcha 2: Active Walkthrough Slot Is Consumed at Publish, Not at First User View

**What happens:** The free-tier limit for active walkthroughs is counted against all currently active
(published and scheduled) walkthroughs, regardless of whether any user has actually triggered them. An org
with legacy walkthroughs from a prior admin — even ones no user has seen in months — cannot publish a new
walkthrough until one is deactivated.

UNVERIFIED (2026-09-04): the "3 active walkthroughs on the free tier" figure. It comes from the existing
"Limits for In-App Guidance" Salesforce Help citation in `references/well-architected.md`;
help.salesforce.com cannot be fetched, the v62 Metadata API guide states no such cap, and the Salesforce
App Limits cheat sheet has no prompt entry at all. Confirm the current number against your org's own
Setup page before planning around it.

**When it occurs:** When a new admin inherits an org and tries to create the first walkthrough, or when a
project produces several walkthroughs sequentially without deactivating older ones. Salesforce's error
("You've reached the limit") does not explain that deactivating an existing walkthrough resolves it.

**How to avoid:** Before creating a walkthrough, retrieve `Prompt` with the `*` wildcard (`api_meta`
L99508–99510) and count the entries whose first step has `<isPublished>true</isPublished>`. That is a
faster and more auditable count than the Setup list, and it also shows you the stale ones with an
`endDate` already in the past.

---

## Gotcha 3: Audience Targeting Is Not Profile-Only — Permissions Are the Better Gate

**What happens:** Admins design around the belief that only profiles can be targeted, then either
over-deliver a prompt to everyone sharing a profile or abandon in-app guidance for the cohort entirely.
The metadata supports two independent gates. `userProfileAccess` takes `Everyone` or `SpecificProfiles`
(`api_meta` L99317–99325) and `userAccess` takes `Everyone` or `SpecificPermissions`, where
`SpecificPermissions` means "only users with all the specific user permissions specified can see the
in-app guidance" (`api_meta` L99308–99316). Both resolve through `uiFormulaRule` criteria whose `leftValue`
accepts `{!$Permission.CustomPermission.<name>}` and `{!$Permission.StandardPermission.<name>}` alongside
the profile expression (`api_meta` L99372–99392).

A custom permission is granted by a permission set, so "target this prompt at exactly the pilot cohort" is
a solved problem: create the custom permission, assign the permission set, gate the prompt on it.

**When it occurs:** Whenever the intended audience is a project cohort, a pilot group, or a role that does
not map to a profile — which is most adoption work in an org that consolidated profiles.

**How to avoid:** Reach for a custom permission first and treat profile criteria as the fallback. Two
constraints shape the design: `operator` has one valid value, `EQUAL` (`api_meta` L99394–99399), so there
is no way to express "hide from users who have X" — invert by gating on a second permission. And
permission expressions are "Supported for app, Home, and record pages only" (`api_meta` L99377–99384), so
a prompt on some other page type cannot use them. See `admin/custom-permissions` for the permission design
and `references/metadata-examples.md` section 5 for the two files the gate needs.

---

## Gotcha 4: Republishing Does Not Reset Analytics — Only Display State

**What happens:** When an admin deactivates and republishes a walkthrough (a common pattern for quarterly
compliance reminders), the `PromptAction` records from the original publication are not deleted. Adoption
reports show cumulative rows spanning both publish cycles, and the aggregate counters make it worse:
`TimesDisplayed`, `TimesActionTaken`, `TimesDismissed`, and `TimesSnoozed` are running totals per user per
prompt version, not per-cycle counts (`object_reference` L234958–235012). A user who saw the Q1 version
four times starts Q2 at four.

**When it occurs:** Any time the "deactivate and republish" pattern is used for recurring prompts.

**How to avoid:** Filter `PromptAction` reports by `LastDisplayDate >= [publication date]` rather than by
`CreatedDate`, and read `LastResult` / `LastResultDate` (the most recent interaction and when) instead of
the `Times*` totals when you need "what happened this cycle". If per-cycle totals genuinely matter,
publish a new `Prompt` rather than republishing the old one — a new prompt means a new `PromptVersionId`
and a clean set of rows.

---

## Gotcha 5: Lightning Experience and *Supported* Experience Cloud Pages — Classic Is Excluded

**What happens:** In-App Guidance does not render in Salesforce Classic. It does render in Experience Cloud
— both guides say so directly: prompts are added "in Lightning Experience pages or apps or in supported
Experience Cloud site pages" (`object_reference` L234829–234831), and the Prompt type's access rules cover
managing guidance "in Lightning Experience or in Experience Cloud sites" (`api_meta` L98931–98933). Teams
that ruled out in-app guidance for a partner community on the belief it was Lightning-only ruled it out
for the wrong reason.

UNVERIFIED (2026-09-04): *which* Experience Cloud pages are supported. Both guides say "supported" without
enumerating; the detail sits in the Considerations for Creating In-App Guidance help article, which cannot
be fetched. Prove it in a sandbox site before committing a partner-facing rollout to it.

**When it occurs:** In orgs that have not fully migrated off Classic, and in any partner or customer
portal rollout where the guidance decision was made from a summary rather than the type documentation.

**How to avoid:** Confirm Classic users are not in the audience — for them there is no fallback, so the
guidance has to be delivered another way. For Experience Cloud, build one prompt in a sandbox site and
confirm it renders on the actual page before planning around it. Watch for `PromptError` rows of type
`NoAccessToApp` and `NoAccessToPage`, which are exactly the "some of your users don't have access to that
step's app/page" case (`object_reference` L235088–235091).

---

## Gotcha 6: Walkthrough Step Numbers Must Be Consecutive, and `versionNumber` Is Always 1

**What happens:** Two integers on `promptVersions` look interchangeable and are not. `stepNumber` is
"Required for walkthroughs only… Include up to 10 steps. Numbers must be consecutive without repeated or
skipped numbers" (`api_meta` L99190–99196). `versionNumber` is required on every entry and "The number
remains 1 since multiple versions aren't saved in the org" (`api_meta` L99326–99329) — it is not a step
counter, not a revision counter, and incrementing it per step is the single most common hand-authoring
error. A file that numbers steps 1, 2, 4 (because step 3 was deleted during review) is malformed for the
same reason.

**When it occurs:** When a walkthrough is hand-edited rather than retrieved — deleting a middle step,
reordering steps, or merging two walkthroughs into one file. Also when an LLM generates the file and maps
"version 1, version 2, version 3" onto the three steps.

**How to avoid:** Renumber `stepNumber` from 1 after any step deletion, and set `versionNumber` to `1` on
every entry without exception. `scripts/check_in_app_guidance_and_walkthroughs.py` checks both.

---

## Gotcha 7: `delayDays` Is Days Between Recurrences, Not a Page-Load Delay

**What happens:** `delayDays` reads like the Setup UI's "delay before the prompt appears" and is not. The
guide defines it as "Required if recurrences are scheduled. Number of days in between occurrences"
(`api_meta` L99001–99005). Setting `<delayDays>3</delayDays>` expecting a three-second render delay
produces a prompt that reappears every three days instead. The control that governs *render* timing is
`shouldIgnoreGlobalDelay`: `true` means the guidance "ignores the global time delay and instead shows on
page load" (`api_meta` L99166–99172) — a single org-wide setting, not a per-prompt number of seconds.

The frequency pair also has a ceiling and a behaviour worth knowing: `timesToDisplay` has a "Maximum value
of 30", and "Salesforce detects whether the user interacts with the in-app guidance, then determines
whether to show the in-app guidance again or cancel scheduled recurrences" (`api_meta` L99276–99294). An
engaged user stops seeing it before the count is exhausted; that is by design, and it means displayed
counts will legitimately differ across users.

**When it occurs:** Any hand-authored or generated prompt file, and any migration of a Setup-built prompt
between orgs where someone "cleans up" the scheduling values on the way through.

**How to avoid:** Read the two fields as what they are — `delayDays` + `timesToDisplay` is the recurrence
schedule; `shouldIgnoreGlobalDelay` is the on-load behaviour. There is no `Once` / `Daily` / `Weekly` enum
in the metadata: "once per user" is `timesToDisplay` of 1 with no `delayDays`.

---

## Gotcha 8: `isPublished` True in a Deploy Means Live on Arrival

**What happens:** `isPublished` "Indicates whether the in-app guidance is active (`true`) or not (`false`)"
(`api_meta` L99133–99138). It is an ordinary metadata field with no separate activation step, so a
`Prompt` deployed with `true` is showing to its audience the moment the deploy finishes — during a release
window, in front of users who have not had the training yet, and possibly before the feature the prompt
describes is itself live.

`startDate` is the only brake, and only if you set it: it is optional in API 49.0 and later, required in
48.0 and earlier (`api_meta` L99172–99181). Omit it and there is no future-dating at all.

**When it occurs:** On any deploy that includes prompts retrieved from a sandbox where they were already
active — which is every prompt retrieved after being built and tested, because they had to be published to
be tested.

**How to avoid:** Decide the activation model before the deploy. Either ship `<isPublished>false</isPublished>`
and flip it in Setup after the release is verified, or ship `true` with a `startDate` on or after go-live.
For a walkthrough, `startDate` and `endDate` go on the first step only (`api_meta` L99066–99068,
L99177–99181) — putting them on step 3 silently does nothing.

---

## Gotcha 9: Media Fields Are Mutually Exclusive and `imageAltText` Is Conditionally Required

**What happens:** A prompt can carry an image or a video, never both. `videoLink` is "The embed URL for a
video in a docked prompt… You can specify this field or the `image` field, but not both" (`api_meta`
L99340–99347), and `image` (a contentAsset developer name) and `imageLink` (a URL, 53.0+) are themselves
mutually exclusive (`api_meta` L99086–99090). On top of that, `imageAltText` is "Required if
`imageLocation`, `imageLink`, or `image` is specified" and `imageLocation` is required if any of
`image`, `imageLink`, or `imageAltText` is specified (`api_meta` L99092–99096 and L99104–99112) — a two-way dependency that
a partial hand-edit breaks in both directions.

`imageLocation` also has a type-specific restriction: `Right` and `Left` are "for floating or targeted
prompts only" (`api_meta` L99109–99112), so a docked prompt with a side image is not a valid shape.

One documentation trap on top: the guide's own Declarative Metadata Sample Definition writes
`<videolink>` in lowercase (`api_meta` L99450) while the field table names it `videoLink` (`api_meta`
L99340). Copy the sample verbatim and the element does not match the field.

**When it occurs:** Whenever a prompt is enriched after the fact — "add a screenshot to the video prompt",
"swap the image for a video" — and only the new element is added without removing the old one.

**How to avoid:** Treat media as one slot. When switching, delete the old element rather than adding
alongside. When adding any image element, add all three (`image` or `imageLink`, plus `imageAltText`, plus
`imageLocation`) in the same edit. Use the field table's `videoLink` casing, not the sample's.

---

## Gotcha 10: `body` Length Depends on the Package API Version, Not the Org

**What happens:** The body ceiling moved. "In API version 60.0 and later, enter up to 4,000 characters for
all prompt types. In earlier API versions, enter up to 240 characters for floating prompts and targeted
prompts. Enter up to 4,000 characters for docked prompts" (`api_meta` L98986–98998). The version that
counts is the `<version>` element in the `package.xml` used for the deploy, so the same 900-character
floating prompt deploys cleanly on a v62 manifest and fails on an inherited v58 one. Nothing about the org
changes; the manifest does.

For docked prompts there is a second edge: "the maximum characters include HTML markup, not just readable
text" (`api_meta` L98994–98998). A 3,000-character message wrapped in tables and inline styles can exceed
4,000 while looking short.

**When it occurs:** In repos with an old pinned `sourceApiVersion` or a hand-maintained manifest, and in
any docked prompt whose copy was authored in a rich-text editor.

**How to avoid:** Pin the manifest at 60.0 or later before writing long bodies, and count the rendered
HTML — not the visible text — when sizing docked-prompt copy.
