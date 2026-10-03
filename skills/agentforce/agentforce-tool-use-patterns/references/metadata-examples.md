# Metadata Examples: Agentforce Tool Use Patterns

`SKILL.md` chooses a tool shape. This file shows what the chosen shape looks like as deployable metadata: the Apex reference action, its test, the `GenAiFunction` that turns it into an agent action, the input and output schemas the planner reads, and a `GenAiPlugin` (subagent) whose instructions encode the chaining order.

## Example 1: A read-only Apex tool with a shaped return, chained before a write

**Context.** An order-support subagent needs two tools. `Look_Up_Order_Status` reads one `Order` by its customer-facing number and returns four display strings plus an error field. `Cancel_Order` (not shown; built the same way with `isConfirmationRequired` set to `true`) must run only after the lookup.

### 1. Apex reference action

**File path:** `force-app/main/default/classes/OrderStatusLookupAction.cls`

```apex
public with sharing class OrderStatusLookupAction {

    public class Request {
        @InvocableVariable(
            required=true
            label='Order Number'
            description='The customer-facing order number exactly as printed on the receipt, for example 00000102. Not the 18-character Salesforce record ID.'
        )
        public String orderNumber;
    }

    public class Result {
        @InvocableVariable(label='Order Number' description='The order number that was looked up.')
        public String orderNumber;
        @InvocableVariable(label='Status' description='The order status as a user can read it, for example Activated.')
        public String status;
        @InvocableVariable(label='Total' description='The order total formatted with its currency, for example USD 149.99.')
        public String totalDisplay;
        @InvocableVariable(label='Start Date' description='The order start date in ISO format.')
        public String effectiveDate;
        @InvocableVariable(label='Error' description='Empty when the lookup worked. NOT_FOUND when no visible order has this number.')
        public String error;
    }

    @InvocableMethod(
        label='Look Up Order Status'
        description='Returns the status, total, and start date of one order identified by its order number. Use it before cancelling or changing an order. It never changes data.'
        category='Order Support'
    )
    public static List<Result> lookUp(List<Request> requests) {
        Set<String> numbers = new Set<String>();
        for (Request req : requests) {
            if (req != null && String.isNotBlank(req.orderNumber)) {
                numbers.add(req.orderNumber.trim());
            }
        }

        Map<String, Order> byNumber = new Map<String, Order>();
        for (Order o : [
            SELECT OrderNumber, Status, TotalAmount, EffectiveDate
            FROM Order
            WHERE OrderNumber IN :numbers
            WITH USER_MODE
        ]) {
            byNumber.put(o.OrderNumber, o);
        }

        // One result per request, in the same order, even when a lookup fails.
        List<Result> results = new List<Result>();
        for (Request req : requests) {
            Result res = new Result();
            String key = (req == null || req.orderNumber == null) ? null : req.orderNumber.trim();
            Order found = key == null ? null : byNumber.get(key);
            if (found == null) {
                res.orderNumber = key;
                res.error = 'NOT_FOUND';
            } else {
                res.orderNumber = found.OrderNumber;
                res.status = found.Status;
                res.totalDisplay = found.TotalAmount == null ? null : UserInfo.getDefaultCurrency() + ' ' + found.TotalAmount.setScale(2).toPlainString();
                res.effectiveDate = found.EffectiveDate == null ? null : String.valueOf(found.EffectiveDate);
                res.error = '';
            }
            results.add(res);
        }
        return results;
    }
}
```

The shape follows the Apex Developer Guide rules for invocable methods: one `List` parameter, a user-defined result type whose members carry `@InvocableVariable`, and outputs that match the inputs in size and order. Failures are reported in the result instead of thrown, as the guide recommends. `WITH USER_MODE` makes the agent user's sharing and field-level security apply. In API 67.0 and later, user mode is also the default.

### 2. Test class

**File path:** `force-app/main/default/classes/OrderStatusLookupActionTest.cls`

