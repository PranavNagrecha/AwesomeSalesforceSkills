# Gotchas - Navigation And Routing

Every claim below is grounded in the Lightning Web Components Developer Guide. Citations name the
page slug and the line in the extracted guide text used to author this file.

## Internal URL Strings Feel Stable Until The Component Moves

**What happens:** A path like `/lightning/r/...` or `/s/...` works in one environment and then breaks or behaves oddly in another.

**When it occurs:** Components are copied between Lightning Experience, mobile, and Experience Cloud without revisiting routing assumptions. The reach of the failure is wider than most authors expect: in an LWR site under Lightning Locker, a component cannot reference the global `window` object at all, so a `window.location.href` fallback does not degrade — it simply never runs.

**How to avoid:** Use PageReference-based navigation and generated URLs instead of internal route concatenation. A PageReference insulates the component from URL-format changes and lets the same component serve applications that use different URL formats.

*Grounded: `use-navigate-basic` L10089; `create-community-info` sample warning L3910–3911.*

---

## Custom URL State Needs Namespaced Keys

**What happens:** Query parameters appear in the URL, but the component cannot rely on them as a supported custom state contract.

**When it occurs:** State keys are added without a namespace prefix such as `c__`. The documented rule is stricter than "prefix it": a `state` property must use a namespace prefix *followed by two underscores*. Outside a managed package the prefix is `c`; inside one it is the package namespace.

**How to avoid:** Namespace every custom state key and keep the state model small and intention-revealing. Reserve un-namespaced keys for the ones the platform itself defines — `filterName` and `defaultFieldValues` on `standard__objectPage`, `nooverride` on record and object pages, `uid` on `standard__component`.

*Grounded: `use-navigate-add-params-url` L10139; `reference-page-reference-type` L22127, L22177–22179, L22198; `use-navigate-url-addressable` L10249.*

---

## `GenerateUrl` Hands Back A Promise, Not A URL

**What happens:** The anchor renders with an empty or `[object Promise]` href, and the link a user copies does not match the page the button actually opens.

**When it occurs:** The result of `this[NavigationMixin.GenerateUrl](pageRef)` is assigned straight to a field, or the component constructs `href` strings by hand while using `NavigationMixin` elsewhere. Two routing implementations then drift apart.

**How to avoid:** Resolve the promise — `.then((url) => { this.url = url; })` — and derive both the href and the `Navigate` call from one PageReference object. The guide's own pattern generates the URL in `connectedCallback()` and stores it in a field that the template binds.

*Grounded: `use-navigate-basic` L10103–10104, L10113–10115.*

---

## Experience Cloud Support Must Be Verified Explicitly

**What happens:** A pattern that works in internal Lightning pages fails in a site because the destination type or attribute requirements are different.

**When it occurs:** Components are built against internal-app navigation only and later reused in Experience Cloud. Three specific divergences bite: `standard__recordPage` does not support the `clone` or `edit` action names in Experience Builder sites; `objectApiName` is *required* on record and record-relationship page references in LWR sites while it is optional everywhere else; and on `standard__objectPage`, `list` and `home` resolve to the same page in a site.

**How to avoid:** Check the per-type support column before finalizing the contract, and always send `objectApiName` even where it is optional so the same page reference survives a move into an LWR site.

*Grounded: `reference-page-reference-type` L22079, L22174, L22192–22194, L22204–22205.*

---

## `standard__component` Does Not Work In Experience Builder Sites

**What happens:** A `standard__component` navigation that is correct in Lightning Experience produces nothing usable inside an Experience Cloud site.

**When it occurs:** A URL-addressable component is reused in a site. The `lightning__UrlAddressable` target — the thing that makes `standard__component` resolvable — is supported only in Lightning Experience, the Salesforce mobile app, and custom apps such as Lightning console apps. It is explicitly unsupported in Experience Builder sites because it interferes with custom domain and CDN support.

**How to avoid:** In a site, route to a named site page instead of a component page. Also note the sibling restriction: the whole `lightning/navigation` service is unsupported in Lightning Components for Visualforce and in Lightning Out 2.0 / Lightning Out (beta), and stays unsupported even when those containers are embedded inside Lightning Experience.

