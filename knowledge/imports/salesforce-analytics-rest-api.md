# Salesforce Analytics REST API Developer Guide
Source: https://developer.salesforce.com/docs/
Downloaded: 2026-04-03

> **Title:** CRM Analytics REST API Developer Guide — Spring '26 (last updated March 20, 2026)
>
> **Scope of this extract:** This document covers all 41 pages of the CRM Analytics REST API Developer Guide. It includes: the API overview and capabilities, Quick Start (Postman setup, authentication), usage examples (Query API, History API, dataflow scheduling), and the REST Resources reference (Wave resource, resource listing, filtering, resource descriptions for all major resource groups).

---


## Crm Analytics Rest Api Overview

You can access CRM Analytics features such as datasets, dashboards, and lenses programmatically using the CRM Analytics REST API.

Using the CRM Analytics REST API, you can:

- Send queries directly to the CRM Analytics Platform.

- Access datasets that have been imported into the CRM Analytics Platform.

- Create and retrieve CRM Analytics lenses.

- Create, validate, and update templates for CRM Analytics apps.

- Back up and restore previous versions of CRM Analytics dashboards, lenses, and dataflows. See Backup and Restore Previous Versions

of CRM Analytics Assets with History API.

- Run, schedule, and sync CRM Analytics dataflows, recipes, and connections. See Run, Schedule, and Sync CRM Analytics Data with

REST APIs

- Retrieve a list of dataflow job nodes and details for each individual node.

- Access XMD information.

- Create and retrieve standard datasets.

- Retrieve a list of dataset versions.

- Convert Data 360 data model objects to datasets.

- Create and retrieve CRM Analytics apps.

- Create, update, and retrieve CRM Analytics dashboards.

- Retrieve a list of dependencies for an application.

- Determine what features are available to the user.

- Work with and schedule Trend in CRM Analytics report snapshots.

- Manipulate synced datasets, also known as connected objects.

- Get, add, update, and delete ‘eclair’ geo map charts.

- Work with data connectors.

- Retrieve or update recipe metadata. See Build, Manage, Schedule, and Run Recipes with REST APIs

- Discover whether objects and particular dataset versions have support for sharing inheritance.

- Create, update, and retrieve auto-install requests for embedded CRM Analytics applications.

- Create and retrieve collections of CRM Analytics resources.

- Create, update, and retrieve email subscriptions for updates on important analytics.

- Create and retrieve watchlists to track important metrics.

- Test JSON template transformation rules.

- Retirive analytics assets and asset files.

- Download a CRM Analytics dashboard or lens or a Lightning Experience dashboard or report as an image or PDF. For more information

see, the Analytics Download resource in the Salesforce Reports and Dashboards REST API Developer Guide.

- Get Einstein Discovery predictions on Salesforce objects and more via the  smartdatadiscovery  API. For more information,

see the Einstein Discovery REST API Developer Guide.


CRM Analytics REST API Overview

CRM Analytics Connect REST API Release Notes

- Access Search Insights features via the  autonomous-analtyics  API. For more information, see the Search Insights REST API

Developer Guide.

The CRM Analytics REST API is based on the Connect REST API and follows its conventions. For more information about the Connect
REST API, see the Connect REST API Developer Guide.

CRM Analytics Connect REST API Release Notes
Use the Salesforce Release Notes to learn about the most recent updates and changes to the CRM Analytics Connect REST API.

Connect REST API Authorization
Connect REST API uses OAuth to securely identify your application before connecting to Salesforce.

CRM Analytics Lightning Web Components
Use CRM Analytics Lightning Web Components to retrieve data and metadata for CRM Analytics assets, execute queries, and schedule
data syncs for recipes and dataflows.

API End-of-Life Policy
Salesforce is committed to supporting each API version for a minimum of three years from the date of first release. In order to mature
and improve the quality and performance of the API, versions that are more than three years old might cease to be supported.

CRM Analytics Connect REST API Release Notes

Use the Salesforce Release Notes to learn about the most recent updates and changes to the CRM Analytics Connect REST API.

For new and changed CRM Analytics Connect REST resources and request and response bodies see CRM Analytics in the Salesforce
Release Notes.

Note:  If the API: New and Changed Items section in the Salesforce Release Notes isn’t present, there aren’t any updates for that
release.

Connect REST API Authorization

Connect REST API uses OAuth to securely identify your application before connecting to Salesforce.

OAuth and Connect REST API

For current OAuth information, see OAuth and Connect REST API in the Connect REST API developer guide.

More Resources

Salesforce offers the following resources to help you navigate connected apps and OAuth:

- Salesforce Help: Connected Apps

- Salesforce Help: Authorize Apps with OAuth

- Salesforce Help: OpenID Connect Token Introspection

- Trailhead: Build Integrations Using Connected Apps


CRM Analytics REST API Overview

CRM Analytics Lightning Web Components

CRM Analytics Lightning Web Components

Use CRM Analytics Lightning Web Components to retrieve data and metadata for CRM Analytics assets, execute queries, and schedule
data syncs for recipes and dataflows.

The lightning/analyticsWaveApi  module provides wire adapters and JavaScript functions built on top of the CRM Analytics
REST API. Use these wire adapters and functions to work with CRM Analytics data and metadata.

Important:  Not all API endpoints have a corresponding wire adapter or function. Assets such as recipes require the recipe editor
UI for creation and aren’t supported in the  lightning/analyticsWaveApi  module.

Wire Adapters

getActions

Retrieves a collection of Salesforce actions available for the specified Analytics user. For more information on syntax and usage, see the
getActions reference in the Lightning Web Components Developer Guide.

getAnalyticsLimits

Retrieves the Analytics limits for CRM Analytics. For more information on syntax and usage, see the getAnalyticsLimits reference in the
Lightning Web Components Developer Guide.

getDataConnector

Retrieves a specific CRM Analytics data connector by ID or developer name. For more information on syntax and usage, see the
getDataConnector reference in the Lightning Web Components Developer Guide.

getDataConnectors

Retrieves a collection of CRM Analytics data connectors. For more information on syntax and usage, see the getDataConnectors reference
in the Lightning Web Components Developer Guide.

getDataConnectorSourceFields

Retrieves a collection of source fields for a source object used by a CRM Analytics data connector. For more information on syntax and
usage, see the getDataConnectorSourceFields reference in the Lightning Web Components Developer Guide.

getDataConnectorSourceObject

