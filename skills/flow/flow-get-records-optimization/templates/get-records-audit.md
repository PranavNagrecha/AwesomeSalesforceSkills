# Get Records Audit

## Flow

Name:
Trigger type:
SOQL count target (per transaction):

## Get Records Inventory

| # | Element name | Object | Filter fields (indexed?) | Fields selected | Limit | In loop? |
|---|--------------|--------|--------------------------|-----------------|-------|----------|
|   |              |        |                          |                 |       | [ ]      |

## Issues

- [ ] Any Get Records inside a loop (move out)
- [ ] Any Get Records using "All fields" (trim)
- [ ] Any Get Records with no explicit limit
- [ ] First filter field on hot queries is not indexed
- [ ] Leading-wildcard LIKE
- [ ] Sort on unindexed field with large result
- [ ] Same query repeated across screens / elements

## Final SOQL count

- Before:
- After:
