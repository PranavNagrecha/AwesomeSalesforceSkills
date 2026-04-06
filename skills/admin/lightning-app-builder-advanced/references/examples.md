# Examples — Lightning App Builder Advanced

## Example 1: Formula Field as Visibility Proxy for Complex Logic

**Context:** An Opportunity record page needs a "Contract Terms" component visible only when Stage is "Closed Won", Amount is greater than 50,000, and the Account's BillingCountry is "US". LAB visibility filters support a maximum of 10 conditions and cannot perform cross-object field references or arithmetic comparisons.

**Problem:** Without a proxy formula field, the practitioner would need to approximate the condition using only Stage (one condition) and rely on users manually ignoring the component in other situations — or build multiple page variants. LAB filters cannot reference related-object fields (like Account.BillingCountry) at all.

**Solution:**

Create a formula checkbox field on Opportunity:

```
Field Label: Show Contract Terms Section
API Name:    Show_Contract_Terms__c
Formula:
    AND(
        StageName = 'Closed Won',
        Amount > 50000,
        Account.BillingCountry = 'US'
    )
```

Then in Lightning App Builder, set the "Contract Terms" component's visibility to a single condition:
- Filter: `Show Contract Terms Section equals True`

**Why it works:** Formula fields are evaluated server-side and cached on the record object. The LAB filter only needs one condition and avoids the 10-condition limit. Future logic changes require only a formula update, not a LAB reconfiguration.

---

## Example 2: Enabling Dynamic Actions Without Duplicate Buttons

**Context:** A Case record page is being upgraded to use Dynamic Actions so that the "Escalate" button only appears when Priority is "High".

**Problem:** After enabling Dynamic Actions in LAB, the "Escalate" button appears twice — once from Dynamic Actions and once from the page layout action bar still assigned to the Support Agent profile.

**Solution:**

Step 1 — Before enabling Dynamic Actions in LAB, go to Setup > Object Manager > Case > Page Layouts. Open the layout assigned to Support Agents and remove "Escalate" from the layout's action section (or note that page-layout actions will conflict).

Step 2 — In LAB, open the Case record page, enable Dynamic Actions (button in the action bar component properties).

Step 3 — Add the "Escalate" action to the Dynamic Actions canvas. Set a visibility filter: `Priority equals High`.

Step 4 — Under Page Assignments, confirm the layout assigned to Support Agents no longer overrides the action bar. If the layout still has a Salesforce Mobile and Lightning Experience Actions section with "Escalate", remove it or reassign profiles to a layout without it.

**Why it works:** Dynamic Actions and page-layout actions render from separate sources. Disabling page-layout action injection for the relevant profile/layout before activation prevents the duplicate render.

---

## Example 3: Custom App Page Template with Aura

**Context:** A company wants a three-column app page layout in Lightning App Builder that is not available in the standard template options.

**Problem:** The standard LAB templates offer limited column configurations. The closest built-in option is two columns, which is insufficient for a dashboard-style page.

**Solution:**

Create an Aura component:

```xml
<!-- ThreeColumnTemplate.cmp -->
<aura:component implements="lightning:template" description="Three equal-column app page template">
    <flexipage:region name="left" defaultWidth="SMALL" />
    <flexipage:region name="center" defaultWidth="SMALL" />
    <flexipage:region name="right" defaultWidth="SMALL" />
</aura:component>
```

With a companion CSS file for layout:

```css
/* ThreeColumnTemplate.css */
:host {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    padding: 1rem;
}
```

Deploy to the org via SFDX or change set. The template then appears in LAB under "New Page > App Page > Choose a Template".

**Why it works:** `lightning:template` is the Aura interface that registers a component as a LAB page template. `flexipage:region` nodes define the drop zones. LWC cannot implement this interface — it must be Aura.

---

## Anti-Pattern: Using Visibility Filters as a Security Gate

**What practitioners do:** They set a component's visibility filter to "Profile does not equal System Administrator" to hide sensitive fields from non-admins, assuming this prevents data access.

**What goes wrong:** Visibility filters are client-side rendering hints. A user with the correct FLS on the field can still retrieve the data via SOQL in Developer Console, a connected app, or any API call. The field is merely not rendered on the page — it is not protected.

**Correct approach:** Remove the field from the FLS grant for profiles that should not see it. Use visibility filters only for UX simplification. Security requires FLS + object permissions enforced by the platform — not page-level display logic.