Retrieves a source object used by a CRM Analytics data connector. For more information on syntax and usage, see the
getDataConnectorSourceObject reference in the Lightning Web Components Developer Guide.

getDataConnectorSourceObjectDataPreviewWithFields

Retrieves the fields for a data preview for a source object used by a CRM Analytics data connector. For more information on syntax and
usage, see the getDataConnectorSourceObjectDataPreviewWithFields reference in the Lightning Web Components Developer Guide.

getDataConnectorStatus

Retrieves the status for a specific CRM Analytics data connector by ID or developer name. For more information on syntax and usage,
see the getDataConnectorStatus reference in the Lightning Web Components Developer Guide.

getDataConnectorTypes

Retrieves the collection of CRM Analytics data connector types. For more information on syntax and usage, see the getDataConnectorTypes
reference in the Lightning Web Components Developer Guide.

getDataflowJob

Retrieves a specific CRM Analytics dataflow job. For more information on syntax and usage, see the getDataflowJob reference in the
Lightning Web Components Developer Guide.


CRM Analytics REST API Overview

CRM Analytics Lightning Web Components

getDataflowJobs

Retrieves a collection of CRM Analytics dataflow jobs. For more information on syntax and usage, see the getDataflowJobs reference in
the Lightning Web Components Developer Guide.

getDataflowJobNode

Retrieves a specific CRM Analytics dataflow job node for a recipe or dataflow. For more information on syntax and usage, see the
getDataflowJobNode reference in the Lightning Web Components Developer Guide.

getDataflowJobNodes

Retrieves a collection of CRM Analytics dataflow job nodes for a recipe or dataflow. For more information on syntax and usage, see the
getDataflowJobNodes reference in the Lightning Web Components Developer Guide.

getDataflows

Retrieves a collection of CRM Analytics dataflows. For more information on syntax and usage, see the getDataflows reference in the
Lightning Web Components Developer Guide.

getDataset

Retrieves a specific CRM Analytics dataset by ID or developer name. For more information on syntax and usage, see the getDataset
reference in the Lightning Web Components Developer Guide.

getDatasets

Retrieves a collection of CRM Analytics datasets. For more information on syntax and usage, see the getDatasets reference in the Lightning
Web Components Developer Guide.

getDatasetVersion

Retrieves a specific CRM Analytics dataset version by ID or developer name. For more information on syntax and usage, see the
getDatasetVersion reference in the Lightning Web Components Developer Guide.

getDatasetVersions

Retrieves a collection of versions for a CRM Analytics dataset. For more information on syntax and usage, see the getDatasetVersions
reference in the Lightning Web Components Developer Guide.

getDependencies

Retrieves a collection of dependencies for a CRM Analytics asset. For more information on syntax and usage, see the getDependencies
reference in the Lightning Web Components Developer Guide.

getRecipe

Retrieves a specific CRM Analytics recipe by ID. For more information on syntax and usage, see the getRecipe reference in the Lightning
Web Components Developer Guide.

getRecipes

Retrieves a collection of CRM Analytics recipes. For more information on syntax and usage, see the getRecipes reference in the Lightning
Web Components Developer Guide.

getReplicatedDataset

Retrieves a specific CRM Analytics replicated dataset by ID, also known as a connected object. For more information on syntax and usage,
see the getReplicatedDataset reference in the Lightning Web Components Developer Guide.

getReplicatedDatasets

Retrieves a collection of CRM Analytics replicated datasets, also known as connected objects. For more information on syntax and usage,
see the getReplicatedDatasets reference in the Lightning Web Components Developer Guide.

getReplicatedFields


CRM Analytics REST API Overview

CRM Analytics Lightning Web Components

Retrieves a collection of fields belonging to a CRM Analytics replicated dataset, also known as connected object. For more information
on syntax and usage, see the getReplicatedFields reference in the Lightning Web Components Developer Guide.

getSchedule

Retrieves a schedule for a CRM Analytics recipe, dataflow, or data sync. For more information on syntax and usage, see the getSchedule
reference in the Lightning Web Components Developer Guide.

getSecurityCoverageDatasetVersion

Retrieves the security coverage for a specific CRM Analytics dataset version by ID or developer name. For more information on syntax
and usage, see the getSecurityCoverageDatasetVersion reference in the Lightning Web Components Developer Guide.

getStories

Retrieves a collection of Einstein Discovery stories. For more information on syntax and usage, see the getStories reference in the Lightning
Web Components Developer Guide.

getWaveFolder

Retrieves a specific CRM Analytics app or folder. For more information on syntax and usage, see the getWaveFolder reference in the
Lightning Web Components Developer Guide.

getWaveFolders

Retrieves a collection of CRM Analytics apps or folders. For more information on syntax and usage, see the getWaveFolders reference in
the Lightning Web Components Developer Guide.

getWaveTemplate

Retrieves a CRM Analytics template by ID or API name. For more information on syntax and usage, see the getWaveTemplate reference
in the Lightning Web Components Developer Guide.

getWaveTemplateConfig

Retrieves the configuration for a CRM Analytics template by ID or API name. For more information on syntax and usage, see the
getWaveTemplateConfig reference in the Lightning Web Components Developer Guide.

getWaveTemplateReleaseNotes

Retrieves the release notes for a CRM Analytics template by ID or API name. For more information on syntax and usage, see the
getWaveTemplateReleaseNotes reference in the Lightning Web Components Developer Guide.

getWaveTemplates

Retrieves a collection of CRM Analytics templates. For more information on syntax and usage, see the getWaveTemplates reference in
the Lightning Web Components Developer Guide.

getXmd

Retrieves a specific CRM Analytics extended metadata type (Xmd) for a version of a dataset. For more information on syntax and usage,
see the getXmd reference in the Lightning Web Components Developer Guide.

Functions

createDataConnector

Creates an instance of a CRM Analytics connector to connect to data in your Salesforce orgs, apps, data warehouses, and database
services. For more information on syntax and usage, see the createDataConnector reference in the Lightning Web Components Developer
Guide.

createDataflowJob


CRM Analytics REST API Overview

CRM Analytics Lightning Web Components

Creates a CRM Analytics dataflow job, which is the equivalent of clicking Run Now for a data prep recipe, a data sync, or a dataflow in
the CRM Analytics Data Manager UI. For more information on syntax and usage, see the createDataflowJob reference in the Lightning
Web Components Developer Guide.