```apex
@IsTest
private class OrderStatusLookupActionTest {

    @TestSetup
    static void makeData() {
        Account acct = new Account(Name = 'Lookup Test Account');
        insert acct;
        insert new Order(AccountId = acct.Id, Status = 'Draft', EffectiveDate = Date.today());
    }

    @IsTest
    static void returnsOneResultPerRequestInOrder() {
        Order existing = [SELECT OrderNumber FROM Order LIMIT 1];

        OrderStatusLookupAction.Request hit = new OrderStatusLookupAction.Request();
        hit.orderNumber = existing.OrderNumber;
        OrderStatusLookupAction.Request miss = new OrderStatusLookupAction.Request();
        miss.orderNumber = 'NO-SUCH-ORDER';

        Test.startTest();
        List<OrderStatusLookupAction.Result> results =
            OrderStatusLookupAction.lookUp(new List<OrderStatusLookupAction.Request>{ hit, miss });
        Test.stopTest();

        Assert.areEqual(2, results.size(), 'One result per request');
        Assert.areEqual('', results[0].error, 'The existing order is found');
        Assert.areEqual('Draft', results[0].status);
        Assert.areEqual('NOT_FOUND', results[1].error, 'The missing order is reported, not thrown');
    }

    @IsTest
    static void blankInputIsReportedNotThrown() {
        OrderStatusLookupAction.Request blank = new OrderStatusLookupAction.Request();
        List<OrderStatusLookupAction.Result> results =
            OrderStatusLookupAction.lookUp(new List<OrderStatusLookupAction.Request>{ blank });
        Assert.areEqual('NOT_FOUND', results[0].error);
    }
}
```

UNVERIFIED (2026-10-03): the test assumes Orders are enabled and that `Draft` is an active Order status value, which is the default; orgs that renamed the status picklist must adjust the literal.

### 3. GenAiFunction (the agent action)

**File path:** `force-app/main/default/genAiFunctions/Look_Up_Order_Status/Look_Up_Order_Status.genAiFunction-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiFunction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Returns the status, total, and start date of one order identified by its customer-facing order number. Use it before cancelling or changing an order. It never changes data and does not accept Salesforce record IDs.</description>
    <invocationTarget>OrderStatusLookupAction</invocationTarget>
    <invocationTargetType>apex</invocationTargetType>
    <isConfirmationRequired>false</isConfirmationRequired>
    <isIncludeInProgressIndicator>true</isIncludeInProgressIndicator>
    <masterLabel>Look Up Order Status</masterLabel>
    <progressIndicatorMessage>Looking up your order</progressIndicatorMessage>
</GenAiFunction>
```

The Metadata API reference documents `input` and `output` folders, each holding a `schema.json`, inside the component. UNVERIFIED (2026-10-03): the exact source-format layout (a component folder named after the action, holding the `-meta.xml` file and the two schema folders) is inferred from that description and should be confirmed by retrieving one action from your org.

**File path:** `force-app/main/default/genAiFunctions/Look_Up_Order_Status/input/schema.json`

```json
{
  "required": ["orderNumber"],
  "properties": {
    "orderNumber": {
      "title": "Order Number",
      "description": "The customer-facing order number the user gave in this conversation. Ask the user for it if it is missing. Never pass a Salesforce record ID.",
      "lightning:type": "lightning__textType",
      "maxLength": 30,
      "lightning:isPII": false,
      "copilotAction:isUserInput": true
    }
  },
  "lightning:type": "lightning__objectType"
}
```

**File path:** `force-app/main/default/genAiFunctions/Look_Up_Order_Status/output/schema.json`

```json
{
  "properties": {
    "status": {
      "title": "Status",
      "description": "The order status to tell the user.",
      "lightning:type": "lightning__textType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": true,
      "copilotAction:isUsedByPlanner": true
    },
    "totalDisplay": {
      "title": "Total",
      "description": "The order total with currency, ready to read out.",
      "lightning:type": "lightning__textType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": true,
      "copilotAction:isUsedByPlanner": true
    },
    "error": {
      "title": "Error",
      "description": "NOT_FOUND when no visible order has this number. When set, apologise and ask the user to check the number.",
      "lightning:type": "lightning__textType",
      "lightning:isPII": false,
      "copilotAction:isDisplayable": false,
      "copilotAction:isUsedByPlanner": true
    }
  },
  "lightning:type": "lightning__objectType"
}
```

