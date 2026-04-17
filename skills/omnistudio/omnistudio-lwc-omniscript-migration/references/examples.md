# Examples — OmniStudio LWC OmniScript Migration

## Example 1: Phased LWC cutover

**Context:** 80 OmniScripts

**Problem:** Big-bang migration risky

**Solution:**

Enable LWC mode org-wide; flip scripts one domain at a time; weekly QA rotation

**Why it works:** Isolated blast radius


---

## Example 2: Custom VF replacement

**Context:** Signature capture inside script

**Problem:** VF component couldn't render in LWC

**Solution:**

Rewrote as lwc-signature-pad component referenced via Custom LWC element in OmniScript

**Why it works:** Parity maintained

