# LLM Anti-Patterns — Feature Flags via Custom Metadata

Scope: the storage and accessor mechanics of a Custom Metadata Type flag. The release
practice around flags — canary design, kill-switch drills, flag lifecycle — belongs to
`apex/feature-flags-and-kill-switches`. A canonical CMDT accessor already exists under
`templates/apex/cmdt/`; reference it rather than re-authoring one.

## Anti-Pattern 1: Reaching for a Custom Setting because it can be written from Apex

The trade that looks like a win and is not. A hierarchy Custom Setting supports ordinary
DML, so a flag can be flipped from an Apex script — which is exactly why assistants pick it.
The cost is that Custom Setting *records* are data, not metadata: they do not travel with a
deployment, so every environment needs the values recreated by hand and prod inevitably ends
up with a set nobody can reproduce.

❌ `Feature_Flags__c` hierarchy Custom Setting, values created per org by a post-deploy
script that has drifted from what production actually contains.
✅ A Custom Metadata Type, whose records **are** metadata and deploy with the source, so the
flag's existence and its default are version-controlled. Accept the constraint that comes
with it: you cannot flip it with plain DML (anti-pattern 3).

## Anti-Pattern 2: Not knowing why the query is free, and then not using it

CMDT is the only store where "just query it wherever you need it" is defensible, and
generated code routinely fails to exploit that — passing a flag value down five method
signatures to avoid a query that costs nothing. The governor documentation is explicit:
**this limit doesn't apply to custom metadata types. In a single Apex transaction, custom
metadata records can have unlimited SOQL queries.**

❌ Thread a boolean through every constructor and method "to save a query".
✅ Read it where the decision is made:

```apex
public with sharing class DiscountEngine {
    public Decimal calculate(Opportunity opp) {
        if (FeatureFlags.isEnabled('NewDiscountEngine')) {   // free query, cached read
            return newAlgorithm(opp);
        }
        return legacyAlgorithm(opp);
    }
}
```

The exemption is specific to custom metadata types. It does not extend to Custom Settings,
and it does not make the *rest* of the transaction free — a flag check inside a loop over
50,000 records still costs CPU even when it costs no queries, so hoist the read out of the
loop for CPU reasons rather than SOQL ones.

Source: Apex Governor Limits — "This limit doesn't apply to custom metadata types. In a single Apex transaction, custom metadata records can have unlimited SOQL queries." — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm

## Anti-Pattern 3: Writing to a Custom Metadata record with DML

The failure that arrives the first time someone tries to build an admin toggle screen.
Apex cannot flip a CMDT record with `update`; changing custom metadata is a *metadata
deployment*, which is enqueued and runs asynchronously.

**Wrong** — does not do what the code says:

```apex
Feature_Flag__mdt flag = Feature_Flag__mdt.getInstance('NewDiscountEngine');
flag.Is_Enabled__c = true;
update flag;                       // not the way custom metadata is modified
```

**Right** — build a deployment and enqueue it, then handle completion in a callback:

```apex
public class FeatureFlagToggle {
    public static void setEnabled(String developerName, Boolean enabled) {
        Metadata.CustomMetadata record = new Metadata.CustomMetadata();
        record.fullName = 'Feature_Flag__mdt.' + developerName;
        record.label    = developerName;

        Metadata.CustomMetadataValue value = new Metadata.CustomMetadataValue();
        value.field = 'Is_Enabled__c';
        value.value = enabled;
        record.values.add(value);

        Metadata.DeployContainer container = new Metadata.DeployContainer();
        container.addMetadata(record);
        // Asynchronous: the flag is NOT flipped when this line returns.
        Metadata.Operations.enqueueDeployment(container, new FlagDeployCallback());
    }
}
```

The asynchrony is the part that breaks assumptions: a UI that calls this and immediately
re-reads the flag shows the old value. Design the toggle screen around a deploy that
completes later, and reserve this path for genuine administration — a kill switch flipped
during an incident is better served by a human in Setup than by a callback chain.

