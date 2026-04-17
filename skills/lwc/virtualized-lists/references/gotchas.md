# Gotchas — LWC Virtualized Lists

## Gotcha 1: Variable row height

**What happens:** Items jump around on scroll.

**When it occurs:** Free-form content.

**How to avoid:** Fix height or measure first.


---

## Gotcha 2: aria-rowcount missing

**What happens:** Screen reader reports 'list with 20 items' on a 10k list.

**When it occurs:** Default HTML.

**How to avoid:** Set aria-rowcount + aria-setsize.


---

## Gotcha 3: Client-side filter on big list

**What happens:** Re-filters 10k rows on each keystroke; jank.

**When it occurs:** Filter input typed fast.

**How to avoid:** Debounce + server-side filter.

