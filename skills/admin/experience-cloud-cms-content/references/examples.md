# Examples — Experience Cloud CMS Content

Cites are to the Winter '27 (264) `api_meta` and `object_reference` guides.

## Example 1: A Custom Content Type for Event Announcements

**Context:** A portal team needs an announcement with a title, a summary, a body and a hero image, which the standard News, Image and Document types do not give them.

**Problem:** The standard types are fixed (object_reference 264 L180343-180362), so the fields have to come from a custom type, which is metadata.

**Solution:** `force-app/main/default/managedContentTypes/EventAnnouncement.managedContentType-meta.xml` (suffix and folder: api_meta 264 L89072-89074), shaped on the guide's sample (L89243-89292):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ManagedContentType xmlns="http://soap.sforce.com/2006/04/metadata">
    <developerName>EventAnnouncement</developerName>
    <masterLabel>Event Announcement</masterLabel>
    <description>Dated announcement with a summary, body and hero image</description>
    <managedContentNodeTypes>
        <nodeName>headline</nodeName>
        <nodeLabel>Headline</nodeLabel>
        <nodeType>NAMEFIELD</nodeType>
        <isRequired>true</isRequired>
    </managedContentNodeTypes>
    <managedContentNodeTypes>
        <nodeName>summary</nodeName>
        <nodeLabel>Summary</nodeLabel>
        <nodeType>MTEXT</nodeType>
        <isRequired>false</isRequired>
    </managedContentNodeTypes>
    <managedContentNodeTypes>
        <nodeName>body</nodeName>
        <nodeLabel>Body</nodeLabel>
        <nodeType>RTE</nodeType>
    </managedContentNodeTypes>
    <managedContentNodeTypes>
        <nodeName>heroimage</nodeName>
        <nodeLabel>Hero Image</nodeLabel>
        <nodeType>IMG</nodeType>
        <isLocalizable>false</isLocalizable>
    </managedContentNodeTypes>
</ManagedContentType>
```

Why it is shaped this way: exactly one `NAMEFIELD` node, and `isRequired` true on it (api_meta 264 L89221-89232); `IMG` cannot be localized, so `isLocalizable` is false (L89174-89175); `MTEXT` holds up to 2000 characters and `RTE` up to 65536 (L89165-89169); a `NAMEFIELD` is 200 characters or fewer (L89222-89223). Check it with `python3 scripts/check_experience_cloud_cms_content.py --manifest-dir force-app/main/default`, deploy it, and add the detail page for the type in the site (api_meta 264 L89296-89299). The custom type's `ContentTypeFullyQualifiedName` is its developer name, `EventAnnouncement` (object_reference 264 L180363-180365).

UNVERIFIED (2026-10-20): the Digital Experiences screens (Add Content menu, Publish button, Channel Assignments panel) and the CMS component names used to render the item in Experience Builder are Help-only.

---

## Example 2: An Audience That Targets an Experience Variation

**Context:** A retail portal wants a loyalty-tier version of one page section, with everyone else seeing the default.

**Problem:** CMS variants are language variants (object_reference 264 L180665-180670), so audience-specific content is not done by adding a variant to the content item.

**Solution:** `Audience` metadata with a site container, a default audience, and a target of type `ExperienceVariation` (api_meta 264 L26225-26256, L26447-26452), shaped on the guide's sample (L26478-26576):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Audience xmlns="http://soap.sforce.com/2006/04/metadata">
    <audienceName>Loyalty Members</audienceName>
    <container>Customer</container>
    <criteria>
        <criterion>
            <criteriaNumber>1</criteriaNumber>
            <criterionValue>
                <profile>customer community user</profile>
            </criterionValue>
            <operator>Equal</operator>
            <type>Profile</type>
        </criterion>
    </criteria>
    <formulaFilterType>AllCriteriaMatch</formulaFilterType>
    <isDefaultAudience>false</isDefaultAudience>
    <targets>
        <target>
            <groupName>REPLACE_WITH_GROUP_NAME_FOR_THE_PAGE_SECTION</groupName>
            <priority>1</priority>
            <targetType>ExperienceVariation</targetType>
            <targetValue>REPLACE_WITH_VARIATION_DEVELOPER_NAME</targetValue>
        </target>
    </targets>
</Audience>
```

Include ExperienceBundle in the package when the audience has experience variation targets (api_meta 264 L26426). The group name and variation developer name are looked up from the Experience Cloud Developer Guide page the metadata guide points to (L26440-26442, L26470-26472). Personalization by audience "varies what the user can see in the browser but doesn't secure data in any way" (L26595-26596), so do not use it to hide sensitive data.

UNVERIFIED (2026-10-20): scheduling the switch on given dates (earlier versions of this example scheduled a December window per variant) is Help-only; `ManagedContentVariant` has no schedule or audience field (object_reference 264 L180683-180780).

---

## Anti-Pattern: Using Unmanaged Content for Shared Promotional Content

**What practitioners do:** They author promotional content directly in Experience Builder as page content or rich-text components rather than creating CMS workspace items, because it needs no workspace or channel configuration.

**What goes wrong:** UNVERIFIED (2026-10-20): that this content is site-local, cannot be reused across sites, has no version history, scheduling or targeting, and is lost on sandbox refresh is Help-only. What the corpus does show is that a managed item has a consistent identifier so variants can be created over time (object_reference 264 L180277-180279), which a page-local component does not give.

**Correct approach:** Even for a single site, create a CMS workspace and publish reusable or governed content as managed content items. Reserve page-local content for one-off page text.
