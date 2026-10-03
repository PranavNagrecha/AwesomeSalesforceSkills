# Gotchas — OmniScript Flow Design Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Sources are Trailhead units fetched on 2026-10-03 (Omniscript modules for Omnistudio for Managed Packages and the Omnistudio Omniscript Fundamentals module) and the Salesforce Industries Developer Guide (Spring '26). help.salesforce.com OmniStudio articles do not render to a fetcher, so claims that rest only on them are marked UNVERIFIED.

## Gotcha 1: A Requirements Spec Without a Navigate Action Strands the User

**What happens:** The OmniScript runs to its last Step and stops there. Users close the tab or click back, and nobody lands on the record they just changed. Trailhead lists a Navigate Action as one of the elements every OmniScript requires, and describes it as what tells the OmniScript where to send the user when it completes.

**When it occurs:** Requirements documents that treat the "Submit" button as implicit (as in Screen Flow) without specifying a Navigate Action and its destination.

**How to avoid:** Document the Navigate Action for every branch: type (record, URL, console return, another OmniScript through the Omniscript page reference type) and destination. UNVERIFIED (2026-10-03): earlier versions of this skill said Preview passes but activation fails without a Navigate Action; no source read for this revision describes that activation check.

**Source:** Trailhead, "Design and Build a Branching Omniscript" (required elements list); Trailhead, "Configure a Simple OmniScript" (Navigate Action at completion).

---

## Gotcha 2: Data Loaded After a Step Is Not on That Step

**What happens:** Data loaded by an action placed after Step N is not available to pre-populate fields on Step N. It runs after the user clicks Next. Requirements that say "load account name on the Address step" without timing produce empty fields that look like broken data loading.

**When it occurs:** When requirements specify pre-population without noting whether the action sits before or after the Step.

**How to avoid:** Requirements must say Pre-Step or Post-Step for every data action. Trailhead's Edit Account design places the get action before the Step "as the data needs to be fetched before the rep can edit it", and the save action after the Step.

**Source:** Trailhead, "Optimize Workflow with OmniScript Design" (placement of the two Integration Procedure actions).

---

## Gotcha 3: Actions Inside a Step Are Buttons, Not Automatic Steps

**What happens:** An action that the requirements meant to run automatically is drawn inside a Step, so it appears as a button the user must click. If nobody clicks it, the data never loads or saves.

**When it occurs:** When a wireframe shows the action "on the page" and the developer builds exactly that.

**How to avoid:** For every action, record one of three placements: before the Step, after the Step, or inside the Step as a button with its label. Trailhead states that actions outside a Step execute automatically in the order they appear, and actions inside a Step appear as a button that must be clicked.

**Source:** Trailhead, "Configure a Simple OmniScript" (Configure Omniscript Action Elements).

---

## Gotcha 4: Field Names in the JSON Must Match Element Names

**What happens:** The Integration Procedure returns the right data, but the fields on screen are empty. The OmniScript uses a parser to match incoming JSON to inputs by element name, and when the node name does not match the element name the field appears empty.

**When it occurs:** When the requirements name screen fields one way ("Account Phone") and the data contract names nodes another way (`Phone`), and nobody reconciles the two before build.

