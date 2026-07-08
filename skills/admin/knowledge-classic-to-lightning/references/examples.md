# Examples — Knowledge Classic to Lightning Migration

## Example 1: Pre-Migration Inventory

```sql
-- Article Types and their published article counts (Classic)
SELECT ArticleType, COUNT(Id) cnt
FROM KnowledgeArticleVersion
WHERE PublishStatus = 'Online' AND IsLatestVersion = true
GROUP BY ArticleType

-- Per-language article distribution
SELECT Language, PublishStatus, COUNT(Id) cnt
FROM KnowledgeArticleVersion
WHERE IsLatestVersion = true
GROUP BY Language, PublishStatus

-- Data category usage
SELECT DataCategoryGroupName, DataCategoryName, COUNT(Id) cnt
FROM KnowledgeArticleVersion
WHERE IsLatestVersion = true
GROUP BY DataCategoryGroupName, DataCategoryName

-- Channel exposure summary
SELECT
    SUM(CASE WHEN IsVisibleInPkb=true THEN 1 ELSE 0 END) public_count,
    SUM(CASE WHEN IsVisibleInCsp=true THEN 1 ELSE 0 END) customer_count,
    SUM(CASE WHEN IsVisibleInPrm=true THEN 1 ELSE 0 END) partner_count,
    SUM(CASE WHEN IsVisibleInApp=true THEN 1 ELSE 0 END) internal_count
FROM KnowledgeArticleVersion
WHERE PublishStatus = 'Online' AND IsLatestVersion = true
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

**Critical:** This must run BEFORE the Migration Tool. Once Lightning Knowledge is enabled and migration runs, the Classic Article Types' field structure can no longer be modified.

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

**What changed:** sObject reference (`FAQ__kav` → `Knowledge__kav`) and added `RecordType.DeveloperName` filter.

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

**Why:** Direct `INSERT Knowledge__kav (PublishStatus='Online')` is not supported. Use the `KbManagement.PublishingService` Apex namespace.

---

## Example 5: Visibility Verification Across User Roles

```apex
@IsTest
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
Week 1: Migration Tool runs in Production; channels disabled in Lightning
Week 2 (Internal cutover):
    - Enable Internal channel in Lightning Knowledge Settings
    - Disable Internal channel in Classic Knowledge Settings
    - Service agents now see Lightning Knowledge in Service Console
    - Validate: agent can search, view, attach articles to Cases
Week 4 (Communities cutover):
    - Update Community Builder pages: Knowledge tab references Knowledge__kav
    - Enable Customer (Csp) channel in Lightning
    - Disable Csp channel in Classic
    - Validate: Community user can search, view, file feedback on articles
Week 6 (Public Knowledge Base cutover):
    - Verify Public KB site templates reference Knowledge__kav
    - Enable Pkb channel in Lightning
    - Disable Pkb channel in Classic
    - Validate: anonymous browser can search and view articles via PKB URL
Week 8: Decommission decision: retain Classic Article Types as read-only OR drop entirely
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
    - Migration_Status__c (Picklist: Migrated, Failed, Skipped, Retained_Classic)
    - Failure_Reason__c (LongTextArea 1000)
    - Verification_Status__c (Picklist: Pending, Verified, Mismatch)
    - Notes__c (LongTextArea)
```

The Migration Tool's log can be exported and loaded into this object for ongoing reconciliation. Reports run off this object: success rate per Article Type, failure reasons grouped, verification status by language.
