# Metadata Examples — Knowledge Base Administration

Deployable shapes taken from the Metadata API Developer Guide (`KnowledgeSettings`, `DataCategoryGroup`, `RecordType`, `ArticleType CustomField`, `Profile`, `PermissionSet`) and the Object Reference (`Knowledge__kav`, `KnowledgeArticleVersion`, `Knowledge__DataCategorySelection`).

A working Lightning Knowledge base is **five metadata types in five different directories**. Deploy a subset and you get a knowledge base that looks configured and shows nobody any articles:

| Piece | Metadata type | Where it lives |
|---|---|---|
| The feature switch, languages, Validation Status | `KnowledgeSettings` | `settings/Knowledge.settings-meta.xml` |
| The taxonomy tree and which object it classifies | `DataCategoryGroup` | `datacategorygroups/<Name>.datacategorygroup-meta.xml` |
| Article types (record types) and custom fields | `CustomObject` / `RecordType` / `CustomField` | `objects/Knowledge__kav/…` |
| **Who can see which categories** | `Profile` only | `profiles/<Name>.profile-meta.xml` |
| Object CRUD and record-type pickability | `PermissionSet` / `Profile` | `permissionsets/`, `profiles/` |

## Where the files live and what `*` does

| Type | package.xml `<name>` | Member format | Wildcard `*`? |
|---|---|---|---|
| KnowledgeSettings | `Settings` | `Knowledge` | **No** — the guide states the wildcard "applies only when retrieving all settings, not for an individual setting" |
| DataCategoryGroup | `DataCategoryGroup` | `Support_Topics` | Yes (but see gotcha 6 — never cross-org) |
| CustomObject | `CustomObject` | `Knowledge__kav` | **Effectively no** — the guide states `*` on `CustomObject` doesn't match standard objects, and `Knowledge__kav` is standard |
| CustomField | `CustomField` | `Knowledge__kav.Root_Cause__c` (dot-qualified) | Follows `CustomObject` |
| RecordType | `RecordType` | `Knowledge__kav.Known_Issue` (dot-qualified) | **No** — the guide states this type doesn't support `*` |
| Layout | `Layout` | `Knowledge__kav-Knowledge Known Issue` | Yes |
| ChannelLayout | `ChannelLayout` | `Knowledge_Email_Layout` | Yes (the guide's own sample manifest uses `*`) |
| Profile | `Profile` | `Support_Agent` | Yes |
| PermissionSet | `PermissionSet` | `Knowledge_Author` | Yes |

`Knowledge__kav` is only the *default* API name. The Object Reference notes the prefix "can be modified by changing the Object Name for the `Knowledge__kav` object in Object Manager" — every path and member below changes with it, and so does `Knowledge__DataCategorySelection`.

## 1. Knowledge settings — enable Lightning Knowledge with two languages

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- settings/Knowledge.settings-meta.xml
     Excerpt: only the fields this skill sets. A retrieved file also carries the
     <answers>, <cases> and showArticleSummaries* blocks from the guide's sample. -->
<KnowledgeSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableKnowledge>true</enableKnowledge>
    <enableLightningKnowledge>true</enableLightningKnowledge>
    <defaultLanguage>en_US</defaultLanguage>
    <enableCreateEditOnArticlesTab>true</enableCreateEditOnArticlesTab>
    <enableExternalMediaContent>false</enableExternalMediaContent>
    <enableKbStandardSharing>true</enableKbStandardSharing>
    <showValidationStatusField>true</showValidationStatusField>
    <showArticleSummariesInternalApp>true</showArticleSummariesInternalApp>
    <showArticleSummariesCustomerPortal>false</showArticleSummariesCustomerPortal>
    <showArticleSummariesPartnerPortal>false</showArticleSummariesPartnerPortal>
    <languages>
        <language>
            <name>en</name>
            <active>true</active>
            <defaultAssigneeType>Queue</defaultAssigneeType>
            <defaultAssignee>Knowledge_Authors_EN</defaultAssignee>
            <defaultReviewerType>Queue</defaultReviewerType>
            <defaultReviewer>Knowledge_Reviewers_EN</defaultReviewer>
        </language>
        <language>
            <name>fr</name>
            <active>true</active>
            <defaultAssigneeType>User</defaultAssigneeType>
            <defaultAssignee>translations@example.com</defaultAssignee>
        </language>
    </languages>
    <suggestedArticles>
        <caseFields>
            <field>
                <name>Subject</name>
            </field>
            <field>
                <name>Description</name>
            </field>
        </caseFields>
        <useSuggestedArticlesForCase>true</useSuggestedArticlesForCase>
    </suggestedArticles>
</KnowledgeSettings>
```

How to read it:

- `enableKnowledge` turns the feature on and is `false` by default; `enableLightningKnowledge` selects the Lightning model. Setting the first without the second leaves the org on Knowledge in Salesforce Classic, where articles live on per-type `<ArticleType>__kav` objects instead of one `Knowledge__kav` — the checker warns on exactly that pair.
- **Two different language code shapes in one file.** `defaultLanguage` takes the locale form ("for example, `en_US` for United States English"); each `<language><name>` takes the bare language code ("English is `en`"). Copying `en_US` into `<name>` is a deploy failure, not a warning.
- `showValidationStatusField` is the org-wide switch that surfaces `Knowledge__kav.ValidationStatus`. It is one flag for the whole knowledge base — there is no per-record-type variant.
- `defaultAssignee` / `defaultReviewer` are per language, and `defaultAssigneeType` / `defaultReviewerType` accept only `User` or `Queue`. A queue is the safer default: a named user who leaves the company silently strands every new draft in that language.
- `suggestedArticles.caseFields` names the Case fields whose text drives article suggestion. The guide also documents `workOrderFields` and `workOrderLineItemFields`, valid only when Work Order objects are enabled.
- `enableKbStandardSharing` turns on standard Salesforce sharing for the knowledge base. It is orthogonal to data category visibility — it does not replace it.

<!-- UNVERIFIED (2026-09-04): that enabling Lightning Knowledge is irreversible is not stated in the extracted Metadata API or Object Reference PDFs — `enableLightningKnowledge` is documented as a plain boolean. The claim comes from Salesforce Help (Set Up Lightning Knowledge), which cannot be fetched from this environment. Treat the deploy as one-way until you have confirmed otherwise in a scratch org you are willing to discard. -->

## 2. Data category group — two-level tree, assigned to articles

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- datacategorygroups/Support_Topics.datacategorygroup-meta.xml -->
<DataCategoryGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Support_Topics</fullName>
    <label>Support Topics</label>
    <description>Subject taxonomy for the support knowledge base. Level 1 is the audience-neutral
        topic; level 2 is the sub-topic agents filter on.</description>
    <active>true</active>
    <dataCategory>
        <name>All_Topics</name>
        <label>All Topics</label>
        <dataCategory>
            <name>Billing</name>
            <label>Billing and Invoicing</label>
        </dataCategory>
        <dataCategory>
            <name>Account_Access</name>
            <label>Account Access</label>
        </dataCategory>
        <dataCategory>
            <name>Internal_Procedures</name>
            <label>Internal Escalation Procedures</label>
        </dataCategory>
    </dataCategory>
    <objectUsage>
        <object>KnowledgeArticleVersion</object>
    </objectUsage>
</DataCategoryGroup>
```

How to read it:

- `fullName` must equal the file name without its suffix, and the file suffix is `.datacategorygroup` in the `datacategorygroups` folder.
- `active` is required. An inactive group is deployable but classifies nothing, so articles tagged against it behave as unclassified.
- `objectUsage/object` is what wires the group to Knowledge. The only valid values are `KnowledgeArticleVersion` (articles) and `Question` (Chatter Answers questions, at most one group). **Omit it and you get a deployable group that no article can ever be filtered by** — the single most common reason a freshly deployed taxonomy does nothing.
- The tree has exactly one top-level `<dataCategory>`; sub-categories nest recursively inside it. The guide caps a group at 100 categories and 5 hierarchy levels.
- `<name>` is the developer name and the guide marks it **defined once and cannot be changed later**. Renaming means delete-and-recreate, which drops every article's classification against the old name.

## 3. Record types and a custom field on `Knowledge__kav`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Knowledge__kav — MDAPI nested form.
     Excerpt: only the record types and the one custom field this example adds. -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <recordTypes>
        <fullName>FAQ</fullName>
        <label>FAQ</label>
        <active>true</active>
        <description>Customer-facing question-and-answer articles. Layout excludes internal fields.</description>
        <compactLayoutAssignment>Knowledge_FAQ_Compact</compactLayoutAssignment>
    </recordTypes>
    <recordTypes>
        <fullName>Known_Issue</fullName>
        <label>Known Issue</label>
        <active>true</active>
        <description>Internal defect write-ups. Never enabled on a customer or public channel.</description>
    </recordTypes>
    <fields>
        <fullName>Root_Cause__c</fullName>
        <label>Root Cause</label>
        <description>Engineering root-cause narrative. Internal only — read access is granted by
            field permissions, not by leaving it off the customer layout.</description>
        <type>LongTextArea</type>
        <length>32000</length>
        <visibleLines>10</visibleLines>
    </fields>
</CustomObject>
```

How to read it:

- Article custom fields are dot-qualified with the knowledge object: `Knowledge__kav.Root_Cause__c`, exactly as the guide qualifies `MyArticleType__kav.MyCustomField__c`.
- No `<businessProcess>` element: the guide states `businessProcess` is required for lead, opportunity, solution, and case record types "and not allowed otherwise". Adding it to a `Knowledge__kav` record type fails the deploy.
- A DX source-format project decomposes the same content into `objects/Knowledge__kav/recordTypes/FAQ.recordType-meta.xml` and `objects/Knowledge__kav/fields/Root_Cause__c.field-meta.xml`. <!-- UNVERIFIED (2026-09-04): the decomposed DX directory layout is a Salesforce DX convention; the Metadata API PDF documents only the nested `<CustomObject>` form shown above, which deploys in either project format. -->
- The guide's `RecordType` entry carries a warning worth quoting into your design doc: "Don't use record types as an access control mechanism… a user assigned to a profile that isn't enabled for a particular record type can't create records with that record type, but **can access records associated with that record type**." Layout separation is a usability control. `Root_Cause__c` stays confidential only because of field permissions and data category visibility.

## 4. Category visibility lives on the Profile — not the permission set

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- profiles/Support_Agent.profile-meta.xml — excerpt: only the Knowledge blocks. -->
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>true</custom>
    <categoryGroupVisibilities>
        <dataCategoryGroup>Support_Topics</dataCategoryGroup>
        <visibility>ALL</visibility>
    </categoryGroupVisibilities>
    <categoryGroupVisibilities>
        <dataCategoryGroup>Product_Lines</dataCategoryGroup>
        <dataCategories>Core_Platform</dataCategories>
        <dataCategories>Analytics</dataCategories>
        <visibility>CUSTOM</visibility>
    </categoryGroupVisibilities>
    <recordTypeVisibilities>
        <recordType>Knowledge__kav.FAQ</recordType>
        <visible>true</visible>
        <default>true</default>
    </recordTypeVisibilities>
    <recordTypeVisibilities>
        <recordType>Knowledge__kav.Known_Issue</recordType>
        <visible>true</visible>
        <default>false</default>
    </recordTypeVisibilities>
</Profile>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- permissionsets/Knowledge_Author.permissionset-meta.xml — excerpt.
     There is deliberately no <categoryGroupVisibilities> here: the Metadata API
     documents that element on Profile only. -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Knowledge Author</label>
    <license>Salesforce</license>
    <hasActivationRequired>false</hasActivationRequired>
    <objectPermissions>
        <object>Knowledge__kav</object>
        <allowCreate>true</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <fieldPermissions>
        <field>Knowledge__kav.Root_Cause__c</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>
    <recordTypeVisibilities>
        <recordType>Knowledge__kav.Known_Issue</recordType>
        <visible>true</visible>
    </recordTypeVisibilities>
</PermissionSet>
```

How to read it:

- **`categoryGroupVisibilities` is a `Profile` field (`ProfileCategoryGroupVisibility`, API 41.0+). The Metadata API's `PermissionSet` field list has no equivalent.** A migration that moves everything else off profiles onto permission sets must leave category visibility behind on the profile — see gotcha 8.
- `visibility` takes exactly `ALL`, `CUSTOM`, or `NONE`. `<dataCategories>` is meaningful only with `CUSTOM`; leave it off for `ALL` and `NONE`.
- Both files list `Knowledge__kav.Known_Issue` because they do different jobs: the permission set makes the record type *pickable*, the profile also decides the *default*. `PermissionSetRecordTypeVisibility` has only `recordType` and `visible` — there is no `default` on the permission-set side.
- Object CRUD and field permissions are not the whole access story, and they are not the licence either. The Object Reference is explicit for `Knowledge__kav`: "Lightning Knowledge must be enabled in your org. A user must have the View Articles permission enabled. Salesforce Knowledge users, unlike customer and partner users, must also be granted the **Knowledge User feature license**." That licence is the `UserPermissionsKnowledgeUser` checkbox on the `User` record (label "Knowledge User"), not anything in this file.
- User permissions such as "Manage Articles", "View Draft Articles", and "View Archived Articles" go in `<userPermissions>` blocks. Retrieve a permission set that already has them and copy the exact `<name>` values rather than guessing — the guide's `PermissionSetUserPermissions` entry does not enumerate the API names.

## 5. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Knowledge</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Support_Topics</members>
        <members>Product_Lines</members>
        <name>DataCategoryGroup</name>
    </types>
    <types>
        <members>Knowledge__kav</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Knowledge__kav.Root_Cause__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Knowledge__kav.FAQ</members>
        <members>Knowledge__kav.Known_Issue</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Knowledge__kav-Knowledge FAQ</members>
        <members>Knowledge__kav-Knowledge Known Issue</members>
        <name>Layout</name>
    </types>
    <types>
        <members>Support_Agent</members>
        <name>Profile</name>
    </types>
    <types>
        <members>Knowledge_Author</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

Three of these entries cannot be wildcarded and are the ones people leave out:

- `Settings` with member `Knowledge` — a bare `*` under `Settings` retrieves *all* settings, and the guide states the wildcard "doesn't apply to metadata types for feature settings" individually.
- `Knowledge__kav` under `CustomObject` — the guide states `*` on `CustomObject` "doesn't match standard objects", so a wildcard manifest silently returns no knowledge object at all.
- `RecordType` members one by one — the guide states this type doesn't support `*`, so a wildcard-only manifest deploys the object and its layouts with no article types.

## 6. Retrieve, check, deploy

```bash
# Always retrieve first: the settings and profile files are whole-file replacements.
sf project retrieve start --manifest manifest/knowledge.xml --target-org my-sandbox

python3 skills/admin/knowledge-base-administration/scripts/check_knowledge_base_administration.py \
  --manifest-dir force-app/main/default

sf project deploy start --manifest manifest/knowledge.xml --target-org my-sandbox --dry-run
sf project deploy start --manifest manifest/knowledge.xml --target-org my-sandbox
```

Retrieve every profile that carries `categoryGroupVisibilities` in the same package as the `DataCategoryGroup`. Deploy them separately and the profile you commit reflects a taxonomy that no longer matches the org's.

## 7. Verify after deploy

Confirm articles actually reach a published state in each language, and that Validation Status came through:

```sql
SELECT Id, ArticleNumber, Title, RecordType.DeveloperName, PublishStatus, Language,
       IsLatestVersion, IsMasterLanguage, VersionNumber, ValidationStatus
FROM Knowledge__kav
WHERE PublishStatus = 'Online' AND Language = 'en_US'
ORDER BY ArticleNumber
```

`PublishStatus` (or `Id`) is not optional in that `WHERE` clause. The Object Reference states article queries and searches "require that you specify either the `PublishStatus` or the `Id` field in the `WHERE` clause". Valid values are `Draft`, `Online`, `Archived` — note it is `Online`, not "Published", even though the UI says Published.

Then confirm the categories landed on the articles, which is the step that proves the taxonomy is live rather than merely deployed:

```sql
SELECT ParentId, DataCategoryGroupName, DataCategoryName
FROM Knowledge__DataCategorySelection
WHERE ParentId = 'ka0xx0000000001AAA'
```

An empty result for an article you classified means the selection never saved — `Knowledge__DataCategorySelection` supports only `create()`, `delete()`, `query()`, `retrieve()` and `getDeleted()`/`getUpdated()`. There is no `update()`: reclassifying is delete-then-create, and the guide notes client applications "can create a categorization for an article with a Draft status", so an already-published version has to be edited back into draft first.

To confirm the group itself is wired to articles at all, retrieve it back and check `objectUsage`:

```bash
sf project retrieve start --metadata DataCategoryGroup:Support_Topics --target-org my-sandbox
grep -A2 objectUsage force-app/main/default/datacategorygroups/Support_Topics.datacategorygroup-meta.xml
```

Setup check that needs no API: **Setup → Data Categories → Data Category Group Assignments** shows which groups are assigned to Knowledge, and **Setup → Profiles → <profile> → Category Group Visibility** shows the `ALL` / `CUSTOM` / `NONE` choice the profile XML above encodes.

## 8. Publish and archive from Apex

`KbManagement.PublishingService` is the only supported programmatic route through the article lifecycle. All methods are static, and the guide notes **date values are based on GMT**.

```apex
// The lifecycle methods take the article Id, not the version Id.
String articleId = 'kA0xx0000000001CAA';

// Publish the current draft as a major version.
KbManagement.PublishingService.publishArticle(articleId, true);

// Or schedule it: a null date publishes immediately, a future date defers.
Datetime goLive = Datetime.newInstanceGmt(2026, 10, 1, 6, 0, 0);
KbManagement.PublishingService.scheduleForPublication(articleId, goLive);

// Archive the online version now (null) or on a date, and cancel either schedule.
KbManagement.PublishingService.archiveOnlineArticle(articleId, null);
KbManagement.PublishingService.cancelScheduledPublicationOfArticle(articleId);

// Roll back: build a new draft from archived version 1, then republish it.
String draftVersionId = KbManagement.PublishingService.restoreOldVersion(articleId, 1);

// Verify. KnowledgeArticleVersion objects reject bind variables in static Apex SOQL
// (compilation error) — the guide's documented workaround is dynamic SOQL.
final String statusOnline = 'Online';
String q = 'SELECT Id, ArticleNumber, PublishStatus, VersionNumber '
         + 'FROM Knowledge__kav '
         + 'WHERE PublishStatus = :statusOnline '
         + 'AND KnowledgeArticleId = :articleId';
List<Knowledge__kav> live = Database.query(q);
System.assertEquals(1, live.size(), 'Expected exactly one Online version per language');
```

<!-- UNVERIFIED (2026-09-04): the Apex Reference Guide types the `articleId` parameter as `String` and does not say whether it is the `KnowledgeArticle` (`kA…`) Id or the `Knowledge__kav` (`ka…`) version Id. The methods are described as operating on "an article" and its versions, which is why the sample above passes the article container Id. Confirm against one record in a sandbox before scripting a bulk publish. -->

Two behaviours worth reading off this snippet before designing a publishing workflow: `scheduleForPublication` and `archiveOnlineArticle` both take a date, so scheduled publication *does* exist programmatically even though the Setup Publish button is immediate; and `restoreOldVersion` is the documented rollback — it creates a draft from an archived version rather than reinstating it in place, so recovery is always a new version, never an undo.

## Related reading

- `references/gotchas.md` — the eleven platform behaviours behind the warnings in this file
- `references/examples.md` — the multi-audience visibility worked example and the approval-process design
- `admin/knowledge-classic-to-lightning` — what happens to `<ArticleType>__kav` objects and their layouts when this settings file flips
- `data/knowledge-article-import` — loading articles into the shapes above, including data categories on import
- `architect/knowledge-taxonomy-design` — how many groups and levels the taxonomy should have before you write the `DataCategoryGroup` XML