*Grounded: `use-navigate` L10078–10079; `targets-lightning-url-addressable` L19402–19406; `reference-page-reference-type` L22098.*

---

## Changing Only The Query String Does Not Rerender The View

**What happens:** The URL updates, the browser history entry updates, and the component keeps showing the old filter or tab.

**When it occurs:** A component navigates to its own page with a modified `state` and expects the framework to re-run its render path. In Lightning Experience and in Experience Builder sites built on Aura or LWR templates, the view is not rerendered when only the URL query string changes.

**How to avoid:** Observe `CurrentPageReference` with `@wire` and compare against the page reference's `state`. That wire is the reactivity mechanism; the navigation call alone is not.

*Grounded: `use-navigate-add-params-url` L10144–10145.*

---

## The PageReference You Are Handed Is Frozen

**What happens:** Assigning to `currentPageReference.state.c__view` throws or silently does nothing, and the navigation goes to the unmodified page.

**When it occurs:** A component tries to mutate the object delivered by the `CurrentPageReference` wire in order to build a "same page, different state" navigation target.

**How to avoid:** Copy before modifying — `Object.assign({}, pageReference)` for the reference and a second `Object.assign` for the nested `state` object, so other parameters already in the URL are preserved. Setting a state property to `undefined` in the copy is the documented way to *remove* it from the URL.

*Grounded: `use-navigate-add-params-url` L10138, L10142, L10173–10183.*

---

## `standard__objectPage` Action Names Do Not Include `view` Or `edit`

**What happens:** A row action that "edits the record" navigates to something other than the record's edit page, or lands on an unexpected object-level view.

**When it occurs:** An author reaches for `standard__objectPage` because the code already knows the `objectApiName`, and passes a record-level action. The valid `actionName` values for `standard__objectPage` are `home`, `list` and `new`; record-level actions (`clone`, `edit`, `view`) belong on `standard__recordPage`, which is also where `recordId` belongs. A `lightning-datatable` sample inside the guide itself pairs `standard__objectPage` with `actionName: "edit"` and a `recordId`, which is exactly the shape LLMs copy.

**How to avoid:** Choose the type by the *unit of navigation* — a record goes to `standard__recordPage`, an object's list or create page goes to `standard__objectPage` — before filling in attributes.

*Grounded: `reference-page-reference-type` L22174–22175, L22192–22195; contrasting in-guide sample, `data-table-tree-grid` L5637–5643.*

---

## `navItemPage.apiName` Is The Tab Name, Not The Tab Label

**What happens:** A custom-tab navigation resolves to nothing and produces no obvious error.

**When it occurs:** The label the admin typed is passed as `apiName`. A tab created with the label "My Custom Tab" has the tab name `My_Custom_Tab` — spaces become underscores. The `apiName` attribute of `standard__navItemPage` matches the tab *name*, and the target component additionally needs the `lightning__Tab` target in its own `.js-meta.xml`.

**How to avoid:** Read the tab name from Setup (or query `TabDefinition`) rather than deriving it from the label, and include the `CustomTab` in the same `package.xml` as the navigating component so the two never deploy apart.

*Grounded: `use-config-custom-tab` L7983, L7988–7989; `reference-page-reference-type` L22166–22169.*

---

## `NavigationMixin` Cannot Be Applied To A `LightningModal` Subclass

**What happens:** Navigation from inside a modal fails, and the usual fix — wrapping the modal's base class in `NavigationMixin()` — does not work either.

**When it occurs:** A screen quick action or custom modal that extends `LightningModal` needs to send the user somewhere on confirm. `NavigationMixin` may be used only with a component that extends `LightningElement`; it cannot be used directly in a component that extends `LightningModal`.

**How to avoid:** Build the PageReference in the modal's child component, dispatch it on a custom event through `Modal.open()`, and call `NavigationMixin.Navigate` in the parent component that opened the modal. Related: when a quick-action modal navigates to another modal, `replace` defaults to `false` and the new modal stacks on top of the old one — pass `true` to close the previous modal.

*Grounded: `use-navigate-modal` L10258–10260; `use-navigate-quick-action` L10323–10326.*