createDataset

Creates a dataset. For more information on syntax and usage, see the createDataset reference in the Lightning Web Components
Developer Guide.

createDatasetVersion

Creates a version for a specific CRM Analytics dataset by ID or developer name. For more information on syntax and usage, see the
createDatasetVersion reference in the Lightning Web Components Developer Guide.

createReplicatedDataset

Creates a CRM Analytics replicated dataset, also known as a connected object. For more information on syntax and usage, see the
createReplicatedDataset reference in the Lightning Web Components Developer Guide.

deleteDataConnector

Deletes a specific CRM Analytics connector by ID or developer name. For more information on syntax and usage, see the
deleteDataConnector reference in the Lightning Web Components Developer Guide.

deleteDataset

Deletes a specific CRM Analytics dataset by ID or developer name. For more information on syntax and usage, see the deleteDataset
reference in the Lightning Web Components Developer Guide.

deleteRecipe

Deletes a specific CRM Analytics recipe by ID. For more information on syntax and usage, see the deleteRecipe reference in the Lightning
Web Components Developer Guide.

deleteReplicatedDataset

Deletes a specific CRM Analytics replicated dataset by ID. For more information on syntax and usage, see the deleteReplicatedDataset
reference in the Lightning Web Components Developer Guide.

deleteWaveFolder

Deletes a specific CRM Analytics app or folder by ID. For more information on syntax and usage, see the deleteWaveFolder reference in
the Lightning Web Components Developer Guide.

executeQuery

Executes a CRM Analytics query written in Salesforce Analytics Query Language (SAQL) or standard SQL. For more information on syntax
and usage, see the executeQuery reference in the Lightning Web Components Developer Guide.

ingestDataConnector

Triggers the CRM Analytics to run a data sync. For more information on syntax and usage, see the ingestDataConnector reference in the
Lightning Web Components Developer Guide.

postWaveFolders

Creates a CRM Analytics app or folder by ID. For more information on syntax and usage, see the postWaveFolders reference in the
Lightning Web Components Developer Guide.

updateDataConnector

Updates a CRM Analytics data connector. For more information on syntax and usage, see the updateDataConnector reference in the
Lightning Web Components Developer Guide.

updateDataflowJob


CRM Analytics REST API Overview

API End-of-Life Policy

Updates a CRM Analytics dataflow job, which is the equivalent of clicking Stop for a data prep recipe, a data sync, or a dataflow in the
CRM Analytics Data Manager UI. For more information on syntax and usage, see the updateDataflowJob reference in the Lightning Web
Components Developer Guide.

updateDataset

Updates a specific CRM Analytics dataset by ID or developer name. For more information on syntax and usage, see the updateDataset
reference in the Lightning Web Components Developer Guide.

updateDatasetVersion

Updates a specific CRM Analytics dataset version by ID or developer name. For more information on syntax and usage, see the
updateDatasetVersion reference in the Lightning Web Components Developer Guide.

updatePartialWaveFolder

Performs a partial update for a CRM Analytics app or folder by ID. For more information on syntax and usage, see the
updatePartialWaveFolder reference in the Lightning Web Components Developer Guide.

updateRecipe

Updates a CRM Analytics recipe. For more information on syntax and usage, see the updateRecipe reference in the Lightning Web
Components Developer Guide.

updateReplicatedDataset

Updates a CRM Analytics replicated dataset by ID. For more information on syntax and usage, see the updateReplicatedDataset reference
in the Lightning Web Components Developer Guide.

updateReplicatedFields

Updates the collection of fields for a CRM Analytics replicated dataset by ID. For more information on syntax and usage, see the
updateReplicatedFields reference in the Lightning Web Components Developer Guide.

updateSchedule

Updates the schedule for a CRM Analytics data prep recipe, data sync, or dataflow. For more information on syntax and usage, see the
updateSchedule reference in the Lightning Web Components Developer Guide.

updateXmd

Updates the user Xmd for a CRM Analytics dataset. For more information on syntax and usage, see the updateXmd reference in the
Lightning Web Components Developer Guide.

updateWaveFolder

Updates a CRM Analytics app or folder by ID. For more information on syntax and usage, see the updateWaveFolder reference in the
Lightning Web Components Developer Guide.

validateWaveTemplate

Validates a CRM Analytics template for org readiness. For more information on syntax and usage, see the valildateWaveTemplate reference
in the Lightning Web Components Developer Guide.

API End-of-Life Policy

Salesforce is committed to supporting each API version for a minimum of three years from the date of first release. In order to mature
and improve the quality and performance of the API, versions that are more than three years old might cease to be supported.

When an API version is to be deprecated, advance notice is given at least one year before support ends. Salesforce will directly notify
customers using API versions planned for deprecation.


CRM Analytics REST API Overview

API End-of-Life Policy

Salesforce API Versions

Version Support Status

Version Retirement Info

Versions 31.0 through 66.0

Supported.

Versions 21.0 through 30.0

As of Summer ’25, these versions are retired
and unavailable.

Salesforce Platform API Versions 21.0 through 30.0
Retirement

Versions 7.0 through 20.0

As of Summer ’22, these versions are retired
and unavailable.

Salesforce Platform API Versions 7.0 through 20.0
Retirement

If you request any resource or use an operation from a retired API version, REST API returns  410:GONE  error code.

To identify requests made from old or unsupported API versions of REST API, access the free API Total Usage event type.


## Quick Start

Connect to a Salesforce Trailhead org and authenticate. Then make a request to the CRM Analytics REST API in Postman, and look at the
response.

Prerequisites
Complete these prerequisites before you begin the quick start.

Configure Your Trailhead Org
To configure your Trailhead org, set up Cross-Origin Resource Sharing (CORS) and a connected app.

Authenticate to Your Trailhead Playground Org
After configuring the connected app, you must authorize your user with the connected app.

Set Up Your Postman Collection
Set up Postman to work with the Salesforce CRM Analytics Connect API collection.

Use Postman to Send a CRM Analytics Request
With Postman, you can explore and test your CRM Analytics API calls across multiple organizations with full control on headers,
parameters, and content type.

Prerequisites

Complete these prerequisites before you begin the quick start.

- Download and install the Postman Desktop App.
- Generate a private-public keypair (.key and .crt files) on your Mac or Microsoft® Windows®machine if you haven’t already done so.

- Sign up for a Trailhead Playground org with CRM Analytics enabled.

