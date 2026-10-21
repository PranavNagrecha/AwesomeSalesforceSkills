# Examples — Knowledge Classic to Lightning Migration

## Example 1: Pre-Migration Inventory

In Classic Knowledge every article query needs a `PublishStatus` or `Id` filter in WHERE (obj 264 L163280-163281), so run one query per status; once Lightning Knowledge is enabled, an API 47.0+ query with no `PublishStatus` filter returns draft, published and archived articles (L163435-163436). `ArticleType` is Filter-only (L163041-163048) and `Language` is groupable (L163190-163193). Category selections live on the per-type `<ArticleType>__DataCategorySelection` object, whose group and category fields are Create-only — not filterable or groupable — so aggregate them offline (L38769-38800).

```sql
-- Published article count for one Article Type (repeat per type)
SELECT COUNT(Id) cnt
FROM KnowledgeArticleVersion
WHERE PublishStatus = 'Online' AND IsLatestVersion = true
  AND ArticleType = 'FAQ__kav'

-- Per-language distribution: repeat with 'Draft' and 'Archived'
-- (for Archived also add IsLatestVersion = false, L163283-163284)
SELECT Language, COUNT(Id) cnt
FROM KnowledgeArticleVersion
WHERE PublishStatus = 'Online'
GROUP BY Language

-- Data category assignments for the FAQ article type (count offline)
SELECT ParentId, DataCategoryGroupName, DataCategoryName
FROM FAQ__DataCategorySelection

-- Channel exposure: one count per flag (repeat for IsVisibleInCsp,
-- IsVisibleInPrm, IsVisibleInApp)
SELECT COUNT(Id) public_count
FROM KnowledgeArticleVersion
WHERE PublishStatus = 'Online' AND IsLatestVersion = true
  AND IsVisibleInPkb = true
```

---

## Example 2: Field Pre-Normalization Apex Script

**Scenario:** Two Article Types (`FAQ__kav`, `Q_and_A__kav`) will collapse to one Lightning record type. They have similar but differently-named fields: `FAQ__kav.Description__c` and `Q_and_A__kav.Summary__c`. Migration Tool maps 1:1; pre-normalization is needed.

```apex
public with sharing class KnowledgePreNormalization {
    public static void unifyDescriptionField() {
        // Step 1: Add a new unified field `Article_Description__c` to both Article Types in metadata.
        // Step 2: Backfill from legacy fields.

        List<FAQ__kav> faqs = [SELECT Id, Description__c, Article_Description__c FROM FAQ__kav];
        for (FAQ__kav f : faqs) {
            f.Article_Description__c = f.Description__c;
        }
        update faqs;

        List<Q_and_A__kav> qas = [SELECT Id, Summary__c, Article_Description__c FROM Q_and_A__kav];
        for (Q_and_A__kav q : qas) {
            q.Article_Description__c = q.Summary__c;
        }
        update qas;
        // Now the Migration Tool can map Article_Description__c on both → Knowledge__kav.Description__c
    }
}
```

**Critical:** This must run BEFORE the Migration Tool. A multi-type migration deletes the article-type KAV objects (apexdev 264 L16013-16014), and "when Lightning Knowledge is enabled, you can't add an article type" (pkg2_dev 264 L4591-4592). UNVERIFIED (2026-10-20): the Tool's field-mapping screen behaviour.

---

## Example 3: Apex Code Update — Article Type Reference to Knowledge__kav

**Before (Classic):**

```apex
public class FaqLookupService {
    @AuraEnabled(cacheable=true)
    public static List<FAQ__kav> findRelevantFaqs(String searchTerm) {
        return [
            SELECT Id, Title, Summary, UrlName
            FROM FAQ__kav
            WHERE PublishStatus = 'Online'
              AND Language = 'en_US'
              AND IsLatestVersion = true
              AND (Title LIKE :('%' + searchTerm + '%')
                   OR Summary LIKE :('%' + searchTerm + '%'))
            LIMIT 10
        ];
    }
}
```

**After (Lightning):**

```apex
public class FaqLookupService {
    @AuraEnabled(cacheable=true)
    public static List<Knowledge__kav> findRelevantFaqs(String searchTerm) {
        return [
            SELECT Id, Title, Summary, UrlName
            FROM Knowledge__kav
            WHERE PublishStatus = 'Online'
              AND Language = 'en_US'
              AND IsLatestVersion = true
              AND RecordType.DeveloperName = 'FAQ'
              AND (Title LIKE :('%' + searchTerm + '%')
                   OR Summary LIKE :('%' + searchTerm + '%'))
            LIMIT 10
        ];
    }
}
```

**What changed:** sObject reference (`FAQ__kav` → `Knowledge__kav`) and added `RecordType.DeveloperName` filter. Deploy this BEFORE the Tool runs: the `FAQ__kav` object is deleted during a multi-type migration (apexdev 264 L16013-16014).

---

## Example 4: Publishing via KbManagement.PublishingService

