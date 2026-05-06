# Well-Architected Notes — LWC Drag and Drop

## Relevant Pillars

- **Operational Excellence** — HTML5 drag-and-drop is the only
  drag primitive that works in LWC without a third-party library.
  The patterns are repetitive (`preventDefault` in `dragover`,
  state reset in `dragend`, MIME-based payload, separate keyboard
  path for accessibility) and centralizing them in a small
  shared module avoids re-litigating the same five bugs in every
  draggable component. Without a shared pattern, every
  drag-related component is a fresh place where `preventDefault`
  was forgotten and the drop didn't fire.

## Architectural Tradeoffs

The main tradeoff is **native HTML5 drag vs third-party library**.
HTML5 native is built in, no dependency, no bundle cost, but
fails on touch devices and has no keyboard support. A library
like Sortable.js wrapped in an LWC handles touch and provides
better visual feedback, at the cost of a bundle and a
maintained dependency.

Specifically:

- **Desktop-only kanban**: HTML5 native + a keyboard menu is
  acceptable.
- **Mobile-aware sortable list**: third-party library.
- **File-drop upload**: `lightning-file-upload` (don't reinvent).
- **Accessibility-first product**: third-party library with
  proven keyboard support.

The keyboard path is non-negotiable. WCAG 2.1 requires keyboard
operability; if the only path is a drag, the component fails.

## Anti-Patterns

1. **Forgetting `preventDefault` in `dragover`.** The drop never
   fires.
2. **No keyboard alternative.** WCAG failure; unusable for
   keyboard-only users.
3. **State reset in `drop`, not `dragend`.** Drop-outside and
   Escape leave the component in a stuck state.

## Official Sources Used

- HTML Living Standard: Drag and Drop — https://html.spec.whatwg.org/multipage/dnd.html
- DataTransfer (MDN) — https://developer.mozilla.org/en-US/docs/Web/API/DataTransfer
- LWC: HTML Templates — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-html-templates.html
- WCAG 2.1 SC 2.1.1 Keyboard — https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html
- Lightning Web Security (LWS) Migration Guide — https://developer.salesforce.com/docs/platform/lwc/guide/security-lws.html
- Salesforce Well-Architected: Trusted (Accessible) — https://architect.salesforce.com/well-architected/trusted/inclusive
