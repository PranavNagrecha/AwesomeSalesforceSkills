# LLM Anti-Patterns — Lightning Record Page Configuration

Common mistakes AI coding assistants make when generating or advising on Lightning record pages.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Answering "Assign This Page to a Profile" with a FlexiPage File

**What the LLM generates:** A complete, well-formed `.flexipage-meta.xml`, presented as the answer to a question about assignment. Sometimes with a closing line like "then activate it in Setup."

**Why it happens:** The question says "record page" and the model reaches for the metadata type whose name matches. `FlexiPage` is also the type with the richest documentation and the most training-data examples, so it dominates the completion. The model has no signal that the answer is incomplete, because the file it produced is genuinely valid.

**Correct pattern:**

```
An assignment is never inside the FlexiPage. Three files, one deploy:

  flexipages/<Page>.flexipage-meta.xml       the page contents
  objects/<Object>/<Object>.object-meta.xml  the ORG DEFAULT (ActionOverride)
  applications/<App>.app-meta.xml            the APP DEFAULT and the
                                             app + record type + profile rows
                                             (AppActionOverride /
                                              AppProfileActionOverride)

package.xml must name FlexiPage, CustomObject, and CustomApplication.
```

**Detection hint:** Any answer to an assignment question whose only artifact is a `.flexipage` file is incomplete. Check whether `CustomObject` or `CustomApplication` appears anywhere in the output.

---

## Anti-Pattern 2: Inventing Assignment Elements Inside FlexiPage

**What the LLM generates:** Plausible-looking children of `<FlexiPage>` that do not exist — `<assignments>`, `<profile>`, `<recordType>`, `<isActive>`, `<active>true</active>`, or a `<pageAssignments>` block.

**Why it happens:** Once the model commits to putting assignment in the FlexiPage (Anti-Pattern 1), it must invent the syntax, and Salesforce metadata conventions make a guess like `<recordType>` look right. Deployment then fails with an unhelpful parse error, or — worse — the element is silently ignored and the page ships inert.

**Correct pattern:**

```
The complete FlexiPage field set is eleven fields:
  description, events, flexiPageRegions, masterLabel, pageTemplate,
  parentFlexiPage, platformActionlist, quickActionList, sobjectType,
  template, type

pageTemplate is DEPRECATED - valid in API 33.0-38.0 only; use template.

There is no active flag. There is no profile field. There is no record type
field. "Activation" in the App Builder writes an ActionOverride or an
AppProfileActionOverride elsewhere; it does not set state on the page.

Take exact element casing from a page retrieved at your project's API
version rather than from memory.
```

**Detection hint:** Diff any generated `<FlexiPage>` child element against the eleven names above. Anything else is invented. Note the trap in the other direction too: `quickActionList` and `platformActionlist` are real FlexiPage children, so an audit that treats only the commonly-seen fields as legitimate will flag valid metadata.

---

## Anti-Pattern 3: Writing Visibility Rules with SQL or Apex Operators

**What the LLM generates:** `<operator>!=</operator>`, `<operator>&gt;=</operator>`, `<operator>LIKE</operator>`, `<operator>IN</operator>`, `<operator>NOT_EQUAL</operator>`, or an attempt to put boolean logic inside the operator: `<operator>AND</operator>`.

**Why it happens:** Visibility criteria look like a WHERE clause, and the model's prior for comparison operators is overwhelmingly SQL and Apex. `UiFormulaCriterion` uses a small, closed enum that appears far less often in training data than `!=` does.

**Correct pattern:**

```xml
<!-- The complete operator set. Nothing else is valid. -->
EQUAL  NE  CONTAINS  GT  GE  LT  LE

<!-- Boolean logic is a SEPARATE field, indexing criteria from 1: -->
<visibilityRule>
    <criteria>
        <leftValue>{!Record.StageName}</leftValue>
        <operator>EQUAL</operator>
        <rightValue>Closed Won</rightValue>
    </criteria>
    <criteria>
        <leftValue>{!$User.Department}</leftValue>
        <operator>NE</operator>
        <rightValue>Finance</rightValue>
    </criteria>
    <booleanFilter>1 AND 2</booleanFilter>
</visibilityRule>
```

**Detection hint:** Grep generated XML for `<operator>` and assert membership in the seven-value set. Grep for `AND` or `OR` inside an `<operator>` element — that logic belongs in `booleanFilter`.

---

## Anti-Pattern 4: Emitting Pre-API-49 Metadata Shape

**What the LLM generates:** `<componentInstances>` directly under `<flexiPageRegions>` with no `<itemInstances>` wrapper; multi-value component properties as a comma-separated `<value>Clone,Edit,Delete</value>`; component instances with no `<identifier>`.

**Why it happens:** The pre-49.0 shape was current for years and dominates blog posts, Stack Exchange answers, and older sample repos. The model has no way to date the snippet it is reproducing, and both shapes look equally plausible.