```apex
// Custom migration scenario: insert articles in Draft, then publish in a controlled second pass
public class KnowledgePublishHelper {
    public static void publishMigratedArticles(Set<Id> articleIds) {
        for (Id articleId : articleIds) {
            try {
                // Publishes the latest draft version as the new online version
                KbManagement.PublishingService.publishArticle(articleId, false);
            } catch (Exception e) {
                System.debug('Publish failed for ' + articleId + ': ' + e.getMessage());
            }
        }
    }

    public static void editOnline(Id articleId) {
        // Creates a new draft from the published version (necessary for safe edit-then-republish)
        KbManagement.PublishingService.editOnlineArticle(articleId, false);
    }

    public static void archiveArticle(Id articleId, Datetime scheduledDate) {
        KbManagement.PublishingService.archiveOnlineArticle(articleId, scheduledDate);
    }
}
```

**Why:** `PublishStatus` has no Create or Update property (obj 264 L162102-162105), so direct `INSERT Knowledge__kav (PublishStatus='Online')` is not supported. Use the `KbManagement.PublishingService` Apex namespace (signatures: apexref 262 L162906, L163226, L163289).

---

## Example 5: Visibility Verification Across User Roles

```apex
// SeeAllData=true: tests saved at API 24.0+ cannot see pre-existing org data
// such as migrated articles otherwise (apexdev 264 L5858-5860).
@IsTest(SeeAllData=true)
public class KnowledgeVisibilityRegression {

    @IsTest
    static void supportAgent_seesExpectedFaqs() {
        User agent = [SELECT Id FROM User WHERE Profile.Name = 'Support Agent' AND IsActive = true LIMIT 1];
        System.runAs(agent) {
            Integer count = [
                SELECT COUNT()
                FROM Knowledge__kav
                WHERE RecordType.DeveloperName = 'FAQ'
                  AND PublishStatus = 'Online'
                  AND Language = 'en_US'
                  AND IsLatestVersion = true
            ];
            // Pre-migration baseline established: 247 FAQs visible to Support Agent
            System.assertEquals(247, count, 'FAQ visibility should match pre-migration baseline');
        }
    }

    @IsTest
    static void communityUser_seesExpectedHowTos() {
        User community = [SELECT Id FROM User WHERE UserType = 'CspLitePortal' AND IsActive = true LIMIT 1];
        System.runAs(community) {
            Integer count = [
                SELECT COUNT()
                FROM Knowledge__kav
                WHERE RecordType.DeveloperName = 'HowTo'
                  AND PublishStatus = 'Online'
                  AND IsVisibleInCsp = true
                  AND Language = 'en_US'
            ];
            System.assertEquals(89, count, 'HowTo community visibility should match baseline');
        }
    }
}
```

**Critical:** These regression tests are pre-migration baseline + post-migration verification. Update the asserted counts to match the pre-migration query results, then run after migration.

---

## Example 6: Channel Cutover Sequencing

```text
Week 0: Migration Tool runs in Sandbox; full validation
Week 1: Migration Tool runs in Production (article-type KAV objects are
        deleted in a multi-type org - apexdev 264 L16013-16014)
Week 2 (Internal cutover):
    - Point internal surfaces (Service Console, Articles tab) at Knowledge__kav
    - Service agents now see Lightning Knowledge in Service Console
    - Validate: agent can search, view, attach articles to Cases
Week 4 (Communities cutover):
    - Update Community Builder pages: Knowledge tab references Knowledge__kav
    - Confirm IsVisibleInCsp values match the pre-migration baseline
    - Validate: Community user can search, view, file feedback on articles
Week 6 (Public Knowledge Base cutover):
    - Verify Public KB site templates reference Knowledge__kav
    - Confirm IsVisibleInPkb values match the pre-migration baseline
    - Validate: anonymous browser can search and view articles via PKB URL
Week 8: Close-out audit: old-to-new IDs via MigratedToFromArticleVersion
        (obj 264 L162069-162076); no Classic article types remain to retain
```

---

## Example 7: Migration Audit Log Schema

```text
Custom Object: Knowledge_Migration_Log__c
Fields:
    - Classic_Article_Id__c (Text 18, External ID, Unique)
    - Classic_Article_Type__c (Text)
    - Classic_Language__c (Text)
    - Lightning_Knowledge_Id__c (Text 18)
    - Lightning_Record_Type__c (Text)
    - Migration_Date__c (Datetime)
    - Migration_Status__c (Picklist: Migrated, Failed, Skipped)
    - Failure_Reason__c (LongTextArea 1000)
    - Verification_Status__c (Picklist: Pending, Verified, Mismatch)
    - Notes__c (LongTextArea)
```

Seed `Lightning_Knowledge_Id__c` from `Knowledge__kav.MigratedToFromArticleVersion` (obj 264 L162069-162076). UNVERIFIED (2026-10-20): that the Migration Tool's log can be exported. Reports run off this object: success rate per Article Type, failure reasons grouped, verification status by language.
