# Examples — MCAE (Pardot) API v5

## Example 1: Upsert a Prospect from a Server-Side Integration

**Context:** A company's e-commerce platform collects email opt-ins at checkout. A backend service needs to create or update the Prospect in Account Engagement each time a customer opts in, populating standard fields and a custom field.

**Problem:** The developer uses a basic HTTP client but forgets the `Pardot-Business-Unit-Id` header. Every request returns `401 Unauthorized`, which looks identical to an invalid OAuth token error. Hours are spent regenerating tokens before the missing header is identified.

**Solution:**

```python
import urllib.request
import urllib.parse
import json

# Step 1: Obtain OAuth token from Salesforce
token_url = "https://login.salesforce.com/services/oauth2/token"
token_data = urllib.parse.urlencode({
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}).encode()
token_req = urllib.request.Request(token_url, data=token_data, method="POST")
with urllib.request.urlopen(token_req) as resp:
    token_json = json.loads(resp.read())
access_token = token_json["access_token"]

# Step 2: Upsert Prospect — POST with email upserts if email already exists
bu_id = "0Uv000000000001"  # from Account Engagement Settings > Account Settings
prospect_url = "https://pi.pardot.com/api/v5/objects/prospects"

payload = json.dumps({
    "email": "customer@example.com",
    "firstName": "Alex",
    "lastName": "Nguyen",
    "company": "Acme Corp",
    "optedIn": True,
    # Custom field — must match API name in MCAE field configuration
    "checkoutSource__pc": "web-checkout"
}).encode()

headers = {
    "Authorization": f"Bearer {access_token}",
    "Pardot-Business-Unit-Id": bu_id,   # REQUIRED — missing this returns 401
    "Content-Type": "application/json",
}

req = urllib.request.Request(prospect_url, data=payload, headers=headers, method="POST")
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())

print(f"Prospect ID: {result['id']}")  # Same ID returned whether created or updated
```

**Why it works:** The `Pardot-Business-Unit-Id` header is present on every request. The POST endpoint upserts by email: if `customer@example.com` already exists in the BU, the existing record is updated and its `id` is returned. No pre-check query is needed.

---

## Example 2: Paginated Visitor Activity Export for a Prospect

**Context:** A data team needs to export all engagement events (email clicks, form submissions, page views) for a specific Prospect into a data warehouse. The Prospect has years of engagement history that spans many pages.

**Problem:** The developer uses a `page` offset parameter copied from a v3 API example. The v5 API ignores the `page` parameter entirely and always returns the first page, causing an infinite loop that repeatedly imports the same 200 records.

**Solution:**

```python
import urllib.request
import urllib.parse
import json

def fetch_all_visitor_activities(access_token: str, bu_id: str, prospect_id: str) -> list:
    """Fetch all visitor activity records for a prospect using nextPageMark pagination."""
    base_url = "https://pi.pardot.com/api/v5/objects/visitor-activities"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Pardot-Business-Unit-Id": bu_id,
    }

    # Activity type codes: 1=email click, 4=form submission, 6=page view,
    # 10=email open, 11=custom redirect, 13=file download
    fields = "id,type,typeName,createdAt,prospectId,emailId,formId,landingPageId"
    params = {
        "fields": fields,
        "prospectId": prospect_id,
        "orderBy": "createdAt",
        "orderByDirection": "ascending",
    }

    all_activities = []
    next_page_mark = None

    while True:
        if next_page_mark:
            params["nextPageMark"] = next_page_mark
        elif "nextPageMark" in params:
            del params["nextPageMark"]

        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        all_activities.extend(data.get("values", []))

        # nextPageMark is absent when there are no more pages
        next_page_mark = data.get("nextPageMark")
        if not next_page_mark:
            break

    return all_activities

activities = fetch_all_visitor_activities(access_token, bu_id, "12345")
print(f"Total activities exported: {len(activities)}")
```

**Why it works:** The loop follows `nextPageMark` from each response instead of incrementing a page offset. The loop terminates when `nextPageMark` is absent, which is the v5-canonical signal that the last page has been reached. Each page returns up to 200 records.

---

## Example 3: Form Handler Integration for an Existing Web Form

**Context:** A company has a contact form built in their CMS. Marketing wants form submissions to flow into MCAE and trigger an autoresponder, but the dev team does not want to replace the form with a Pardot-hosted form.

**Problem:** The developer tries to call the Prospects API directly from the browser-side JavaScript, which exposes the OAuth client secret in client-side code and violates security requirements.

**Solution:**

Configure a Form Handler in Account Engagement:
1. In Account Engagement, go to Content > Form Handlers > New Form Handler.
2. Name the handler, set the success location (redirect URL), and configure completion actions (e.g., "Add to List: Newsletter", "Send autoresponder email: Welcome Email").
3. Map each external form field name to the corresponding Prospect field (e.g., HTML `name="email"` maps to Prospect `email`; `name="company"` maps to `company`).
4. Note the Form Handler endpoint URL (format: `https://go.pardot.com/l/...` or the custom domain equivalent).

External form HTML — the action URL points to the Form Handler, no API credentials required:

```html
<form method="POST" action="https://go.pardot.com/l/123456/2024-01-01/abc123">
  <!-- Hidden field to identify the campaign source -->
  <input type="hidden" name="utm_source" value="website-contact">
  <input type="text"   name="first_name"  placeholder="First Name" required>
  <input type="text"   name="last_name"   placeholder="Last Name"  required>
  <input type="email"  name="email"       placeholder="Email"      required>
  <input type="text"   name="company"     placeholder="Company">
  <button type="submit">Contact Us</button>
</form>
```

**Why it works:** The Form Handler endpoint is a public URL — no OAuth token or BU ID header is required from the browser. Account Engagement receives the POST server-side, creates or upserts the Prospect, executes all configured completion actions, and redirects the visitor to the success URL. The client secret stays server-side.

---

## Anti-Pattern: Querying Visitors by Email

**What practitioners do:** Issue `GET /api/v5/objects/visitors?email=user@example.com` expecting to find visitor session records for a known contact.

**What goes wrong:** Visitors are anonymous session records — they are identified by a tracking cookie, not by email. The API does not support filtering Visitors by email. The request either returns an empty result set or a 400 error, depending on whether email is included as a valid filter field.

**Correct approach:** If you have a Prospect and want their engagement history, query VisitorActivities filtered by `prospectId`. The Prospect record links to Visitor records after conversion, but the correct query path for engagement data is VisitorActivities, not Visitors.
