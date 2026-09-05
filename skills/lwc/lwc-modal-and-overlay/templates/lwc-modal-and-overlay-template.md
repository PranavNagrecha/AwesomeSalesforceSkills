# Overlay Decision Worksheet

## Interaction Summary

- User action:
- Why interruption is needed:
- Expected outcome:

## Pattern Choice

| Option | Choose? | Why |
|---|---|---|
| Toast |  |  |
| Inline message |  |  |
| Confirmation dialog |  |  |
| `LightningModal` |  |  |

## Modal Contract

- Opened from:
- Initial focus target:
- Cancel behavior:
- Success behavior:
- Close result shape (every path, tagged): cancel = , confirm = , error =
- Focus return target:
- Navigation out of the modal (relay through launcher? PageReference built where?):
- `replace` value if this navigates onto another modal:

## Risk Review

- Nested overlays avoided:
- Temporary close lock needed:
- Accessibility owner:

## Sign-Off Checklist

- [ ] Chosen pattern is the lightest one that works.
- [ ] Focus and dismissal are explicit.
- [ ] Returned result is documented.
- [ ] Overlay is not standing in for a larger page workflow.
- [ ] Every `@api` input on the modal appears in the launcher's `open({...})` config.
- [ ] `python3 scripts/check_lwc_modal_and_overlay.py --manifest-dir <lwc dir>` reports no ISSUE.
