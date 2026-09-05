# LWC Accessibility Review Template

## Component Scope

- Component name:
- User journey:
- Interactive elements:
- Custom markup or composite widgets:

## Accessibility Contract

- Keyboard entry point:
- Expected tab order:
- Focus target on open:
- Focus target on validation error:
- Focus target on close:

## Labeling Review

- Inputs with labels:
- Icon-only actions and text equivalents:
- Decorative content marked presentational:
- ARIA attributes that need justification:

## Validation And Messaging

- Error surfaces:
- Programmatic association for errors:
- Live-region needs:

## Sign-Off Checklist

- [ ] Interactive elements are semantic.
- [ ] Focus behavior is documented and tested.
- [ ] Screen-reader names are clear.
- [ ] No custom widget ships without a keyboard model.

## Boundary And Association Check

Fill this in before writing markup — it is the design, not documentation of it.

| Field / control | Component that owns the label | Component that owns the error text | Same template? | If no: light DOM or redesign? |
|---|---|---|---|---|
|  |  |  |  |  |

- ARIA attributes exposed with `@api` (each must use `setAttribute`/`getAttribute` if it references an id):
- Focus mechanism chosen (`delegatesFocus` / explicit `@api` method / parent-set `tabindex`):
- `tabindex` values used (must be only `0` or `-1`, and none at all with `delegatesFocus`):
- Live-region announcements, and polite (`role="status"`) vs assertive (`role="alert"`):
- Target environments (Lightning Experience / Experience Cloud / Lightning Out / native shadow):

## Verification Record

- [ ] `python3 skills/lwc/lwc-accessibility/scripts/check_lwc_accessibility.py --manifest-dir <lwc root>` — clean
- [ ] `npm run test:unit` — accessibility assertions pass
- [ ] Keyboard-only pass: tab in, tab through, error state, save, close
- [ ] Screen-reader pass: label, help text, error announcement, status announcement
- Reviewer / date:
