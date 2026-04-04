# Common LWC Runtime Errors — Work Template

Use this template when diagnosing or fixing a runtime error in a Lightning Web Component.

---

## Scope

**Skill:** `lwc/common-lwc-runtime-errors`

**Request summary:** (fill in: which component, what behavior, what error message was observed)

**Component name:** ___________

**Component path:** `force-app/main/default/lwc/___________/`

---

## Context Gathered

Answer these before making changes:

| Question | Answer |
|---|---|
| Debug mode enabled? | Yes / No |
| Security model active | Lightning Web Security (LWS) / Legacy Locker Service / Unknown |
| Lifecycle phase where error occurs | connectedCallback / renderedCallback / wire handler / event handler / other |
| Error message from console | (paste here) |
| Stack trace available? | Yes (paste) / No |
| Wire adapter involved? | Yes (LDS / Apex) / No |
| Third-party library involved? | Yes (name: ___) / No |
| Component renders child LWC components? | Yes / No |

---

## Error Category

Select the category that best matches the symptom:

- [ ] **Wire adapter failure** — `undefined` data, `TypeError` on wire result, stale data
- [ ] **Shadow DOM boundary violation** — `querySelector` returns null, can't reach child internals
- [ ] **Event propagation error** — parent never receives event, wrong target, event lost
- [ ] **Async rendering timing** — `connectedCallback` DOM access fails, `renderedCallback` runs repeatedly
- [ ] **NavigationMixin error** — navigation does nothing, page reference error
- [ ] **Locker / LWS conflict** — third-party library fails, `Access check failed`, SecureElement error
- [ ] **Slot projection problem** — slot content missing or in wrong location
- [ ] **Missing error boundary** — child error crashes page, no recovery UI shown

---

## Approach

**Error category selected:** ___________

**Pattern from SKILL.md that applies:**

(Example: "Wire Handler with Error Normalization" for wire failures)

**Root cause identified:**

(Describe what specific line or pattern is causing the issue)

**Fix planned:**

(Describe what change will be made and why it addresses the root cause)

---

## Fix Checklist

Copy the relevant items from the SKILL.md Review Checklist. Tick items as you complete them.

**Wire adapter errors:**
- [ ] Wire handler destructures `data` and `error` — not accessing `wiredResult.data` directly
- [ ] Template has `lwc:if={isLoading}`, `lwc:elseif={errorMessage}`, `lwc:else` guards
- [ ] `isLoading` flag initialized to `true` and set to `false` once wire responds
- [ ] `refreshApex` is only used if the wire uses an LDS adapter (not an Apex wire)

**Shadow DOM / DOM access errors:**
- [ ] All DOM queries use `this.template.querySelector`, not `document.querySelector`
- [ ] DOM-dependent initialization is in `renderedCallback`, not `connectedCallback`
- [ ] `renderedCallback` has an early-return guard to prevent repeat initialization

**Event propagation errors:**
- [ ] `composed: true` added to `CustomEvent` if it must cross shadow boundaries
- [ ] Event payload is in `event.detail`, not read from `event.target`

**NavigationMixin errors:**
- [ ] `type` string uses double underscores (e.g., `standard__recordPage`)
- [ ] All required attributes (`recordId`, `actionName`) are defined before Navigate is called
- [ ] Navigate is called after `connectedCallback` (component is connected)

**Third-party library / security model errors:**
- [ ] Security model identified (LWS vs Locker)
- [ ] Library tested against the active security model in a scratch org
- [ ] Library initialization is in `renderedCallback` with a guard

**Slot projection errors:**
- [ ] `slot="name"` in parent template matches `name` attribute on `<slot>` in child
- [ ] Default slot content is not accidentally consuming named slot content

**Error boundary errors:**
- [ ] Parent implements `errorCallback(error, stack)`
- [ ] Error state renders a user-visible message when `errorCallback` fires
- [ ] Child component DOM is removed on error (expected platform behavior — account for it in UX)

---

## Checker Output

Run after making the fix:

```bash
python3 skills/lwc/common-lwc-runtime-errors/scripts/check_common_lwc_runtime_errors.py \
  --manifest-dir force-app/main/default/lwc
```

Paste results here:

```
(paste checker output)
```

---

## Notes

Record any deviations from the standard patterns and why:

(e.g., "Used imperative Apex instead of @wire because data must refresh after save operations")

---

## Definition of Done

- [ ] Console error no longer appears in debug mode
- [ ] Error path is handled gracefully (user sees a message, not a blank area)
- [ ] Checker script reports no issues for this component
- [ ] `disconnectedCallback` cleans up any timers, instances, or external listeners
