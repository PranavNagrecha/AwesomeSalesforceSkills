# Examples — Marketing Integration Patterns

## Example 1: Real-Time Transactional Email via Triggered Send (E-Commerce Order Confirmation)

**Context:** An e-commerce platform (Node.js backend) needs to send an order confirmation email immediately after a customer completes checkout. The email includes order number, line items, and estimated delivery date. Marketing Cloud owns the template and brand standards.

**Problem:** Without a Triggered Send pattern, the team considered using a Journey with an API Entry Source. This introduces 10–30 seconds of Journey processing overhead, and the multi-step Journey architecture adds unnecessary complexity for a one-shot transactional message. Additionally, the team initially tried to authenticate using the SOAP API username/password — this does not work for REST endpoints.

**Solution:**

1. In Marketing Cloud Email Studio, create a Triggered Send Definition (TSD):
   - Template: Order Confirmation (Content Builder)
   - Send Classification: Transactional
   - External Key: `ecomm-order-confirmation`
   - Status: Active

2. Create an Installed Package in Marketing Cloud Setup with API Integration. Enable scope: `Email` > `Send Email`. Note the `clientId`, `clientSecret`, and the tenant-specific `auth.marketingcloudapis.com` subdomain.

3. E-commerce backend — token acquisition (cached for 18 minutes):

```javascript
// Token acquisition — cache this, do not call per send
const tokenResponse = await fetch(
  'https://<subdomain>.auth.marketingcloudapis.com/v2/token',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      grant_type: 'client_credentials',
      client_id: process.env.MC_CLIENT_ID,
      client_secret: process.env.MC_CLIENT_SECRET
    })
  }
);
const { access_token, rest_instance_url } = await tokenResponse.json();
```

4. Send the transactional email on order completion:

```javascript
// Fire Triggered Send for order confirmation
const sendResponse = await fetch(
  `${rest_instance_url}/messaging/v1/messageDefinitionSends/key:ecomm-order-confirmation/send`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      To: {
        Address: order.customerEmail,
        SubscriberKey: order.customerId,
        ContactAttributes: {
          SubscriberAttributes: {
            FirstName: order.customerFirstName,
            OrderNumber: order.orderId,
            OrderTotal: order.total.toFixed(2),
            EstimatedDelivery: order.deliveryDate
          }
        }
      }
    })
  }
);
// Expect HTTP 202 Accepted
```

**Why it works:** The Triggered Send Definition acts as a pre-approved send slot. The REST call fires immediately, bypassing Journey Builder processing. The send classification marked Transactional ensures the message delivers even if the subscriber has unsubscribed from commercial messages.

---

## Example 2: Journey Injection from External E-Commerce Cart Abandonment

**Context:** An e-commerce platform detects that a logged-in customer added items to their cart but did not check out after 60 minutes. The platform needs to enroll the customer in a Marketing Cloud cart abandonment Journey that sends a reminder email at 1 hour, a discount offer at 24 hours, and a final nudge at 72 hours.

**Problem:** Using a Triggered Send cannot support a multi-step timed sequence. The team also needs to pass the cart value and product category into the Journey for personalization. Initially the team used the Journey ID in the API payload instead of the `eventDefinitionKey`, which produced a confusing 400 error.

**Solution:**

1. Build the Journey in Journey Builder:
   - Entry Source: REST API
   - After publishing, open Entry Source properties and copy the `eventDefinitionKey` (format: `APIEvent-<UUID>`)
   - Note: this key is NOT the Journey ID visible in the URL bar

2. Create an Installed Package with API Integration. Enable scope: `Journeys` > `Execute`.

3. Cart abandonment backend job (runs 60 minutes after cart creation with no purchase):

```python
import requests
import os

def get_mc_token():
    resp = requests.post(
        f"https://{os.environ['MC_SUBDOMAIN']}.auth.marketingcloudapis.com/v2/token",
        json={
            "grant_type": "client_credentials",
            "client_id": os.environ['MC_CLIENT_ID'],
            "client_secret": os.environ['MC_CLIENT_SECRET']
        }
    )
    resp.raise_for_status()
    data = resp.json()
    return data['access_token'], data['rest_instance_url']

def inject_into_journey(contact_key, email, cart_value, category, event_def_key):
    token, rest_url = get_mc_token()
    resp = requests.post(
        f"{rest_url}/interaction/v1/events",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "ContactKey": contact_key,
            "EventDefinitionKey": event_def_key,  # NOT the Journey ID
            "Data": {
                "EmailAddress": email,
                "CartValue": str(cart_value),
                "ProductCategory": category
            }
        }
    )
    resp.raise_for_status()
    return resp.json()
```