Configure Your Trailhead Org

To configure your Trailhead org, set up Cross-Origin Resource Sharing (CORS) and a connected app.

Set up CORS and your connected app.

Set Up CORS

CORS allows code running in a web browser to communicate with Salesforce from a specific origin. To add the URL patterns for Postman:

1.

2.

In your Trailhead Playground, from Setup, in the Quick Find box, enter  cors, and then select CORS.

In the Allowed Origins List, click New.

3. Enter  https://*.postman.com  as the Origin URL Pattern.

4. Save your work.

5. Click New, and enter  https://*.postman.com  as the Origin URL Pattern.

6. Save your work again.


Quick Start

Set Up a Connected App

Set Up a Connected App

To set up your connected app:

1. From Setup, in the Quick Find box, enter  App Manager, and then select New Connected App.

2. Enter the app name in the Connected App Name field, and enter your email address in the Contact Email field.

3. Under API Heading, select Enable OAuth Settings.

4. Enter the callback URL:  https://oauth.pstmn.io/v1/callback.

5. Select Use digital signatures.

6. Select Choose File, and then select the host.crt file from your private public keypair.

7. Under Selected OAuth Scopes, select the Manage user data via APIs (api) and the Perform requests at any time (refresh_token,

offline_access) scopes.

8. Deselect Require Proof Key for Code Exchange (PKCE) Extension for Supported Authorization Flow.

9. Save your work.

10. On the connected app details page, click the Manage Consumer Details button. This action triggers a verification code sent to

your email. Then you can see the Key and Secret values.

11. At the top of the new connected app, click Manage, and then select Edit Policies.

12. Under IP Relaxation, select Relax IP restrictions, and save your changes.

Authenticate to Your Trailhead Playground Org

After configuring the connected app, you must authorize your user with the connected app.

Authorize the app

Construct a URL by using this format.

YOUR_ORG_URL/services/oauth2/authorize?response_type=code&client_id=YOUR_CONSUMER_KEY&scope=api

refresh_token offline_access &redirect_uri=https://oauth.pstmn.io/v1/callback

- YOUR_ORG_URL  is the fully qualified instance URL.

- YOUR_CONSUMER_KEY  is the consumer key noted when you set up the connected app.

Next, paste the URL into a browser and execute it, and then select Allow for each of the scopes requested in the modal that appears. If
you receive an alert from the callback, select Open Postman.. To verify that everything is authorized, from Setup, in the box, enter
Connected Apps OAuth Usage, and confirm that you see your connected app with a user count of 1.

Set Up Your Postman Collection

Set up Postman to work with the Salesforce CRM Analytics Connect API collection.

Create your Postman workspace, fork the collection, and authorize your org.

Create a Postman Workspace

Configure the desktop Postman app if you haven’t already done so.


Quick Start

Fork the Salesforce CRM Analytics API Collection

1. Make sure that you previously downloaded and installed the Postman Desktop App.

2. Select the Workspaces menu.

3. Select Create Workspace.

4. Name your workspace, for example, SalesforceCRMACollection.

5. For Visibility, set it to Personal.

6. Click Create Workspace.

Fork the Salesforce CRM Analytics API Collection

Fork the main collection for your own use.

1. At the top of your Postman Desktop app, click Search Postman, click Teams, and enter  Salesforce Developers  in the

search bar.

2. Click Salesforce Developers, then click the Salesforce Developers tile.

3. Hover over the Subscription Management collection, click the three dots, then click Create a Fork.

4. Label the fork, choose the workspace, and click Fork Collection. Your workspace contains your fork of the CRM Analytics Connect

API collection.

Authorize your Org

Authorize your Salesforce Trailhead org for your forked collection.

1.

In your Postman workspace, select your forked Salesforce CRM Analytics Connect APIs collection.

2. Select No Environment.

3. Click the Authorization tab, and select OAuth 2.0 as the type.

4. At the bottom of the Authorization tab, click Get New Access Token.

5. To let the Collection access your Trailhead Playground, click Allow. A success message appears briefly, and then you’re redirected

to the Manage Access Tokens dialog.

6. Verify that the  instance_url  points to your Trailhead Playground.

7. Copy the  instance_url, making sure to copy only the URL with no extra characters.

8. Click Use Token.

9. Select the Variables tab.

10. In the  _endpoint  row,  CURRENT VALUE  column, paste the  instance_url  value that you copied previously.

11. Set the Salesforce API version number in the  version  row,  CURRENT VALUE  column.

12. Enter the URL that you run each request against in the  baseURL row,  CURRENT VALUE  column.

13. Save your work.

Use Postman to Send a CRM Analytics Request

With Postman, you can explore and test your CRM Analytics API calls across multiple organizations with full control on headers, parameters,
and content type.

To make a request to your org:


Quick Start

Use Postman to Send a CRM Analytics Request

1. Select the CRM Analytics Collect API folder to expand it.

2. To access a related collection of endpoints, select a subfolder. For this example, we use the Folders | GETWaveFolderCollection.

3. Click Send, and verify that the status is 200

OK.


## Crm Analytics Rest Api Examples

Use CRM Analytics REST API examples to perform tasks.

While using the CRM Analytics REST API, keep this in mind:

- Request parameters may be included as part of the CRM Analytics REST API resource URL, for example,

/wave/folders?q=searchtext. A request body is a rich input which may be included as part of the request. When accessing
a resource, you can use either a request body or request parameters. You cannot use both.

- With a request body, use  Content-Type: application/json  or  Content-Type: application/xml.

- With request parameters, use  Content-Type: application/x-www-form-urlencoded.

- To test working example of the CRM Analytics API endpoints and view payload information, see theCRM Analytics Connect API
Collection in Postman. For information about how to authenticate your org with Postman, see the CRM Analytics Rest API Quick
Start

Query CRM Analytics Data with the Query API
Use the CRM Analytics REST API to directly query analytics data using SAQL or SQL queries.

Backup and Restore Previous Versions of CRM Analytics Assets with History API
When you edit CRM Analytics dashboards, lenses, recipes, and dataflows, CRM Analytics backs them up automatically. When you
save a new version of an asset, CRM Analytics creates a snapshot of it. You can then preview snapshots and revert to previous versions
using the REST History API.

Run, Schedule, and Sync CRM Analytics Data with REST APIs
You can use the CRM Analytics REST API to automate features, like running and scheduling data syncs, dataflows and recipes.

Query CRM Analytics Data with the Query API

Use the CRM Analytics REST API to directly query analytics data using SAQL or SQL queries.

Execute Analytics Queries Programmatically

You can use a REST API to query analytics datasets using either SAQL or SQL query statements. The query endpoint is  wave/query
and takes a POST request body using a SAQL Query Input to execute the query.

Note:  You can use the Lightning Web Component  lightning/analyticsWaveApi  module to bring this functionality
into Salesforce, without proxying REST APIs directly. For more information, see the reference section for the executeQuery
function.

Example SAQL Query Request

For SAQL queries executed using REST API, you must have both the dataset ID and the dataset version ID to specify the dataset you
want to query. Using the name of the dataset in the query returns an error. The only required attribute for the request is  query.

{

"query" : "q = load \"<datasetId>/<datasetVersionId>\"; q = group q by 'Status'; q

= foreach q generate 'Status' as 'Status', count() as 'count'; q = limit q 20;",


CRM Analytics REST API Examples

Query CRM Analytics Data with the Query API

"queryLanguage" : "SAQL"

}

Example SAQL Query Response

The response results include  metadata  and  records. It also returns the original query and the response time. If there are
warnings or errors,  warnings  is included. For the SAQL query executed in the previous example, here’s the response:

{

"action" : "query",
"responseId" : "4l-kl6BTnH4ay9-qbx2Re-",
"results" : {

"metadata" : [ {
"lineage" : {

"type" : "foreach",
"projections" : [ {

"field" : {

"id" : "q.Status",
"type" : "string"

},
"inputs" : [ {

"id" : "q.Status"

} ]

}, {

"field" : {

"id" : "q.count",
"type" : "numeric"

}
} ],
"input" : {

"type" : "group",
"groups" : [ {

"id" : "q.Status"

} ]

}

},
"queryLanguage" : "SAQL"

} ],
"records" : [ {

"Status" : "Closed",
"count" : 7

}, {

"Status" : "Open",
"count" : 6

} ]

},
"query" : "q = load \"<datasetId>/<datasetVersionId>\"; q = group q by 'Status'; q =

foreach q generate 'Status' as 'Status', count() as 'count'; q = limit q 20;",

"responseTime" : 3,
"warnings" : [

{

"code" : "001",
"message" : "Limit exceeded"

},
{


CRM Analytics REST API Examples

Query CRM Analytics Data with the Query API

"code" : "002",
"message" : "Another warning..."

}

]

}

Example SQL Request Body

The default language for query execution is SAQL. To use SQL, include the attribute  "queryLanguage" : "SQL"  in your
request. For SQL queries, you can use the dataset name. Here’s the same query request in SQL.

{

"query" : "SELECT Status, COUNT(*) as StatusCount FROM \"<name>\" GROUP BY Status

LIMIT 20;",

"queryLanguage": "SQL"

}

Note:  If you forget to specify  "queryLanguage" : "SQL", the request returns a syntax error.

Example SQL Query Response

The response records look the same as the SAQL response, but the  metadata  is different. The  columns  key includes the name
and type of projections in the query.

{

"action" : "query",
"responseId" : "4l-mtW26NZ4OYu-qbx3GN-",
"results" : {

"metadata" : [

{

}

"columns" : [

{

"columnLabel" : "Status",
"columnType" : "varchar"

},
{

"columnLabel" : "StatusCount",
"columnType" : "numeric"

}

],
"queryLanguage" : "SQL"

],
"records" : [

{

"Status" : "Closed",
"StatusCount" : 7

},
{

"Status" : "Open",
"StatusCount" : 6

}

]

},
"query" : "SELECT Status, COUNT(*) as StatusCount FROM \"Cases1\" GROUP BY Status

LIMIT 20;",


CRM Analytics REST API Examples

Query CRM Analytics Data with the Query API

"responseTime" : 9

}

Example SQL Metadata: Group By Query With an Aggregation

The query projects the aggregation  avg(Sales)  as  AvgSales, which returns numerical data. In the  metadata, the
corresponding column type is returned as numeric.

"metadata": [

"columns": [

{

"columnLabel": "City",
"columnType": "varchar"

},
{

"columnLabel": "AvgSales",
"columnType": "numeric"

}

],
"queryLanguage": "SQL"

]

Example SQL Query and Response Body: Extract Date Parts from a Date Field

This example returns the year, month, and day from the CloseDate  field as numerical values. The request features the timezone
attribute, which is attribute is optional and can only be used if timezone is enabled for the org.

{

"query" : "SELECT EXTRACT(YEAR FROM CloseDate) as year, EXTRACT(MONTH FROM CloseDate)

as month, EXTRACT(DAY FROM CloseDate) as day From "OpportunityFiscalEM"

"queryLanguage" : "SQL",
"timezone" : "America/Los_Angeles"

}

"metadata": [

"columns": [

{

"columnLabel": "year",
"columnType": "numeric"

},
{

"columnLabel": "month",
"columnType": "numeric"

},
{

"columnLabel": "day",
"columnType": "numeric"

}

],
"timezone": "America/Los_Angeles",
"queryLanguage": "SQL"

]


CRM Analytics REST API Examples

Query CRM Analytics Data with the Query API

Example SQL Query and Response Body: Project Date Field of Type  DateTime

This query returns date information as timestamps.

{

}

"query" : "SELECT CloseDate From "OpportunityFiscalEM",
"queryLanguage" : "SQL"

"metadata": [

"columns": [

{

}

"columnLabel": "CloseDate",
"columnType": "timestamp"

],
"queryLanguage": "SQL"

]

Query Metadata Details

Clients can parse the queries to figure out what dimensions and groups are used, but this can be expensive. So, in most cases, the
query response contains a  metadata  section, which provides grouping and column information. The  metadata  section, if
present, is found in the  results  key in the query response payload. The  metadata  section is structured with  columns  and
groups  keys:

"metadata":{

"columns" : [

{

}

"name" : "dim name",
"type" : "String"

],
"groups" : [
"name",
"destination"

]

}

The columns key includes the name and type of the projections of the query, and the groups key contains a list of groups used in
the query.

Note:

- The metadata is added when the query is successful. If the query fails to run, if there’s a syntax error, or if the authorization

callback fails then the metadata isn’t added to the results.

- The value set in a column name is the alias given to the projection and not the name of the dimension.

- A list of the groups used in the query is returned in the groups key, provided the query isn’t considered complex—where
the group name returned is nondeterministic (the name of the group is used in multiple streams of the query). This is the
case when the query uses cogroup or union. In such cases, the groups key is empty.

SEE ALSO:

Analytics SAQL Developer Guide

SQL for Analytics Developer Guide


CRM Analytics REST API Examples

Backup and Restore Previous Versions of CRM Analytics
Assets with History API

Backup and Restore Previous Versions of CRM Analytics Assets with
History API

When you edit CRM Analytics dashboards, lenses, recipes, and dataflows, CRM Analytics backs them up automatically. When you save
a new version of an asset, CRM Analytics creates a snapshot of it. You can then preview snapshots and revert to previous versions using
the REST History API.

Every time you save a new version of a dashboard, lens, recipe, or dataflow, CRM Analytics saves the older version. It also saves dashboard
and lens conditional formatting.

CRM Analytics saves 20 versions of an asset, including 10 tagged and 10 untagged versions. When you save more than 20 new versions
of an asset, CRM Analytics saves the new version and purges older versions. When the limit is reached and the save is for a tagged version,
the oldest tagged version is purged. An untagged version save purges the oldest untagged version. To increase this limit, contact
Salesforce and ask your representative to increase the org value Maximum analytics asset histories to track in the database, also
known as  AnalyticsMaxHistories.

You can add tags that describe asset versions to give you and other team members reminders of what's been changed and why. You
can use either manual or automatic tagging.

CRM Analytics gives you two ways to manually tag an asset version.

- The Save dialog displays a Version History box when you save a dashboard or lens. Enter a short description of your changes there.

