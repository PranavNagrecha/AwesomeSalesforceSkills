# Examples — Clickjack and Frame Protection

## Example 1: Partner portal embedded in partner site

**Context:** Customer portal iframe'd by dealer.com.

**Problem:** Framing fails; default policy is same-origin.

**Solution:**

Experience Cloud site → Clickjack Protection → 'Allow framing by specific external domains' → add https://dealer.com.

**Why it works:** Minimum necessary allow-list preserves clickjack protection.


---

## Example 2: Visualforce page invoked by a canvas app

**Context:** Canvas app frames the VF.

**Problem:** VF refuses to load.

**Solution:**

Canvas apps require 'Framing by Salesforce servers' on the page; enable the matching option in Session Settings.

**Why it works:** Canvas proxies through Salesforce domain — the targeted option is appropriate.

