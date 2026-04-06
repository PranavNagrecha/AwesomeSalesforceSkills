# Mixed DML and Setup Objects — Work Template

Use this template when resolving or preventing MIXED_DML_OPERATION errors.

## Scope

**Skill:** `mixed-dml-and-setup-objects`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Execution context:** (test class / production trigger / batch / scheduled / queueable)
- **Setup objects involved:** (User / UserRole / PermissionSet / PermissionSetAssignment / Group / GroupMember / other)
- **Non-setup objects involved:** (list all)
- **Is the setup DML essential in the same logical operation?** (yes — must happen together / no — can be deferred)

## DML Classification

| DML Statement | SObject | Setup? | Current Location |
|---|---|---|---|
| insert | | yes/no | (method/class name) |
| insert | | yes/no | (method/class name) |
| update | | yes/no | (method/class name) |

## Approach

- [ ] **Test context:** Use `System.runAs()` to isolate setup-object DML
- [ ] **Production context:** Use `@future` or Queueable to defer setup-object DML
- [ ] **Order:** Non-setup DML runs first; setup DML runs in isolated context

## Checklist

- [ ] All DML targets classified as setup or non-setup
- [ ] No setup and non-setup DML share the same synchronous execution context
- [ ] Test classes use `System.runAs()` to isolate setup-object DML
- [ ] Production code uses `@future` or Queueable for setup-object DML
- [ ] `@future` methods tested with `Test.startTest()` / `Test.stopTest()` boundaries
- [ ] User creation uses unique username (timestamp suffix) to avoid duplicate conflicts
- [ ] `@testSetup` methods also respect the mixed DML boundary

## Notes

(Record any deviations from the standard pattern and why.)
