# Commerce LWC Components — Work Template

Use this template when building or reviewing a custom LWC for a B2B Commerce or D2C LWR storefront.

## Scope

**Skill:** `commerce-lwc-components`

**Request summary:** (fill in — e.g., "Build a custom product price display tile for the B2B store PDP")

## Context Gathered

Record answers to the Before Starting questions from SKILL.md:

- **Store type (B2B or D2C):**
- **Target page type (PDP, PLP, cart page, checkout step, wishlist page):**
- **Salesforce release version:**
- **Component role (product display / cart / checkout / wishlist / comparison):**
- **Known constraints (field restrictions, buyer account context, catalog limitations):**

## Wire Adapters Selected

List the `commerce/*` wire adapters or imperative functions this component will use:

| Operation | Module | Adapter / Function | Read or Mutate? |
|---|---|---|---|
| (e.g.) Load product fields | `commerce/productApi` | `getProduct` | Read |
| (e.g.) Get negotiated price | `commerce/productApi` | `getProductPrice` | Read |
| (e.g.) Add to cart | `commerce/cartApi` | `addItemToCart` | Mutate |
| (e.g.) Toggle wishlist | `commerce/wishlistApi` | `addToWishlist` / `removeFromWishlist` | Mutate |

## Component Structure

**Component name:** `______________`

**Files:**
- `______.js` — controller
- `______.html` — template
- `______.js-meta.xml` — registration

**Meta XML checklist:**
- [ ] `<isExposed>true</isExposed>` is set
- [ ] `<capability>lightningCommunity__RelaxedCSP</capability>` is declared
- [ ] Correct `<target>` entries for the store page type
- [ ] Design-time `<targetConfigs>` declared for any admin-configurable properties

## Approach

Which pattern from SKILL.md applies?

- [ ] Product display with storefront wire adapter
- [ ] Cart mutation with imperative call
- [ ] Wishlist toggle (wire read + imperative mutate)
- [ ] Custom checkout step component
- [ ] Other: ___________

Reason for pattern choice:

## Review Checklist

- [ ] All data reads use `commerce/*` wire adapters — no `lightning/uiRecordApi` imports
- [ ] All cart/wishlist mutations are in user-gesture event handlers (not lifecycle hooks)
- [ ] `lightningCommunity__RelaxedCSP` capability declared in `.js-meta.xml`
- [ ] `isExposed: true` and correct `<targets>` in `.js-meta.xml`
- [ ] No hardcoded store IDs, catalog IDs, or buyer group IDs
- [ ] `getProduct` fields use bare field API names (e.g., `'Name'`, not `'Product2.Name'`)
- [ ] `innerHTML` assignments (if any) sanitize data before rendering
- [ ] Component tested in Experience Builder preview AND live store page
- [ ] Deployed via SFDX (`sf project deploy start`), not Change Set
- [ ] `python3 scripts/check_commerce_lwc_components.py --manifest-dir <lwc-dir>` passes

## Deployment Notes

- SFDX deploy command used:
- Org alias:
- Component visible in Experience Builder after deploy: yes / no
- Tested on page types:

## Notes

Record any deviations from the standard pattern and why:
</content>
</invoke>