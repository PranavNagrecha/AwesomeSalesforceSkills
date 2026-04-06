# Gotchas — OmniStudio Remote Actions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Namespace Mismatch Compiles but Fails at Runtime

**What happens:** An Apex class implements `vlocity_cmt.VlocityOpenInterface2` in an org that has native OmniStudio (or vice versa). The class compiles successfully. When the OmniScript calls the action, a `System.TypeException` or `ClassCastException` is thrown because the framework looks for the implementation under its own namespace.

**When it occurs:** During sandbox refresh from a managed-package org to a native org, or when copying code between orgs with different OmniStudio installation types. The error surfaces only at runtime because Apex does not cross-validate interface namespaces at compile time.

**How to avoid:** Check the installed package type before writing or deploying an Apex Remote Action class. Query `SELECT NamespacePrefix FROM PackageLicense WHERE NamespacePrefix IN ('vlocity_cmt','omnistudio')` to determine which namespace is active. Use a factory pattern or conditional compilation if you must support both.

---

## Gotcha 2: outputMap Return Value Is Ignored

**What happens:** A developer writes the Apex class to return a value from `invokeMethod` (e.g., `return resultMap;`) and puts nothing in `outputMap`. The OmniScript action completes without error, but the Response JSON Path mapping finds nothing because the framework reads exclusively from `outputMap`.

**When it occurs:** Developers coming from standard Apex or Aura controller patterns expect the return value to carry the response. The `VlocityOpenInterface2` contract is unusual in that the return value is ignored by the framework for data purposes.

**How to avoid:** Always populate `outputMap` with all data the OmniScript needs. Treat the return value as reserved for the framework (returning `null` is the standard practice). Add a unit test that asserts `outputMap` contains the expected keys after `invokeMethod` executes.

---

## Gotcha 3: Blank Send JSON Path Sends the Entire Step Node Including Internal Keys

**What happens:** When Send JSON Path is left blank, the framework sends the entire OmniScript step node to the backend. This node includes internal framework keys (e.g., `vlcSI`, `vlcClass`, element-level metadata) in addition to user-entered data. If the backend parses strictly (e.g., rejects unknown fields), the call fails with a deserialization error.

**When it occurs:** Common in early development when the action is tested with minimal data and the extra keys do not cause problems. Breaks in production when more elements are added to the step or when the backend schema validation becomes stricter.

**How to avoid:** Always set an explicit Send JSON Path that targets only the data the backend expects. If multiple fields from different elements are needed, use a Set Values element to assemble them into a single node before the action fires.

---

## Gotcha 4: Response JSON Path Case Sensitivity Causes Silent Nulls

**What happens:** The Apex class writes `outputMap.put('accountName', value)` but the OmniScript Response JSON Path or downstream merge field references `AccountName` (capital A, capital N). The field resolves to null. No error is thrown because JSON path resolution in OmniStudio is case-sensitive — a miss is simply null, not an exception.

**When it occurs:** When different developers build the Apex class and the OmniScript. Also common after refactoring Apex code where a variable rename changes the key casing in `outputMap`.

**How to avoid:** Establish a naming convention (e.g., PascalCase for all outputMap keys) and document it in the input/output contract. Add assertions in Apex unit tests that verify exact key names. In the OmniScript, use the debugger to inspect the raw action response and confirm key casing before building downstream references.

---

## Gotcha 5: Fire and Forget Actions in Conditional Steps Can Fire Multiple Times

**What happens:** A Fire and Forget action inside a conditional step (show/hide logic) fires every time the step becomes visible. If the user navigates back and forth, the action fires on each re-entry. This can create duplicate records, send duplicate callouts, or trigger idempotency violations on external systems.

**When it occurs:** When the conditional step's visibility toggles based on earlier step data and the user revises their inputs. Each visibility transition re-initializes the step and re-fires Fire and Forget actions.

**How to avoid:** Guard the server-side logic with idempotency checks (e.g., check for existing records before inserting). Alternatively, switch to On Click invoke mode so the action fires only on explicit user intent. If the action must fire automatically, use a Set Values element with a flag to track whether the action has already executed and skip re-execution.
