# Well-Architected Notes - LWC Modal And Overlay

## Relevant Pillars

### User Experience

Overlays change how users move through the application. Choosing the lightest appropriate pattern and keeping dismissal clear improves flow and reduces friction.

### Reliability

Reliable overlays have explicit open, save, cancel, and close behavior. Weak result contracts or broken focus return create inconsistent experiences that are hard to reproduce.

## Architectural Tradeoffs

- **Modal focus vs on-page continuity:** a modal can focus the user on one task, but it removes page context and requires stronger lifecycle management.
- **Reusable modal component vs parent-owned markup:** centralizing overlay logic improves consistency, while local markup can feel quicker until defects accumulate.
- **Blocking save windows vs cancel freedom:** sometimes close must be delayed briefly, but extended lockout harms usability.
- **`LightningModal` vs screen quick action:** a `LightningModal` gives you a result promise and a launcher you control; a screen quick action gives you Setup-managed placement on the record page but no return value and an X button that bypasses your Cancel logic. Placement convenience is paid for in control.
- **Custom modal component vs `confirm`/`alert`/`prompt`:** the three notification modules need no component, no template, and no test bundle. Building a `LightningModal` subclass for a yes/no question buys nothing but a file to maintain.
- **Portability across containers:** `ShowToastEvent` does not work in LWR Experience Cloud sites or standalone apps, so a component intended to run in more than one container should standardise on `lightning/toast` even where the older module would work.

## Anti-Patterns

1. **Modal for every message** - the UI blocks users even when a toast or inline message would be clearer.
2. **Hand-rolled dialog markup everywhere** - focus and dismissal behavior drift across components, and the markup depends on base-component internals that change between releases.
3. **Nested overlay stacks** - users lose context and escape paths become unclear; when stacking is unavoidable, it should be a chosen `replace` value rather than the inherited default.
4. **Result contracts left implicit** - `close()` with no argument makes cancel and save indistinguishable to the caller.
5. **Cleanup behind a quick action's Cancel button** - the header X skips it, so the cleanup is optional in practice.

## Official Sources Used

- Lightning Web Components Developer Guide, *Modal Windows* (`use-dialog-modal`) - the extension model rather than a `<lightning-modal>` tag, the default import from `lightning/modal`, `lightning-modal-body` required with header and footer optional, `close(value)` returning the value to the caller, and `open()` supplying the modal's properties. https://developer.salesforce.com/docs/platform/lwc/guide/use-dialog-modal.html
- Lightning Web Components Developer Guide, *Navigate From a Modal* (`use-navigate-modal`) - `NavigationMixin` is restricted to components extending `LightningElement` and cannot be used directly on a `LightningModal` subclass; the child/modal/parent relay is the supported workaround. https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate-modal.html
- Lightning Web Components Developer Guide, *Quick Action Navigation* (`use-navigate-quick-action`) - `replace` defaults to false so a newer modal stacks on the previous one, `replace` true closes it, and two documented cases preserve the previous modal regardless. https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate-quick-action.html
- Lightning Web Components Developer Guide, *Create Screen Quick Actions* (`use-quick-actions-screen`) - the screen quick action's modal, `CloseActionScreenEvent` from `lightning/actions`, the header X bypassing custom Cancel logic, `recordId` arriving through an `@api` setter rather than `connectedCallback()`, and `lightning-quick-action-panel` as the frame. https://developer.salesforce.com/docs/platform/lwc/guide/use-quick-actions-screen.html
- Lightning Web Components Developer Guide, *Alert / Confirm / Prompt Modals* (`use-dialog-alert`, `use-dialog-confirm`, `use-dialog-prompt`) - each module's `open()` returns a promise instead of halting execution, alert and prompt take `theme` while confirm takes `variant`, confirm resolves `true`/`false`, prompt resolves the entered text or `null`. https://developer.salesforce.com/docs/platform/lwc/guide/use-dialog.html
- Lightning Web Components Developer Guide, *Toast Notifications* (`use-toast`) - `lightning/toast` is the preferred module, `lightning/platformShowToastEvent` is unsupported in LWR Experience Cloud sites and standalone apps, and `lightning/toastContainer` defaults to 3 toasts, top-center, fixed, one instance per page, queueing the rest. https://developer.salesforce.com/docs/platform/lwc/guide/use-toast.html
- Lightning Web Components Developer Guide, *Base Components Usage Patterns* (`base-components-patterns`) - only `lightning/modal` and `lightning/datatable` support class extension, extension supplies the open and close mechanisms, and you must not rely on a base component's internal markup or CSS classes. https://developer.salesforce.com/docs/platform/lwc/guide/base-components-patterns.html
- Lightning Web Components Developer Guide, *Handle Focus* (`create-components-focus`) - only `tabindex` values `0` and `-1` are supported, and `tabindex` must not be combined with `delegatesFocus`; the constraint that makes hand-built focus traps expensive. https://developer.salesforce.com/docs/platform/lwc/guide/create-components-focus.html
- Lightning Web Components Developer Guide, *Write Jest Tests* (`unit-testing-using-jest-create-tests`) - the `^lightning/modal$` `moduleNameMapper` entry, the shared-jsdom reset in `afterEach`, and `element.shadowRoot` as the test-only API for crossing the shadow boundary. https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-create-tests.html
- Lightning Web Components Developer Guide, *API Versioning* (`get-started-api-versioning`) - setting `apiVersion` in the `-meta.xml` is required from Spring '25 (v63.0) onward, and the latest valid value is the org's current release. https://developer.salesforce.com/docs/platform/lwc/guide/get-started-api-versioning.html
- Lightning Web Components Developer Guide, *General Guidelines for Creating a Custom Property Editor* (`use-experience-cloud-general-guidelines`) - flyouts, popouts, and window overlays are prohibited in an Experience Builder custom property editor. https://developer.salesforce.com/docs/platform/lwc/guide/use-experience-cloud-general-guidelines.html
- Component Reference: `lightning/modal` - the specification tab is the only source for `size`, `label`, `description`, and `disableClose`; every claim in this package that depends on those properties carries an UNVERIFIED marker. https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-modal.html

UNVERIFIED (2026-09-05): the Component Reference pages could not be fetched while this package was
written (help.salesforce.com and the Lightning Component Library are not retrievable here). Every
attribute-level claim sourced from them is marked at the point of use in `references/code-examples.md`
and `references/gotchas.md` rather than being asserted silently.
