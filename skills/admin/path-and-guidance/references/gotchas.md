# Gotchas — Path and Guidance

Non-obvious Salesforce platform behaviors that cause real production problems with Path configuration.

---

## Gotcha 1: The Org-Level Path Toggle Is Off After a Scratch Org or Deployment

**What happens:** Paths are created and activated, but the chevron bar never appears on any record page. Everything looks correct in Path Settings — paths are active, the component is on the Lightning page — but the UI shows nothing.

**When it occurs:** Most commonly after a scratch org is spun up from a package, after a sandbox refresh, or when metadata is deployed without the org preference. The individual path records deploy but the org-level "Enable Path" setting in Setup > Path Settings does not deploy as a metadata change in the same way.

**How to avoid:** Always verify the org-level Path toggle in Setup > Path Settings as the first debugging step when Path is missing. After any org creation or refresh, enable the toggle manually or include it in a post-install script. The metadata type `PathAssistantSettings` can carry this flag in the org preference XML if included in the deployment package.

---

## Gotcha 2: Long Text Area and Encrypted Fields Cannot Be Key Fields

**What happens:** An admin tries to add a long text area field (e.g., Description, a custom rich-text area) as a key field for a stage. The field does not appear in the available field list in Path Settings. If the admin expects it to be there based on seeing it on the page layout, they may spend time searching for it.

**When it occurs:** Any time the designed key fields include long text area, encrypted, or certain relationship fields that Path does not support inline.

**How to avoid:** Before designing key fields, know the restriction: only short text, number, currency, percent, date, datetime, checkbox, email, phone, URL, and lookup (read-only display) fields are supported as key fields. Long text area fields, rich text area fields, encrypted fields, and formula fields are either excluded or read-only. Design the stage key field list around supported types, or accept that rich content belongs in the guidance text block rather than a key field.

---

## Gotcha 3: Missing Stages in Path Are a Sales Process Problem, Not a Path Problem

**What happens:** An admin expects a specific Stage picklist value (e.g., "Verbal Commit") to appear in the Path chevron bar but it is absent. The value exists in the global picklist, but Path does not show it.

**When it occurs:** When the Stage value is not included in the Sales Process assigned to the Opportunity record type. Path only renders stages that are in the underlying picklist value set available to the record type. If the Sales Process filters out a value, Path will not show it.

**How to avoid:** Before editing Path stages, verify the Sales Process assigned to the target record type (Setup > Sales Processes). Confirm every expected stage value is in the Sales Process value list. If a stage is missing from Path, add it to the Sales Process first, then return to Path Settings to configure key fields and guidance for it.

---

## Gotcha 4: Confetti Does Not Fire on Automation-Driven Stage Changes

**What happens:** A Flow or Process Builder advances the Stage picklist to "Closed Won" automatically (e.g., when a related contract is activated). Reps expected to see confetti but the animation never fires.

**When it occurs:** Any time the stage change that should trigger confetti is performed by automation (Flow, Process Builder, Apex, API) rather than by the user manually clicking through the Path component UI.

**How to avoid:** Document clearly that confetti is a UI interaction reward, not an event-driven trigger. If reps will always advance the stage through automation, confetti is not achievable for that transition. If mixed (sometimes manual, sometimes automated), confetti fires only on the manual interactions. Consider managing expectations by noting this in the Path guidance text itself, or by having a separate Flow send a Chatter congratulations post when Stage = Closed Won, regardless of how the change happened.

---

## Gotcha 5: Path Metadata Deploys Without the Lightning Page Update

**What happens:** Path configurations are deployed to production (path records, key fields, guidance text), but the Path component was added to the Lightning page in the source org via Lightning App Builder and the Lightning page metadata was not included in the deployment. Production shows no Path component on the record page.

**When it occurs:** When the change set or package includes Path metadata but not the Lightning page metadata (`FlexiPage` type in the Metadata API). This is a common oversight in iterative deployments where the page was changed manually.

**How to avoid:** When deploying Path changes, always check whether the associated Lightning page (`FlexiPage` metadata) also needs to be included. If the Path component was added or repositioned in Lightning App Builder in the source org, retrieve and deploy the `FlexiPage` for that object's record page along with the path metadata. Verify in Lightning App Builder on production after deployment.

---

## Gotcha 6: Path Renders Incorrectly Inside Narrow Columns or Tabs

**What happens:** The Path component is placed inside a two-column layout or inside a tab on the record page. The chevron labels overlap, truncate aggressively, or the component renders as a collapsed bar with no visible stage names.

**When it occurs:** Any time the Path component is constrained to less than full page width, such as inside a 50%-width column, inside a sub-tab, or stacked with other components in a sidebar.

**How to avoid:** Always place the Path component in a full-width, one-column region at the top of the record Lightning page. This is the officially recommended placement. Avoid embedding Path inside tabs, accordions, or multi-column sections. If the page layout cannot accommodate a full-width header region, reconsider whether Path is the right component for this page.