Source: Retrieving and Deploying Metadata in Apex — `Metadata.Operations.enqueueDeployment()` deploys metadata asynchronously — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_metadata_retrieve_deploy.htm

## Anti-Pattern 4: Reading a long field through `getInstance()`

A silent truncation that produces a flag which is subtly wrong rather than obviously broken.
`getAll()` and `getInstance()` read from the application cache, and **only the first 255
characters are returned for any field in a custom metadata type record**. An allow-list of
user ids or profile names in a long text field comes back cut off, so users past the cut
silently lose the feature.

❌ `Feature_Flag__mdt.getInstance(name).Allowed_Profiles__c` where that field holds more than
255 characters of comma-separated values.
✅ Use the cached accessors for short scalar fields — the boolean, the percentage — and SOQL
when a field can exceed 255 characters:

```apex
// Cheap, cached, and safe: the fields read are short.
Feature_Flag__mdt flag = Feature_Flag__mdt.getInstance('NewDiscountEngine');

// Long field: must come from SOQL, or it arrives truncated.
Feature_Flag__mdt full = [
    SELECT Is_Enabled__c, Percent_Rollout__c, Allowed_Profiles__c
    FROM Feature_Flag__mdt
    WHERE DeveloperName = 'NewDiscountEngine'
    LIMIT 1
];
```

Better still, model the allow-list as child CMDT records rather than a delimited string, so
the 255-character boundary never applies and the values are individually deployable.

Source: Custom Metadata Type Methods — "Only the first 255 characters are returned for any field in a custom metadata type record" — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_custom_metadata_types.htm

## Anti-Pattern 5: Random percentage rollout

`Math.random()` in the gate is the most common generated implementation and it is not a
rollout — it is a coin flip per evaluation. A user sees the new feature on one page load and
the old one on the next, in-flight work is lost mid-wizard, and nothing is reproducible, so
a bug report cannot be tied to a code path.

❌ `if (Math.random() * 100 < flag.Percent_Rollout__c)`
✅ A stable hash of an identifier, so a given user's answer never changes for a given
percentage:

```apex
private static Boolean inRollout(String flagName, Decimal percent) {
    if (percent == null || percent <= 0) return false;
    if (percent >= 100) return true;
    // Deterministic per user AND per flag, so two 10% flags do not select the same users.
    String seed = UserInfo.getUserId() + ':' + flagName;
    Blob digest = Crypto.generateDigest('SHA-256', Blob.valueOf(seed));
    Integer bucket = Math.mod(Math.abs(EncodingUtil.convertToHex(digest)
                        .substring(0, 6).hashCode()), 100);
    return bucket < percent;
}
```

Including the flag name in the seed matters: hashing the user id alone means every flag at
10% picks the same unlucky 10% of users, who then experience every canary simultaneously.

## Anti-Pattern 6: Shipping the record enabled

The flag exists so that deploying and releasing are separate events. A CMDT record committed
with `Is_Enabled__c = true` collapses them again — the feature turns on for everyone the
moment the deployment finishes, which is precisely the outcome the flag was added to avoid.

❌ Commit the record with the value the developer used locally.
✅ Default the committed record to disabled, and treat enabling as a deliberate,
per-environment action recorded somewhere. Deploying the code and enabling the flag should
never be the same change.

## Anti-Pattern 7: Using a flag where a permission belongs

Flags and permissions look interchangeable in code and are not. A flag answers "is this code
path live in this org"; a permission answers "is this user allowed to do this". Assistants
implement per-user entitlement as a CMDT allow-list because the flag framework is already
there — which puts an access-control decision in a place with no sharing model, no audit
trail, and no visibility in a permissions review.

❌ `Allowed_Users__c` on a flag as the mechanism for who may use a feature permanently.
✅ A Custom Permission plus a permission set for entitlement, checked with
`FeatureManagement.checkPermission('Use_New_Discount_Engine')`, and the CMDT flag only for
the temporary rollout question. The distinguishing test is time: if the list is expected to
still exist in a year, it is a permission, not a flag.
