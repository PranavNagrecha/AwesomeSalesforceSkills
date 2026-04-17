# Examples — OmniStudio Multi-Language

## Example 1: Four-language deploy

**Context:** Global retail

**Problem:** Previously hard-coded English

**Solution:**

Extract LDJ → translate → import; FlexCard static text replaced with `{$Label.…}`

**Why it works:** Centralized translation


---

## Example 2: Layout regression

**Context:** German labels 40% longer

**Problem:** Buttons truncated

**Solution:**

Flex layout + min-width on labels

**Why it works:** Design for length variance

