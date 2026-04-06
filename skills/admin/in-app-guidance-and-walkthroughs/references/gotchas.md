# Gotchas — In-App Guidance and Walkthroughs

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Targeted Prompts Silently Stop Rendering When Anchor Is Removed

**What happens:** A targeted prompt anchored to a specific UI element — a field, button, or component — stops appearing entirely if that element is removed from the page layout, renamed, or relocated. No error is surfaced in the UI, no notification is sent to the admin, and the PromptAction object produces no records for the affected prompt. From a user perspective, the prompt simply never shows.

**When it occurs:** After any Lightning page layout change that removes or renames the element the prompt was anchored to. This also occurs when a field is removed from a compact layout that the targeted prompt pointed at, or when a Lightning component is replaced by a newer version with a different DOM selector.

**How to avoid:** Document the UI anchor element in the prompt's Description or Internal Notes field at creation time. After every layout change deployment, audit targeted prompts against the current page layout. Consider adding targeted prompt anchors to the list of dependencies in your deployment checklist.

---

## Gotcha 2: Active Walkthrough Slot Is Consumed at Publish, Not at First User View

**What happens:** The 3-slot free-tier limit for active walkthroughs is counted against all currently active (published and scheduled) walkthroughs, regardless of whether any user has actually triggered them. An org with 3 legacy walkthroughs from a prior admin — even ones no user has seen in months — cannot publish a new walkthrough until one is deactivated.

**When it occurs:** When a new admin inherits an org and tries to create the first walkthrough, or when a project produces more than 3 walkthroughs sequentially without deactivating older ones. The error message from Salesforce ("You've reached the limit") does not explain that deactivating an existing walkthrough resolves it.

**How to avoid:** Before creating a walkthrough, navigate to Setup > In-App Guidance and count active walkthroughs on the Manage Prompts page. Deactivate stale or completed walkthroughs. Note that single-step floating and docked prompts (not multi-step walkthroughs) do not count against the 3-slot cap.

---

## Gotcha 3: Profile-Only Audience Targeting Creates Over-Delivery Problems

**What happens:** In-App Guidance audience filters support only profiles as of Spring '25. If a profile is shared across users who do need to see a prompt and users who do not (e.g., a "Standard User" profile used by both new hires and 5-year veterans), the prompt will display to all matching profiles with no way to narrow it further natively.

**When it occurs:** Common in orgs where profiles were not designed with granular adoption segmentation in mind, or where org policy limits the total number of profiles to prevent sprawl.

**How to avoid:** If the intended audience cannot be expressed by a single profile or set of profiles, consider one of these alternatives: (1) create a lightweight profile clone specifically for the users who need the prompt, then remove it after the adoption window; (2) use a Flow-triggered process to send in-app notifications as a substitute; (3) evaluate the Sales Enablement license for more advanced targeting capabilities.

---

## Gotcha 4: Republishing Does Not Reset Analytics — Only Display State

**What happens:** When an admin deactivates and republishes a walkthrough (a common pattern for quarterly compliance reminders), the PromptAction records from the original publication are not deleted. Adoption reports will show cumulative records spanning both the old and new publish cycles, making it difficult to measure adoption for the current cycle only without date-filtering every report.

**When it occurs:** Any time the "deactivate and republish" pattern is used for recurring prompts.

**How to avoid:** Filter all PromptAction reports by `CreatedDate >= [publication date]` when analyzing the current cycle. Consider adding the republish date to the prompt Title or Description so report consumers know the effective start date.

---

## Gotcha 5: Lightning Experience-Only — Classic and Experience Cloud Are Excluded

**What happens:** In-App Guidance prompts and walkthroughs are not rendered in Salesforce Classic or in Experience Cloud sites (partner portals, customer portals, digital experience sites). If users access records via a Classic bookmark or via an Experience Cloud site, they will never see prompts that are active and scheduled.

**When it occurs:** In orgs that have not fully migrated to Lightning Experience, or in orgs that use Experience Cloud for partner or customer access and expect guidance prompts to reach those users.

**How to avoid:** Confirm that the target users exclusively access Salesforce via Lightning Experience before investing in In-App Guidance. For Experience Cloud users, custom LWC components or Flow-driven notifications are the current alternatives.