`maxLength` 30 matches `Order.OrderNumber` (maximum 30 characters, Object Reference). The `lightning__textType` maximum is 250 characters (Metadata API reference). At least one output property must set `copilotAction:isUsedByPlanner` to `true`, or the planner returns random responses (Metadata API reference, GenAiFunction output folder).

### 4. GenAiPlugin (the subagent) with the chaining instruction

**File path:** `force-app/main/default/genAiPlugins/Order_Support/Order_Support.genAiPlugin-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiPlugin xmlns="http://soap.sforce.com/2006/04/metadata" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <description>Handles questions about the status of an existing order and requests to cancel an order the customer already placed.</description>
    <developerName>Order_Support</developerName>
    <genAiFunctions>
        <functionName>Look_Up_Order_Status</functionName>
    </genAiFunctions>
    <genAiFunctions>
        <functionName>Cancel_Order</functionName>
    </genAiFunctions>
    <genAiPluginInstructions>
        <description>Look_Up_Order_Status must be called directly prior to Cancel_Order to confirm the order exists and to read its status back to the user.</description>
        <developerName>lookup_before_cancel</developerName>
        <language xsi:nil="true"/>
        <masterLabel>lookup before cancel</masterLabel>
    </genAiPluginInstructions>
    <genAiPluginInstructions>
        <description>If Look_Up_Order_Status returns NOT_FOUND, ask the user to check the order number and do not call Cancel_Order.</description>
        <developerName>stop_on_not_found</developerName>
        <language xsi:nil="true"/>
        <masterLabel>stop on not found</masterLabel>
    </genAiPluginInstructions>
    <language>en_US</language>
    <masterLabel>Order Support</masterLabel>
    <pluginType>Topic</pluginType>
    <scope>Your job is to look up existing orders and cancel them when the customer confirms. You do not create orders or issue refunds.</scope>
</GenAiPlugin>
```

The dependent-action wording mirrors the Generative AI guide's own example ("The action IdentifyRecordByName must be called directly prior to this action") and the standard General CRM topic's instruction ("ExtractRecordFieldsAndValuesFromUserInput must be called prior to UpdateRecordFields"). UNVERIFIED (2026-10-03): the accepted value format for the top-level `language` element; `en_US` is assumed from the locale codes the guide lists.

## package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>OrderStatusLookupAction</members>
        <members>OrderStatusLookupActionTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Look_Up_Order_Status</members>
        <name>GenAiFunction</name>
    </types>
    <types>
        <members>Order_Support</members>
        <name>GenAiPlugin</name>
    </types>
    <version>66.0</version>
</Package>
```

`GenAiFunction` and `GenAiPlugin` deployed this way land in the asset library. In Winter '26 and later orgs, actions and subagents created inside a particular agent are retrieved through `GenAiPlannerBundle` instead (Metadata API reference, GenAiFunction and GenAiPlugin usage notes).

## Deploy order

1. Apex classes and tests first. Publishing an agent does not deploy Apex or flows, so the reference action must already exist.
2. `GenAiFunction`, which references the class through `invocationTarget`.
3. `GenAiPlugin`, which references the function by API name.
4. Add the subagent to the agent in Agentforce Builder, or publish the agent definition that references it.

## Verification

- Run `OrderStatusLookupActionTest`; both methods pass.
- Run `python3 skills/agentforce/agentforce-tool-use-patterns/scripts/check_agentforce_tool_use_patterns.py --manifest-dir force-app/main/default`; no ERROR lines.
- In Agentforce Builder preview, ask "what is the status of order 00000102, and then cancel it". The plan shows `Look_Up_Order_Status` before `Cancel_Order`, and the cancel step asks for confirmation.
