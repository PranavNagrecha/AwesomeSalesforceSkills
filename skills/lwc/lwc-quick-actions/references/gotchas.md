# Gotchas — LWC Quick Actions

Non-obvious Salesforce platform behaviors that cause real production problems when building quick-action LWCs.

## Gotcha 1: Headless Actions Cannot Render Markup

**What happens:** An `actionType="Action"` bundle with a `.html` template has the template silently ignored. Developers add a spinner or a confirmation message expecting it to render while the Apex call runs — nothing appears.

**When it occurs:** Any time a headless action tries to show feedback during the `invoke()` promise.

**How to avoid:** If visual feedback is required, use a screen action. If only a yes/no is required, call `LightningConfirm.open({ ... })` from `invoke()` — it renders a platform dialog without the component needing its own template. Resolve the promise only after the user responds.

---

## Gotcha 2: `CloseActionScreenEvent` Does Not Save

**What happens:** The modal closes, but the custom fields are empty. The team assumes the close event committed the form.

**When it occurs:** Any screen action where the save is fired in parallel with the close, or where the close is dispatched in a `.then()` that was forgotten inside a detached callback.

**How to avoid:** Treat `CloseActionScreenEvent` as a dismiss signal only. Always `await` the Apex call (or the `lightning-record-edit-form` `onsuccess` event) before dispatching it. On error, keep the modal open so the user can retry.

---

## Gotcha 3: Modal Size Is Capped And Not Freely Configurable

**What happens:** Designers mock up a wide side-by-side layout; the quick-action modal caps the width and the layout squeezes.

**When it occurs:** Any design that assumes modal width is a component-level decision. The quick-action modal follows platform sizing rules and does not honor arbitrary CSS overrides.

**How to avoid:** Check the `lightning__RecordAction` docs for current sizing guidance. If the UX truly needs a wide surface, use `lwc-lightning-modal` from a button on the page instead of a quick action, or navigate to a dedicated page.

---

## Gotcha 4: `recordId` Is Only Auto-Injected Under `lightning__RecordAction`

**What happens:** The component is reused on an App Page or Home Page; `recordId` is now `undefined` and the Apex call throws.

**When it occurs:** Any time a quick-action bundle is also exposed to `lightning__AppPage`, `lightning__HomePage`, or `lightning__RecordPage` without wiring `recordId` for those targets explicitly.

**How to avoid:** Keep the quick-action bundle focused on one target, or wire each additional target explicitly via `targetConfig` properties. Guard `recordId` usage with an explicit null check at the top of every path that needs it.

---

## Gotcha 5: `invoke()` Must Return Or Resolve

**What happens:** The headless action button appears to hang or silently does nothing. No toast, no save confirmation. Console shows an uncaught promise rejection.

**When it occurs:** When `invoke()` throws synchronously, rejects without a `.catch`, or branches into a code path that never returns.

**How to avoid:** Wrap the body of `async invoke()` in a try/catch, always resolve by returning from the function, and fire a user-visible error toast on failure. Never leave an unhandled rejection inside `invoke()`.

---

## Gotcha 6: List-View Actions Do Not Inject `recordId`

**What happens:** A component works fine from the Opportunity record page, then fails silently when the same action is added to the Opportunity list view.

**When it occurs:** Any reuse of a single-record quick action on a list-view surface. List actions receive a list of ids via the target config, not a single `recordId`.

**How to avoid:** Build list actions as a separate bundle — or branch inside the component on the injected list input — and design for bulk semantics (transaction limits, partial success, progress feedback).

---

## Gotcha 7: Screen-Action Navigation Leaves The Record Context

**What happens:** A user clicks the quick action, fills the form, saves, lands on a newly created related record, and hits browser back expecting the original record — they bounce through an intermediate modal state or lose context.

**When it occurs:** Any screen action that calls `NavigationMixin.Navigate` after save without deciding whether the user should stay on the current record.

**How to avoid:** Decide the navigation intent up front. If users should stay, call `getRecordNotifyChange` instead of navigating. If users should leave, navigate before dispatching `CloseActionScreenEvent` so the modal dismissal is a single transition.
