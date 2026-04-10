# Marketing Cloud Custom Activities — Work Template

Use this template when building, debugging, or reviewing a custom Journey Builder activity, custom split activity, or custom entry source.

## Scope

**Skill:** `marketing-cloud-custom-activities`

**Request summary:** (fill in what the practitioner asked for — e.g., "build a custom split activity that routes contacts by loyalty tier")

**Activity type:** (custom activity / custom split / custom entry source)

---

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding:

- **Marketing Cloud BU:** (which BU owns this journey?)
- **Installed Package name:** (name of the package where the App Extension is/will be registered)
- **Hosting environment:** (Heroku / AWS / Azure / other — confirm HTTPS is provisioned)
- **Execute endpoint timeout budget:** (default 30s — is async pattern required?)
- **For custom splits — outcome branches:** (list each branch key and label)
- **JWT validation strategy:** (will HS256 with the package secret be used? Where is the secret stored?)
- **Known constraints:** (rate limits on downstream APIs, concurrent contact volume, etc.)

---

## Activity Definition (config.json)

Document the planned config.json structure before implementing:

**workflowApiVersion:** `1.1`

**Endpoints:**
- execute: `https://`
- save: `https://`
- publish: `https://`
- validate: `https://`

**UI URL:** `https://`

**configurationArguments schema:**
- Field 1: (name, type, purpose)
- Field 2: (name, type, purpose)

**For custom splits — outcomes:**
| Key | Label |
|-----|-------|
| (key) | (display label) |

---

## Postmonger Event Plan

Document the Postmonger events this activity will use:

| Event | Direction | Purpose |
|-------|-----------|---------|
| `ready` | JB → Activity | Initialization complete; triggers may now be called |
| `requestedSchema` | JB → Activity | Returns journey entry event schema for field mapping |
| `requestedData` | JB → Activity | Returns current saved configurationArguments |
| `requestedInteractionDefaults` | JB → Activity | Returns journey-level defaults |
| `updatedActivity` | JB → Activity | Fired when practitioner saves activity configuration |

---

## Execute Endpoint Design

**Async or sync?** (async if downstream calls may exceed ~5s; sync acceptable for fast lookups)

**JWT verification:** (confirm library and where Installed Package secret is stored — never in code)

**Response format:**
- Standard activity: `{ "status": "ok" }` with HTTP 200
- Custom split: `{ "branchResult": "<outcome_key>" }` with HTTP 200

**Fallback behavior on error:** (what branchResult is returned if the downstream API fails or times out?)

---

## Approach

Which pattern from SKILL.md applies and why:

- [ ] Standard Custom Activity (no branching; side-effect only)
- [ ] Custom Split Activity (real-time API-based routing)
- [ ] Custom Entry Source (non-DE entry into journey)

Rationale: (explain why this pattern was chosen over alternatives)

---

## Implementation Checklist

Copy and tick each item as you complete it:

**config.json**
- [ ] All URLs use HTTPS
- [ ] `workflowApiVersion` set to `"1.1"`
- [ ] `endpoints.execute.url` is present and correct
- [ ] `userInterfaces.configModal.url` is present and correct
- [ ] For custom splits: all outcome keys and labels are present in `metaData.outcomes`

**customActivity.js / UI**
- [ ] Postmonger session instantiated before any event registration
- [ ] All `connection.on(...)` listeners registered before `connection.trigger('ready')`
- [ ] `connection.trigger('ready')` called to begin handshake
- [ ] `requestedSchema` handler populates field mapping UI
- [ ] `updatedActivity` handler persists activity configuration
- [ ] UI is served over HTTPS

**Execute endpoint**
- [ ] JWT verified from `Authorization: Bearer <token>` header on every request
- [ ] Returns HTTP 200 (not 201, 202, 204)
- [ ] Returns within 30s (or configured timeout); async enqueue pattern used if needed
- [ ] For custom splits: `branchResult` key matches exactly a key in config.json `metaData.outcomes`
- [ ] Fallback `branchResult` returned on error (never let exceptions bubble to a 500)

**save / publish / validate endpoints**
- [ ] All three implemented and return HTTP 200
- [ ] `validate` returns appropriate validation state

**Testing**
- [ ] Tested with a real contact in a test journey in a sandbox BU
- [ ] Journey activity error logs checked — no errors
- [ ] Custom split: all branches exercised with test contacts
- [ ] Execute endpoint tested with an invalid JWT — returns 401/403

---

## Notes

Record any deviations from the standard pattern and why:

- (e.g., "Using synchronous execute because downstream API p99 is <2s and traffic volume is low")
- (e.g., "Outcome keys are prefixed with BU identifier to support multi-BU deployment")
