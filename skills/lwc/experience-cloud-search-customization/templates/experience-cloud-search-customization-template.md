# Experience Cloud Search Customization — Work Template

Use this template when configuring or extending search on an Experience Cloud site.

## Scope

**Skill:** `experience-cloud-search-customization`

**Request summary:** (fill in what the site owner or practitioner asked for — e.g., "Restrict search to Knowledge only", "Set up federated search from Confluence", "Guest users can't find articles")

---

## Context Gathered

Answer these before making any configuration changes.

| Question | Answer |
|---|---|
| Site name | |
| Site template type (LWR or Aura) | |
| Site URL (live or preview) | |
| Guest user search required? (yes/no) | |
| Org — Secure Guest User Record Access enabled? | |
| Objects to include in search scope | |
| Objects to exclude from search scope | |
| Federated search required? (yes/no) | |
| External endpoint URL (if federated) | |
| External endpoint authentication method (if federated) | |

---

## Search Manager Configuration

### Objects in Scope (target state)

| Object API Name | Allow Search enabled? | Searchable fields confirmed? | Added to Search Manager? |
|---|---|---|---|
| (e.g., Knowledge__kav) | | | |
| | | | |

### Promoted Search Terms

| Keyword / Phrase | Promoted Record / Article |
|---|---|
| | |

### Search Filters Exposed to Users

| Object | Filter Field | Rationale |
|---|---|---|
| | | |

---

## Guest User Access Configuration

Complete this section only if guest user search is required.

| Check | Status | Notes |
|---|---|---|
| Secure Guest User Record Access setting reviewed | | (Enabled / Disabled) |
| Guest User profile has read permission on each searchable object | | |
| OWD or sharing rules grant record-level access to guests for each object | | |
| Sharing sets configured (if applicable) | | |
| Guest data category visibility configured (for Knowledge) | | |
| Tested as real guest user in incognito browser | | |

---

## Search Component Placement

| Page | Component Name | Template Compatibility Confirmed? |
|---|---|---|
| Header / Search bar page | (Search Bar for LWR / Search for Aura) | |
| Search results page | (Search Results for LWR / N/A for Aura) | |

---

## Federated Search Configuration

Complete this section only if federated search is required.

| Item | Value |
|---|---|
| External source name | |
| Endpoint URL | |
| Endpoint reachable from Salesforce outbound IPs? | |
| Authentication type | |
| Federated source registered in Setup > Federated Search? | |
| Source enabled in Search Manager for this site? | |
| Custom federatedSearchResult LWC required? | |

---

## Checklist

- [ ] Site template type confirmed (LWR or Aura)
- [ ] Correct search component type placed for the template
- [ ] Search Manager scope explicitly configured (no default over-broad scope)
- [ ] All objects in scope have "Allow Search" enabled in Setup
- [ ] Guest user access requirements documented and configured (if applicable)
- [ ] Secure Guest User Record Access setting impact assessed (if guest search)
- [ ] Federated search endpoint tested end-to-end (if applicable)
- [ ] Search tested as real guest user in incognito session (if guest search)
- [ ] Promoted terms configured for high-volume known queries (if applicable)
- [ ] Admin Experience Builder preview NOT used as the sole guest search test

---

## Notes

(Record any deviations from the standard pattern, edge cases encountered, or configuration decisions that require future review.)
