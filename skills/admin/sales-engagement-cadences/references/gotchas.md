# Gotchas — Sales Engagement Cadences

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Email Steps Silently Skip When Target Email Field Is Blank

**What happens:** When a Lead or Contact enrolled in a cadence has no value in the email field, the Email step is silently skipped. The prospect either advances to the next step or the cadence stalls without any error, warning, or task logged for the rep.

**When it occurs:** Any time a prospect is enrolled in a cadence containing an Email step and the target email field (Lead.Email or Contact.Email) is empty. This is common when leads are imported from events or partner lists with incomplete data.

**How to avoid:** Run a validation report before bulk-enrolling leads — filter for blank email and resolve or exclude those records. Add an entry criteria check (via Flow or assignment rule) to prevent enrollment of records missing required fields.

---

## Gotcha 2: Org-Wide Active Tracker Limit (150,000) Is Separate From the Active Target Cap (500,000)

**What happens:** Admins plan against the 500,000 active target cap but miss the 150,000 active tracker limit. The tracker limit governs email engagement tracking (opens, clicks). When the tracker limit is reached, new enrollments have email steps that execute but tracking silently stops — engagement signals no longer fire, which breaks positive and negative track branching.

**When it occurs:** High-volume orgs running multiple active cadences across a large rep base can hit 150,000 active trackers well before reaching 500,000 active targets. Trackers are not released until a prospect completes or exits the cadence.

**How to avoid:** Monitor both limits separately via Setup > Sales Engagement Settings > Usage. Build a cadence governance process: complete or remove stale prospects regularly, deactivate unused cadences, and set a policy for maximum active enrollment per cadence.

---

## Gotcha 3: Cloned Cadences Inherit Template References, Not Template Copies

**What happens:** When a cadence is cloned using the Cadence Builder clone action, the new cadence references the same email templates and call scripts as the original. If a team edits the shared template to update messaging, both cadences reflect the change. Admins who intended cadence isolation for A/B testing or different teams inadvertently share template changes.

**When it occurs:** Any time a cadence is cloned and the team does not immediately review and reassign templates to dedicated copies of those templates.

**How to avoid:** After cloning a cadence, immediately open every Email step and reassign it to a new duplicate of the original template. Do not share templates across cadences intended for separate messaging strategies.

---

## Gotcha 4: LinkedIn Steps Appear in the Builder Even Without Sales Navigator

**What happens:** Cadence Builder always shows LinkedIn as an available step type regardless of whether LinkedIn Sales Navigator is integrated. Admins can add LinkedIn steps to a cadence and activate it with no error. At runtime the rep sees the step in the Work Queue but cannot take the LinkedIn action — the integration is missing.

**When it occurs:** LinkedIn Sales Navigator integration is not enabled under Setup > LinkedIn Sales Navigator, but a cadence with a LinkedIn step has already been activated and prospects enrolled.

**How to avoid:** Verify LinkedIn Sales Navigator integration is enabled and tested before adding LinkedIn steps. Do not treat availability in the Builder as confirmation that the underlying integration is configured.

---

## Gotcha 5: Prospects Paused by Engagement Signals Remain Paused Until Manually Resumed

**What happens:** When an engagement signal triggers a branch (e.g., a positive reply routes the prospect to the positive track), the system pauses the main track. If the positive track completes without manual resumption, the prospect stays in a paused state indefinitely. From the rep's view the prospect simply disappears from the Work Queue.

**When it occurs:** Common after a prospect replies to an email and is routed to the positive track, which has a short sequence. After the positive track completes, if the rep does not take action and there is no exit step configured, the record sits paused.

**How to avoid:** Design positive and negative tracks with explicit exit steps — either a final Custom task ("Convert lead or close cadence") or a configured end-of-cadence outcome. Monitor paused prospects with a report filtered by Cadence Status = Paused.
