# Examples - Org Hardening And Baseline Config

## Example 1: New Org Baseline Before App Growth

**Context:** A new business unit is launching on a fresh Salesforce org.

**Problem:** Teams want to defer security settings until after the first release.

**Solution:** Establish baseline settings for browser protections, session policy, trusted-site governance, and release-update review before application sprawl begins.

**Why it works:** The org grows from a known security baseline instead of accumulating exceptions first.

---

## Example 2: Exception Register For Trusted Sites

**Context:** The org has accumulated many CSP Trusted Sites and CORS allowlist entries.

**Problem:** Nobody can explain which ones are still needed.

**Solution:** Create an exception register that records owner, purpose, review date, and removal path for each trust exception.

**Why it works:** Convenience exceptions become governed risk decisions instead of hidden configuration drift.

---

## Anti-Pattern: Health Check Score As The Only Signal

**What practitioners do:** They point to the score and assume hardening is complete.

**What goes wrong:** Browser trust, session, and release-update gaps remain untreated.

**Correct approach:** Use Health Check as an input, not as the entire hardening program.