(Dataflows don't have a user interface for adding tags to previous versions.)

- You can also tag changes with the public REST API. Use the API to tag history records with a description, which you can do after

saving the asset. You can edit existing descriptions.

*PATCH:
/services/data/v46.0/wave/dashboards/0FKxx0000004CAeGAM/histories/0Rmxx0000004Cx2CAE*
*REQUEST BODY: {"label" : "new description"}*

CRM Analytics automatically adds tags to history records in one of two ways.

- When you create and save the initial version of an asset, CRM Analytics adds the tag  Initial Create  to the history record.

- When you create or upgrade an app from a template, CRM Analytics tags history records for the app. The tag includes the template
action, template name, and template version. This information helps you restore the correct previous version of an asset after you
upgrade an app from a new template version.


CRM Analytics REST API Examples

Backup and Restore Previous Versions of CRM Analytics
Assets with History API

Previewing and Reverting to Previous Asset Versions

To get a list of history records for an asset, either use cURL or Postman and execute an API call. Or enter the appropriate command in
the Salesforce Command Line Interface (CLI) with the CRM Analytics plugin.

Warning:  A previous version of a dashboard doesn’t work if assets that the version relies on have been removed from CRM
Analytics. Those assets can be other dashboards, datasets, lenses, and images.

- Dashboard history records.

– API call:

GET: /services/data/v526.0/wave/dashboards/<dashboardId>/histories

– CLI command:

sf analytics dashboard history list

- Lens history records.

– API call:

GET: /services/data/v52.0/wave/dashboards/<lensId>/histories

– CLI command:

sf analytics lens history list

- Recipe history records.

– API call:

GET: /services/data/v52.0/wave/recipes/<recipeId>/histories

- Dataflow history records.

– API call:

GET: /services/data/v52.0/wave/dataflows/<dataflowId>/histories

– CLI command:

sf analytics dataflow history list

Optionally, you can navigate to the History API endpoint with the URL in  historiesUrl  in the Asset Response (HATEOAS) and
execute it with cURL or Postman.

Or manually execute the following REST calls from cURL or Postman:

- Get a list of all dashboards:

GET: /services/data/v52.0/wave/dashboards

- Find a dashboard, use its details URL in the response body:

GET: /services/data/v52.0/wave/dashboards/<dashboardId>


CRM Analytics REST API Examples

Run, Schedule, and Sync CRM Analytics Data with REST APIs

- Get a list of histories, use the  historiesUrl  in the dashboard details response:

GET: /services/data/v52.0/wave/dashboards/*<dashboardId>/histories*

Preview a Previous Version

After listing asset version histories, preview the JSON for a version. During preview, you see the JSON as it looked when it was saved.

To preview the JSON for previous asset versions, use the URL from  previewUrl  in the response body and execute it with cURL or
Postman.

Note:  Dataflows have two preview URLs: previewUrl  and privatePreviewUrl. The private preview URL provides the
same JSON format as you see if you downloaded the JSON file declaratively using the CRM Analytics dataflow editor. The preview
URL provides the public version of the JSON.

Restore a Previous Version

After you confirm you’re previewing the correct asset version, restore it using either REST API calls or the CLI.

Using REST API calls, in the version you want to revert to, locate the  revertUrl.

Then copy the  historyId  of the version you want to restore. You use it in the request body.

Now, to restore an asset from the previous version, perform a  PUT.

*PUT: /services/data/v52.0/wave/dashboards/*<dashboardId>/bundle**
*REQUEST BODY: {"historyId": "<historyId>, historyLabel" : "optional description of new
change"}*

The CLI commands for restoring assets are as follows:

- Dashboards.  sf analytics dashboard history revert -i <dashboardid> -h <historyid>

- Lenses.  sf analytics lens history revert -i <lensid> -h <historyid>

- Dataflows.  sf analytics dataflow history revert -i <dataflowid> -h <historyid>

historyid  is the ID for the version of the asset you want to restore.

Limitations

When you restore the previous version of an asset, the asset doesn’t run as expected. If the asset depends on other assets (for example,
datasets) and those assets have been deleted or modified, you can get errors. However, every time you restore a previous version, you
create a history record. You can always restore the last working copy.

When you delete an asset, all history is deleted with it, and you can’t undelete it.

Currently, CRM Analytics doesn’t back up previous versions of dataset XMD files.

Run, Schedule, and Sync CRM Analytics Data with REST APIs

You can use the CRM Analytics REST API to automate features, like running and scheduling data syncs, dataflows and recipes.


CRM Analytics REST API Examples

Run, Schedule, and Sync CRM Analytics Data with REST APIs

Start and Stop a Dataflow Job or Recipe

You can use REST APIs to automate the start of a dataflow job or recipe to load data into datasets. This API is the equivalent of the "Run
Now" functionality in the Data Manager. You can also stop the job while it’s running. Dataflow jobs include dataflows defined in
wave/dataflows  and recipes defined in  wave/recipes.

Note:  You can use the Lightning Web Component  lightning/analyticsWaveApi  module to access wire adapters
and functions to bring this functionality into Salesforce, without proxying the REST APIs directly. For more information, see the
reference section for lightning/analyticsWaveApi  Wire Adapters and Functions .

- Start a Dataflow Job or Recipe

To start a dataflow or recipe, use the /wave/dataflowjobs endpoint with a POST request. In the POST request body, use the
dataflowId  parameter to specify the dataflow to start. For a recipe, use the targetDataflowId  value for the dataflowId.

{

}

"dataflowId": "02KS700000004G3eMAE",
"command" : "start"

The POST request returns a Dataflow Job.

Note:  If the sync has not previously run or has been updated since the last run, when you run a dataflow or recipe using this
method, the data sync of associated objects runs automatically.

- Stop a Dataflow Job or Recipe

To stop a specific dataflow job, use the /wave/dataflowjobs/<dataflowjobId> endpoint with a PATCH request. The
PATCH request uses the  dataflowjobId request parameter to specify the dataflow job to stop.

{

}

"command" : "stop"

Explore Dataflow Job Nodes

You can use REST APIs to describe and explore each node of a dataflow job, including nodes for standard dataflows and for recipes.

- View All Dataflow Job Nodes

To list the nodes for the dataflow job, use the /wave/dataflowjobs/<dataflowJobId>/nodes endpoint with a GET
request.

The GET request returns a Dataflow Job Node Collection.

Note: This request only works for dataflow jobs with ids starting with  030,  03C, or  0eP. If the dataflow job id starts with  030, the
result is an empty collection.

- View a Single Dataflow Job Node

To view the details of a single dataflow job node, use the /wave/dataflowjobs/<dataflowJobId>/nodes/<nodeId>
endpoint with a GET request.

The GET request returns a Dataflow Job Node.


CRM Analytics REST API Examples

Run, Schedule, and Sync CRM Analytics Data with REST APIs

Schedule Dataflows, Recipes, and Data Syncs

You can automate dataflows, recipes, and data syncs to run on a time-based schedule by hour, week, or month, on specific days of the
week, or dates in the month via the CRM Analytics REST API. For example, schedule a dataflow to ensure that the data is available by a
particular time or to run the job during non-business hours. Use the assetId request parameter to specify the data asset type to schedule.

You can also set an event-based schedule to run a dataflow or recipe after the Salesforce Local connection syncs. Set an event-based
schedule if the dataflow or recipe extracts data from Salesforce objects that have to sync before the dataflow or recipe runs. The
event-based schedule applies to dataflows and recipes only and isn’t currently available for data syncs.

- Schedule a Data Asset

To schedule a data asset, use the /wave/asset/<assetId>/schedule endpoint with a PUT request. The following are
examples for the different types of schedules that can be set in the request body.

Set Hourly Schedule - request body example

This request body sets a time-based schedule that runs hourly every day from 2:30am America/Los Angeles, every 3 hours, and stops
queuing at 8:00pm.

{

}

"daysOfWeek" : [

"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"

],
"lastHour" : 20,
"hourlyInterval" : 3,
"time" : {

"hour" : 2,
"minute" : 30,
"timeZone" : "America/Los_Angeles"

},
"frequency" : "hourly"

Set Weekly Schedule - request body example

This request body sets a time-based schedule that runs weekly on Mondays and Thursdays at 12:45am America/Los Angeles.

{

}

"daysOfWeek" : [

"Monday", "Thursday"

],
"time" : {

"hour" : 0,
"minute" : 45,
"timeZone" : "America/Los_Angeles"

},
"frequency" : "weekly"

Set Monthly Specific Schedule - request body example

This request body sets a time-based schedule that runs monthly on the 1st, 15th, and 31st at 12:00am America/Los Angeles.

{

"daysOfMonth" : [

1, 31, 15

],
"time" : {


CRM Analytics REST API Examples

Run, Schedule, and Sync CRM Analytics Data with REST APIs

"hour" : 0,
"minute" : 0,
"timeZone" : "America/Los_Angeles"

},
"frequency" : "monthly"

}

Set Monthly Relative Schedule - request body example

This request body sets a time-based schedule that runs every month on the last Sunday at 12:00am America/Los Angeles.

{

}

"weekInMonth": "Last",
"dayInWeek": "Sunday"
"time" : {

"hour" : 0,
"minute" : 0,
"timeZone" : "America/Los_Angeles"

},
"frequency" : "monthlyrelative"

Set Event-Based Schedule - request body example

This request body sets an event-based schedule that runs a dataflow after the Salesforce Local connection syncs. Event-based
schedules aren’t supported for Data Connections.

{

}

"triggerRule" : "$ALL_SALESFORCE_OBJECTS",
"frequency" : "eventdriven"

The PUT request uses the  assetId request parameter to specify the dataflow, recipe, or data sync to schedule.

/services/data/<API_VERSION>/wave/asset/02KS7000000xxxxxxx/schedule

The PUT response is empty unless there’s an API error.

The DELETE request uses the  assetId  request parameter to specify the dataflow, recipe, or data sync schedule to delete.

Sync Data Connections

Use the CRM Analytics REST API to automate syncing connected data from your local Salesforce org or external data sources. Synced
data is stored as objects that can be used in dataflows and recipes. This API is the equivalent of the "Run Now" functionality in the Data
Manager.

- Data Sync Run Now

To start a data sync, use the/wave/dataConnectors/<connectorId>/ingest endpoint with a POST request. Execute
the POST to the URL with an empty request body.

{}

The POST request uses the  connectorId  request parameter to specify the data sync to run.

/services/data/<API_VERSION>/wave/dataConnectors/0ItS0000000xxxxxxx/ingest

The POST request returns a Restore Dataset Version.


## Crm Analytics Rest Resources

REST API resources are sometimes called endpoints.

Wave Resource
Lists the top-level resources available for Analytics.

Actions Resource
Returns the Salesforce actions available for the user in Analytics. The  entityId  is the user id.

Analytics Assets Resources
Query Analytics assets using parameters for a collections or query a single asset by ID.

Annotation Resources
Annotate Analytics dashboard widgets with comments posted in the dashboard and in Chatter.

Asset Files Resources
Analytics assets contain files to define their previews. Get a collection of files available and individual files, and create and update
asset files

Auto-Install Request Resources
Auto-Install requests are used to create, update, and delete Analytics embedded apps. Analytics embedded apps are run-time
implementations of Analytics templates and instead of user interaction, they’re managed via auto-install requests.

Collection Resources
Analytics collections let users manage their own groups of items and personalize their Analytics Studio home page.

Dashboard Resources
Analytics dashboards allow users to continuously monitor key metrics of their business. These resources allow users to manage
collections of dashboards, individual dashboards, dashboard saved views, dashboard histories, and dashboard publishers.

Data Connector Resources
Data connectors are prebuilt connectors to quickly connect to data in your Salesforce orgs, apps, data warehouses, and database
services. These resources allow users to manage data connectors and their source objects, run data syncs, and check statuses.

Dataflow Job Resources
Dataflow jobs are used to sync data for data prep recipes and standard dataflows.

Dataflow Resources
Dataflows are used to prepare data for Analytics, creating one or more datasets using transformations to manipulate the data.

Dataset Resources
Manage Analytics dataset and dataset versions.

Dependencies Resource
Returns the dependencies for an asset.

Eclair Chart Resources
Eclair charts render maps and geodata in Analytics dashboards.

Features Configuration Resource
The Analytics features that are available to a user.


CRM Analytics REST Resources

CRM Analytics REST API Resources Overview

Folder Resources
Analytics folders represent apps, a collection of assets. Folders can be created by users or by Analytics templates.

JsonXform Transformation Resource
Performs a JSON transformation by invoking a set of rules and expressions on a JSON document. The transformed JSON is returned
in the REST response and isn't saved on the server. This service is provided to test rules used in Analytics templates.

Limits Resource
The Analytics limits for the Salesforce org.

Lens Resources
Analytics lenses are how users view data in a dataset and are the basis for building any dashboard. These resources allow users to
manage collections of lenses, individual lenses, and lens files.

Query Resource
Executes a query written in Salesforce Analytics Query Language (SAQL) or SQL for CRM Analytics.

Recipe Resources
Recipes are used to prepare data, creating a dataset using transformations to manipulate the data.

Replicated Dataset Resources
Manage Analytics replicated datasets, also know as connected objects. A data sync loads source object data as a connected object
in Analytics. Connected objects can’t be visualized directly, but are used like a cache to speed up other jobs that pull from the source
object and load it into a dataset.

Schedule Resource
Retrieve, create or delete a schedule for a dataflow, recipe, or connection sync.

Subscription Resources
Manages subscriptions for Analytics dashboards.

Security Coverage Dataset Version Resource
Returns the security coverage (sharing inheritance) for a particular dataset version. The source objects listed are local to the org
(there are no objects from other orgs or other external sources).

Security Coverage Object Resource
Returns the security coverage for a particular object. Use this API to discover whether Analytics can inherit sharing settings from an
object.

Template Resources
Manage Analytics templates, template configuration, and template release notes.

Trended Report Resources
Manage Analytics trending reports.

Watchlist Resources
Manages watchlists for Analytics dashboards.

Xmd Resources
Manages Xmds for Analytics datasets and assets.

CRM Analytics REST API Resources Overview

The CRM Analytics REST API provides resources so you can access your CRM Analytics data.

All CRM Analytics REST API resources are accessed using:


CRM Analytics REST Resources

CRM Analytics REST API Resources Overview

- A base URL for your company (for example, https://yourInstance.salesforce.com)

- Version information (for example, /services/data/v53.0)

- A named resource (for example, /wave)

Put together, an example of the full URL to the resource is:

https://yourInstance.salesforce.com/services/data/v53.0/wave

Org and Object Identifiers

Id fields in Salesforce, and in the CRM Analytics UI, are typically 15-character, base-62, case-sensitive strings. This is true of JSON XMD
too. However, many Salesforce APIs, including the CRM Analytics REST API, use 18-character, case-insensitive strings—for example, the
Id  property of the Dataset resource/wave/datasets/<dataset ID>. The last 3 digits are a checksum of the preceding 15
characters. The use of case-insensitive Id’s eases interaction with external applications and development environments that use
case-insensitive references. To convert an 18-character Id back to a 15-character ID, simply remove the last 3 characters.

General Resources

General resources for CRM Analytics are covered here, while specific features like dashboards and recipes have their own sections.

Resource

Description

Resource URL

Supported
HTTP
Method

Actions Resource

Returns the Salesforce actions available for the
user in Analytics.

GET

/wave

Returns the dependencies for an asset.

Returns the CRM Analytics features that are
available to a user.

GET

GET

/wave/dependencies/<folderId>

/wave/config/features

Performs a JSON transformation.

POST

/jsonxform/transformation

Dependencies
Resource

Feature
Configuration
Resource

JsonXform
Transformation
Resource

Limits Resource

Get the Analytics limits for the Salesforce org.

GET

/wave/limits

Query Resource

Executes a query written in Salesforce Analytics
Query Language (SAQL).

POST

/wave/query

Security
Resources

Discover whether objects and particular dataset
versions have support for sharing inheritance.

GET

- /wave/security/coverage/

datasets/<datasetIdOrApiName>/
versions/<versionId>

- /wave/security/coverage/objects/

<objectApiName>

Wave Resource

Lists the top-level resources available for CRM
Analytics.

GET

/wave


CRM Analytics REST Resources

Wave Resource

Filtering REST Responses

Returns the representation for a CRM Analytics application or folder (GET), replaces an application or folder (PUT), updates it (PATCH),
or deletes it (DELETE).

In addition to CRM Analytics REST API input parameters, you can use the following Connect REST API input parameters to filter the results
returned from a request:  filterGroup,  external, and  internal. For more information, see Specifying Response Sizes in the
Connect REST API Developer Guide.

Wave Resource

Lists the top-level resources available for Analytics.

Resource URL

/wave

Formats
JSON

Available Version

36.0

HTTP Methods

GET

Response body for GET

Directory Item Collection

Actions Resource

Returns the Salesforce actions available for the user in Analytics. The  entityId  is the user id.

Resource URL

/wave/actions/<entityId>

Formats

JSON

Available Version

40.0

Available in Postman

To view and test a working example of this resource, see getActionCollection in Postman. For information about how to authenticate
your org with Postman, see the CRM Analytics Rest API Quick Start.