**Correct pattern:**

```xml
<!-- API 49.0+ : itemInstances wraps componentInstance or fieldInstance -->
<flexiPageRegions>
    <itemInstances>
        <componentInstance>
            <componentInstanceProperties>
                <name>enabledActions</name>
                <valueList>
                    <valueListItems><value>Clone</value></valueListItems>
                    <valueListItems><value>Edit</value></valueListItems>
                </valueList>
            </componentInstanceProperties>
            <componentName>force:highlightsPanel</componentName>
            <identifier>force_highlightsPanel</identifier>  <!-- required API 53.0+, max 120 chars -->
        </componentInstance>
    </itemInstances>
    <name>header</name>
    <type>Region</type>
</flexiPageRegions>
```

**Detection hint:** Three greps. `<componentInstances>` as a direct child of a region is the removed pre-49.0 element. A `<value>` containing a comma inside a property that represents a list should be a `valueList`. A `componentInstance` or `fieldInstance` with no `identifier` fails validation at API 53.0 and later.

---

## Anti-Pattern 5: Claiming a Record Page Can Be Assigned by Permission Set

**What the LLM generates:** "Assign the page to the Sales Manager permission set", or metadata with an invented `<permissionSet>` qualifier alongside `<profile>`, often offered helpfully in an org the model has been told is migrating away from profiles.

**Why it happens:** Almost every other access decision in modern Salesforce moved to permission sets, and the model generalises. The absence of a permission-set option here is a genuine platform gap, not something the model can infer from adjacent patterns.

**Correct pattern:**

```
AppProfileActionOverride fields: actionName, content, formFactor,
                                 pageOrSobjectType, recordType, type, profile

`profile` is the ONLY identity qualifier. There is no permission set,
no permission set group, and no custom permission in the assignment.

To differentiate by something permission-set-assignable, use ONE page and
put a custom permission in the COMPONENT visibility rule instead:

  <leftValue>{!$Permission.CustomPermission.View_Risk_Panel}</leftValue>
  <operator>EQUAL</operator>
  <rightValue>true</rightValue>
```

**Detection hint:** Any output containing both "permission set" and "page assignment" in the same recommendation. The correct answer routes the differentiation to component visibility, not to the assignment.

---

## Anti-Pattern 6: Treating Component Visibility as an Access Control

**What the LLM generates:** "Hide the Discount__c field from non-managers by adding a visibility filter on the field instance" — offered as the answer to a security or confidentiality requirement, with no mention of field-level security.

**Why it happens:** The requirement is phrased as "users should not see X", the filter mechanism visibly satisfies it on screen, and the model has no runtime feedback that the field is still fully readable elsewhere.

**Correct pattern:**

```
Component and field visibility rules are PRESENTATION only. A hidden field is
still readable through:
    the REST/SOAP/Bulk APIs, reports, list views, SOQL in Apex,
    any LWC that queries it, and data exports.

To restrict:  field-level security (and sharing, for record access).
To declutter: visibility rules.

Correct answer to "non-managers must not see Discount__c":
    1. Remove Read from the field's FLS for the relevant permission sets.
    2. Optionally ALSO add a visibility rule, so the layout does not show a
       blank space where the field would be.
```

**Detection hint:** Look for a confidentiality or compliance requirement answered purely with `visibilityRule`. If field-level security is not mentioned, the answer is wrong regardless of how correct the XML is.

---

## Anti-Pattern 7: Auditing Pages with a Deprecated or Illegal Tooling API Query

**What the LLM generates:** `SELECT Id, Metadata FROM FlexiPage` across an entire org; or `SELECT ... FROM FlexiPage WHERE SobjectType = 'Account'`; or a claim that record page assignments can be read from the `FlexiPage` object.

**Why it happens:** `SobjectType` is the intuitive field name and was correct before API 39.0. `Metadata` is the field that appears to hold what the user wants. And since assignment is conceptually "about" the page, the model assumes the page object exposes it.

**Correct pattern:**

```soql
-- Enumerate (cheap, works at any result size):
SELECT Id, DeveloperName, MasterLabel, Type, EntityDefinitionId
FROM FlexiPage
WHERE Type = 'RecordPage'

-- Then fetch Metadata ONE page at a time. FullName and Metadata may only be
-- queried when the result contains a single record.
SELECT Id, FullName, Metadata FROM FlexiPage WHERE Id = '0M0xx0000004Cxx'
```

```
SobjectType is deprecated as of API 39.0 — filter on EntityDefinitionId.
Standard objects filter by name ('Account'); custom objects by the
EntityDefinition ID, not the API name.

Assignment is NOT on the FlexiPage object. Retrieve CustomObject and
CustomApplication metadata to read the overrides.
```

**Detection hint:** Any generated Tooling API query that selects `Metadata` or `FullName` without a single-record `WHERE Id =` filter, or that filters on `SobjectType`. Any claim that an assignment can be read from `FlexiPage`.
