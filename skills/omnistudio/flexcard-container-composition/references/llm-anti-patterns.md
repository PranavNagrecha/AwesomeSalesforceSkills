# LLM Anti-Patterns — FlexCard Composition

## Anti-Pattern 1: Direct SOQL Datasource On User-Facing Card

**What the LLM generates:** `SELECT AmountPaid__c, SSN__c FROM Contact`.

**Why it happens:** easiest to wire.

**Correct pattern:** IP with `WITH USER_MODE`, returning only the fields
the card needs.

## Anti-Pattern 2: Fat Card With Seven Tabs And Five Datasources

**What the LLM generates:** one card does everything.

**Why it happens:** fewer files to manage.

**Correct pattern:** parent container + child cards, each with its own
datasource and event contract.

## Anti-Pattern 3: Generic Event Name On A Shared Page

**What the LLM generates:** `rowselected` on two cards.

**Why it happens:** unaware names are global.

**Correct pattern:** `quoteselected`, `caseselected` — namespaced.

## Anti-Pattern 4: Pushing Detail Record Into Child Via Input Param

**What the LLM generates:** parent stringifies record, child parses.

**Why it happens:** "save a server call."

**Correct pattern:** parent fires event with id, child fetches detail.
Fresh data, cache-aware, less coupled.

## Anti-Pattern 5: Hardcoded URL In Action

**What the LLM generates:** `/lightning/r/Quote/{!recordId}/view`.

**Why it happens:** copy-paste from a browser.

**Correct pattern:** Navigate action type, let platform resolve.
