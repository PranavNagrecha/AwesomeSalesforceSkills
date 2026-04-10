# LLM Anti-Patterns — MCAE (Pardot) API v5

Common mistakes AI coding assistants make when generating or advising on MCAE (Pardot) API v5 integrations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating Deprecated v3/v4 API URLs

**What the LLM generates:** Code that calls `https://pi.pardot.com/api/3/do/query/prospect?...` or `https://pi.pardot.com/api/4/do/create/prospect`, often with XML-formatted request bodies.

**Why it happens:** Large volumes of public tutorials, Stack Overflow answers, and GitHub repositories still reference v3/v4 patterns. Training data is biased toward older, more prevalent examples. The model may not have reliable signal that these versions are deprecated.

**Correct pattern:**

```
Base URL: https://pi.pardot.com/api/v5/objects/{object}
Method:   GET / POST / PATCH / DELETE
Body:     JSON (application/json)
Headers:  Authorization: Bearer {token}
          Pardot-Business-Unit-Id: {buId}
          Content-Type: application/json
```

**Detection hint:** Flag any URL containing `/api/3/`, `/api/4/`, `do/query/`, `do/create/`, or `do/update/`. Also flag any XML body or `output=json` parameter in v5 context.

---

## Anti-Pattern 2: Omitting the `Pardot-Business-Unit-Id` Header

**What the LLM generates:** HTTP request examples that include `Authorization: Bearer {token}` but no `Pardot-Business-Unit-Id` header. The generated code looks syntactically correct but will always fail at runtime.

**Why it happens:** This header is unique to the MCAE API and is not present in generic OAuth REST API patterns. Models trained on general REST API patterns do not include domain-specific required headers by default.

**Correct pattern:**

```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Pardot-Business-Unit-Id": bu_id,   # Required on every request
    "Content-Type": "application/json",
}
```

**Detection hint:** Search generated code for `pi.pardot.com` requests that lack `Pardot-Business-Unit-Id`. Any request to the MCAE API without this header will return 401.

---

## Anti-Pattern 3: Using Offset/Page Pagination Instead of nextPageMark

**What the LLM generates:** Pagination loops that increment a `page` counter or use an `offset` parameter, such as:

```python
# Wrong — offset pagination does not work in v5
for page in range(1, max_pages):
    url = f"{base_url}?page={page}&pageSize=200"
```

**Why it happens:** Offset-based pagination is the dominant pattern in most REST APIs and is what models default to. The cursor-based `nextPageMark` pattern used by MCAE v5 is less common and may not appear in training data.

**Correct pattern:**

```python
next_page_mark = None
while True:
    params = {"fields": "id,email,createdAt"}
    if next_page_mark:
        params["nextPageMark"] = next_page_mark
    resp = make_request(url, params=params)
    records.extend(resp["values"])
    next_page_mark = resp.get("nextPageMark")
    if not next_page_mark:
        break
```

**Detection hint:** Flag any generated code that uses `page=`, `offset=`, or increments a page counter in a loop when calling MCAE API v5 endpoints.

---

## Anti-Pattern 4: Confusing MCAE Prospects with Salesforce CRM Leads or Contacts

**What the LLM generates:** Code that tries to update Salesforce Leads or Contacts via the MCAE API, or code that queries MCAE Prospects via the Salesforce CRM REST API (`/services/data/vXX.X/sobjects/Lead/...`), treating them as the same object.

**Why it happens:** The MCAE/Pardot and Salesforce CRM are deeply connected, and documentation frequently references both objects in the same context. Models conflate the two because they represent the same real-world person, even though they are stored in different systems with different APIs.

**Correct pattern:**

```
MCAE Prospect operations:
  → https://pi.pardot.com/api/v5/objects/prospects

Salesforce CRM Lead/Contact operations:
  → https://{instance}.salesforce.com/services/data/vXX.X/sobjects/Lead/{id}

Sync between them:
  → Managed by Marketing Data Sharing rules; not called directly by integrations
```

**Detection hint:** Flag any code that mixes `pi.pardot.com` and `/services/data/` REST calls in the same operation assuming they read/write the same record. Also flag any SOQL queries in the context of MCAE Prospect retrieval.

---

## Anti-Pattern 5: Querying Visitors by Email to Find a Contact's Session History

**What the LLM generates:** A request like `GET /api/v5/objects/visitors?email=user@example.com` to find all browsing sessions for a known contact.

**Why it happens:** The model assumes Visitor records can be searched by identifying information in the same way as Prospect records. The naming ("Visitor") implies a known party, but in MCAE, Visitors are anonymous until converted.

**Correct pattern:**

```python
# Wrong: Visitors cannot be filtered by email
# GET /api/v5/objects/visitors?email=user@example.com

# Correct: Query VisitorActivities by prospectId
# First: get the Prospect ID from email
GET /api/v5/objects/prospects?email=user@example.com&fields=id

# Then: query all their engagement events
GET /api/v5/objects/visitor-activities?prospectId={id}&fields=id,type,typeName,createdAt
```

**Detection hint:** Flag any generated code that attempts to filter the `/visitors` endpoint by `email`, `name`, or other PII fields. Visitors are anonymous; use `/visitor-activities?prospectId=` for contact-specific engagement history.

---

## Anti-Pattern 6: Authenticating with Standalone Pardot Username/Password

**What the LLM generates:** Authentication code that POSTs to a Pardot-specific auth endpoint with a Pardot username, password, and user key — a pattern from the deprecated API v3/v4 authentication flow.

**Why it happens:** Old Pardot authentication (before SSO enforcement) used `https://pi.pardot.com/api/login/v3` with Pardot credentials. This pattern is prevalent in legacy documentation and tutorials. API v5 eliminates this entirely.

**Correct pattern:**

```python
# Correct: Salesforce OAuth only for API v5
token_url = "https://login.salesforce.com/services/oauth2/token"
payload = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}
# Use the returned access_token as Bearer token in all MCAE v5 requests
```

**Detection hint:** Flag any reference to `api/login/v3`, Pardot `user_key`, or authentication against `pi.pardot.com/api/login`. All authentication for v5 goes through `login.salesforce.com` or the org's My Domain OAuth endpoint.
