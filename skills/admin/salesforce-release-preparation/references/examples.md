# Examples — Salesforce Release Preparation

## Example 1: Catching a Release Update Before Auto-Activation Breaks Production Flow

**Context:** A mid-size Service Cloud org is two weeks from the Winter '26 production upgrade. An admin doing a routine Setup review notices a Release Update called "Enforce Stricter Behavior for Null Values in Flow Decision Elements" with an auto-activation date three days after the production upgrade. The org has 14 active Flows that use Decision elements comparing picklist values to null.

**Problem:** Without proactive testing, the auto-activation would fire on all 14 Flows in production simultaneously. Three of those Flows drive case escalation and SLA breach notifications. If the null comparison behavior changes and a Flow throws a fault, the affected cases stop routing and SLA timers run without escalation until someone notices manually.

**Solution:**

1. Admin activates the Release Update in the Developer sandbox immediately.
2. Admin runs a targeted test: opens each of the 14 Flows in Flow Builder and manually tests the Decision paths that compare picklist fields to null.
3. Two Flows fail — the null comparison no longer evaluates as expected. The admin updates those Flows to use `{!$GlobalConstant.EmptyString}` or an explicit `ISNULL()` check in formula conditions instead of a bare null comparison.
4. Admin re-runs affected automated tests and UAT scripts. All pass.
5. Admin activates the Release Update in a Full Sandbox used for UAT and re-validates.
6. Admin activates the Release Update in production 10 days before the auto-activation deadline, with monitoring in place.

```
Before (broken after update):
  Decision condition: {!Case.Status} = null   ← null literal comparison

After (correct):
  Decision condition: ISNULL({!Case.Status})  ← formula-based null check
  or
  Decision condition: {!Case.Status} = {!$GlobalConstant.EmptyString}
```

**Why it works:** Testing the Release Update in sandbox before auto-activation converts a potential production incident into a planned, low-risk change. The fix is deployed and validated before the update is active in production.

---

## Example 2: Structured Release Notes Triage for a Multi-Cloud Org

**Context:** A retail org running Sales Cloud, Service Cloud, and Experience Cloud has a team of three admins sharing release preparation responsibility. The Summer '25 release notes are 340 items long. In prior releases the team read notes "when they had time" and missed two End User behavior changes that caused support tickets.

**Problem:** Unfiltered review of 340 items across three people produces inconsistent coverage and misses high-signal items buried in unrelated sections.

**Solution:**

The lead admin applies the following triage process:

1. Opens the Summer '25 release notes at help.salesforce.com and applies the Feature Impact filter with the following selections: Admin, Developer, End User.
2. From those filtered results, applies the product-area filter for: Sales Cloud, Service Cloud, and Experience Cloud (three passes).
3. The combined filtered list is 38 items — an 89% reduction.
4. The 38 items are copied into a shared tracking doc with four columns: Item, Impact Type, Owner, Status.
5. Items tagged "Requires Setup" are elevated immediately — they are opt-in features with a deadline. Items tagged "End User" go to the stakeholder communication brief. Items tagged "Developer" go to the Apex developer on the team.
6. Release Updates discovered in Setup > Release Updates are added as separate rows with enforcement dates.
7. The triage doc is reviewed in a 45-minute team call. Each item is assigned an owner and a target sandbox test date.

**Why it works:** The Feature Impact filter is the highest-leverage step in release preparation. It reduces review volume by 80–90% for a typical multi-cloud org and ensures every remaining item gets explicit ownership.

---

## Example 3: Sandbox Preview Enrollment to Catch an LWC Rendering Change Early

**Context:** A manufacturing org has a custom Lightning Web Component that renders a quote line item table. The component uses a deprecated Lightning Base Component property that is marked for removal in the upcoming Spring '26 release notes.

**Problem:** If the admin doesn't test until after production upgrades, any rendering failure surfaces to sales reps in a live environment mid-quarter.

**Solution:**

1. Admin enrolls one spare Developer Pro sandbox in Sandbox Preview during the open enrollment window via Setup > Sandboxes. The sandbox has no active sprint work and can absorb the upgrade.
2. After the preview upgrade runs (approximately four weeks before production), admin loads the component in the Developer Pro sandbox in Lightning Experience.
3. The component renders with a console warning indicating the deprecated property. The component still functions but the warning signals future failure.
4. Admin files a ticket with the development team. The LWC is updated to use the supported replacement property and redeployed to the preview sandbox.
5. Component renders cleanly. Change is promoted to production before the production upgrade date.

**Why it works:** Sandbox Preview provides four to six weeks of lead time on LWC rendering issues, deprecated API behavior, and Apex compilation warnings that only surface after an actual org upgrade.

---

## Anti-Pattern: Reviewing Release Notes in the Week Before Production Upgrade

**What practitioners do:** Defer release notes review until one to two weeks before the production upgrade, treating it as a final check rather than a structured preparation process.

**What goes wrong:** Release Updates cannot be meaningfully tested and fixed in one week if they touch complex automations or code. Sandbox Preview enrollment window is already closed. Stakeholder communication is rushed or skipped. Any issue found is either accepted as risk or triggers an emergency patch that itself introduces risk.

**Correct approach:** Begin release preparation as soon as release notes are published — typically six to eight weeks before the production upgrade. The triage, sandbox enrollment, and Release Update testing are each separate phases that require lead time. The week before production should be sign-off, not discovery.
