# Examples — CSP and Trusted URLs

## Example 1: Add Stripe.js to an LWC checkout

**Context:** B2C LWR site.

**Problem:** Browser blocks https://js.stripe.com with 'Refused to load script'.

**Solution:**

Trusted URL https://js.stripe.com, context Experience Cloud LWR, directives script-src + connect-src + frame-src (for 3DS).

**Why it works:** Stripe needs all three; omitting frame-src breaks 3D Secure challenges.


---

## Example 2: Call internal analytics API from Lightning

**Context:** LEX dashboard.

**Problem:** fetch('https://analytics.corp.com/...') blocked.

**Solution:**

Trusted URL https://analytics.corp.com, context Lightning Experience, directive connect-src only.

**Why it works:** Read-only API; no scripts or frames from that origin.

