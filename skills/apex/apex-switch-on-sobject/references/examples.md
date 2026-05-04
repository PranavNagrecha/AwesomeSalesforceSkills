# Examples — Apex Switch on SObject

## Example 1 — Replacing an instanceof chain in a generic handler

**Context.** Legacy framework code dispatches a generic `validate(SObject)`
across Account, Contact, Lead. The current implementation casts inside each
branch.

**Before.**

```apex
public static List<String> validate(SObject record) {
    List<String> errs = new List<String>();
    if (record instanceof Account) {
        Account a = (Account) record;
        if (String.isBlank(a.Name)) errs.add('Name required');
    } else if (record instanceof Contact) {
        Contact c = (Contact) record;
        if (String.isBlank(c.LastName)) errs.add('Last name required');
    } else if (record instanceof Lead) {
        Lead l = (Lead) record;
        if (String.isBlank(l.Company)) errs.add('Company required');
    }
    return errs;
}
```

**After.**

```apex
public static List<String> validate(SObject record) {
    List<String> errs = new List<String>();
    switch on record {
        when Account a   { if (String.isBlank(a.Name))     errs.add('Name required');       }
        when Contact c   { if (String.isBlank(c.LastName)) errs.add('Last name required');  }
        when Lead l      { if (String.isBlank(l.Company))  errs.add('Company required');    }
        when null        { errs.add('record was null');                                     }
        when else        { errs.add('Unsupported type: ' + record.getSObjectType());        }
    }
    return errs;
}
```

**Why it works.** The bindings (`a`, `c`, `l`) are typed inside their branches —
no manual cast. The `when null` and `when else` branches make the
unhandled-case behavior explicit instead of silent.

---

## Example 2 — Null-safety from `when null`

**Context.** Caller can pass null; old implementation crashed with NPE.

```apex
// Crashes when 'record' is null.
public static String labelFor(SObject record) {
    return record.getSObjectType().getDescribe().getLabel();
}

// Null-safe via switch on.
public static String labelFor(SObject record) {
    switch on record {
        when null        { return '(null)'; }
        when Account a   { return 'Account: ' + a.Name; }
        when Contact c   { return 'Contact: ' + c.LastName; }
        when else        { return 'Other: ' + record.getSObjectType(); }
    }
    return null; // unreachable, satisfies compiler
}
```

**Why it works.** `when null` is reached *before* any method is called on
`record`, so the dispatch itself can't NPE.

---

## Example 3 — Dispatch from a string API name (Type.forName trap)

**Context.** A custom-metadata-driven router takes the SObject API name as a
string and constructs a default record.

**Wrong instinct.**

```apex
// Compile error: switch expression isn't an SObject; Type.forName returns Type.
public static SObject createByName(String apiName) {
    switch on Type.forName(apiName) {  // ← Type, not SObject
        when ... { ... }
    }
}
```

**Why it's wrong.** `Type.forName()` returns `System.Type`. The switch-on-SObject
form needs an actual SObject expression.

**Right answer.**

```apex
public static SObject createByName(String apiName) {
    Schema.SObjectType t = Schema.getGlobalDescribe().get(apiName);
    if (t == null) throw new IllegalArgumentException('Unknown: ' + apiName);
    SObject prototype = t.newSObject();
    switch on prototype {
        when Account _   { return new Account(Name = 'Default'); }
        when Contact _   { return new Contact(LastName = 'Default'); }
        when else        { throw new IllegalArgumentException('Unsupported: ' + apiName); }
    }
    return null; // unreachable
}
```

The prototype is throw-away — only its type matters for the switch.

---

## Example 4 — Multi-type "shared logic" workaround

**Context.** Account and Lead both need the same address normalization;
Contact has different rules.

**Won't compile.**

```apex
when Account a, Lead l { /* ... 'a' or 'l'? compile error. */ }
```

**Workaround.** Two `when` branches calling a shared private method that
takes the common interface (here, the BillingStreet/Address fields, exposed
generically):

```apex
switch on record {
    when Account a   { normalize(a, a.BillingCity, a.BillingState); }
    when Lead l      { normalize(l, l.City, l.State);               }
    when Contact c   { /* different rules */                         }
    when else        { /* throw or log */                            }
}

private static void normalize(SObject r, String city, String state) {
    // Shared work without re-binding.
}
```

---

## Anti-Pattern: Omitting `when else`

```apex
// Latent bug — 'Order' silently does nothing.
switch on record {
    when Account a   { handleAccount(a); }
    when Contact c   { handleContact(c); }
}
```

**What goes wrong.** A future record type (Order, Case, custom object) gets
handed in. The switch produces no output, no exception, no log. The bug is
discovered weeks later when a stakeholder asks "why didn't the validation
fire on these orders?"

**Correct.** Always declare `when else` — either `throw` (programmer error,
the dispatch is supposed to be exhaustive) or `log + safe-default`
(non-exhaustive on purpose).
