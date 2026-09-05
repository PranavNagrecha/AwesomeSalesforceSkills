# Well-Architected Notes — In-App Guidance and Walkthroughs

## Relevant Pillars

- **Operational Excellence** — In-App Guidance is fundamentally an operational excellence tool. It reduces support load, improves process adherence, and accelerates feature adoption without requiring live training. Well-designed prompts are part of a deliberate org maintenance and change adoption practice. The risk is operational debt: stale prompts that reference removed UI elements or outdated processes erode user trust in the system.

- **Reliability** — Targeted prompts have a degradation mode, not a silent one: when the anchored element moves, the prompt converts to a floating prompt and a `PromptError` row of type `ReferenceElementNotFound` is written. Nothing raises that row to an admin, so reliability here means owning the query. A reliable implementation puts the `PromptError` check in the post-deploy step of any release that touches page layouts or Lightning pages, not in a quarterly audit.

- **Security** — In-App Guidance content is visible to all users matching the audience profile. Avoid including any sensitive data, internal system details, PII, or security-relevant instructions inside prompt copy. Prompt content is stored in Salesforce metadata and is accessible to admins with the "Manage Prompts" permission.

- **Performance** — The metadata exposes no per-prompt render delay. `shouldIgnoreGlobalDelay` is a boolean: leaving it `false` keeps the prompt behind the org's global time delay so it does not compete with the initial page render, and setting it `true` shows the prompt on page load. `delayDays` is the gap between recurrences, in days. Treating the global delay as the default is the low-cost practice that reduces premature dismissal.

- **Scalability** — The active walkthrough limit on the free tier (documented as 3; see the UNVERIFIED note in `gotchas.md` Gotcha 2) is a hard constraint that does not scale with org complexity. Orgs with broad adoption programs (multiple products, many teams, high-churn onboarding needs) will hit this ceiling quickly. Architectural planning should account for the Sales Enablement license cost as a programmatic scaling decision, not a per-walkthrough decision.

## Architectural Tradeoffs

**Targeted prompts vs. floating prompts:** Targeted prompts provide the highest user comprehension for specific UI actions but create a maintenance dependency on page layout stability. Floating prompts are maintenance-free but lower-signal. In orgs with frequent layout changes, a floating-heavy approach reduces operational risk at the cost of some guidance precision.

**Free tier vs. Sales Enablement:** The active-walkthrough limit forces prioritization. This is not purely a budget decision — it is an architectural discipline that prevents prompt sprawl. Orgs that upgrade to Sales Enablement without a governance model often end up with dozens of overlapping prompts degrading user experience. The free tier's constraint enforces a deliberate "highest value first" approach.

**Custom permission vs. profile as the audience gate:** `uiFormulaRule` accepts both. A profile criterion needs no new metadata but cannot narrow a shared profile and drifts as profiles are consolidated. A custom permission adds two files and a permission-set assignment, and in exchange the audience becomes grantable, revocable, and auditable per user. For anything cohort-shaped — a pilot, a region, a rollout wave — the permission is the cheaper option over the life of the prompt. Its two limits are that `operator` supports only `EQUAL`, so exclusion has to be modelled as a positive gate on a second permission, and that permission expressions work on app, Home, and record pages only.

**In-App Guidance vs. custom LWC onboarding:** For scenarios that depend on record data or user behaviour (e.g., "show only to users who have logged a call in the past 30 days"), custom LWC components or Flow-based solutions provide flexibility that In-App Guidance cannot — `uiFormulaRule` reads permissions and profile, never a field value. The trade-off is implementation and maintenance cost. In-App Guidance is the correct first choice for any scenario that fits within its targeting model.

## Anti-Patterns

1. **Creating new walkthroughs without deactivating stale ones** — Orgs accumulate walkthroughs over time. Without a periodic audit and deactivation process, the 3-slot cap becomes a blocker precisely when a high-priority adoption campaign needs a new walkthrough. Governance practice: review all active walkthroughs at the start of each release cycle and deactivate any that are past their intended window.

2. **Anchoring targeted prompts to frequently-changed UI elements** — Fields added to page layouts via seasonal releases, admin customization, or managed package updates are at risk of removal without notice. Anchoring targeted prompts to frequently-changed elements (e.g., a field added by a managed package) creates a brittle guidance implementation. Prefer floating prompts for content that is expected to persist beyond a single release cycle, and reserve targeted prompts for stable, long-lived UI elements.

3. **Using In-App Guidance as a substitute for change management** — Prompts are a reinforcement tool, not a replacement for stakeholder communication, training documentation, and rollout planning. An org that relies on a single walkthrough to drive adoption of a significant process change without any other communication will see poor outcomes. In-App Guidance should augment a change management program, not replace it.

## Official Sources Used

- Metadata API Developer Guide (v62 PDF), `Prompt` and `PromptVersion`, pp. 1801–1810 — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (every element name, enum value, and character limit in `references/metadata-examples.md`; the `isPublished`, `stepNumber`/`versionNumber`, `delayDays`/`timesToDisplay`, media-field, and `body`-length gotchas; the Experience Cloud access-rules wording)
- Metadata API Developer Guide (v62 PDF), `UiFormulaRule` / `UiFormulaCriterion`, pp. 1810–1811 — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the audience-gate tradeoff above; the three `leftValue` expression forms, the `EQUAL`-only operator, and the app/Home/record-page restriction)
- Metadata API Developer Guide (v62 PDF), `Prompt` Declarative Metadata Sample Definition and manifest, pp. 1811–1812 — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the shapes all examples are built from; `Prompt` wildcard support in package.xml; the `<videolink>` casing discrepancy)
- Metadata API Developer Guide (v62 PDF), `CustomPermission` p. 841 and `PermissionSetCustomPermissions` p. 1729 — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the two files section 5 of `metadata-examples.md` deploys alongside the prompt)
- Object Reference for Salesforce (v62 PDF), `PromptAction` pp. 4610–4613 — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the Analytics pillar and every adoption query; the `LastResult` value list; the lifetime-counter behaviour behind the republish gotcha)
- Object Reference for Salesforce (v62 PDF), `PromptError` pp. 4614–4615 — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the Reliability pillar: `ReferenceElementNotFound` and the targeted-to-floating conversion, plus `NoAccessToApp` / `NoAccessToPage` / `Unavailable`)
- Salesforce Help: Limits for In-App Guidance — https://help.salesforce.com/s/articleView?id=sf.customhelp_lex_prompt_limits.htm (the active-walkthrough cap and the Sales Enablement licence requirement; not fetchable as of 2026-09-04, and every restatement of the figure carries an UNVERIFIED marker)
- Salesforce Help: Considerations for Creating In-App Guidance — https://help.salesforce.com/s/articleView?id=sf.customhelp_lex_prompt_considerations.htm (referenced by both guides for supported Experience Cloud pages and for `videoLink`; not fetchable as of 2026-09-04)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (pillar framing for this file)
