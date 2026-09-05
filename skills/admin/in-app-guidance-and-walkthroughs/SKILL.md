---
name: in-app-guidance-and-walkthroughs
description: "Configuring Salesforce In-App Guidance: floating, docked, and targeted prompts, multi-step walkthroughs, audience targeting, scheduling, and adoption analytics. Use when designing user onboarding or feature adoption programs in Lightning Experience. Covers the Prompt metadata type, promptVersions, displayType, uiFormulaRule, stepNumber, isPublished, PromptAction and PromptError. NOT for guidance on a record's Path — use admin/path-and-guidance. NOT for adoption and training — use admin/change-management-and-training."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "how do I create a walkthrough to guide users through a new process in Salesforce"
  - "set up in-app prompts to help users adopt a feature without a training session"
  - "targeted prompt is not showing up for users on the opportunity page"
  - "what is the limit on custom walkthroughs before needing a Sales Enablement license"
  - "configure audience filtering for in-app guidance by profile"
  - "deploy a Prompt metadata file with sf project deploy start"
  - "targeted prompt turned into a floating prompt after a page layout change"
  - "restrict an in-app prompt to users with a custom permission using uiFormulaRule"
  - "walkthrough step numbers must be consecutive without repeated or skipped numbers"
  - "query PromptAction to report on prompt views dismissals and walkthrough completions"
  - "prompt went live the moment I deployed it isPublished"
tags:
  - in-app-guidance
  - walkthroughs
  - prompts
  - user-adoption
  - onboarding
  - lightning-experience
inputs:
  - Target Lightning Experience page and UI element anchor (for targeted prompts)
  - Audience definition — the custom permission, permission set, or profiles that scope it
  - Walkthrough step content and display type (FloatingPanel, DockedComposer, Targeted)
  - Scheduling window (startDate, endDate, timesToDisplay, delayDays)
  - Whether Sales Enablement license is provisioned
outputs:
  - Deployable `prompts/<Name>.prompt-meta.xml` and its package.xml entry
  - The custom permission and permission set that the uiFormulaRule gate resolves against
  - Adoption tracking queries against the PromptAction and PromptError standard objects
  - Recommendations on prompt type selection and step count
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# In-App Guidance and Walkthroughs

This skill activates when a practitioner needs to design, configure, or troubleshoot Salesforce In-App Guidance — the platform's native mechanism for delivering contextual prompts and multi-step walkthroughs to users directly inside Lightning Experience. It covers prompt type selection, walkthrough authoring, audience filtering, scheduling, limit management, and adoption analytics.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the rendering surface.** In-App Guidance does not function in Salesforce Classic. It *does* work in supported Experience Cloud site pages — both the Metadata API guide and the Object Reference say so — so a partner-portal rollout is not automatically ruled out. See `references/gotchas.md` Gotcha 5 for the exact wording and what remains unverified.
- **Identify how many active custom walkthroughs the org already has.** The free tier is documented as 3 active walkthroughs, with more requiring a Sales Enablement license; prompts installed by AppExchange managed packages are exempt. UNVERIFIED (2026-09-04): both the 3-slot figure and the licence requirement rest on the Salesforce Help "Limits for In-App Guidance" article, which cannot be fetched; the v62 Metadata API guide and the App Limits cheat sheet state no such cap. Count the org's own active prompts before planning around it.
- **Decide the audience gate.** Targeting is *not* profile-only. `userAccess` = `SpecificPermissions` plus a `uiFormulaRule` on `{!$Permission.CustomPermission.<name>}` targets an arbitrary cohort; the profile expression is the fallback, not the only option.
- **Identify the anchor element for any targeted prompt.** If the anchor is removed or moved, the targeted prompt does not disappear — it degrades into a floating prompt and writes a `PromptError` row of type `ReferenceElementNotFound`. Nothing notifies the admin, so the query has to be run.
- **Decide the activation model before the deploy.** `isPublished` is a plain metadata field. Deploying `true` makes the prompt live on arrival.

## Questions to Ask Before Configuring

