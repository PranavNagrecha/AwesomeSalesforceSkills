# Gotchas: OmniScript Design Patterns

Non-obvious platform behaviors that cause real production problems in this domain. Each gotcha names the source it rests on, or says plainly where the claim is not grounded.

## Gotcha 1: Only One Active OmniScript per Type, SubType, and Language

**What happens:** A team clones an OmniScript for a second business unit, keeps the Type and SubType, and tries to activate it. Only one can be active, so one journey silently stops serving the copy users expected.

**When it occurs:** Cloning scripts for variants, regions, or partner portals.

**How to avoid:** Plan the Type, SubType, and Language scheme up front. Variants get a different SubType. Language variants get a different Language. The Name can repeat; the identity can't.

**Source:** Trailhead, "Create a Simple Omniscript": "An Omniscript's Type, Subtype, and Language gives an Omniscript its unique identity. Only one active Omniscript may have the same Type, SubType, and Language at any time." Industries Common Resources Developer Guide, OmniScript `uniqueName` ("Type_SubType_Language_VersionNumber").

---

## Gotcha 2: Changing an Active Script Means a New Version

**What happens:** A fix is made to the active OmniScript expecting users to get it immediately. The designer requires a new version, and users keep the old behavior until that version is activated in each environment.

**When it occurs:** Hotfixes, and deployments where the new version arrives but the old one stays active.

**How to avoid:** Create a new version, test it in Preview, activate it, and record the active version per environment after each deployment.

**Source:** Trailhead, "Create a Simple Omniscript": "Only one version of an Omniscript can be active at a time. To make a change to an active Omniscript, create a new version." Industries Common Resources Developer Guide, OmniScript `isActive`.

---

## Gotcha 3: A Child OmniScript Must Be Marked Embeddable

**What happens:** A shared address-capture script can't be selected in the Omniscripts element of the parent, or the parent fails to load it after deployment.

**When it occurs:** Reusable child scripts that were built as standalone journeys.

**How to avoid:** Set the child's embeddable flag (`isOmniScriptEmbeddable` in metadata) and keep its Type, SubType, and Language stable, because the parent references them.

**Source:** Industries Common Resources Developer Guide, OmniScript `isOmniScriptEmbeddable` ("Indicates whether the OmniScript can be embedded in other OmniScripts"). UNVERIFIED (2026-10-03): the exact designer symptom when the flag is off is not described in the fetched sources.

---

## Gotcha 4: Step Validation Is Not a Server Boundary

**What happens:** Required fields, step conditions, and messaging live in the OmniScript. A caller that invokes the Integration Procedure or Apex directly skips all of them, and the write still happens.

**When it occurs:** Guest or partner journeys that "validate on the step" and trust the backend action.

**How to avoid:** Validate again inside the Integration Procedure or Apex for every write. Restrict which fields a write may set. Treat the script's validation as user experience only.

**Source:** Trailhead, "Dig into the Omniscript Designer" (Messaging and validation are configured on the script's elements in the browser). UNVERIFIED (2026-10-03): the specific remote entry points that bypass the script (for example a managed-package `GenericInvoke2NoCont` class) are not documented in the fetched sources.

---

## Gotcha 5: Many Actions per Step Multiply Round Trips

**What happens:** A step grows six or more Integration Procedure, Data Mapper, and HTTP actions. Each one is a separate request, so the step feels slow and fails in more ways.

**When it occurs:** Scripts that add an action for every data need instead of orchestrating.

**How to avoid:** Default to one Integration Procedure Action per user intent. Let the Integration Procedure call Data Mappers and HTTP actions server-side.

**Source:** Trailhead, "Design a Simple Omniscript" (Integration Procedure Action calls "a series of actions") and "Create a Simple Omniscript" ("Using Integration Procedures is best practice... Integration Procedures help you separate data configuration from Omniscript configuration").

---

## Gotcha 6: Save and Resume Can Reopen a Different World

**What happens:** A user resumes a saved journey days later. Eligibility, prices, or record ownership changed meanwhile, and the script submits stale assumptions.

**When it occurs:** Long journeys with Save Options enabled and no revalidation on resume.

**How to avoid:** List the values that must be re-read on resume and re-run the prefill Integration Procedure before the final submit.

**Source:** Trailhead, "Dig into the Omniscript Designer" (Save Options in the Setup panel). The drift risk itself is design reasoning, not a documented platform rule.

---

## Gotcha 7: OmniScript Records Are Internal Objects

**What happens:** A script bulk-edits `OmniProcess` or `OmniProcessElement` records to rename elements. Scripts start failing.

**When it occurs:** Data Loader or Apex edits on the standard objects behind OmniScripts.

**How to avoid:** Change OmniScripts in the designer or through the `OmniScript` metadata type only.

**Source:** Industries Common Resources Developer Guide, Omnistudio Standard Objects (OmniProcess, OmniProcessElement, OmniScriptSavedSession: "For internal use only").

---

## Gotcha 8: Type Ahead Searches Fire as the User Types

**What happens:** A Type Ahead Block on a guest-facing script calls a Data Mapper or Integration Procedure while the user types. Load rises, and suggestion labels can expose records the guest should not see listed.

**When it occurs:** "Search-as-you-type" against Contact or Account on public scripts.

**How to avoid:** Require a minimum number of characters, keep personal data out of suggestion labels, and use a server action that enforces sharing. Leave Type Ahead out if a picklist works.

**Source:** Trailhead, "Design a Simple Omniscript" (Type Ahead Blocks: "The user begins to enter information. The system searches for matches and displays a list"). UNVERIFIED (2026-10-03): per-keystroke call frequency and debounce settings are not specified in the fetched sources.
