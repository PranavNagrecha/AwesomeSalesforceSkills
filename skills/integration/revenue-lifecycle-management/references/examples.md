# Examples — Revenue Lifecycle Management

## Example 1: DRO Fulfillment Plan with Parallel Billing and Provisioning

**Context:** A SaaS company uses Revenue Cloud (RLM) for enterprise software orders. When an order is activated, billing setup, license provisioning, and welcome email must happen in parallel. Previously done manually, the team wanted to automate via DRO.

**Problem:** The team initially built a sequential Flow that ran billing → provisioning → email in order, taking 2+ hours. Parallel execution via DRO was needed.

**Solution:**

Design in DRO Setup:

```
Fulfillment Plan: "Enterprise Software Fulfillment"
  Swimlane 1: Billing
    Step 1: Auto-Task → Create Billing Schedule via Connect API
    Step 2: Milestone → "Billing Ready"
  
  Swimlane 2: Provisioning  
    Step 1: Callout → POST /api/provision to provisioning system
    Step 2: Manual Task → Provisioning team confirms activation
    Step 3: Milestone → "Provisioned"
  
  Swimlane 3: Communications
    Step 1: Auto-Task → Invoke "Send Welcome Flow" autolaunched Flow
    
  Synchronization: Communications swimlane waits for "Billing Ready" AND "Provisioned" milestones
    Step 2: Auto-Task → Invoke "Send Order Confirmation Flow"
```

**Why it works:** Billing and Provisioning run in parallel, reducing cycle time. The Communications swimlane waits for both to complete before sending the final confirmation. DRO handles the parallel coordination natively.

---

## Example 2: Creating Billing Schedule via Connect API After Order Activation

**Context:** After an enterprise order is activated, a billing schedule needs to be created for monthly invoicing over a 12-month contract.

**Problem:** The team expected billing schedules to auto-create like in legacy Salesforce Billing. In RLM, they must be explicitly created via Connect API after activation.

**Solution:**

```python
import requests

def create_billing_schedule(access_token: str, instance_url: str, 
                             order_item_id: str, contract_start: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "orderItemId": order_item_id,
        "billingStartDate": contract_start,
        "billingFrequency": "Monthly",
        "numberOfBillingPeriods": 12,
        "amount": 1200.00  # Monthly amount
    }
    resp = requests.post(
        f"{instance_url}/services/data/v63.0/commerce/billing/schedules",
        headers=headers,
        json=payload
    )
    resp.raise_for_status()
    return resp.json()

# Called from DRO Auto-Task after order activation
result = create_billing_schedule(
    access_token=token,
    instance_url="https://myorg.my.salesforce.com",
    order_item_id="0Oi...",
    contract_start="2026-05-01"
)
print(f"Created BillingSchedule: {result['id']}")
```

**Why it works:** Connect API creates a standard `BillingSchedule` object linked to the `OrderItem`. Unlike legacy Salesforce Billing, this is an explicit API call, not automatic on order activation.

---

## Anti-Pattern: Using blng__* Objects in an RLM Org

**What practitioners do:** Write SOQL against `blng__BillingSchedule__c` and `blng__Invoice__c` in a Revenue Cloud (RLM) org expecting to find billing data.

**What goes wrong:** These managed package objects from the legacy Salesforce Billing product do not exist in native RLM orgs. SOQL returns "object not found" errors. Even if the managed package is coincidentally installed, the data lives in completely different objects.

**Correct approach:** In native RLM orgs, use standard API object names: `BillingSchedule`, `Invoice`, `Payment`, `FinanceTransaction`. Confirm the product in use before writing any billing-related code.
