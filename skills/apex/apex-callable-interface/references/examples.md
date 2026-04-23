# Examples — Apex Callable Interface

## Example 1: Managed Package Extension Point

**Context:** An ISV ships a payment-gateway package. Subscribers need to override the "customize payment receipt" step with their own Apex logic without modifying the package.

**Problem:** Hardcoded class references inside the package only work for whatever the package shipped. Subscribers have no way to inject.

**Solution:**

```apex
// ============ In the managed package ============
global with sharing class PaymentExtensionPoint {
    global static Map<String, Object> customizeReceipt(Map<String, Object> args) {
        PaymentExtension__mdt config = PaymentExtension__mdt.getInstance('Receipt_Customizer');
        if (config == null || String.isBlank(config.ClassName__c)) {
            return args; // no customization
        }
        Type t = Type.forName(config.Namespace__c, config.ClassName__c);
        if (t == null || !Callable.class.isAssignableFrom(t)) {
            throw new PaymentExtensionException(
                'Configured class is not Callable: ' + config.ClassName__c);
        }
        Object result = ((Callable) t.newInstance()).call('customize', args);
        return (Map<String, Object>) result;
    }
}

// ============ In the subscriber org ============
public with sharing class AcmeReceiptCustomizer implements Callable {
    public Object call(String action, Map<String, Object> args) {
        if (action != 'customize') {
            throw new CalloutException('Unsupported action: ' + action);
        }
        Map<String, Object> updated = new Map<String, Object>(args);
        updated.put('receiptFooter', 'Thanks for choosing Acme!');
        return updated;
    }
}
```

**Why it works:** The package references the subscriber class by name (via metadata), not by type. The subscriber implements `Callable`, a stable interface. Package upgrades never break the subscriber; subscriber changes never require a package deploy.

---

## Example 2: In-Repo Plugin Registry

**Context:** A sales team wants to enable different territories to run different lead-enrichment logic — without redeploying Apex every time a territory changes its rules.

**Problem:** A giant `if (territory == 'NA') ... else if ('EU') ...` block grows unbounded and requires code changes for every territory.

**Solution:**

```apex
public with sharing class LeadEnricher {
    public static void enrich(List<Lead> leads, String territory) {
        Territory_Plugin__mdt plugin = Territory_Plugin__mdt.getInstance(territory);
        if (plugin == null) return; // no enrichment configured
        Type t = Type.forName(plugin.ClassName__c);
        if (t == null || !Callable.class.isAssignableFrom(t)) {
            System.debug(LoggingLevel.WARN, 'Unusable plugin: ' + plugin.ClassName__c);
            return;
        }
        Callable c = (Callable) t.newInstance();
        c.call('enrich', new Map<String, Object>{ 'leads' => leads });
    }
}

public with sharing class NaLeadEnricher implements Callable {
    public Object call(String action, Map<String, Object> args) {
        if (action != 'enrich') return null;
        List<Lead> leads = (List<Lead>) args.get('leads');
        for (Lead l : leads) {
            l.LeadSource = l.LeadSource == null ? 'NA-Auto' : l.LeadSource;
        }
        return null;
    }
}
```

**Why it works:** Adding a new territory means creating one custom metadata record and one class that implements `Callable`. No changes to `LeadEnricher`.

---

## Example 3: Documented Multi-Action Contract

**Context:** A service class exposes multiple CRUD-ish actions for a managed-package extension point.

**Solution:**

```apex
/**
 * Callable actions:
 *   'create':
 *      args  { 'name': String, 'amount': Decimal, 'closeDate': Date }
 *      returns Id of created Opportunity
 *   'close':
 *      args  { 'opportunityId': Id, 'won': Boolean }
 *      returns null
 *   'quote':
 *      args  { 'opportunityId': Id }
 *      returns Decimal total
 */
global with sharing class OpportunityActions implements Callable {
    global Object call(String action, Map<String, Object> args) {
        switch on action {
            when 'create' {
                return createOpp(
                    (String) args.get('name'),
                    (Decimal) args.get('amount'),
                    (Date) args.get('closeDate')
                );
            }
            when 'close' {
                closeOpp((Id) args.get('opportunityId'), (Boolean) args.get('won'));
                return null;
            }
            when 'quote' {
                return quote((Id) args.get('opportunityId'));
            }
            when else {
                throw new CalloutException('Unknown OpportunityActions action: ' + action);
            }
        }
    }
    // private implementations elided
}
```

---

## Anti-Pattern: Using `Callable` For Flow Invocation

**What practitioners do:** Mark an Apex class as `implements Callable` and expect Flow to call it.

**What goes wrong:** Flow's "Apex Action" picker only sees `@InvocableMethod` methods. `Callable` is invisible to Flow. The admin's Flow has nothing to select.

**Correct approach:** Use `@InvocableMethod` for Flow. If you also want dynamic dispatch, the `@InvocableMethod` body can internally call a `Callable` registry — but the interface Flow binds to is always `@InvocableMethod`.

---

## Anti-Pattern: Raw Cast On Unknown Implementation

**What practitioners do:**

```apex
Callable c = (Callable) Type.forName('Unknown.Class').newInstance(); // NPE if null
```

**What goes wrong:** `Type.forName` returns `null` when the class doesn't exist. `.newInstance()` throws NPE. Also, if the class exists but doesn't implement `Callable`, the cast throws `TypeException` at runtime with a cryptic message.

**Correct approach:** Guard both: check `t == null` and `Callable.class.isAssignableFrom(t)` before instantiating.