Ask these before opening Setup; the answers decide the metadata, and an LLM that skips them produces a prompt that deploys cleanly and reaches the wrong people at the wrong time.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who exactly should see this — and is that group a profile?" | Decides `userAccess` vs `userProfileAccess`, and whether a custom permission has to be built first | The `uiFormulaRule` criteria list, plus the `CustomPermission` + `PermissionSet` files the gate needs |
| "What page does this sit on, and does anyone have a prompt on it already?" | `targetPageType` / `targetPageKey1` are required and opaque — they can only be harvested from a retrieve. Permission-based criteria work on app, Home, and record pages only | The sandbox prompt to build and retrieve, and confirmation the gate is even usable on that page |
| "Is it anchored to a specific element, or is it just a message?" | A targeted prompt takes a maintenance dependency on the page layout; a floating one does not | A `displayType` decision, and — if `Targeted` — the anchor recorded in `description` and added to the post-deploy `PromptError` check |
| "Should this go live on deploy, or later?" | `isPublished` has no separate activation step; `startDate` is optional after API 49.0 | Either `isPublished` false plus a manual flip, or true plus a `startDate` on or after go-live |
| "How many times should one user see it, and how far apart?" | There is no Once/Daily/Weekly enum — the Setup choices resolve to `timesToDisplay` (max 30) and `delayDays` (days, not seconds) | Two integers instead of a frequency word, and the knowledge that engaged users stop seeing it early by design |
| "How will we know whether it worked, and who owns that read?" | `PromptAction` is the only record of engagement, and its `Times*` fields are lifetime totals that survive a republish | A named owner, a query filtered on `LastDisplayDate`, and a decision date to extend or retire |
| "What layout or Lightning-page changes are in flight for this page?" | A layout deploy can silently degrade a targeted prompt on the same release | The anchor added to the release's dependency list |

What a proper configuration adds over just building it in Setup: the audience is a permission you can grant and revoke rather than a profile you cannot narrow, the prompt goes live when the feature does rather than when the deploy lands, and a broken anchor is caught by a post-deploy query instead of by a user asking why a card is floating in the corner.

---

## Core Concepts

### One Metadata Type

Everything in this domain is the `Prompt` metadata type, stored at `prompts/<Name>.prompt-meta.xml`. A `Prompt` holds a `masterLabel` and a list of `promptVersions`. A single prompt is one `promptVersions` entry; a walkthrough is several, each with a `stepNumber`. There is no separate walkthrough type and no `isWalkthrough` flag. `versionNumber` is always `1`.

Full deployable shapes are in `references/metadata-examples.md`.

### Prompt Types

Three values of the required `displayType` field:

| `displayType` | What it is | Use it for |
|---|---|---|
| `FloatingPanel` | A repositionable card. `displayPosition` places it in one of six page corners/edges. Supports `dismissButtonLabel`. | Org-wide announcements and explanatory steps that reference no specific element |
| `DockedComposer` | Anchored to the bottom corner. Carries `header` (the label in the window's browser bar) and is the only type that takes `videoLink`. | Feature demo video, richer content, lower workflow intrusion |
| `Targeted` | Anchored to a UI element via `referenceElementContext`, positioned by `elementRelativePosition`. API 52.0+. | Guiding a user to a precise field, button, or component |

`Targeted` is the highest-signal type and the only one that takes a maintenance dependency on the page layout. `referenceElementContext` is written by Setup's targeting mode and has no documented hand-authoring syntax — targeted steps are built in the org and retrieved, not written from scratch.

### Walkthroughs

A walkthrough is up to 10 steps, and step numbers must be consecutive with no repeats and no gaps. Salesforce's own adoption guidance recommends 5 or fewer; completion rates drop sharply beyond that.

Where a value goes matters, because a walkthrough's settings are not evenly distributed:

- **First step:** `startDate`, `endDate`, `delayDays`, `timesToDisplay`, `publishedDate`, `themeColor`, `themeSaturation`
- **Last step:** `actionButtonLabel`, `actionButtonLink`
- **Every step:** `body`, `masterLabel`, `title`, `displayType`, `versionNumber`, `targetPageType`, `targetPageKey1`

Walkthroughs count against the active walkthrough limit. A walkthrough is counted as active from the moment it is published, not when a user views it. Deactivating one frees the slot.

### Audience

Two independent enums, both resolved through `uiFormulaRule`:

- `userProfileAccess` — `Everyone` or `SpecificProfiles` (API 48.0+)
- `userAccess` — `Everyone` or `SpecificPermissions`

A `uiFormulaRule` holds a `booleanFilter` string and a list of `criteria`. Each criterion is a `leftValue` / `operator` / `rightValue` triple. `operator` accepts only `EQUAL`. `leftValue` accepts exactly three expression forms:

```text
{!$Permission.CustomPermission.<name>}    rightValue: true    app, Home, record pages only
{!$Permission.StandardPermission.<name>}  rightValue: true    app, Home, record pages only
{!ENCODED:{!ID:$User.Profile.Key}}        rightValue: <profile name>   API 48.0+
```

If `uiFormulaRule` is null, the guidance displays to everyone by default. Because there is no negative operator, "everyone except X" has to be expressed as a positive gate on a second custom permission. See `admin/custom-permissions` for the permission design.

### Scheduling

There is no Once / Daily / Weekly enum in the metadata. The Setup UI's frequency choices resolve to two integers plus a boolean:

- `startDate` / `endDate` — the eligibility window. `startDate` is optional in API 49.0+ and required in 48.0 and earlier.
- `timesToDisplay` — maximum showings per user, capped at 30. Salesforce cancels remaining recurrences once the user interacts, so "up to 3" often means one.
- `delayDays` — **days between occurrences**, not seconds before render.
- `shouldIgnoreGlobalDelay` — `true` skips the org's global time delay and shows on page load.

"Once per user" is `timesToDisplay` of 1 with no `delayDays`.

### Analytics

`PromptAction` is one row per user per prompt version and is the only record of engagement. It carries `TimesDisplayed`, `TimesActionTaken`, `TimesDismissed`, `TimesSnoozed`, `LastDisplayDate`, `LastResultDate`, `StepNumber`, `StepCount`, `SnoozeUntil`, and `LastResult` — whose values are `CustomAction`, `Dismiss`, `Error`, `Finish` (walkthroughs only), `NoAction`, `NotSeen`, and `Snooze`.

`PromptError` is the diagnostic companion, one row per failure, with `Type` in `NoAccessToApp`, `NoAccessToPage`, `ReferenceElementNotFound`, `Unavailable`. This is the table that tells you a targeted prompt's anchor is gone. Queries for both are in `references/metadata-examples.md` section 8.

---

## Common Patterns

### Pattern: Onboarding Walkthrough for a New Process

**When to use:** A new business process has been deployed — new fields, a new quick action, a changed approval flow — and you need users to understand the new steps without a live training session.

**How it works:**
1. Build the custom permission and permission set for the cohort first, so the gate has something to resolve against.
2. Open Setup > In-App Guidance and build the walkthrough against the live UI, using targeting mode for any anchored step.
3. Keep it to 5 steps or fewer. Use `Targeted` for precise anchors and `FloatingPanel` for explanatory steps.
4. Retrieve the prompt (`sf project retrieve start --metadata Prompt:<Name>`) — this is how you get real `targetPageKey1` / `targetPageType` / `referenceElementContext` values into source control.
5. Edit the retrieved file for the audience gate and schedule, run the checker, and deploy to the next environment.
6. Verify as a cohort user, not as the admin — the admin will usually not hold the gating permission and is *supposed* to see nothing.

**Why not just a floating announcement:** A single prompt can announce a change but cannot guide a multi-step interaction. Sequential in-context instruction is what raises task completion.

### Pattern: Feature Adoption Prompt with Video

**When to use:** You want to announce a new feature with a short demo video — common for Salesforce seasonal release updates or internal tooling launches.

**How it works:**
1. Use `displayType` of `DockedComposer` — it is the only type that takes `videoLink`.
2. Set `videoLink` to the *embed* URL, max 1,000 characters. Do not also set `image`; the two are mutually exclusive.
3. Set `header` (max 36 chars) as well as `title` — docked prompts show both.
4. Gate on the cohort and set a 30-day `endDate` so the announcement retires itself.
5. Leave `shouldIgnoreGlobalDelay` false so the prompt does not compete with the initial page render.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Announcing an org-wide change to all users | `FloatingPanel`, `uiFormulaRule` omitted | Null rule means it displays by default; no gate to maintain |
| Guiding users through a specific field or button | `Targeted`, built in targeting mode and retrieved | `referenceElementContext` cannot be hand-authored |
| Delivering a feature demo video | `DockedComposer` with `videoLink` | Only type that supports video; less intrusive than a modal |
| Multi-step process adoption | Walkthrough (up to 5 steps) | Sequential guidance; higher completion than a single prompt |
| Audience is a pilot or project cohort, not a profile | `userAccess` = `SpecificPermissions` + custom permission criterion | Grantable and revocable per user via a permission set |
| Audience is "everyone except group X" | Positive gate on a second custom permission | `operator` accepts only `EQUAL`; there is no negation |
| Page is not an app, Home, or record page | Profile criterion, or no gate | Permission expressions are unsupported on other page types |
| Org already at the active walkthrough limit | Deactivate a stale walkthrough (`isPublished` false) to free the slot, or use single-step prompts | Single prompts do not consume walkthrough slots |
| Prompt must not go live with the deploy | Ship `isPublished` false, or true with a future `startDate` | There is no separate activation step after deploy |

---

## Recommended Workflow

1. **Answer the Questions table above**, then read `references/gotchas.md` — Gotcha 3 (audience is not profile-only) and Gotcha 8 (`isPublished` is live on arrival) change the design, not just the review.
2. **Build the audience gate first.** Create the `CustomPermission` and the `PermissionSet` that enables it (shapes in `references/metadata-examples.md` section 5), and assign it to at least one test user who is not you.
3. **Build the prompt in a sandbox with Setup > In-App Guidance, then retrieve it** — `sf project retrieve start --metadata Prompt:<Name>`. This is the only way to obtain valid `targetPageType`, `targetPageKey1`, and `referenceElementContext` values; the guide publishes no vocabulary for them.
4. **Edit the retrieved file** against `references/metadata-examples.md`: add the `uiFormulaRule`, set `timesToDisplay` / `delayDays` / `startDate` / `endDate`, and decide `isPublished`. For a walkthrough, put schedule fields on step 1 and the action button on the last step, and renumber `stepNumber` consecutively from 1.
5. **Run the checker** — `python3 skills/admin/in-app-guidance-and-walkthroughs/scripts/check_in_app_guidance_and_walkthroughs.py --manifest-dir force-app/main/default`. It fails the build on a published version with no `targetPageType`, an `endDate` before its `startDate`, step numbers that repeat or skip, and `timesToDisplay` above 30; it warns on ungated prompts, one-step walkthroughs, and field-length overruns.
6. **Deploy with `--dry-run` first**, then for real, ordering `CustomPermission` → `PermissionSet` → `Prompt` in one manifest (`references/metadata-examples.md` sections 6–7).
7. **Verify as a gated user, then instrument.** Confirm the prompt renders for a user holding the permission and not for one without it. Add the `PromptError` query to the post-deploy check for this page, and schedule the `PromptAction` read that decides whether to extend or retire the prompt.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Active walkthrough count confirmed against the org's own limit before publishing a new one
- [ ] `displayType` matches the communication goal (`FloatingPanel` / `DockedComposer` / `Targeted`)
- [ ] Walkthrough step count is 5 or fewer, and `stepNumber` runs 1..n with no repeats or gaps
- [ ] `versionNumber` is `1` on every `promptVersions` entry
- [ ] Audience gate is deliberate — a custom permission where the cohort is not a profile, and the permission set is in the same deployment
- [ ] `targetPageType` / `targetPageKey1` came from a retrieve, not from a guess
- [ ] Targeted prompts have the anchor element recorded in `description`
- [ ] Schedule reviewed as metadata: `timesToDisplay` (≤30), `delayDays` in days, `startDate` / `endDate` on step 1
- [ ] `isPublished` matches the intended go-live, and a `startDate` backs it up if the deploy lands early
- [ ] Media fields are singular — `videoLink` **or** `image`/`imageLink`, with `imageAltText` and `imageLocation` if any image element is present
- [ ] Checker run clean against the manifest directory
- [ ] Tested under a user who holds the gating permission, and under one who does not
- [ ] `PromptError` query added to the post-deploy check for the affected page
- [ ] `PromptAction` reporting approach and owner identified for post-launch adoption measurement

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems. Full detail, grounding, and the fix for each is in `references/gotchas.md`.

1. **A broken anchor degrades rather than disappears** — a `Targeted` prompt whose element has moved converts to a floating prompt and logs `PromptError.Type = ReferenceElementNotFound`. No admin notification, so the query is the only signal.
2. **Slots are held by publication, not by usage** — an inherited walkthrough nobody has opened in a year still occupies its slot until `isPublished` is set false.
3. **Profiles are the fallback gate, not the only one** — `SpecificPermissions` plus a custom-permission criterion targets a cohort that no profile describes.
4. **`versionNumber` is not a step counter** — it stays `1` on every entry; `stepNumber` is the one that increments, and it must be consecutive.
5. **`delayDays` is days, not seconds** — it sets the gap between recurrences; `shouldIgnoreGlobalDelay` is the page-load control.
6. **A deploy with `isPublished` true is a go-live** — there is no post-deploy activation step.
7. **Media fields are mutually exclusive**, and `imageAltText` / `imageLocation` require each other.
8. **`body` length depends on the manifest's API version**, not the org's — 240 chars for floating and targeted prompts before v60.0.
9. **Republishing resets display state, not analytics** — the `Times*` counters are lifetime totals per user.
10. **AppExchange package prompts are exempt from org limits**, though the Setup list shows them alongside org-created ones.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `prompts/<Name>.prompt-meta.xml` | The deployable `Prompt`, with `promptVersions`, `uiFormulaRule`, and schedule |
| `customPermissions/` + `permissionsets/` files | The gate the `uiFormulaRule` resolves against, in the same manifest |
| `package.xml` entry | `Prompt`, `CustomPermission`, `PermissionSet` types, deploy-ordered |
| PromptAction adoption report | Views, action clicks, dismissals, snoozes, and walkthrough drop-off step |
| PromptError post-deploy query | The anchor audit; run after every layout or Lightning-page deploy |
| Targeted prompt anchor inventory | Which UI element each targeted step depends on, for maintenance tracking |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing the actual XML: floating / docked / walkthrough shapes, the `uiFormulaRule` gate, the custom permission and permission set, package.xml, retrieve and deploy commands, and the `PromptAction` / `PromptError` verification SOQL |
| `references/gotchas.md` | Something is not rendering, a deploy failed, or you are about to trust a field name that reads like it means something else — 10 grounded platform behaviours with guide line citations |
| `references/examples.md` | You want a worked scenario end to end: the walkthrough, the video prompt, and the recurring-acknowledgement pattern, with the anti-pattern that produces an 8-step walkthrough |
| `references/well-architected.md` | You are justifying the design in a review — pillar mapping, the targeted-vs-floating and free-tier-vs-licence tradeoffs, and the official sources this skill rests on |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated in-app guidance advice or configuration and need the specific failure modes to check for |

---

## Related Skills

- `admin/change-management-and-training` — decides *which* guidance to build, for whom, and alongside what other communication; this skill builds what that one specified
- `admin/custom-permissions` — the audience gate: naming, dependency chains, and permission-set assignment for the custom permission a `uiFormulaRule` targets
- `admin/dynamic-forms-and-actions` — the layout changes most likely to move or remove a targeted prompt's anchor element
- `admin/app-and-tab-configuration` — app and Home page context for `targetPageType`, and the app-access errors behind `PromptError.Type = NoAccessToApp`
- `admin/path-and-guidance` — Path's Guidance for Success is the record-stage-bound alternative to a prompt; use it when the guidance belongs to a stage rather than to a rollout
- `security/experience-cloud-security` — read before extending guidance to a partner or customer site, where supported-page coverage and site permissions both apply
