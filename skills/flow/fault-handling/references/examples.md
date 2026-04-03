# Flow Fault Handling — Examples

## Example 1: Record-Triggered Flow Fault Branch

Use this pattern whenever an `Update Records` or `Create Records` element can fail:

```text
[Update Records: Update Case]
    ├── Success -> [Next business step]
    └── Fault -> [Assignment: set errorDetail = {!$Flow.FaultMessage}]
                 -> [Create Records: Flow_Error_Log__c]
                 -> [Send Email / Custom Notification]
                 -> [End]
```

Why it works:
- The user-safe path and support path are separate.
- `$Flow.FaultMessage` is preserved for diagnostics.
- The batch failure is observable instead of silent.

## Example 2: Screen Flow User Message Pattern

```text
[Action or DML step]
    └── Fault -> [Assignment: userMessage = "We could not complete your request right now."]
                 -> [Assignment: supportDetail = {!$Flow.FaultMessage}]
                 -> [Screen: Friendly error + next step]
```

Rules:
- Show the user what to do next.
- Do not dump raw system text to the screen.
- Log the detailed message elsewhere for admins.

## Example 3: Bulk Review Questions for Record-Triggered Flow

Use these review prompts before approving a data-load-facing Flow:

```text
- Does the Flow query related data once per interview?
- Does any after-save path create many related records per source record?
- Does the invocable Apex behind any Action accept lists?
- If one record fails, do we understand how the batch behaves?
```
