# Gotchas — Flow Data Tables

## Gotcha 1: Huge collection

**What happens:** Browser sluggish.

**When it occurs:** >1500 rows.

**How to avoid:** Pre-filter or use LWC.


---

## Gotcha 2: Missing empty state

**What happens:** Empty screen with no action.

**When it occurs:** Collection zero-length.

**How to avoid:** Decision + message screen.


---

## Gotcha 3: Lookup column confusion

**What happens:** Shows Id not Name.

**When it occurs:** Lookup config.

**How to avoid:** Configure displayed field to Name via column type.

