# In-App Guidance and Walkthroughs — Work Template

Fill this in as you work. It mirrors the Questions table and the Review Checklist in `SKILL.md`, and it is
what the next admin reads when a prompt stops behaving.

## Scope

**Skill:** `in-app-guidance-and-walkthroughs`

**Request summary:** (what the user asked for, in one sentence)

**Prompt developer name:** `` — file: `force-app/main/default/prompts/<Name>.prompt-meta.xml`

## Context Gathered

Answers to the Questions to Ask Before Configuring table in `SKILL.md`.

| Question | Answer |
|---|---|
| Who exactly should see this, and is that group a profile? | |
| What page does it sit on? Does a prompt already exist there? | |
| Anchored to an element, or just a message? | |
| Live on deploy, or later? | |
| How many showings per user, and how far apart? | |
| How will we know whether it worked, and who owns that read? | |
| What layout / Lightning-page changes are in flight for this page? | |

## Configuration

| Field | Value | Note |
|---|---|---|
| `displayType` | | `FloatingPanel` / `DockedComposer` / `Targeted` |
| `title` | | max 36 chars |
| `header` | | docked prompts only, max 36 chars |
| `body` | | 4,000 chars on API 60.0+; 240 for floating/targeted below that |
| `actionButtonLabel` / `actionButtonLink` | | max 25 / 1,000 chars; last step of a walkthrough |
| `dismissButtonLabel` | | floating or targeted only, max 15 chars |
| Media | | `videoLink` **or** `image`/`imageLink` + `imageAltText` + `imageLocation` — never both |
| `targetPageType` / `targetPageKey1` | | harvested from a retrieve, not guessed |
| `userAccess` / `userProfileAccess` | | |
| `uiFormulaRule` criteria | | `operator` is always `EQUAL` |
| `isPublished` | | true = live on deploy |
| `startDate` / `endDate` | | first step of a walkthrough |
| `timesToDisplay` / `delayDays` | | max 30 / **days**, not seconds |
| `versionNumber` | 1 | always 1, on every entry |

**Anchor elements (targeted steps only).** Record these — they are the dependency a layout change breaks.

| Step | Anchored element | Page / layout |
|---|---|---|
| | | |

**Audience gate files.** Both deploy in the same manifest, before the prompt.

- Custom permission: `customPermissions/<Name>.customPermission-meta.xml`
- Permission set: `permissionsets/<Name>.permissionset-meta.xml`
- Assigned to test user (not the admin):

## Approach

Which pattern from `SKILL.md` applies, and why. If none does, say what is different about this case.

## Checklist

- [ ] Active walkthrough count confirmed before publishing
- [ ] `stepNumber` runs 1..n with no repeats or gaps; `versionNumber` is 1 everywhere
- [ ] Audience gate deliberate, and the permission set is in the same deployment
- [ ] `targetPageType` / `targetPageKey1` came from a retrieve
- [ ] Anchor elements recorded above and added to the release dependency list
- [ ] `isPublished` matches the intended go-live, backed by a `startDate`
- [ ] Checker run clean: `python3 skills/admin/in-app-guidance-and-walkthroughs/scripts/check_in_app_guidance_and_walkthroughs.py --manifest-dir force-app/main/default`
- [ ] Deployed with `--dry-run` first
- [ ] Tested as a user who holds the gating permission, and as one who does not
- [ ] `PromptError` query added to the post-deploy check for this page
- [ ] `PromptAction` read scheduled, with a named owner and a decision date

## Post-Launch

| Date | `PromptAction` reading | Decision |
|---|---|---|
| | displays / actions / dismissals / drop-off step | extend / revise / retire |

Retirement: set `isPublished` to `false` and redeploy. That frees the walkthrough slot; deleting the
prompt is not required and destroys nothing useful.

## Notes

Deviations from the standard pattern and why. Anything an LLM reviewing this later would get wrong.