4. For batch processing of multiple abandoned carts (up to 100 per call), use the async endpoint:

```python
def inject_batch_into_journey(contacts_list, event_def_key):
    # contacts_list: list of dicts with ContactKey, EmailAddress, CartValue, etc.
    # Maximum 100 contacts per call
    token, rest_url = get_mc_token()
    resp = requests.post(
        f"{rest_url}/interaction/v1/events/async",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "EventDefinitionKey": event_def_key,
            "contacts": [
                {
                    "ContactKey": c["contact_key"],
                    "Data": {
                        "EmailAddress": c["email"],
                        "CartValue": str(c["cart_value"]),
                        "ProductCategory": c["category"]
                    }
                }
                for c in contacts_list[:100]  # Enforce 100-contact cap
            ]
        }
    )
    resp.raise_for_status()
    return resp.json()  # Returns requestId for polling
```

**Why it works:** The Journey processes each enrolled contact through the timed steps independently. Passing `CartValue` and `ProductCategory` as Data attributes makes them available as personalization strings in the Journey's email content. The `eventDefinitionKey` is the correct identifier for the REST API Entry Source — not the Journey ID.

---

## Example 3: Nightly Audience Sync from Data Warehouse via SFTP

**Context:** A retail company runs a data warehouse that calculates daily customer segments (high-value, lapsed, at-risk). Each night at 2 AM, the warehouse exports a CSV with 500,000 subscriber records. Marketing Cloud needs to refresh its segmentation Data Extension before morning campaigns run at 8 AM.

**Problem:** Calling the Marketing Cloud Data Extension REST API row by row for 500,000 records is not feasible — rate limits and per-call overhead make this a multi-hour process. The team initially attempted to use Journey Injection for this, which is designed for event-driven individual enrollments, not bulk data refreshes.

**Solution:**

1. Data warehouse generates CSV at 2 AM:
   ```
   SubscriberKey,EmailAddress,Segment,LTV,DaysSinceLastPurchase
   cust-001,jane@example.com,HighValue,1250.00,12
   cust-002,bob@example.com,Lapsed,89.00,365
   ...
   ```
   Column headers must exactly match the Data Extension field API names (case-sensitive).

2. Warehouse uploads the file to Marketing Cloud SFTP:
   ```
   Host: ftp.exacttarget.com (tenant-specific)
   Path: /import/nightly-segments/customers_<YYYYMMDD>.csv
   Credentials: From Marketing Cloud Setup > SFTP Users
   ```

3. Automation Studio automation:
   - Trigger: File Drop on `/import/nightly-segments/` (or scheduled at 2:30 AM)
   - Activity 1: Import Activity — Source: SFTP path pattern, Destination: `Segments_DE` Data Extension, Mode: "Add and Update", Subscriber management: "Map subscriber field" on `SubscriberKey`
   - Activity 2: SQL Activity — Refresh segmentation views
   - Activity 3: Send Activity — Campaign sends at 8 AM

**Why it works:** SFTP import handles bulk volumes natively. The Import Activity upserts records using `SubscriberKey` as the unique identifier. The Automation Studio trigger-to-send pipeline ensures the data is fresh before campaigns execute.

---

## Anti-Pattern: Using Journey ID Instead of `eventDefinitionKey`

**What practitioners do:** When injecting contacts into a Journey via the Event API, developers look up the Journey in the Journey Builder UI, copy the Journey ID from the browser URL bar (e.g., `abc123-def456-...`), and use that as the identifier in the API payload.

**What goes wrong:** The `/interaction/v1/events` endpoint does not accept a Journey ID. It requires the `eventDefinitionKey`, which is generated when the REST API Entry Source is added to the Journey. Using a Journey ID produces HTTP 400 with a payload like `{"message":"Event Definition not found"}`. The error message does not mention "wrong ID type," leading developers to assume the Journey is misconfigured rather than that they are using the wrong identifier.

**Correct approach:** In Journey Builder, open the Journey in edit mode. Click on the Entry Source. In the Entry Source properties panel, copy the value labeled `eventDefinitionKey` (formatted as `APIEvent-<UUID>`). Use this value — not the Journey ID — in all API calls.
