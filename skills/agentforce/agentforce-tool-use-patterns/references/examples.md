# Examples — Agentforce Tool Use Patterns

## Example 1: Tool description tuned for LLM selection

**Context:** An agent has two actions: `Look_Up_Order` (by order number) and `Look_Up_Customer_Orders` (all orders for an account). The LLM keeps calling the wrong one.

**Problem:** Descriptions were:
- `Look_Up_Order`: "Fetches order details."
- `Look_Up_Customer_Orders`: "Fetches customer orders."

Too similar; the LLM can't discriminate.

**Solution:**

```apex
@InvocableMethod(
    label='Look Up Order (by order number)',
    description='Retrieve one specific order by its customer-facing order number (like "A7842"). USE WHEN the user provides an order number. DO NOT use for browsing or listing — use Look_Up_Customer_Orders instead.'
)

@InvocableMethod(
    label='List Recent Orders',
    description='Retrieve a list of a customer\'s recent orders (last 12 months). USE WHEN the user asks to "see my orders" or "find an order" without providing an order number. DO NOT use when the user already provided an order number.'
)
```

**Why it works:** The "USE WHEN / DO NOT use" contrast in the description is what discriminates the two tools for the LLM. Selection accuracy improves sharply.

---

## Example 2: Short, shaped return

**Context:** `Look_Up_Order` was returning the entire `Order` sObject — 47 fields, 800 tokens — and the agent's next-turn responses were degrading.

**Problem:** The LLM has to process every returned field. Most are irrelevant; they consume context.

**Solution:**

```apex
public class OrderResult {
    @InvocableVariable(label='Order Number')
    public String orderNumber;

    @InvocableVariable(label='Status (display text)')
    public String statusDisplay;      // "Processing", not "PROC_INT_2"

    @InvocableVariable(label='Total (formatted)')
    public String totalDisplay;       // "$149.99", not 149.99

    @InvocableVariable(label='Item Summary')
    public String itemsSummary;       // "2× Blue Scarf, 1× Hat"

    @InvocableVariable(label='Place Date')
    public String placedDisplay;      // "March 3, 2026"

    @InvocableVariable(label='Error')
    public String error;
}
```

Five fields, ~60 tokens. LLM response quality recovers.

**Why it works:** LLMs perform better with human-readable strings ("$149.99") than raw codes (149.99, OrderCurrency__c). Every omitted field is a token saved.

---

## Example 3: Action chaining vs monolith

**Context:** A "cancel order and refund" workflow.

**Problem:** Monolithic `Cancel_And_Refund` action:
- Opaque to the user ("did it cancel? did it refund?")
- If refund fails after cancellation, recovery is complex
- Agent can't branch mid-operation

**Solution:**

Split into three actions:
1. `Look_Up_Order(orderNumber)` → returns order + user-confirmation-required flag.
2. `Cancel_Order(orderNumber)` → returns cancellation confirmation.
3. `Issue_Refund(orderNumber, amount)` → returns refund ID.

Agent flow:
```
User: "Cancel my order A7842 and refund me."
Agent: [Look_Up_Order(A7842)] → "I see A7842 for $149.99. Proceed?"
User: "Yes."
Agent: [Cancel_Order(A7842)] → "Cancelled. Now issuing refund..."
Agent: [Issue_Refund(A7842, 149.99)] → "Refunded $149.99 to your Visa ending 4242. Will post in 3-5 days."
```

**Why it works:** Each step is independently testable, independently recoverable. If refund fails after cancel, the agent can say "cancel succeeded but refund is pending — let me get you a specialist" — user isn't left wondering.

---

## Anti-Pattern: Ambiguous argument names

**What practitioners do:** `@InvocableVariable public String id;` with no description.

**What goes wrong:** LLM passes account Id when the action wants order number, or vice versa.

**Correct approach:** Name by semantics, describe precisely, give format examples:

```apex
@InvocableVariable(
    required=true
    label='Order Number'
    description='Customer-facing order number exactly as printed on the receipt (format: letter+4 digits, e.g. A7842). NOT the 15-character Salesforce record ID.'
)
public String orderNumber;
```

---

## Anti-Pattern: Dumping the sObject into the return

**What practitioners do:** Return an `Account` record as `@InvocableVariable public Account account;`.

**What goes wrong:** The LLM gets all 200 fields, most irrelevant. Context cost balloons.

**Correct approach:** Extract 3-6 fields into a purpose-built DTO with human-readable values. See Example 2.
