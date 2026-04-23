# Apex Callable Interface — Work Template

Use this template when authoring a `Callable` extension point or dispatching via one.

## Scope

**Skill:** `apex-callable-interface`

**Request summary:** (what is being exposed for dynamic dispatch, and to whom)

## Classification

- [ ] Managed-package extension point (`global`)
- [ ] In-repo plugin registry (`public`)
- [ ] Test double / mock
- [ ] One-off dynamic-dispatch use

## Action Vocabulary

List every action the class will accept:

| Action | Args keys (name : type) | Return type | Notes |
|---|---|---|---|
| `{{action1}}` | `{{key1}}: {{Type1}}, {{key2}}: {{Type2}}` | `{{ReturnType}}` | |
| `{{action2}}` | | | |

## Context Gathered

- **Caller(s):** (Flow facade? Managed package consumer? Other Apex?)
- **Trust level:** (trusted internal vs external subscriber)
- **Transaction model:** (sync in caller's transaction — any governor concerns?)
- **Versioning plan:** (how will you add/remove actions without breaking consumers?)

## Approach

- [ ] Document action vocabulary in class header
- [ ] Implement `switch on action` with `when else` throw
- [ ] Validate args presence via `args.containsKey` before cast
- [ ] Publish action-name constants for consumers to import

## Code Sketch

```apex
/**
 * Callable actions:
 *   '{{action1}}':
 *      args   { '{{key1}}': {{Type1}}, '{{key2}}': {{Type2}} }
 *      returns {{ReturnType}}
 */
{{global|public}} with sharing class {{ClassName}} implements Callable {
    public static final String ACTION_{{ACTION1}} = '{{action1}}';

    public Object call(String action, Map<String, Object> args) {
        switch on action {
            when '{{action1}}' {
                if (!args.containsKey('{{key1}}')) {
                    throw new IllegalArgumentException('{{key1}} required');
                }
                return do{{Action1}}(({{Type1}}) args.get('{{key1}}'));
            }
            when else {
                throw new CalloutException('Unknown action: ' + action);
            }
        }
    }
}
```

## Checklist

- [ ] Class-level doc comment enumerates every action, args, return type.
- [ ] `switch on action` has `when else` that throws with a clear message.
- [ ] Every `args.get` is preceded by a `containsKey` or typed-null guard.
- [ ] Unknown-action test asserts the specific exception.
- [ ] Each documented action has a happy-path test.
- [ ] `global` chosen only if a managed-package extension point; otherwise `public`.

## Notes

Any edge cases (subscriber-namespace lookup, governor-cost documentation, deprecation plan for legacy actions).
