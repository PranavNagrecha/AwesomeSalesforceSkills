# Feature Parameter Metadata — Worked Example

This example takes one 2GP package from source files to a per-customer override. It ships two parameters: an `LmoToSubscriber` boolean that turns on beta reports, and a `SubscriberToLmo` integer that reports how many ledgers each customer uses.

## Source files

Every Feature Parameter type lives in the same `featureParameters` folder. The suffix tells the platform which type the file is: `.featureParameterBoolean`, `.featureParameterDate` or `.featureParameterInteger`, with `-meta.xml` appended in source format. Each type has three fields. `dataFlowDirection` sets which side can write the value, `masterLabel` is the name shown in the UI, and `value` holds the default.

```xml
<!-- force-app/main/default/featureParameters/Enable_Beta_Reports.featureParameterBoolean-meta.xml -->
<FeatureParameterBoolean xmlns="http://soap.sforce.com/2006/04/metadata">
    <dataflowDirection>LmoToSubscriber</dataflowDirection>
    <masterLabel>Enable Beta Reports</masterLabel>
    <value>false</value>
</FeatureParameterBoolean>
```

```xml
<!-- force-app/main/default/featureParameters/NumberOfLedgers.featureParameterInteger-meta.xml -->
<FeatureParameterInteger xmlns="http://soap.sforce.com/2006/04/metadata">
    <dataflowDirection>SubscriberToLmo</dataflowDirection>
    <masterLabel>Number of Ledgers</masterLabel>
    <value>0</value>
</FeatureParameterInteger>
```

The element is spelled `dataFlowDirection` in the Metadata API field table and `dataflowDirection` in the guide's own samples. The skill checker accepts either spelling. A `<defaultValue>` element is not a field of any Feature Parameter type, so the checker raises a WARN when it sees one. A file with no `<value>` gets an ERROR.

## Apex that reads and writes them

Each `checkPackage*Value` method takes a single `String apiName` argument, and each `setPackage*Value` method takes `(apiName, value)`. Neither has a namespace overload.

```apex
public with sharing class LedgerFeatures {
    public static Boolean betaReportsOn() {
        return System.FeatureManagement.checkPackageBooleanValue('Enable_Beta_Reports');
    }
    public static void reportLedgerCount(Integer n) {
        // SubscriberToLmo: written here, read in the LMO, never read back in this transaction
        System.FeatureManagement.setPackageIntegerValue('NumberOfLedgers', n);
    }
}
```

The setters run DML on setup sObjects. Tests that call them alongside other DML therefore need the mixed-DML pattern described in the Apex Reference.

## Turning the feature on for one customer

The 2GP guide puts the override on the subscriber's license record in the LMO, not in the package:

1. Open the license record for that customer's installation.
2. In the Feature Parameter Booleans related list, select `Enable Beta Reports`.
3. Click Edit, set the value, and click Save.

Once the version is released, the direction of either parameter can't be changed. If `NumberOfLedgers` needs to become writable from the LMO, add a new parameter for it.

## Gate before promoting the version

```bash
python3 skills/devops/isv-license-management-and-trialforce/scripts/check_isv_license_management_and_trialforce.py \
  --manifest-dir force-app --strict
```

On the files above the checker exits 0. Three slips from the first draft of this example would each have failed the gate:

- A `checkPackageBooleanValue('acme', 'Enable_Beta_Reports')` call is an ERROR, because no such overload exists.
- `<defaultValue>0</defaultValue>` in place of `<value>` produces an ERROR for the missing value and a WARN for the unknown element.
- A `checkPackageIntegerValue('NumberOfLedgers')` placed right after the setter is a WARN, which `--strict` turns into a failure.
