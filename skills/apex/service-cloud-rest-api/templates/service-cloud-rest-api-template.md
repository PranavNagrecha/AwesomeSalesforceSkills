# Service Cloud REST API — Work Template

Use this template when working on a Service Cloud REST API integration task (Knowledge API or Enhanced Chat API).

## Scope

**Skill:** `service-cloud-rest-api`

**Request summary:** (fill in what the user asked for)

**API family in scope:** (check all that apply)
- [ ] Knowledge REST API — `/knowledgeManagement/` (authenticated authoring/agent access)
- [ ] Knowledge REST API — `/support/knowledgeWithSEO/` (guest/Experience Cloud access)
- [ ] Enhanced Chat API — MIAW (Messaging for In-App and Web)
- [ ] Legacy Chat REST API migration (retiring/retired Feb 14, 2026)

## Context Gathered

- **Salesforce API version:** (confirm v44+ for URL-name lookup)
- **Authentication context:** (authenticated internal user / Experience Cloud guest / external system)
- **Data category group developer name(s):** (from Setup > Data Categories)
- **Data category developer name(s):** (from Setup > Data Categories — not the label)
- **Guest profile data category visibility confirmed:** (yes / no / not applicable)
- **Legacy Chat REST API references found:** (list files/classes or "none")

## Endpoint Selection

| Use Case | Endpoint |
|---|---|
| Authenticated agent article retrieval | `/services/data/v62.0/knowledgeManagement/articles` |
| Guest/portal article retrieval | `/services/data/v62.0/support/knowledgeWithSEO/articles` |
| Article lookup by URL name (guest) | `/services/data/v62.0/support/knowledgeWithSEO/articles?urlName=<slug>` |
| Enhanced Chat session (MIAW) | `/services/data/v62.0/connect/messaging/` |

**Selected endpoint for this task:** (fill in)

**Justification:** (why this endpoint for this auth context)

## Approach

(Which pattern from SKILL.md applies? Why?)

- [ ] Pattern 1: Authenticated Knowledge retrieval with data category filter
- [ ] Pattern 2: Guest article lookup by URL name
- [ ] Pattern 3: Legacy Chat REST API migration to MIAW

## Implementation Notes

**Data category parameters:**
- `categoryGroup` developer name: ___________
- `category` developer name: ___________
- URL-encoded values confirmed: (yes / no)

**Response empty-array handling:** (describe how the code handles `articles: []`)

**Error handling:** (describe 4xx/5xx handling and retry strategy if any)

## Checklist

- [ ] Correct endpoint family for authentication context
- [ ] API version is v44+ if URL-name lookup is used
- [ ] Data category developer names (not labels) used in query parameters
- [ ] No remaining references to legacy Chat REST API (`/chat/rest/` or `X-LIVEAGENT-*`)
- [ ] Empty-array response handled explicitly
- [ ] OAuth token / session ID not exposed in client-side JavaScript
- [ ] Apex test class mocks `HttpResponse` for both success and empty-result scenarios
- [ ] `EncodingUtil.urlEncode()` applied to all query parameter values

## Notes

(Record any deviations from the standard pattern and why.)
