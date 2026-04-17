# Gotchas — LWC Internationalization

## Gotcha 1: String concat dates

**What happens:** 'MM/DD/YYYY' reads as DD/MM in EU.

**When it occurs:** Manual date formatting.

**How to avoid:** Use lightning-formatted-date-time.


---

## Gotcha 2: Label over 255 chars

**What happens:** Deploy fails.

**When it occurs:** Long help text.

**How to avoid:** Break into multiple labels or store in CMDT.


---

## Gotcha 3: RTL icon mirroring

**What happens:** Chevron points wrong way.

**When it occurs:** SVG embedded inline.

**How to avoid:** Use lightning-icon; test in RTL.