**How to avoid:** Put the element name and the JSON node name side by side in the data requirements matrix. Use one record-ID variable name consistently (Trailhead's example passes `AccountId` through every element). Where names cannot match, specify Response JSON Path / Response JSON Node or a Post-Transform Data Mapper on the action.

**Source:** Trailhead, "Configure a Simple OmniScript" (How Data Flows into and out of an Omniscript); Trailhead, "Design and Build a Branching Omniscript" (Send/Response JSON Path and Node properties).

---

## Gotcha 5: Conditional Views Work on Almost Every Element, So Per-Field Rules Multiply

**What happens:** Earlier versions of this skill said Conditional Views only work on Block containers and silently do nothing on fields or Steps. Trailhead says the opposite: almost every element lets you define conditional views, and Steps can be shown conditionally to route users to different pages. The real problem is requirements that list "show field X if Y" for every field. The developer then sets the same condition on ten fields, and a later rule change has to be made in ten places.

**When it occurs:** Requirements documents that list field-level conditions in wireframe notation without grouping.

**How to avoid:** Group elements that share a condition into a named Block with one Conditional View, as Trailhead's primary-contact example does with one Block per radio-button choice. Use a Step-level condition when a whole page applies to one branch only. Record each condition as element, operator, and value.

**Source:** Trailhead, "Design and Build a Branching Omniscript" (Add Conditional Branching; "almost every element in an Omniscript lets you define conditional views"); Trailhead, "Explore Omniscript Group and Input Elements" (Step: "You can apply conditional logic so that users are directed to one step or another").

---

## Gotcha 6: Required Fields Only Guard the Current Step

**What happens:** A value collected on Step 1 is needed by a choice on Step 4. The user skips it on Step 1, picks the option on Step 4, and the save fails or stores incomplete data. Required fields and formula messaging only work on the current Step.

**When it occurs:** When requirements state a cross-step rule ("mobile number is required if the user opts into text alerts later") as if it were an ordinary required field.

**How to avoid:** List cross-step rules separately and specify a Set Errors element for each. Trailhead names the three properties it needs: Element Error Map (which element shows the error), Value (the message), and Conditional View (when it fires). It sends the user back to the Step that needs fixing.

**Source:** Trailhead, "Validate Data and Handle Errors" (Set Errors Elements Make Sure Data Is Complete).

---

## Gotcha 7: Child OmniScripts Nest Only One Level Deep

**What happens:** A design reuses an address-capture OmniScript inside a contact OmniScript, and then tries to embed the contact OmniScript inside an onboarding OmniScript. The second embed is not allowed: if a parent contains a child, that parent cannot itself be used inside another OmniScript. Element names also must be unique across the parent and the child.

**When it occurs:** Requirements that decompose a long journey into layers of reusable pieces without checking depth.

**How to avoid:** Draw the parent/child map in the requirements and keep it to one level. Reserve an element-name prefix per child OmniScript so names cannot collide. Trailhead also advises avoiding single-page child OmniScripts and consolidating them into the parent.

**Source:** Trailhead, "Use Action, Function, and Display Elements" (Use Omniscripts in Omniscripts).

---

## Gotcha 8: Type, SubType, and Language Are the Identity, and Only One Version Is Active

**What happens:** Two teams build "intake" OmniScripts with the same Type, SubType, and Language and find only one can be active. Or a change is made by editing the active version, which is not how OmniScripts are changed.

**When it occurs:** When requirements name OmniScripts only by their display Name, which does not need to be unique.

**How to avoid:** Assign Type, SubType, and Language in the requirements header. Trailhead says only one active OmniScript may have the same Type, SubType, and Language, only one version can be active at a time, and changes to an active OmniScript are made in a new version while the active one stays in place. Trailhead also recommends starting Type with a lowercase letter.

**Source:** Trailhead, "Configure a Simple OmniScript" (What Makes an Omniscript Unique?); Salesforce Industries Developer Guide (Spring '26), OmniScript metadata type (`type`, `subType`, `language`, `versionNumber`, and `uniqueName` as Type_SubType_Language_VersionNumber).

---

## Gotcha 9: Managed Package Runtime and Standard Runtime Are Different Products to Build In

**What happens:** Requirements written against one runtime reference designer features, storage, or deployment steps from the other. Trailhead's OmniScript modules state they cover Omnistudio for Managed Packages, "which uses the managed package runtime and custom objects", and point standard-runtime readers elsewhere. Omnistudio for Managed Packages is not available in the Trailhead Playground.

**When it occurs:** Orgs that are mid-migration between runtimes, or teams that learned on one and implement on the other.

**How to avoid:** State the runtime in the requirements header and keep runtime-specific notes (custom component overrides, deployment approach) in a separate section. UNVERIFIED (2026-10-03): the Setup path for checking the runtime (Setup > OmniStudio Settings) comes from Help, not from a source read for this revision.

**Source:** Trailhead, "Design and Build a Branching Omniscript" and "Configure a Simple OmniScript" (module scope notes).
