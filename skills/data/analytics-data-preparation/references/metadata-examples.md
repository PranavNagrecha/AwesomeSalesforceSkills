# Metadata Examples: Deployable XMD With WaveXmd

The Primary User XMD can travel in a deployment or package because it is "tied to a dataset container instead of a dataset version" (XMD Developer Guide, Packaging Considerations for XMD). Deploy it as a WaveXmd component. Element names follow the Metadata API Developer Guide, Version 67.0, WaveXmd entry (WaveXmd, WaveXmdDimension, WaveXmdDimensionMember, WaveXmdMeasure). Required elements per that entry: `dataset` on WaveXmd; `field`, `isDerived`, and `sortIndex` on each dimension and measure; `member` and `sortIndex` on each member.

## File: `wave/Opportunity_Pipeline.xmd` (Metadata API format: suffix `.xmd`, folder `wave`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WaveXmd xmlns="http://soap.sforce.com/2006/04/metadata">
    <dataset>Opportunity_Pipeline</dataset>
    <dimensions>
        <field>Acct_Tier__c</field>
        <isDerived>false</isDerived>
        <label>Account Tier</label>
        <members>
            <label>Tier 1 (Strategic)</label>
            <member>T1</member>
            <sortIndex>0</sortIndex>
        </members>
        <members>
            <label>Tier 2 (Growth)</label>
            <member>T2</member>
            <sortIndex>1</sortIndex>
        </members>
        <showInExplorer>true</showInExplorer>
        <sortIndex>0</sortIndex>
    </dimensions>
    <dimensions>
        <field>Prod_Cat__c</field>
        <isDerived>false</isDerived>
        <label>Product Category</label>
        <showInExplorer>true</showInExplorer>
        <sortIndex>1</sortIndex>
    </dimensions>
    <measures>
        <field>Amount</field>
        <formatDecimalDigits>2</formatDecimalDigits>
        <formatPrefix>$</formatPrefix>
        <isDerived>false</isDerived>
        <label>Amount</label>
        <showInExplorer>true</showInExplorer>
        <sortIndex>0</sortIndex>
    </measures>
    <type>User</type>
</WaveXmd>
```

Do not copy the Metadata API guide's own WaveXmd sample verbatim: it opens `<dimesions>` and closes `</dimensions>`, so it does not parse.

UNVERIFIED (2026-10-03): the guide does not show the source-format (sfdx) file name for WaveXmd or a package.xml member example; `Opportunity_Pipeline` as the member name assumes the component is named after the dataset. Retrieve one WaveXmd from a sandbox first and match its name and path. The value `User` for `type` is one of the listed valid values (System, User, Main, Asset); the guide does not say which value a Primary User XMD deploy expects.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity_Pipeline</members>
        <name>WaveXmd</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy and verify

1. Validate locally: `python3 skills/data/analytics-data-preparation/scripts/check_analytics_data_preparation.py --manifest-dir wave`.
2. Deploy to a sandbox with the Metadata API.
3. Run the dataflow or recipe that updates `Opportunity_Pipeline`; "The Primary User XMD is applied to a dataset only after a dataflow that updates the dataset runs."
4. Open a lens on the dataset and confirm the labels and the Tier member labels.
5. From now on, change this dataset's formatting only through this file. A UI or REST edit makes the next Metadata API retrieve return an empty XMD.
