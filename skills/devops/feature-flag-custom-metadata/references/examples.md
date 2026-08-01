# Examples — Feature Flags via Custom Metadata

The accessor below is the skill-specific shape. Before writing your own, check
`templates/apex/cmdt/` for the canonical CMDT accessor and extend that rather than starting
over.

## Example 1: A deterministic canary for a new discount engine

**Context:** A replacement pricing algorithm that needed to run for a small share of users
before going org-wide.

**Problem:** The first implementation used a hierarchy Custom Setting so it could be flipped
from an anonymous Apex script. Custom Setting records are data rather than metadata, so
nothing travelled with the deployment — each sandbox had a different set of values, and
production's were created by hand by someone who had since left. The rollout percentage was
then applied with `Math.random()`, so a user saw the new prices on one page and the old ones
on the next.

**Solution:** A Custom Metadata Type whose records deploy with the source, and a hash-based
gate that gives a stable answer per user.

```apex
public with sharing class FeatureFlags {

    // Cached per transaction. The SOQL exemption makes the read cheap, but a repeated
    // read inside a loop still costs CPU — hoist it, for CPU reasons rather than SOQL ones.
    private static Map<String, Boolean> resolved = new Map<String, Boolean>();

    public static Boolean isEnabled(String flagName) {
        if (resolved.containsKey(flagName)) {
            return resolved.get(flagName);
        }

        // Short scalar fields only: getInstance() truncates any field at 255 characters.
        Feature_Flag__mdt flag = Feature_Flag__mdt.getInstance(flagName);
        Boolean answer = false;

        if (flag != null && flag.Is_Enabled__c == true) {
            answer = inRollout(flagName, flag.Percent_Rollout__c);
        }
        resolved.put(flagName, answer);
        return answer;
    }

    private static Boolean inRollout(String flagName, Decimal percent) {
        if (percent == null || percent <= 0)  return false;
        if (percent >= 100)                   return true;

        // Seed includes the flag name so two 10% flags do not pick the same users.
        String seed = UserInfo.getUserId() + ':' + flagName;
        Blob digest = Crypto.generateDigest('SHA-256', Blob.valueOf(seed));
        Integer bucket = Math.mod(
            Math.abs(EncodingUtil.convertToHex(digest).substring(0, 6).hashCode()), 100);
        return bucket < percent;
    }
}
```

```apex
// The committed record ships DISABLED. Enabling is a separate, per-environment act.
// force-app/main/default/customMetadata/Feature_Flag.NewDiscountEngine.md-meta.xml
public class DiscountEngine {
    public Decimal calculate(Opportunity opp) {
        if (FeatureFlags.isEnabled('NewDiscountEngine')) {
            return newAlgorithm(opp);
        }
        return legacyAlgorithm(opp);      // the path a kill switch returns everyone to
    }
}
```

**Why it works:** the flag's existence, its fields and its safe default are all in source
control, so a new sandbox has the flag without anyone remembering to create it. The hash
makes a user's answer stable across page loads and reproducible from a bug report — given a
user id and a percentage you can determine which path they were on, which random selection
makes impossible.

**Why the read is free but not weightless:** the governor documentation states the SOQL
limit does not apply to custom metadata types and that a transaction can issue unlimited
queries against them. That removes the usual reason to thread a boolean through five method
signatures. It does not remove CPU cost, so a flag evaluated per record inside a bulk loop
still belongs outside the loop.

**The truncation trap:** `getInstance()` and `getAll()` read from the application cache and
return only the first 255 characters of any field. Reading a long allow-list this way gives
a silently short answer. Keep the cached accessor for the boolean and the percentage; SOQL
anything that can be longer, or model the list as child records so the limit never applies.

---

## Example 2: An admin toggle, and why it cannot be a simple update

**Context:** Support wanted a screen to flip the kill switch during an incident without
raising a deployment.

**Problem:** The obvious implementation — read the record, set the field, `update` it —
does not work. Custom metadata is not modified with DML; changing it is a metadata
deployment. The second attempt used `Metadata.Operations.enqueueDeployment` and then
immediately re-read the flag to confirm, which reported the old value every time, because
the deployment is asynchronous and had not run yet.

**Solution:** Enqueue the deployment, and design the UI around a result that arrives later.

```apex
public with sharing class FeatureFlagAdmin {

    @AuraEnabled
    public static Id setEnabled(String developerName, Boolean enabled) {
        // Guard the toggle itself with a real permission, not with another flag.
        if (!FeatureManagement.checkPermission('Administer_Feature_Flags')) {
            throw new AuraHandledException('Not permitted.');
        }

        Metadata.CustomMetadata record = new Metadata.CustomMetadata();
        record.fullName = 'Feature_Flag__mdt.' + developerName;
        record.label    = developerName;

        Metadata.CustomMetadataValue enabledValue = new Metadata.CustomMetadataValue();
        enabledValue.field = 'Is_Enabled__c';
        enabledValue.value = enabled;
        record.values.add(enabledValue);

        Metadata.DeployContainer container = new Metadata.DeployContainer();
        container.addMetadata(record);

        // Returns a deployment id. The flag is NOT yet flipped when this returns.
        return Metadata.Operations.enqueueDeployment(container, new FlagDeployCallback());
    }
}

public class FlagDeployCallback implements Metadata.DeployCallback {
    public void handleResult(Metadata.DeployResult result,
                             Metadata.DeployCallbackContext context) {
        if (result.status == Metadata.DeployStatus.Succeeded) {
            // Publish a platform event or write a log; do not assume the UI is still open.
        } else {
            // Surface the failure somewhere durable — the user may have navigated away.
        }
    }
}
```

**Why it works:** the asynchrony is acknowledged rather than fought. The UI reports "change
requested" and learns the outcome from the callback, instead of re-reading a value that
cannot have changed yet.

**When not to build this at all:** during an incident, a human flipping the record in Setup
is faster and has fewer moving parts than a custom screen that depends on a callback chain.
This is worth building for routine administration by non-admins, and it is not worth
depending on as the kill-switch mechanism.

**The boundary this example draws twice:** the toggle is protected by a Custom Permission
checked with `FeatureManagement.checkPermission`, not by another flag. Flags answer "is this
code path live"; permissions answer "may this user do this". An allow-list that is expected
to exist in a year is a permission, and putting it in a flag hides an access decision
somewhere with no sharing model and no audit trail.
