# Salesforce Metadata API Developer Guide
Source: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/
Downloaded: 2026-04-03

> **Version:** 66.0, Spring '26 — Last updated: April 3, 2026
>
> **Scope of this extract:** This document covers pages 1–117 of the full guide: Chapters 1–12 covering concepts, use cases, deployment workflows, file-based calls, CRUD-based calls, REST resources, error handling, the Metadata API Context MCP Tool (Beta), result objects, and the Chapter 13 Metadata Types table of contents. The detailed per-type reference for CustomObject, CustomField, Profile, PermissionSet, Flow, ValidationRule, and all other types begins at page 143 in the full guide and is not contained in this extract.

---

INTRODUCTION TO METADATA API


## CHAPTER 1 Understanding Metadata API

Salesforce Metadata

Metadata is data that describes other data. To understand how Salesforce defines metadata, contrast business data with Salesforce
metadata. Business data includes the records that directly correspond to your company’s business such as an address, account, or product.
Salesforce metadata describes the schema, process, presentation, authorization, and general configuration of your Salesforce org.

To contrast Salesforce metadata with business data, first examine how schema metadata describes the properties of business data. For
example, the Salesforce standard object Address has schema metadata and business data. Address fields such as  Address Type,
City, and  Postal Code, are all schema metadata. The corresponding values in each field, such as Mailing address, Chicago, IL,
and 60106, are all data. While personally identifiable information (PII) is usually found in business data, metadata can also include PII,
such as custom object names, report names, etc.

Metadata in Salesforce also defines how your org functions. For example, process metadata describes what happens when a user presses
the Save button. Presentation metadata concerns the layout of your org, and authorization metadata determines user access. Salesforce
metadata also describes your org’s general configuration. For example, you can configure Chatter to block emoticons in posts.

Metadata API works with metadata types and components. A metadata type defines the structure of application metadata. A metadata
component is an instance of a metadata type. The fields and values of a metadata type are all metadata. For example, the metadata type
CustomTab on page 838 represents a custom tab that displays content. The CustomTab field  hasSidebar  indicates if the tab is on
the sidebar panel, which is an example of metadata determining presentation. Metadata types like CustomTab build the metadata model
that describe how your org is structured, displayed, or functions. Use Metadata API to develop customizations and build tools that
manage the metadata model, not the data itself.

Metadata API Functionality

The main purpose of Metadata API is to move metadata between Salesforce orgs during the development process. Use Metadata API
to deploy, retrieve, create, update, or delete customization information, such as custom object definitions and page layouts. Metadata
API doesn’t work directly with business data. To create, retrieve, update, or delete records such as accounts or leads, use SOAP API or
REST API.

You can move metadata with one of two ways. The first method is with Metadata API  deploy()  and  retrieve() calls. Admins
often use the  deploy()  and  retrieve()  calls to move the full metadata model. These calls are best fit for the final stages of
development, such as deploying tested customizations to the production org.


Understanding Metadata API

Use Cases for Metadata API

The second method is source push and pull commands that move only changes in metadata. These commands use source tracking,
which makes them friendlier for developers and better for intermediary stages of development.

SEE ALSO:

Metadata Components and Types

Deploying and Retrieving Metadata

source Commands

Use Cases for Metadata API

Use Metadata API to move metadata between orgs during the development cycle. Metadata API is also used for deploying large metadata
configuration changes from development.

To understand how to use Metadata API, let’s imagine you’re a Salesforce developer at Zephyrus Relocation Services. Zephyrus is a
talent-mobility firm that helps companies develop processes for domestic and international employee relocation. Zephyrus is expanding
into Asia and South America and wants to add orientation services for both regions. Orientation services include in-country assistance
in housing and school searches, area tours, and transportation information.

Your development team must add these new orientation services to their existing org. Products such as in-country orientations are
objects that can be customized in Salesforce. When you add objects and customize your org, you change its metadata. The development
process of creating a custom product is where Metadata API can help.

Use Metadata API in the Development Process

Currently, Zephyrus has production metadata and orientation services tailored to other countries. To begin building the new product
customizations, you need the existing configurations from Zephyrus’ production Salesforce org in a separate repository. The configuration
of the production org is all metadata. To save production metadata in a repository, move the metadata from the Zephyrus production
org to your local file system.

Move Metadata from Production to Your Local File System on page 3

To make development changes without affecting your existing configurations, use Metadata API to move metadata to your local file
system. Next, push metadata from your local file system to a shareable repository for development.

With all the Zephyrus metadata retrieved, you can develop locally or in a scratch org. Scratch orgs are disposable Salesforce environments
with no data. Many developers use both tools together. Loading files and making changes are much faster locally than doing so in a
scratch org. Developers often build customizations on their local file system and run tests in a scratch org. Move changes between your
local file system and scratch org as you test and develop.

Move Metadata Changes to and from a Scratch Org on page 3

You can use a scratch org along with your local file system to develop and test changes to metadata. To move the changes you make
locally to and from the scratch org, use Metadata API.

The rest of the Zephyrus development team has their own customizations. After developing and testing on your own, it’s time for the
team to integrate changes and run tests in sandboxes. Sandboxes are development environments used for developing and testing
integrations.

Move Metadata to a Sandbox at Integration Points on page 4

During development, use Metadata API to move metadata to sandboxes for integrating changes, testing, and collaborating with your
team.


Understanding Metadata API

Move Metadata from Production to Your Local File System

After your team builds the orientation service customization and completes testing, deploy these components to production with
Metadata API.

Deploy Metadata to Production on page 4

In the final step of the development cycle, move customizations from a source control system such as Git into production with Metadata
API.

Other Use Cases

You can use Metadata API for larger changes in Salesforce, such as splitting and merging production orgs.

For example, Zephyrus wants to split the company into two divisions, one that specializes in domestic relocation and another for
international relocation. In this case, you split Zephyrus’ Salesforce org and decide which metadata belongs in which org. Metadata API
can move metadata to the new org.

Then, let’s say Zephyrus acquires Apollo Global Relocation and both companies use Salesforce. To consolidate information, you use
Metadata API to merge the Apollo org into the Zephyrus org.

Move Metadata for Production-Level Changes on page 5

Use Metadata API to move metadata during large changes, such as merging or splitting Salesforce orgs.

You can use Metadata API to make configuration changes during the development process that are too large for alternative API calls.
For example, Zephyrus supports many languages for their global clients. To translate different languages for your objects, you include
an object translation file for each language.

Make Large Metadata Configuration Changes on page 5

Metadata is better suited than other APIs for deploying large changes to your org.

Move Metadata from Production to Your Local File System

To make development changes without affecting your existing configurations, use Metadata API to move metadata to your local file
system. Next, push metadata from your local file system to a shareable repository for development.

When you build customizations on Salesforce, you must preserve the functionality of your existing org during the development cycle.
To build customizations without affecting your production org, save your production metadata in a version control system. Git integrates
best with SFDX tools.

First, move the required metadata from the production org to your local file system. To move metadata to your local machine, use a
retrieve call instead of a source pull. Next, push your files to a repository that is accessible to your team members with Git commands.
The repository is now the original source of production metadata for your team’s development cycle.

Now that your production metadata is stored in a repository, move the necessary metadata back to your local file system to begin
development work.

SEE ALSO:

retrieve()

source Commands

Move Metadata Changes to and from a Scratch Org

Use a scratch org to develop and test changes to metadata. You can perform your development within or outside the scratch org using
Salesforce CLI or Salesforce Extensions for VS Code, which leverage the power of Metadata API.


Understanding Metadata API

Move Metadata to a Sandbox at Integration Points

Scratch orgs are created empty so that developers can specify the exact metadata and data to include from the source control system.
The lifespan of a scratch org is indicated during creation, 1–30 days. They’re ephemeral to ensure the source of truth is always the source
control system, and not the org itself.

You can move metadata from the source control system or to the scratch org using Salesforce CLI. Because scratch orgs use source
tracking to identify changes, the CLI is the most efficient way to move metadata between your local repository and the scratch org.
Continue to iterate through this process of moving metadata between your local file system and your scratch org until development is
complete.

SEE ALSO:

Push Source to the Scratch Org

Pull Source from the Scratch Org to Your Project

Move Metadata to a Sandbox at Integration Points

During development, use Metadata API to move metadata to sandboxes for integrating changes, testing, and collaborating with your
team.

After developing on your own in a scratch org or your local file system, combine work from your team at integration points in a sandbox.
Sandboxes are development environments that you can use to integrate and test changes from multiple developers. Admins often
create and assign sandboxes. To create a sandbox on the Salesforce UI, navigate to Setup. Next, in the Quick Find box, search for sandboxes.

You have several levels of sandboxes to choose from with differing amounts of data. The Developer sandbox and Developer Pro sandbox
are development environments where you build customizations and test changes on fictional data. The Partial Copy sandbox and Full
sandbox are testing environments loaded with copies of production data. Move metadata to different sandboxes with a Metadata API
deploy command depending on your development and testing needs.

Outside of Metadata API, admins typically use change sets to send customizations from one sandbox to another. Unlike Metadata API
calls, you must build change sets manually. To add components to a continuous integration system more easily, you can automate
Metadata API calls on Salesforce CLI.

SEE ALSO:

Sandbox Types and Templates

Change Sets

Continuous Integration

Deploy Metadata to Production

In the final step of the development cycle, move customizations from a source control system such as Git into production with Metadata
API.

When your team finishes integration tests and is ready to deploy to production, move the completed customizations from a local
environment to the repository. For the release, move metadata from the repository to production by pulling the updated repository
back to the local environment with Git commands. Next, deploy metadata to production with Metadata API deploy call.

Moving metadata to production requires a deploy call instead of a push command because the deploy call deploys the entire metadata
model and not just changes in the metadata.


Understanding Metadata API

Move Metadata for Production-Level Changes

Deploy Recent Validation

A regular deploy call executes automated Apex tests that can take a long time to complete. To skip tests for validated components and
deploy components to production quickly, use the deploy recent validation option.

SEE ALSO:

deploy()

force:source:push Command

Deploy a Recently Validated Component Set Without Tests

Move Metadata for Production-Level Changes

Use Metadata API to move metadata during large changes, such as merging or splitting Salesforce orgs.

To split an org, first retrieve the metadata to be moved. Then, use a deploy call to push those configurations to the new org. Similarly,
to merge two orgs, retrieve existing metadata from one org. Next, use a deploy call to migrate metadata from one org to another.

SEE ALSO:

retrieve()

deploy()

Make Large Metadata Configuration Changes

Metadata API is better suited than other APIs for deploying large changes to your Salesforce org.

Metadata API  deploy()  and  retrieve()  calls are file-based and therefore asynchronous. With synchronous commands, large
configuration changes require unreasonably long load times. Instead, deploy and retrieve calls begin an asynchronous process that
notifies you when it’s complete. Because file-based calls are asynchronous, Metadata API can also handle a queue of deploy requests.

SEE ALSO:

deploy()

retrieve()

Metadata API Release Notes

Use the Salesforce Release Notes to learn about the most recent updates and changes to Metadata API.

For updates and changes that impact the Salesforce Platform, including Metadata API, see the API Release Notes.

For new, changed, and deprecated metadata types and other changes specific to Metadata API, see Metadata API in the Salesforce
Release Notes.

Metadata API Developer Tools

Use the Salesforce Extensions for Visual Studio Code on Salesforce CLI to access Metadata API commands. Salesforce CLI and the Salesforce
Extensions for Visual Studio Code streamline the process of using Metadata API.


Understanding Metadata API

Supported Salesforce Editions

The easiest way to access the functionality in Metadata API is to use the Salesforce Extensions for Visual Studio Code or Salesforce CLI.
Both tools are built on top of Metadata API and use the standard tools to simplify working with Metadata API.

- The Salesforce Extensions for Visual Studio Code includes tools for developing on the Salesforce platform in the lightweight, extensible
VS Code editor. These tools provide features for working with development orgs (scratch orgs, sandboxes, and DE orgs), Apex, Aura
components, and Visualforce.

- Salesforce CLI is ideal if you use scripting or the command line for moving metadata between a local directory and a Salesforce org.

For more information about the Salesforce Extensions for Visual Studio Code or Salesforce CLI, see Salesforce Tools and Toolkits.

If you prefer to build your own client applications, the underlying calls of Metadata API have been exposed for you to use directly. This
guide gives you more information about working directly with Metadata API.

You can use the Metadata API to manage setup and customization information (metadata) in Salesforce. For example:

- Export customizations as XML metadata files. See Working with the Zip File and retrieve().

- Migrate configuration changes between orgs. See deploy() and retrieve().

- Modify existing customizations using XML metadata files. See deploy() and retrieve().

- Manage customizations programmatically. See CRUD-Based Metadata Development.

You can modify metadata in test orgs in Developer Edition or sandboxes, and then deploy tested changes to production orgs in Enterprise,
Unlimited, or Performance Editions. You can also create scripts to populate a new org with your custom objects, custom fields, and other
components.

SEE ALSO:

Deploying and Retrieving Metadata

Supported Salesforce Editions

To use Metadata API, your organization must use Enterprise Edition, Unlimited Edition, Performance Edition, or Developer Edition.
If you’re an existing Salesforce customer and want to upgrade to Enterprise, Unlimited, or Performance Edition, contact your account
representative.

We strongly recommend that you use a sandbox, which is an exact replica of your production organization. Enterprise, Unlimited, and
Performance Editions come with free developer sandboxes. For more information, see
http://www.salesforce.com/platform/cloud-infrastructure/sandbox.jsp.

Alternatively, you can use a Developer Edition (DE) org. A DE org provides access to all features that are available with Enterprise Edition,
but is limited by the number of users and the amount of storage space. A DE org isn’t a copy of your production org/ It provides an
environment where you can build and test your solutions without affecting your organization’s data. Developer Edition accounts are
available for free at https://developer.salesforce.com/signup.

Note:  A metadata component must be visible in the org for Metadata API to act on it. Also, a user must have the API Enabled
permission to have access to metadata components.

Metadata API Access for Professional Edition

ISV partners can request Metadata API access to Professional Edition orgs for apps that have passed AppExchange Security Review.
Access is granted through an API token (client ID). This special key enables the app to make Metadata API calls to customers’ Professional
Edition orgs.

As an ISV partner, you can request Metadata API access by following these steps.


Understanding Metadata API

Metadata API Edit Access

1. Submit your app for security review. See Steps in the Security Review in the ISVForce Guide.

2. After your app is approved, log a case in the Partner Community in AppExchange and Feature Requests > API Token Request,

and specify SOAP for the type of token.

To make calls to the Metadata API, append the API token to the CallOptions SOAP header in your calls.

Metadata API Edit Access

To use Metadata API, a user must have these things.

- One of these editions: Enterprise, Unlimited, or Developer

- Either the Modify Metadata Through Metadata API Functions OR Modify All Data permission

- Permission that enables use of the feature supported by the metadata that they want to modify

- Permission that enables their deployment tool, such as Salesforce CLI, or change sets

With the Modify Metadata Through Metadata API Functions permission, a user can access and edit metadata via Metadata API as long
as the user has any additional permission needed to access certain metadata types. This additional permission information is listed in
the Metadata API Developer Guide for each metadata type. With the Modify All Data permission, a user can access and edit all data.

The Modify Metadata Through Metadata API Functions permission doesn’t affect direct customization of metadata using Setup UI pages
because those pages don’t use Metadata API for updates.

Some metadata, such as Apex, executes in system context, so be careful how you delegate the Modify Metadata Through Metadata API
Functions permission. The Modify Metadata Through Metadata API Functions permission allows deployment of Apex metadata, but it
doesn’t allow certain Apex development and debugging features that still require the Modify All Data permission.

The Modify Metadata Through Metadata API Functions permission is enabled automatically when either the Deploy Change Sets OR
Author Apex permission is selected.

When the Manage Prompts user permission and the Modify Metadata Through Metadata API Functions permission are combined, users
can manage In-App Guidance in Lightning Experience.

Development Platforms

Metadata API supports both file-based and CRUD-based development.

File-Based Development

The declarative or file-based asynchronous Metadata API  deploy() and retrieve() operations deploy or retrieve a  .zip  file
that holds components in a set of folders, and a manifest file named package.xml. For more information, see Deploying and Retrieving
Metadata on page 25. The easiest way to access the file-based functionality is to use the Salesforce Extensions for Visual Studio Code
or Salesforce CLI.

CRUD-Based Development

The CRUD Metadata API calls act upon the metadata components in a manner similar to the way synchronous API calls in the enterprise
WSDL act upon objects. For more information about the enterprise WSDL, see the SOAP API Developer Guide.


Understanding Metadata API

Standards Compliance

Standards Compliance

Metadata API is implemented to comply with the following specifications:

Standard Name

Website

Simple Object Access Protocol (SOAP) 1.1

http://www.w3.org/TR/2000/NOTE-SOAP-20000508/

Web Service Description Language (WSDL)
1.1

http://www.w3.org/TR/2001/NOTE-wsdl-20010315

WS-I Basic Profile 1.1

http://www.ws-i.org/Profiles/BasicProfile-1.1-2004-08-24.html

Extensible Markup Language (XML) 1.0

https://www.w3.org/TR/xml

Metadata API Support Policy

Salesforce supports previous versions of Metadata API. However, your new client applications should use the most recent version of the
Lightning Platform Metadata API WSDL file to fully exploit the benefits of richer features and greater efficiency.

Backward Compatibility

Salesforce strives to make backward compatibility easy when using the Lightning Platform.

Each new Salesforce release consists of two components:

- A new release of platform software that resides on Salesforce systems

- A new version of the API

For example, the Spring '07 release included API version 9.0 and the Summer '07 release included API version 10.0.

We maintain support for each API version across releases of the platform software. The API is backward compatible in that an application
created to work with a given API version will continue to work with that same API version in future platform software releases.

Salesforce does not guarantee that an application written against one API version will work with future API versions: Changes in method
signatures and data representations are often required as we continue to enhance the API. However, we strive to keep the API consistent
from version to version with minimal, if any, changes required to port applications to newer API versions.

For example, an application written using API version 9.0, which shipped with the Spring ’07 release, will continue to work with API
version 9.0 on the Summer ’07 release, and on future releases beyond that. However, that same application might not work with API
version 10.0 without modifications to the application.

API End-of-Life Policy

See which Metadata REST and SOAP API versions are supported, unsupported, or unavailable.

Salesforce is committed to supporting each API version for a minimum of 3 years from the date of first release. To improve the quality
and performance of the API, versions that are over 3 years old sometimes are no longer supported.

Salesforce notifies customers who use an API version scheduled for deprecation at least 1 year before support for the version ends.


Understanding Metadata API

Related Resources

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

If you request any resource or use an operation from a retired API version, REST API returns the  410:GONE  error code.

If you request any resource or use an operation from a retired API version, SOAP API returns 500:UNSUPPORTED_API_VERSION error
code.

To identify requests made from old or unsupported API versions, use the API Total Usage event type.

Related Resources

The Salesforce developer website provides a full suite of developer toolkits, sample code, sample SOAP messages, community-based
support, and other resources to help you with your development projects. Be sure to visit
https://developer.salesforce.com/page/Getting_Started for more information, or visit
https://developer.salesforce.com/signup to sign up for a free Developer Edition account.

You can visit these websites to find out more about Salesforce applications:

- Salesforce Developers provides useful information for developers.

- Salesforce for information about the Salesforce application.

- Lightning Platform AppExchange for access to apps created for Salesforce.

- Trailblazer Community for services to ensure Salesforce customer success.


## CHAPTER 2 Quick Start: Metadata API

In this chapter ...

- Prerequisites

- 

- 

- 

Step 1: (Optional) Add
Metadata
Components to an
Org Using the UI

Step 2: Build a
Package.xml
Manifest

Step 3: Retrieve
Components with
Metadata API

Get started with Metadata API by retrieving a small set of metadata components from your org on the
Salesforce CLI.

Resources for Beginner Developers

If you’re a beginner developer and haven’t used Salesforce CLI before, learn how to set up your
environment and practice with a sample application. These Trailheads guide you through setup with
SFDX and introduce you to Metadata API.

App Development with Salesforce DX

Walk through setting up your environment and developing with Salesforce CLI using the Dreamhouse
sample app. After you add a feature to your Dreamhouse app, you deploy metadata to your Dev Hub
org with Salesforce CLI.

Package.xml Metadata Management

Learn more about metadata and package.xml files. Build a package.xml file to deploy changes from a
scratch org to your Trailhead Playground.

Quick Start for Developing with Metadata API

If you have some experience in Salesforce development but want to get started with Metadata API, use
this quick start. The quick start walks you through a retrieval of metadata components, which is the first
step of the development process.

SEE ALSO:

Move Metadata from Production to Your Local File System


Quick Start: Metadata API

Prerequisites

Prerequisites

Complete these prerequisites before you start developing with Metadata API.

- To access Metadata API through the command line, install Salesforce CLI.

- To create a development environment, sign up for Salesforce Developer Edition. A Developer Edition org is a free development

environment for building and testing solutions independent of production data.

- Install Salesforce Extensions for Visual Studio Code. These tools provide features for working with development orgs (scratch orgs,

sandboxes, and DE orgs), Apex, Aura components, and Visualforce.

- Confirm that you have API Enabled permission and Modify Metadata Through Metadata API Functions permission or Modify All Data

permission. If you don’t have these permissions set, modify your metadata permissions.

- Enable Dev Hub in your org. Dev Hub allows you to create and manage scratch orgs so that you can develop without affecting your

production data or metadata.

- To allow access to protected resources such as production data and metadata, authorize your org .

Step 1: (Optional) Add Metadata Components to an Org Using the UI

If you’re starting with a new practice org that doesn’t have customizations, you only have standard metadata that can’t be retrieved. To
use the Metadata API retrieve call, add a component on the Salesforce UI to your practice org. If you’re working on an existing project,
you already have components to retrieve and can skip this step.

1. From the Object Manager tab in Setup, click Create > Custom Object.

2. Enter an arbitrary name for Label and Plural Label.

3. Save the component.

Step 2: Build a Package.xml Manifest

The package.xml manifest file lists the components to retrieve from your org.

Package.xml Manifest Structure

The package.xml manifest uses Extensible Markup Language (XML) to identify and migrate metadata components. The basic framework
of the package.xml manifest is built with  <types>  elements. A  <types>  element specifies which metadata type you want to work
with. You can add multiple  <types>  to a package.xml file.

Inside the <types>  element is the <name>  element and the <members>  element. The <members>  element selects for individual
components of a specific type, and the <name> element selects for metadata component types. To work with a specific component,
input the  fullName  of the component in the  <members>  element.

For example, to retrieve Account components, add Account in the <members>  element and CustomObject in the <name>  element
in your package.xml. When you issue a retrieve call, you retrieve only the Account component from your org.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>Account</members>
<name>CustomObject</name>

</types>


Quick Start: Metadata API

Step 3: Retrieve Components with Metadata API

<version>66.0</version>

</Package>

Retrieve Custom Objects

To retrieve all components of a metadata type, you don’t specify the  fullName  of a component. Instead, use the wildcard character
* (asterisk) in the  <members>  tag. Some components, such as standard objects, don’t support * (asterisk) as a specifier.

To retrieve all custom objects from your org:

1.

(Optional) If you do not have a project folder, use Salesforce CLI to create a new directory that organizes your project. Run this
command with your specified project name:

sf project generate --name YourProjectName

2. Create a file called package.xml in your project.

3.

In your text editor, open the file and paste in this script:

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>*</members>
<name>CustomObject</name>

</types>
<version>66.0</version>

</Package>

Now you have a package.xml file that we can use to retrieve all custom objects. When you develop more on your own, you can retrieve
more components from your org with multiple  <types>  elements.

SEE ALSO:

Sample package.xml Manifest Files

Deploying and Retrieving Metadata with the Zip File

Step 3: Retrieve Components with Metadata API

With Salesforce CLI, retrieve a file representation of the specified components in your package.xml manifest.

Two Options for Metadata API Retrieve

You can use one of two commands to retrieve metadata components.

1. To retrieve the components specified in your package.xml manifest, issue a retrieve call using a Salesforce CLI command. On the

command line, run this call with the appropriate file path:

sf project retrieve start --manifest path/to/package.xml

Metadata  retrieve()  is an asynchronous, file-based command. You can issue multiple retrieve or deploy requests that run on
their own when resources are available.

With this command, you send a request to retrieve all custom objects as specified in your package.xml manifest. Your requests are
queued until our systems are ready to process your retrieve call. After your request is dequeued, your retrieve call is run. The client


Quick Start: Metadata API

Step 3: Retrieve Components with Metadata API

checks the status of the retrieve and notifies you when the call is complete. The call returns a file representation of the chosen
components. When you use Salesforce CLI to issue a retrieve call, all these processes are automated.

The  project retrieve start  command allows for source tracking. Source tracking includes information about which
revision you’re working on and when the last changes were made, which makes source commands more developer-friendly. To use
source tracking, ensure that it’s enabled in your org.

2. Alternatively, run this command in your terminal:

sf project retrieve start --manifest path/to/package.xml --target-metadata-dir
path/to/retrieve/dir

This command retrieves components in mdapi format rather than source format, and doesn’t allow for source tracking. In practice,
admins use mdapi commands more often because the commands don’t include source tracking.

SEE ALSO:

retrieve()

source Commands

Source Tracking

mdapi Commands


## CHAPTER 3 Build Client Applications for Metadata API

Use Metadata API to retrieve, deploy, create, update, or delete customizations for your org. The most common use is to migrate changes
from a sandbox or testing org to your production environment. Metadata API is intended for managing customizations and for building
tools that can manage the metadata model, not the data itself.

Salesforce CLI automates the underlying calls of Metadata API. However, you can use these calls directly with your own client application.
This guide gives you all the information you require to start writing applications that directly use Metadata API to manage customizations
for your organization. It shows you how to get started with File-Based Development. For an example of CRUD-Based Development, see
Java Sample for CRUD-Based Development with Synchronous Calls.

Prerequisites

Make sure that you complete these prerequisites before you start using Metadata API.

- Create a development environment.

We strongly recommend that you use a sandbox, which is an exact replica of your production organization. Enterprise, Unlimited,
and Performance Editions come with free developer sandboxes. For more information, see
http://www.salesforce.com/platform/cloud-infrastructure/sandbox.jsp.

Alternatively, you can use a Developer Edition (DE) org. A DE org provides access to all features that are available with Enterprise
Edition, but is limited by the number of users and the amount of storage space. A DE org isn’t a copy of your production org/ It
provides an environment where you can build and test your solutions without affecting your organization’s data. Developer Edition
accounts are available for free at https://developer.salesforce.com/signup.

- Identify a user that has the API Enabled permission and the Modify Metadata Through Metadata API Functions permission or Modify

All Data permission. These permissions are required to access Metadata API calls.

Note:  If a user requires access to metadata but not to data, enable the Modify Metadata Through Metadata API Functions on
page 7 permission. Otherwise, enable the Modify All Data permission.

- Install a SOAP client. Metadata API works with current SOAP development environments, including, but not limited to, Visual Studio®

.NET and the Web Service Connector (WSC).

In this document, we provide Java examples based on WSC and JDK 6 (Java Platform Standard Edition Development Kit 6). To run
the samples, first download the latest force-wsc JAR file and its dependencies from
mvnrepository.com/artifact/com.force.api/force-wsc/. Dependencies are listed on the page when you select a version.

Note:  Development platforms vary in their SOAP implementations. Implementation differences in certain development
platforms can prevent access to some or all features in Metadata API.


Build Client Applications for Metadata API

Step 1: Generate or Obtain the Web Service WSDLs for Your
Organization

Step 1: Generate or Obtain the Web Service WSDLs for Your
Organization

To access Metadata API calls, you need a Web Service Description Language (WSDL) file. The WSDL file defines the Web service that is
available to you. Your development platform uses this WSDL to generate stub code to access the Web service it defines. You can obtain
the WSDL file from your organization’s Salesforce administrator, or if you have access to the WSDL download page in the Salesforce user
interface, you can generate it yourself. For more information about WSDL, see http://www.w3.org/TR/wsdl.

Before you can access Metadata API calls, you must authenticate to use the Web service using the  login()  call, which is defined in
the enterprise WSDL and the partner WSDL. Therefore, you must also obtain one of these WSDLs.

Any user with the Modify Metadata Through Metadata API Functions or Modify All Data permission can download the WSDL file to
integrate and extend the Salesforce platform.

Note:  If a user requires access to metadata but not to data, enable the Modify Metadata Through Metadata API Functions on
page 7 permission. Otherwise, enable the Modify All Data permission.

The sample code in Step 3: Walk Through the Java Sample Code on page 16 uses the enterprise WSDL, though the partner WSDL works
equally well.

To generate the metadata and enterprise WSDL files for your organization:

1. Log in to your Salesforce account. You must log in as an administrator or as a user who has the “Modify All Data” permission.

2. From Setup, enter  API  in the  Quick Find  box, then select API.

3. Click Generate Metadata WSDL, and save the XML WSDL file to your file system.

4. Click Generate Enterprise WSDL, and save the XML WSDL file to your file system.

Step 2: Import the WSDL Files Into Your Development Platform

Once you have the WSDL files, import them into your development platform so that your development environment can generate the
necessary objects for use in building client Web service applications. This section provides sample instructions for WSC. For instructions
about other development platforms, see your platform’s product documentation.

Note:  The process for importing WSDL files is identical for the metadata and enterprise WSDL files.

Instructions for Java Environments (WSC)

Java environments access the API through Java objects that serve as proxies for their server-side counterparts. Before using the API, you
must first generate these objects from your organization's WSDL file.

Each SOAP client has its own tool for this process. For WSC, use the  wsdlc  utility.

Note:  Before you run  wsdlc, you must have the WSC JAR file installed on your system and referenced in your classpath. You
can download the latest force-wsc JAR file and its dependencies (dependencies are listed on the page when you select a version)
from mvnrepository.com/artifact/com.force.api/force-wsc/.

The basic syntax for  wsdlc  is:

java -classpath pathToWsc;pathToWscDependencies com.sforce.ws.tools.wsdlc
pathToWsdl/WsdlFilename pathToOutputJar/OutputJarFilename


Build Client Applications for Metadata API

Step 3: Walk Through the Java Sample Code

For example, on Windows:

java –classpath force-wsc-30.0.0.jar;ST4-4.0.7.jar;antlr-runtime-3.5.jar
com.sforce.ws.tools.wsdlc metadata.wsdl metadata.jar

On Mac OS X and Unix, use a colon instead of a semicolon in between items in the classpath:

java –classpath force-wsc-30.0.0.jar:ST4-4.0.7.jar:antlr-runtime-3.5.jar
com.sforce.ws.tools.wsdlc metadata.wsdl metadata.jar

wsdlc  generates a JAR file and Java source code and bytecode files for use in creating client applications. Repeat this process for the
enterprise WSDL to create an enterprise.JAR file.

Step 3: Walk Through the Java Sample Code

When you have imported the WSDL files, you can build client applications that use Metadata API. The sample is a good starting point
for writing your own code.

Before you run the sample, modify your project and the code to:

1.

Include the WSC JAR, its dependencies, and the JAR files you generated from the WSDLs.

Note:  Although WSC has other dependencies, the following sample only requires Rhino (js-1.7R2.jar), which you can
download from mvnrepository.com/artifact/rhino/js.

2. Update USERNAME and PASSWORD variables in the  MetadataLoginUtil.login()  method with your user name and

password. If your current IP address isn’t in your organization's trusted IP range, you'll need to append a security token to the password.

3.

If you are using a sandbox, be sure to change the login URL.

Login Utility

Java users can use ConnectorConfig  to connect to Enterprise, Partner, and Metadata SOAP API. MetadataLoginUtil  creates
a  ConnectorConfig  object and logs in using the Enterprise WSDL login method. Then it retrieves  sessionId  and
metadataServerUrl  to create a  ConnectorConfig  and connects to Metadata API endpoint.  ConnectorConfig  is
defined in WSC.

The  MetadataLoginUtil  class abstracts the login code from the other parts of the sample, allowing portions of this code to be
reused without change across different Salesforce APIs.

import com.sforce.soap.enterprise.EnterpriseConnection;
import com.sforce.soap.enterprise.LoginResult;
import com.sforce.soap.metadata.MetadataConnection;
import com.sforce.ws.ConnectionException;
import com.sforce.ws.ConnectorConfig;

/**

* Login utility.
*/

public class MetadataLoginUtil {

public static MetadataConnection login() throws ConnectionException {

final String USERNAME = "user@company.com";
// This is only a sample. Hard coding passwords in source files is a bad practice.


Build Client Applications for Metadata API

Step 3: Walk Through the Java Sample Code

final String PASSWORD = "password";
final String URL = "https://login.salesforce.com/services/Soap/c/66.0";
final LoginResult loginResult = loginToSalesforce(USERNAME, PASSWORD, URL);
return createMetadataConnection(loginResult);

}

private static MetadataConnection createMetadataConnection(

final LoginResult loginResult) throws ConnectionException {

final ConnectorConfig config = new ConnectorConfig();
config.setServiceEndpoint(loginResult.getMetadataServerUrl());
config.setSessionId(loginResult.getSessionId());
return new MetadataConnection(config);

}

private static LoginResult loginToSalesforce(

final String username,
final String password,
final String loginUrl) throws ConnectionException {

final ConnectorConfig config = new ConnectorConfig();
config.setAuthEndpoint(loginUrl);
config.setServiceEndpoint(loginUrl);
config.setManualLogin(true);
return (new EnterpriseConnection(config)).login(username, password);

}

}

Note:  This example uses user and password authentication to obtain a session ID, which is then used for making calls to Metadata
API. Alternatively, you can use OAuth authentication. After you athenticate with OAuth to Salesforce, pass the returned access
token instead of the session ID. For example, pass the access token to the  setSessionId()  call on  ConnectorConfig.
To learn how to use OAuth authentication in Salesforce, see Authenticating Apps with OAuth in the Salesforce Help.

Java Sample Code for File-Based Development

The sample code logs in using the login utility. Then it displays a menu with retrieve, deploy, and exit.

The  retrieve()  and  deploy()  calls both operate on a .zip file named  components.zip. The  retrieve()  call retrieves
components from your organization into  components.zip, and the  deploy()  call deploys the components in
components.zip  to your organization. If you save the sample to your computer and execute it, run the retrieve option first so that
you have a  components.zip  file that you can subsequently deploy. After a retrieve call, the sample calls
checkRetrieveStatus()  in a loop until the operation is completed. Similarly, after a deploy call, the sample checks
checkDeployStatus()  in a loop until the operation is completed.

The retrieve()  call uses a manifest file to determine the components to retrieve from your organization. A sample package.xml
manifest file follows. For more details on the manifest file structure, see Deploying and Retrieving Metadata with the Zip File. For this
sample, the manifest file retrieves all custom objects, custom tabs, and page layouts.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>*</members>
<name>CustomObject</name>

</types>
<types>

<members>*</members>


Build Client Applications for Metadata API

Step 3: Walk Through the Java Sample Code

<name>CustomTab</name>

</types>
<types>

<members>*</members>
<name>Layout</name>

</types>
<version>66.0</version>

</Package>

Note the error handling code that follows each API call.

Note:  This sample requires API version 34.0 or later.

import java.io.*;
import java.nio.channels.Channels;
import java.nio.channels.FileChannel;
import java.nio.channels.ReadableByteChannel;
import java.rmi.RemoteException;
import java.util.*;

import javax.xml.parsers.*;

import org.w3c.dom.*;
import org.xml.sax.SAXException;

import com.sforce.soap.metadata.*;

/**

* Sample that logs in and shows a menu of retrieve and deploy metadata options.
*/

public class FileBasedDeployAndRetrieve {

private MetadataConnection metadataConnection;

private static final String ZIP_FILE = "components.zip";

// manifest file that controls which components get retrieved
private static final String MANIFEST_FILE = "package.xml";

private static final double API_VERSION = 29.0;

// one second in milliseconds
private static final long ONE_SECOND = 1000;

// maximum number of attempts to deploy the zip file
private static final int MAX_NUM_POLL_REQUESTS = 50;

private BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));

public static void main(String[] args) throws Exception {

FileBasedDeployAndRetrieve sample = new FileBasedDeployAndRetrieve();
sample.run();

}


Build Client Applications for Metadata API

Step 3: Walk Through the Java Sample Code

public FileBasedDeployAndRetrieve() {
}

private void run() throws Exception {

this.metadataConnection = MetadataLoginUtil.login();

// Show the options to retrieve or deploy until user exits
String choice = getUsersChoice();
while (choice != null && !choice.equals("99")) {

if (choice.equals("1")) {

retrieveZip();

} else if (choice.equals("2")) {

deployZip();

} else {

break;

}
// show the options again
choice = getUsersChoice();

}

}

/*

* Utility method to present options to retrieve or deploy.
*/

private String getUsersChoice() throws IOException {

System.out.println(" 1: Retrieve");
System.out.println(" 2: Deploy");
System.out.println("99: Exit");
System.out.println();
System.out.print("Enter 1 to retrieve, 2 to deploy, or 99 to exit: ");
// wait for the user input.
String choice = reader.readLine();
return choice != null ? choice.trim() : "";

}

private void deployZip() throws Exception {

byte zipBytes[] = readZipFile();
DeployOptions deployOptions = new DeployOptions();
deployOptions.setPerformRetrieve(false);
deployOptions.setRollbackOnError(true);
AsyncResult asyncResult = metadataConnection.deploy(zipBytes, deployOptions);
DeployResult result = waitForDeployCompletion(asyncResult.getId());
if (!result.isSuccess()) {

printErrors(result, "Final list of failures:\n");
throw new Exception("The files were not successfully deployed");

}
System.out.println("The file " + ZIP_FILE + " was successfully deployed\n");

}

/*
* Read the zip file contents into a byte array.
*/
private byte[] readZipFile() throws Exception {

byte[] result = null;


Build Client Applications for Metadata API

Step 3: Walk Through the Java Sample Code

// We assume here that you have a deploy.zip file.
// See the retrieve sample for how to retrieve a zip file.
File zipFile = new File(ZIP_FILE);
if (!zipFile.exists() || !zipFile.isFile()) {

throw new Exception("Cannot find the zip file for deploy() on path:"

+ zipFile.getAbsolutePath());

}

FileInputStream fileInputStream = new FileInputStream(zipFile);
try {

ByteArrayOutputStream bos = new ByteArrayOutputStream();
byte[] buffer = new byte[4096];
int bytesRead = 0;
while (-1 != (bytesRead = fileInputStream.read(buffer))) {

bos.write(buffer, 0, bytesRead);

}

result = bos.toByteArray();

} finally {

fileInputStream.close();

}
return result;

}

/*
* Print out any errors, if any, related to the deploy.
* @param result - DeployResult
*/
private void printErrors(DeployResult result, String messageHeader) {

DeployDetails details = result.getDetails();
StringBuilder stringBuilder = new StringBuilder();
if (details != null) {

DeployMessage[] componentFailures = details.getComponentFailures();
for (DeployMessage failure : componentFailures) {

String loc = "(" + failure.getLineNumber() + ", " +

failure.getColumnNumber();

if (loc.length() == 0 &&

!failure.getFileName().equals(failure.getFullName()))

{

loc = "(" + failure.getFullName() + ")";

}
stringBuilder.append(failure.getFileName() + loc + ":"

+ failure.getProblem()).append('\n');

}
RunTestsResult rtr = details.getRunTestResult();
if (rtr.getFailures() != null) {

for (RunTestFailure failure : rtr.getFailures()) {

String n = (failure.getNamespace() == null ? "" :

(failure.getNamespace() + ".")) + failure.getName();

stringBuilder.append("Test failure, method: " + n + "." +

failure.getMethodName() + " -- " + failure.getMessage() +
" stack " + failure.getStackTrace() + "\n\n");

}

}


Build Client Applications for Metadata API

Step 3: Walk Through the Java Sample Code

if (rtr.getCodeCoverageWarnings() != null) {

for (CodeCoverageWarning ccw : rtr.getCodeCoverageWarnings()) {

stringBuilder.append("Code coverage issue");
if (ccw.getName() != null) {

String n = (ccw.getNamespace() == null ? "" :
(ccw.getNamespace() + ".")) + ccw.getName();
stringBuilder.append(", class: " + n);

}
stringBuilder.append(" -- " + ccw.getMessage() + "\n");

}

}

}
if (stringBuilder.length() > 0) {

stringBuilder.insert(0, messageHeader);
System.out.println(stringBuilder.toString());

}

}

private void retrieveZip() throws Exception {

RetrieveRequest retrieveRequest = new RetrieveRequest();
// The version in package.xml overrides the version in RetrieveRequest
retrieveRequest.setApiVersion(API_VERSION);
setUnpackaged(retrieveRequest);

AsyncResult asyncResult = metadataConnection.retrieve(retrieveRequest);
RetrieveResult result = waitForRetrieveCompletion(asyncResult);

if (result.getStatus() == RetrieveStatus.Failed) {

throw new Exception(result.getErrorStatusCode() + " msg: " +

result.getErrorMessage());

} else if (result.getStatus() == RetrieveStatus.Succeeded) {

// Print out any warning messages
StringBuilder stringBuilder = new StringBuilder();
if (result.getMessages() != null) {

for (RetrieveMessage rm : result.getMessages()) {

stringBuilder.append(rm.getFileName() + " - " + rm.getProblem() + "\n");

}

}
if (stringBuilder.length() > 0) {

System.out.println("Retrieve warnings:\n" + stringBuilder);

}

System.out.println("Writing results to zip file");
File resultsFile = new File(ZIP_FILE);
FileOutputStream os = new FileOutputStream(resultsFile);

try {

os.write(result.getZipFile());

} finally {

os.close();

}

}


Build Client Applications for Metadata API

Step 3: Walk Through the Java Sample Code

}

private DeployResult waitForDeployCompletion(String asyncResultId) throws Exception {

int poll = 0;
long waitTimeMilliSecs = ONE_SECOND;
DeployResult deployResult;
boolean fetchDetails;
do {

Thread.sleep(waitTimeMilliSecs);
// double the wait time for the next iteration

waitTimeMilliSecs *= 2;
if (poll++ > MAX_NUM_POLL_REQUESTS) {

throw new Exception(

+

"Request timed out. If this is a large set of metadata components, "

"ensure that MAX_NUM_POLL_REQUESTS is sufficient.");

}
// Fetch in-progress details once for every 3 polls
fetchDetails = (poll % 3 == 0);

deployResult = metadataConnection.checkDeployStatus(asyncResultId, fetchDetails);

System.out.println("Status is: " + deployResult.getStatus());
if (!deployResult.isDone() && fetchDetails) {

printErrors(deployResult, "Failures for deployment in progress:\n");

}

}
while (!deployResult.isDone());

if (!deployResult.isSuccess() && deployResult.getErrorStatusCode() != null) {

throw new Exception(deployResult.getErrorStatusCode() + " msg: " +

deployResult.getErrorMessage());

}

if (!fetchDetails) {

// Get the final result with details if we didn't do it in the last attempt.
deployResult = metadataConnection.checkDeployStatus(asyncResultId, true);

}

return deployResult;

}

private RetrieveResult waitForRetrieveCompletion(AsyncResult asyncResult) throws

Exception {

// Wait for the retrieve to complete

int poll = 0;
long waitTimeMilliSecs = ONE_SECOND;
String asyncResultId = asyncResult.getId();
RetrieveResult result = null;
do {

Thread.sleep(waitTimeMilliSecs);
// Double the wait time for the next iteration


Build Client Applications for Metadata API

Step 3: Walk Through the Java Sample Code

waitTimeMilliSecs *= 2;
if (poll++ > MAX_NUM_POLL_REQUESTS) {

throw new Exception("Request timed out. If this is a large set " +
"of metadata components, check that the time allowed " +
"by MAX_NUM_POLL_REQUESTS is sufficient.");

}
result = metadataConnection.checkRetrieveStatus(

asyncResultId, true);

System.out.println("Retrieve Status: " + result.getStatus());

} while (!result.isDone());

return result;

}

private void setUnpackaged(RetrieveRequest request) throws Exception {

// Edit the path, if necessary, if your package.xml file is located elsewhere
File unpackedManifest = new File(MANIFEST_FILE);
System.out.println("Manifest file: " + unpackedManifest.getAbsolutePath());

if (!unpackedManifest.exists() || !unpackedManifest.isFile()) {

throw new Exception("Should provide a valid retrieve manifest " +

"for unpackaged content. Looking for " +
unpackedManifest.getAbsolutePath());

}

// Note that we use the fully quualified class name because
// of a collision with the java.lang.Package class
com.sforce.soap.metadata.Package p = parsePackageManifest(unpackedManifest);
request.setUnpackaged(p);

}

private com.sforce.soap.metadata.Package parsePackageManifest(File file)
throws ParserConfigurationException, IOException, SAXException {

com.sforce.soap.metadata.Package packageManifest = null;
List<PackageTypeMembers> listPackageTypes = new ArrayList<PackageTypeMembers>();
DocumentBuilder db =

DocumentBuilderFactory.newInstance().newDocumentBuilder();

InputStream inputStream = new FileInputStream(file);
Element d = db.parse(inputStream).getDocumentElement();
for (Node c = d.getFirstChild(); c != null; c = c.getNextSibling()) {

if (c instanceof Element) {

Element ce = (Element) c;
NodeList nodeList = ce.getElementsByTagName("name");
if (nodeList.getLength() == 0) {

continue;

}
String name = nodeList.item(0).getTextContent();
NodeList m = ce.getElementsByTagName("members");
List<String> members = new ArrayList<String>();
for (int i = 0; i < m.getLength(); i++) {

Node mm = m.item(i);
members.add(mm.getTextContent());

}
PackageTypeMembers packageTypes = new PackageTypeMembers();


Build Client Applications for Metadata API

Step 3: Walk Through the Java Sample Code

packageTypes.setName(name);
packageTypes.setMembers(members.toArray(new String[members.size()]));
listPackageTypes.add(packageTypes);

}

}
packageManifest = new com.sforce.soap.metadata.Package();
PackageTypeMembers[] packageTypesArray =

new PackageTypeMembers[listPackageTypes.size()];

packageManifest.setTypes(listPackageTypes.toArray(packageTypesArray));
packageManifest.setVersion(API_VERSION + "");
return packageManifest;

}

}


USING METADATA API


## CHAPTER 4 Deploying and Retrieving Metadata

Use the deploy() and retrieve() calls to move metadata (XML files) between a Salesforce org and a local file system. After you retrieve
your XML files into a file system, you can manage changes in a source-code control system, copy and paste code or setup configurations,
diff changes to components, and perform many other file-based development operations. At any time you can deploy those changes
to another Salesforce org.

Data in XML files is formatted using the English (United States) locale. This formatting ensures that fields that depend on locale, such as
date fields, are interpreted consistently during data migrations between organizations using different languages. Organizations can
support multiple languages for presentation to their users.

The deploy() and retrieve() calls are used primarily for these development scenarios:

- Development of a custom application (or customization) in a sandbox organization. After development and testing are completed,

the application or customization is then deployed into a production organization using Metadata API.

- Team development of an application in a Developer Edition organization. After development and testing are completed, you can

then distribute the application via Lightning Platform AppExchange.

You receive an API notification each time you retrieve 90% or more of the maximum number of custom fields that you can deploy at
once with Metadata API. The maximum number of custom fields for one deployment is 45,000. The custom fields retrieved in one
package.xml file are: 1) the sum of the fields on each object in the CustomObjects section of package.xml and 2) the sum of the custom
fields in the CustomFields section of package.xml.

You can still retrieve above the deployable maximum up to the limit on total size of retrieved files. But you must use more than one
deployment to deploy all of the custom fields.

Example:  Warning: You’ve retrieved 47,000 instances of CustomField. You can’t redeploy all these instances at the same time;
the maximum is 45,000.

SEE ALSO:

Metadata Components and Types

Unsupported Metadata Types

Metadata Type Limits

Deploying and Retrieving Metadata with the Zip File

The  deploy()  and  retrieve()  calls are used to deploy and retrieve a .zip file. Within the .zip file is a project manifest
(package.xml)  that lists what to retrieve or deploy, and one or more XML components that are organized into folders.

Note:  A component is an instance of a metadata type. For example,  CustomObject  is a metadata type for custom objects,
and the  MyCustomObject__c  component is an instance of a custom object.

The files that are retrieved or deployed in a .zip file might be unpackaged components that reside in your org (such as standard objects)
or packaged components that reside within named packages.


Deploying and Retrieving Metadata

Deploying and Retrieving Metadata with the Zip File

Note:  You can deploy or retrieve up to 10,000 files at once. The maximum size of the deployed or retrieved .zip file is 39 MB. If
the files are uncompressed in an unzipped folder, the size limit is 600 MB or 629,145,600 bytes. The size limit in bytes is calculated
as 600 x 1024 x 1024.

Managed packages use different limits: First-generation managed packages that have passed AppExchange Security Review can
contain up to 35,000 files. Second-generation managed packages can contain up to 10,000 files.

- Metadata API base-64 encodes components after they’re compressed. The resulting .zip file can't exceed 50 MB, which is the
limit for SOAP messages. Base-64 encoding increases the size of the payload, so your compressed payload can't exceed
approximately 39 MB before encoding.

- You can perform a retrieve()  call for a big object only if its index is defined. If a big object is created in Setup and doesn’t

yet have an index defined, you can’t retrieve it.

- Limits can change without notice.

Every .zip file contains a project manifest, a file that’s named  package.xml, and a set of directories that contain the components.
The manifest file defines the components that you're trying to retrieve or deploy in the .zip file. The manifest also defines the API version
that's used for the deployment or retrieval.

Note:  You can edit the project manifest, but be careful if you modify the list of components it contains. When you deploy or
retrieve components, Metadata API references the components listed in the manifest, not the directories in the .zip file.

Note:  Note: If you’re retrieving any components that have dependencies by using the  rootTypesWithDependencies
parameter in the RetrieveRequest  object, the dependent metadata components are added to the returned .zip  file and
package.xml  file in the same directory as the root type that’s being retrieved. This directory has a JSON file for each component
with dependencies in the format  ComponentName.roottype.dependencies-meta.json.

The following is a sample  package.xml  file. You can retrieve an individual component for a metadata type by specifying its
fullName field value in a  members  element. You can also retrieve all components of a metadata type by using
<members>*</members>.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>MyCustomObject__c</members>
<name>CustomObject</name>

</types>
<types>

<members>*</members>
<name>CustomTab</name>

</types>
<types>

<members>Standard</members>
<name>Profile</name>

</types>
<version>66.0</version>

</Package>

The following elements can be defined in  package.xml.

- <fullName>  contains the name of the server-side package. If no <fullName>  exists, the package.xml  defines a client-side

unpackaged  package.

- <types>  contains the name of the metadata type (for example,  CustomObject) and the named members (for example,

myCustomObject__c) to be retrieved or deployed. You can add multiple  <types>  elements in a manifest file.


Deploying and Retrieving Metadata

Slow Deployments

- <members>  contains the  fullName  of the component, for example  MyCustomObject__c. The listMetadata()
call is useful for determining the  fullName  for components of a particular metadata type if you want to retrieve an individual
component. For many metadata types, you can replace the value in  members with the wildcard character  *  (asterisk) instead of
listing each member separately. See the reference topic for a specific type to determine whether that type supports wildcards.

Note:  You specify Security in the <members>  element and Settings in the name element when retrieving the SecuritySettings
component type.

- <name>  contains the metadata type, for example CustomObject  or Profile. There is one name defined for each metadata
type in the directory. Any metadata type that extends Metadata is a valid value. The name that’s entered must match a metadata
type that’s defined in the Metadata API WSDL. See Metadata Types for a list.

- <version>  is the API version number that’s used when the .zip file is deployed or retrieved. Currently the valid value is 66.0.

For more sample  package.xml  manifest files that show you how to work with different subsets of metadata, see Sample
package.xml  Manifest Files.

To delete components, see Deleting Components from an Organization.

SEE ALSO:

Metadata Types

Slow Deployments

If a file-based Metadata API deployment occurs during server downtime, such as a Salesforce service upgrade, the deployment can take
longer than expected. This behavior happens because both component deployment and validation are retried from the beginning after
the service is restored. However, if Apex tests were part of the deployment, only tests that weren’t run before the downtime are run.

This behavior affects file-based deployment and retrieval, change sets, some package installs and upgrades, second-generation managed
package creation, and deploys and retrieves started from the Salesforce CLI or the Salesforce VS Code extensions. It doesn’t affect
CRUD-based metadata operations.

If your instance is due for a planned service upgrade, avoid running deployments during the service upgrade. To check whether your
Salesforce instance is due for an upgrade, check Salesforce Trust. Salesforce performs major service upgrades three times per year and
other maintenance updates throughout the year.

Does a Retrieve Job Have a Status of Pending?

If you initiate several concurrent retrieve operations for a single org, Metadata API automatically puts some of those jobs in a queue, if
that becomes necessary for service protection. If a retrieve job has a status of Pending, it’s in the queue. When one of the active retrieve
jobs completes, Metadata API takes a pending job from the queue and activates it. If a retrieve job has a status of  InProgress, it’s
active. The process repeats until the job queue is cleared.

For more information, see "Metadata Limits" in the Salesforce Developer Limits and Allocations Quick Reference.

Sample package.xml Manifest Files

This section includes sample package.xml manifest files that show you how to work with different subsets of metadata. A manifest file
can include multiple <types> elements so you could combine the individual samples into one package.xml manifest file if you want to
work with all the metadata in one batch.


Deploying and Retrieving Metadata

Sample package.xml Manifest Files

The following samples are listed:

- Standard Objects on page 28

- All Custom Objects on page 28

- Standard Picklist Fields on page 29

- Custom and Standard Fields on page 30

- List Views for Standard Objects on page 30

- Packages on page 31

- Security Settings on page 31

- Assignment Rules, Auto-Response Rules, Escalation Rules on page 32

- Sharing Rules on page 32

- Managed Component Access on page 33

For more information about the structure of a manifest file, see Deploying and Retrieving Metadata with the Zip File.

Standard Objects

This sample package.xml  manifest file illustrates how to work with the standard Account object. Retrieving or deploying a standard
object includes all custom and standard fields except for standard fields that aren’t customizable. All custom fields are supported. Only
standard fields that you can customize are supported, that is, standard fields to which you can add help text or enable history tracking
or Chatter feed tracking. Other standard fields aren't supported, including system fields (such as  CreatedById  or
LastModifiedDate) and autonumber fields.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>Account</members>
<name>CustomObject</name>

</types>
<version>66.0</version>

</Package>

Note how you work with the standard Account object by specifying it as a member of a CustomObject type. However, you can’t use an
asterisk wildcard to work with all standard objects; each standard object must be specified by name.

All Custom Objects

This sample  package.xml  manifest file illustrates how to work with all custom objects.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>*</members>
<name>CustomObject</name>

</types>
<version>66.0</version>

</Package>

This manifest file can be used to retrieve or deploy all custom objects, but not all standard objects.


Deploying and Retrieving Metadata

Sample package.xml Manifest Files

Standard Picklist Fields

In API version 38.0 and later, the StandardValueSet type represents standard picklists. Picklists are no longer represented by fields as in
earlier versions. This sample  package.xml  represents the  Industry  standard picklist as a StandardValueSet type.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>Industry</members>
<name>StandardValueSet</name>

</types>
<version>66.0</version>

</Package>

Note:  The name of a standard value set is case-sensitive.

The  Industry  standard value set corresponds to the  Account.Industry  or  Lead.Industry field in API version 37.0 and
earlier. This example shows a  package.xml  sample for the  Account.Industry  picklist.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>Account.Industry</members>
<name>CustomField</name>

</types>
<version>37.0</version>

</Package>

Note:  The name of a picklist field is case-sensitive.

Note the objectName.picklistField syntax in the <members>  field where objectName  is the name of the object, such
as  Account, and  picklistField  is the name of the standard picklist field, such as  Industry.

This next  package.xml  sample represents opportunity team roles in API version 38.0 and later. Specify opportunity team roles as a
SalesTeamRole  standard value set. Opportunity team roles have the same picklist values as the account team roles.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>SalesTeamRole</members>
<name>StandardValueSet</name>

</types>
<version>66.0</version>

</Package>

The  SalesTeamRole  standard value set corresponds to one of these field names in API version 37.0 and earlier:
OpportunityTeamMember.TeamMemberRole,  UserAccountTeamMember.TeamMemberRole,
UserTeamMember.TeamMemberRole, and  AccountTeamMember.TeamMemberRole. Opportunity team roles are
represented in this sample  package.xml  as the  OpportunityTeamMember.TeamMemberRole  field.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>OpportunityTeamMember.TeamMemberRole</members>
<name>CustomField</name>


Deploying and Retrieving Metadata

Sample package.xml Manifest Files

</types>
<version>37.0</version>

</Package>

To learn about the names of standard value sets and how they map to picklist field names, see StandardValueSet Names and Standard
Picklist Fields.

Custom and Standard Fields

This sample  package.xml  manifest file illustrates how to work with custom fields in custom and standard objects and standard
fields in a standard object.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>MyCustomObject__c.MyCustomField__c</members>
<name>CustomField</name>

</types>
<types>

<members>Account.SLA__c</members>
<members>Account.Phone</members>
<name>CustomField</name>

</types>
<version>66.0</version>

</Package>

Note the objectName.field  syntax in the <members>  field where objectName  is the name of the object, such as Account,
and  field  is the name of the custom or standard field, such as an  SLA  picklist field representing a service-level agreement option.
The  MyCustomField  custom field in the MyCustomObject custom object is uniquely identified by its full name
MyCustomObject__c.MyCustomField__c. Similarly, the  Phone  standard field in the Account standard object is uniquely
identified by its full name  Account.Phone.

All custom fields are supported. Only standard fields that you can customize are supported, that is, standard fields to which you can add
help text or enable history tracking or Chatter feed tracking. Other standard fields aren't supported, including system fields (such as
CreatedById  or  LastModifiedDate) and autonumber fields.

List Views for Standard Objects

The easiest way to retrieve list views for a standard object is to retrieve the object. The list views are included in the retrieved component.
See the section of this topic on Standard Objects.

You can also work with individual list views if you don’t want to retrieve all the details for the object. This sample  package.xml
manifest file illustrates how to work with a list view for the standard Account object.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>Account.AccountTeam</members>
<name>ListView</name>

</types>
<version>66.0</version>

</Package>


Deploying and Retrieving Metadata

Sample package.xml Manifest Files

Note the  objectName.listViewUniqueName syntax in the  <members>  field where  objectName  is the name of the
object, such as Account, and  listViewUniqueName  is the  View Unique Name  for the list view. If you retrieve this list view,
the component is stored in  objects/Account.object.

Packages

To retrieve a package, set the name of the package in the packageNames field in RetrieveRequest when you call  retrieve().
The package.xml  manifest file is automatically populated in the retrieved .zip  file. The <fullName>  element in package.xml
contains the name of the retrieved package.

If you use an asterisk wildcard in a  <members> element to retrieve all the components of a particular metadata type, the retrieved
contents don’t include components in managed packages.

For more information about managed packages, see the Second-Generation Managed Packaging Developer Guide.

The easiest way to retrieve a component in a managed package is to retrieve the complete package by setting the name of the package
in the packageNames field in  RetrieveRequest, as described earlier. The following sample  package.xml  manifest file
illustrates an alternative to retrieve an individual component in a package.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>myns__MyCustomObject__c</members>
<name>CustomObject</name>

</types>
<version>66.0</version>

</Package>

Note the namespacePrefix__objectName syntax in the <members>  field where namespacePrefix  is the namespace
prefix of the package and  objectName  is the name of the object. A namespace prefix is a 1-character to 15-character alphanumeric
identifier that distinguishes your package and its contents from other publishers’ packages. For more information, see Create and Register
Your Namespace for Second-Generation Managed Packages.

Note:  The namespace prefix is important to help identify the source of items like fields, custom objects, and more from different
managed packages. For example, when working with FlexiPages in your org, we recommend against removing namespaces for
object fields, because it can cause unexpected results such as name collisions.

Security Settings

This sample package.xml  manifest file illustrates how to work with an org’s security settings. You specify Security in the <members>
element and Settings in the name element when retrieving the SecuritySettings component type.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>Security</members>
<name>Settings</name>

</types>
<version>66.0</version>

</Package>


Deploying and Retrieving Metadata

Sample package.xml Manifest Files

Assignment Rules, Auto-Response Rules, Escalation Rules

Assignment rules, auto-response rules, and escalation rules use different package.xml  type names to access sets of rules or individual
rules for object types. For example, this sample  package.xml  manifest file illustrates how to access an org’s assignment rules for
just Cases and Leads.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>Case</members>
<members>Lead</members>
<name>AssignmentRules</name>

</types>
<version>66.0</version>

</Package>

The following sample  package.xml  manifest file illustrates how to access just the “samplerule” Case assignment rule and the
“newrule” Lead assignment rule. Notice that the type name is  AssignmentRule  and not  AssignmentRules.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>Case.samplerule</members>
<members>Lead.newrule</members>
<name>AssignmentRule</name>

</types>
<version>66.0</version>

</Package>

Similarly, for accessing individual auto-response rules and escalation rules, use  AutoResponseRule  and  EscalationRule
instead of  AutoResponseRules  and  EscalationRules.

Sharing Rules

In API version 33.0 and later, you can retrieve and deploy sharing rules for all standard and custom objects. This sample package.xml
manifest file illustrates how to work with an org’s sharing rules, such as retrieving a specific criteria-based sharing rule for the lead object,
retrieving all ownership-based sharing rules for all objects, and retrieving all territory-based sharing rules for the account object.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>Lead.testShareRule</members>

<name>SharingCriteriaRule</name>

</types>
<types>

<members>*</members>
<name>SharingOwnerRule</name>

</types>
<types>

<members>Account.*</members>
<name>SharingTerritoryRule</name>

</types>
<version>33.0</version>

</Package>


Deploying and Retrieving Metadata

Sample package.xml Manifest Files

Managed Component Access

In API version 29.0 and later, you can retrieve and deploy access settings for these managed components in profiles and permission sets:

- Apex classes

- Apps

- Custom field permissions

- Custom object permissions

- Custom tab settings

- External data sources

- Record types

- Visualforce pages

In API version 51.0 and later, you can retrieve and deploy access settings for login flows.

When retrieving and deploying managed component permissions, specify the namespace followed by two underscores. Wildcards
aren’t supported.

For example, let’s say you install a managed package with the namespace MyNamespace  and the custom object JobRequest__c.
To set object permissions for  JobRequest__c  in the package to the custom profile MyProfile, you would add the following to the
.profile file.

To deploy:

<objectPermissions>

<allowCreate>true</allowCreate>
<allowDelete>true</allowDelete>
<allowEdit>true</allowEdit>
<allowRead>true</allowRead>
<viewAllRecords>false</viewAllRecords>
<modifyAllRecords>false</modifyAllRecords>
<object>MyNamespace__JobRequest__c</object>

</objectPermissions>

To retrieve:

<types>

<members>MyNamespace__JobRequest__c</members>
<name>CustomObject</name>

</types>
<types>

<members>MyProfile</members>
<name>Profile</name>

</types>

When retrieving permission sets and profiles, make sure that you also retrieve any components that are related to the permissions and
settings. For example, when retrieving app visibilities, you must also retrieve the associated app, and when retrieving object or field
permissions, you must also retrieve the associated object.


Deploying and Retrieving Metadata

Running Tests in a Deployment

Running Tests in a Deployment

Default Test Execution in Production

When no test level is specified in the deployment options, the default test execution behavior depends on the contents of your deployment
package. When deploying to production, all tests, except those that originate from managed packages, are executed if your deployment
package contains Apex classes or triggers. If your package doesn’t contain Apex components, no tests are run by default.

In API version 33.0 and earlier, tests were run for components that required tests, such as custom objects, and not only for Apex
components. For example, if your package contains a custom object, all tests are run in API version 33.0 and earlier. In contrast, starting
with API version 34.0, no tests are run for this package. The API version corresponds to the version of your API client or the version of the
tool you’re using (Ant Migration Tool).

You can run tests for a deployment of non-Apex components. You can override the default test execution behavior by setting the test
level in your deployment options. Test levels are enforced regardless of the types of components present in your deployment package.
We recommend that you run all local tests in your development environment, such as sandbox, before deploying to production. Running
tests in your development environment reduces the number of tests needed to run in a production deployment.

Default Test Execution in Production for API Version 33.0 and Earlier

For deployment to a production organization, all local tests in your organization are run by default. Tests that originate from installed
managed packages aren’t run by default. If any test fails, the entire deployment is rolled back.

If the deployment includes components for the following metadata types, all local tests are run.

- ApexClass

- ApexComponent

- ApexPage

- ApexTrigger

- ArticleType

- BaseSharingRule

- CriteriaBasedSharingRule

- CustomField

- CustomObject

- DataCategoryGroup

- Flow

- InstalledPackage

- NamedFilter

- OwnerSharingRule

- PermissionSet

- Profile

- Queue

- RecordType

- RemoteSiteSetting

- Role

- SharingReason


Deploying and Retrieving Metadata

Running a Subset of Tests in a Deployment

- Territory

- Validation Rules

- Workflow

For example, no tests are run for the following deployments:

- 1 CustomApplication component

- 100 Report components and 40 Dashboard components

But all local tests are run for any of the following example deployments, because they include at least one component from the list
above:

- 1 CustomField component

- 1 ApexComponent component and 1 ApexClass component

- 5 CustomField components and 1 ApexPage component

- 100 Report components, 40 Dashboard components, and 1 CustomField component

SEE ALSO:

deploy()

Run Relevant Apex Tests in a Deployment (Beta)

Running a Subset of Tests in a Deployment

Test levels enable you to have more control over which tests are run in a deployment. To shorten deployment time to production, run
a subset of tests when deploying Apex components. The default test execution behavior in production has also changed. By default, if
no test level is specified, no tests are executed, unless your deployment package contains Apex classes or triggers.

If the code coverage of an Apex component in the deployment is less than 75%, the deployment fails. If one of the specified tests fails,
the deployment also fails. We recommend that you test your deployment in sandbox first to ensure that the specified tests cover each
component sufficiently. Even if your organization’s overall code coverage is 75% or more, the individual coverage of the Apex components
being deployed can be less. If the code coverage requirement isn’t met, write more tests and include them in the deployment.

To run a subset of tests, set the  RunSpecifiedTests  test level on the  DeployOptions  object. Next, specify each test class to
run in DeployOptions. Finally, pass DeployOptions  as an argument to the deploy()  call. The following example performs
those steps to run only the specified test classes.

// Create the DeployOptions object.
DeployOptions deployOptions = new DeployOptions();

// Set the appropriate test level.
deployOptions.setTestLevel(TestLevel.RunSpecifiedTests);

// Specify the test classes to run.
// String array contains test class names.
String[] tests = {"TestClass1", "TestClass2", "TestClass3"};
// Add the test class names array to the deployment options.
deployOptions.setRunTests(tests);

// Call deploy() by passing the deployment options object as an argument.
AsyncResult asyncResult = metadatabinding.deploy(zipBytes,deployOptions);


Deploying and Retrieving Metadata

Run Relevant Apex Tests in a Deployment (Beta)

Notes About Running Specific Tests

- You can specify only test classes. You can’t specify individual test methods.

- We recommend that you refactor test classes to include the minimum number of tests that meet code coverage requirements.

Refactoring your test classes can contribute to shorter test execution times, and as a result, shorter deployment times.

- You can deactivate a trigger in the target organization by deploying it with an inactive state. However, the trigger must have been

previously deployed with an active state.

SEE ALSO:

Run Relevant Apex Tests in a Deployment (Beta)

Run Relevant Apex Tests in a Deployment (Beta)

Use the RunRelevantTests (beta) test level to run only the Apex tests that are relevant to your deployment. Salesforce automatically
identifies the relevant tests based on an analysis of the deployment payload and the payload dependencies.

Important:  The RunRelevantTests  test level and the associated @IsTest()  annotations are pilot or beta services that
are subject to the Beta Services Terms at Agreements — Salesforce.com or a written Unified Pilot Agreement if executed by
Customer, and applicable terms in the Product Terms Directory. Use of these pilot or beta services are at the Customer’s sole
discretion.

Why Use RunRelevantTests

Compared to the default RunLocalTests  test level set for production deployments, using RunRelevantTests  can significantly
shorten deployment time. Whereas the  RunLocalTests  test level runs all Apex tests in the org except the ones that originate from
installed managed and unlocked packages,  RunRelevantTests  runs only Apex tests relevant to the deployment payload. In orgs
with extensive test suites,  RunLocalTests  causes long deployment times even for minor code changes, but with
RunRelevantTests, the number of tests that are run are proportionally scaled to deployment size. In other words, smaller
deployments result in the inclusion of fewer relevant tests compared to larger deployments.

Compared to the  RunSpecifiedTests  test level, where only a specified subset of Apex tests are run,  RunRelevantTests
requires less DevOps overhead. For RunSpecifiedTests, you must manually determine the tests that are applicable to the changes,
which often requires custom DevOps tooling. In contrast, the  RunRelevantTests  test engine analyzes the deployment payload
and automatically runs a subset of tests based on that analysis.

When you set the deployment test level to  RunRelevantTests, you must still meet at least 75% test coverage for every class and
trigger included in the deployment package. This coverage is computed for each class and trigger individually and is different from the
overall coverage percentage. If your deployment package doesn’t meet code coverage requirements when  RunRelevantTests
is set, you can use test class annotations to augment your test suite. See the “Apply Test Class Overrides to RunRelevantTests” section.

Set the Test Level to RunRelevantTests

To run relevant tests, set the  RunRelevantTests  test level on the  DeployOptions  object. Then pass  DeployOptions  as
an argument to the  deploy()  call.

// Create the DeployOptions object.
DeployOptions deployOptions = new DeployOptions();

// Set the appropriate test level.


Deploying and Retrieving Metadata

Run the Same Tests in Sandbox and Production Deployments

deployOptions.setTestLevel(TestLevel.RunRelevantTests);

// Call deploy() by passing the deployment options object as an argument.
AsyncResult asyncResult = metadatabinding.deploy(zipBytes,deployOptions);

You can Deploy Metadata with Apex Testing Using REST on page 46. Set the  RunRelevantTests  test level on the
deployOptions  object in the request body.

You can deploy metadata from a local project by using the Salesforce CLI. Set the  --test-level  flag on one of the supported
project commands to  RunRelevantTests.

Apply Test Class Overrides to RunRelevantTests

For fine-grained control of the tests run with the  RunRelevantTests  level, you can use  @IsTest annotations.

Add the @IsTest(critical=true)  annotation to a test class so that it always runs during deployments, regardless of the classes
or triggers in the deployment payload. Add the @IsTest(testFor='...') annotation to a test class so that its tests run whenever
specified classes or triggers are new or changed in the deployment payload.

For implementation instructions, see @IsTest(critical=true) and @IsTest(testFor='...') in the Apex Developer Guide.

SEE ALSO:

Apex Developer Guide: @IsTest Annotation

Run the Same Tests in Sandbox and Production Deployments

Starting in API version 34.0, you can choose which tests to run in your development environment, such as only local tests, to match the
tests run in production. In earlier versions, if you enabled tests in your sandbox deployment, you couldn’t exclude managed package
tests.

By default, no tests are run in a deployment to a non-production organization, such as a sandbox or a Developer Edition organization.
To specify tests to run in your development environment, set a testLevel  deployment option. For example, to run local tests in a
deployment and to exclude managed package tests, set  testLevel  on the  DeployOptions  object to
TestLevel.RunLocalTests. Next, pass this object as an argument to the  deploy()  call as follows.

// Create the DeployOptions object.
DeployOptions deployOptions = new DeployOptions();

// Set the appropriate test level.
deployOptions.setTestLevel(TestLevel.RunLocalTests);

// Call deploy() by passing the deployment options object as an argument.
AsyncResult asyncResult = metadatabinding.deploy(zipBytes,deployOptions);

Note:  The RunLocalTests  test level is enforced regardless of the contents of the deployment package. In contrast, tests are
executed by default in production only if your deployment package contains Apex classes or triggers. You can use
RunLocalTests  for sandbox and production deployments.


Deploying and Retrieving Metadata

Limit on Enqueued Deployments from Apex

Limit on Enqueued Deployments from Apex

We limit the number of Metadata API deployments originating from Apex that can be enqueued at a time. This limit helps preserve
service function and resources for all customers on a server. Because this limit is a queue-depth limit, as long as the server can keep
dequeuing, you can keep enqueuing deploys through Apex. This limit is based on analysis to make sure that it doesn’t affect your
day-to-day operations.

When you reach the limit, you receive this exception as an API response in Apex.

[
{

"message" : "The service received too many metadata deployment requests from Apex and

doesn’t have the resources to accept new requests",

"errorCode" : "System.AsyncException"

}
]

The limit applies only to enqueued Metadata API deployments that originate from Apex. It doesn’t affect Metadata API deployments
from Salesforce CLI, change sets, or packaging. The limit does apply if a package contains Apex that triggers metadata deployments. It
also applies to the Metadata.Operations.enqueueDeployment() Apex method. This limit applies to all Salesforce editions.

Maintaining User References

User fields are preserved during a metadata deployment.

When a component in your deployment refers to a specific user, such as a recipient of a workflow email notification or a dashboard
running user, then Salesforce attempts to locate a matching user in the destination organization by comparing usernames during the
deployment.

For example, when you copy data to a sandbox, the fields containing usernames from the production organization are altered to include
the sandbox name. In a sandbox named  test, the username  user@acme.com  becomes  user@acme.com.test. When you
deploy the metadata in the sandbox to another organization, the  test  in the username is ignored.

For user references in deployments, Salesforce performs the following sequence:

1. Salesforce compares usernames in the source environment to the destination environment and adapts the organization domain

name.

2.

3.

If two or more usernames match, Salesforce lists the matching names and requests one of the users in the source environment be
renamed.

If a username in the source environment doesn’t exist in the destination environment, Salesforce displays an error, and the deployment
stops until the usernames are removed or resolved to users in the destination environment.


## CHAPTER 5 CRUD-Based Metadata Development

Use the CRUD-based metadata calls to create, update, or delete setup and configuration components for your organization or application.
These configuration components include custom objects, custom fields, and other configuration metadata. The metadata calls mimic
the behavior in the Salesforce user interface for creating, updating, or deleting components. Whatever rules apply there also apply to
these calls.

Metadata calls are different from the core, synchronous API calls in these ways.

- Metadata API calls are available in a separate WSDL. To download the WSDL, log into Salesforce, from Setup, enter  API  in the

Quick Find  box, then select API and click the Download Metadata WSDL link.

- After logging in, you must send Metadata API calls to the Metadata API endpoint, which has a different URL than SOAP API. Retrieve
the metadataServerUrl  from the LoginResult returned by your SOAP API login()  call. For more information about SOAP
API, see the SOAP API Developer Guide.

- Metadata calls are either synchronous or asynchronous. CRUD calls are synchronous in API version 30.0 and later, and similar to the
API core calls the results are returned in a single call. In earlier API versions, create, update, and delete are only asynchronous, which
means that the results aren’t immediately returned in one call.

- There are synchronous metadata calls that map to the corresponding core SOAP API synchronous calls.

– createMetadata() maps to the  create()  SOAP API call.

– updateMetadata() maps to the  update()  SOAP API call.

– deleteMetadata() maps to the  delete()  SOAP API call.

Note:  Metadata API also supports  retrieve()  and  deploy()  calls for retrieving and deploying metadata components.
For more information, see Deploying and Retrieving Metadata.

Java Sample for CRUD-Based Development with Synchronous Calls

This section guides you through a sample Java client application that uses CRUD-based calls. This sample application performs the
following main tasks.

1. Uses the MetadataLoginUtil.java  class to create a Metadata connection. For more information, see Step 3: Walk Through

the Java Sample Code.

2. Calls createMetadata() to create a custom object. This call returns the result in one call.

3.

Inspects the returned SaveResult  object to check if the operation succeeded, and if it didn’t, writes the component name, error
message, and status code to the output.

import com.sforce.soap.metadata.*;

/**

* Sample that logs in and creates a custom object through the metadata API
*/

public class CRUDSampleCreate {


CRUD-Based Metadata Development

private MetadataConnection metadataConnection;

// one second in milliseconds
private static final long ONE_SECOND = 1000;

public CRUDSampleCreate() {
}

public static void main(String[] args) throws Exception {
CRUDSampleCreate crudSample = new CRUDSampleCreate();
crudSample.runCreate();

}

/**

* Create a custom object. This method demonstrates usage of the
* create() and checkStatus() calls.
*
* @param uniqueName Custom object name should be unique.
*/

private void createCustomObjectSync(final String uniqueName) throws Exception {

final String label = "My Custom Object";
CustomObject co = new CustomObject();
co.setFullName(uniqueName);
co.setDeploymentStatus(DeploymentStatus.Deployed);
co.setDescription("Created by the Metadata API Sample");
co.setEnableActivities(true);
co.setLabel(label);
co.setPluralLabel(label + "s");
co.setSharingModel(SharingModel.ReadWrite);

// The name field appears in page layouts, related lists, and elsewhere.
CustomField nf = new CustomField();
nf.setType(FieldType.Text);
nf.setDescription("The custom object identifier on page layouts, related lists

etc");

nf.setLabel(label);
nf.setFullName(uniqueName);
customObject.setNameField(nf);

SaveResult[] results = metadataConnection

.createMetadata(new Metadata[] { co });

for (SaveResult r : results) {

if (r.isSuccess()) {

System.out.println("Created component: " + r.getFullName());

} else {

System.out

.println("Errors were encountered while creating "

for (Error e : r.getErrors()) {

+ r.getFullName());

System.out.println("Error message: " + e.getMessage());
System.out.println("Status code: " + e.getStatusCode());

}

}


CRUD-Based Metadata Development

}

}

private void runCreate() throws Exception {

metadataConnection = MetadataLoginUtil.login();
// Custom objects and fields must have __c suffix in the full name.
final String uniqueObjectName = "MyCustomObject__c";
createCustomObjectSync(uniqueObjectName);

}

}

Java Sample for CRUD-Based Development with Asynchronous Calls

Important:  The sample in this section depends on the asynchronous  create()  CRUD call. Asynchronous CRUD calls are no
longer available as of API version 31.0 and are available only in earlier API versions.

This section guides you through a sample Java client application that uses asynchronous CRUD-based calls. This sample application
performs the following main tasks:

1. Uses the MetadataLoginUtil.java  class to create a Metadata connection. For more information, see Step 3: Walk Through

the Java Sample Code.

2. Calls create() to create a custom object.

Salesforce returns an AsyncResult object for each component you tried to create. The AsyncResult object is updated with status
information as the operation moves from a queue to completed or error state.

3. Calls checkStatus() in a loop until the status value in AsyncResult indicates that the create operation is completed.

Note the error handling code that follows each API call.

import com.sforce.soap.metadata.*;

/**

* Sample that logs in and creates a custom object through the metadata api
*/

public class CRUDSample {

private MetadataConnection metadataConnection;

// one second in milliseconds
private static final long ONE_SECOND = 1000;

public CRUDSample() {
}

public static void main(String[] args) throws Exception {

CRUDSample crudSample = new CRUDSample();
crudSample.runCreate();

}

/**

* Create a custom object. This method demonstrates usage of the
* create() and checkStatus() calls.
*
* @param uniqueName Custom object name should be unique.


CRUD-Based Metadata Development

*/

private void createCustomObject(final String uniqueName) throws Exception {

final String label = "My Custom Object";
CustomObject customObject = new CustomObject();
customObject.setFullName(uniqueName);
customObject.setDeploymentStatus(DeploymentStatus.Deployed);
customObject.setDescription("Created by the Metadata API Sample");
customObject.setLabel(label);
customObject.setPluralLabel(label + "s");
customObject.setSharingModel(SharingModel.ReadWrite);

// The name field appears in page layouts, related lists, and elsewhere.
CustomField nf = new CustomField();
nf.setType(FieldType.Text);
nf.setDescription("The custom object identifier on page layouts, related lists

etc");

nf.setLabel(label);
nf.setFullName(uniqueName);
customObject.setNameField(nf);

AsyncResult[] asyncResults = metadataConnection.create(

new CustomObject[]{customObject});

if (asyncResults == null) {

System.out.println("The object was not created successfully");
return;

}

long waitTimeMilliSecs = ONE_SECOND;

// After the create() call completes, we must poll the results of the checkStatus()

// call until it indicates that the create operation has completed.
do {

printAsyncResultStatus(asyncResults);
waitTimeMilliSecs *= 2;
Thread.sleep(waitTimeMilliSecs);
asyncResults = metadataConnection.checkStatus(new

String[]{asyncResults[0].getId()});

} while (!asyncResults[0].isDone());

printAsyncResultStatus(asyncResults);

}

private void printAsyncResultStatus(AsyncResult[] asyncResults) throws Exception {

if (asyncResults == null || asyncResults.length == 0 || asyncResults[0] == null)

{

}

throw new Exception("The object status cannot be retrieved");

AsyncResult asyncResult = asyncResults[0]; //we are creating only 1 metadata object

if (asyncResult.getStatusCode() != null) {

System.out.println("Error status code: " +


CRUD-Based Metadata Development

asyncResult.getStatusCode());

System.out.println("Error message: " + asyncResult.getMessage());

}

System.out.println("Object with id:" + asyncResult.getId() + " is " +

asyncResult.getState());

}

private void runCreate() throws Exception {

metadataConnection = MetadataLoginUtil.login();
// Custom objects and fields must have __c suffix in the full name.
final String uniqueObjectName = "MyCustomObject__c";
createCustomObject(uniqueObjectName);

}

}


## CHAPTER 6 REST Resources

In this chapter ...

- Deploy Metadata
with Apex Testing
Using REST

- Deploy Metadata
with REST API in
Salesforce CLI

Use the REST resource  deployRequest  to move metadata (XML files) between a Salesforce
organization and a local file system.

Data in XML files is formatted using the English (United States) locale. This approach ensures that fields
that depend on locale, such as date fields, are interpreted consistently during data migrations between
organizations using different languages. Organizations can support multiple languages for presentation
to their users.

Metadata deployment is used primarily for the following development scenarios.

- Development of a custom application (or customization) in a sandbox organization. After development
and testing are completed, the application or customization is then deployed into a production
organization using Metadata API.

- Team development of an application in a Developer Edition organization. After development and
testing are completed, you can then distribute the application via Lightning Platform AppExchange.

Working with the Zip File

The  deployRequest  resource is used to deploy a .zip file. Within the .zip file is a project manifest
(package.xml)  that lists what to retrieve or deploy, and one or more XML components that are
organized into folders.

A component is an instance of a metadata type. For example,  CustomObject is a metadata type for
custom objects, and the  MyCustomObject__c  component is an instance of a custom object.

The files that are deployed in a .zip  file can be unpackaged components that reside in your organization
(such as standard objects). The files can also be packaged components that reside within named packages.

Note:  You can deploy up to 10,000 files at once. (In API version 43.0 and later, AppExchange
packages can contain up to 12,500 files.) The .zip file size limit that applies to SOAP calls doesn’t
apply to the deployRequest  REST resource. However, the 400-MB limit for components that
are uncompressed into an unzipped folder after upload applies to both SOAP and REST
deployments.

Every .zip file contains a project manifest, a file that’s named  package.xml, and a set of directories
that contain the components. The manifest file defines the components that you’re trying to retrieve or
deploy and the API version used for the deployment or retrieval.

The following is a sample  package.xml  file.

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>MyCustomObject__c</members>


REST Resources

<name>CustomObject</name>

</types>
<types>

<members>*</members>
<name>CustomTab</name>

</types>
<types>

<members>Standard</members>
<name>Profile</name>

</types>
<version>66.0</version>

</Package>

The following elements can be defined in  package.xml.

- <fullName>  contains the name of the server-side package. If no  <fullName>  exists, it’s a

client-side  unpackaged  package.

- <types>  contains the name of the metadata type (for example,  CustomObject) and the

named members (for example,  myCustomObject__c) to be deployed. You can add multiple
<types>  elements in a manifest file.

- <members>  contains the  fullName  of the component, such as  MyCustomObject__c.
For many metadata types, you can replace the value in  members  with the wildcard character  *
(asterisk) instead of listing each member separately. For a list of metadata types that allow the
wildcard character, see the “Allows Wildcard (*)?” column in Metadata Types.

Note:  You specify Security in the  <members>  element and Settings in the name element
when retrieving the SecuritySettings component type.

- <name>  contains the metadata type, for example  CustomObject  or  Profile. There’s one
name defined for each metadata type in the directory. Any metadata type that extends Metadata is
a valid value. The name that’s entered must match a metadata type that’s defined in the Metadata
API WSDL. See Metadata Types for a list.

- <version>  is the API version number that’s used when the .zip file is deployed or retrieved.

Currently the valid value is  66.0.

For more sample  package.xml  manifest files that show you how to work with different subsets of
metadata, see Sample package.xml Manifest Files.

To delete components, see Deleting Components from an Organization.


REST Resources

Deploy Metadata with Apex Testing Using REST

Deploy Metadata with Apex Testing Using REST

Deploy using the  deployRequest  REST resource to initiate a request that handles all operations for the deployment.

You can deploy or retrieve up to 10,000 files at once. The maximum size of the deployed or retrieved .zip file is 39 MB. If the files are
uncompressed in an unzipped folder, the size limit is 600 MB or 629,145,600 bytes. The size limit in bytes is calculated as 600 x 1024 x
1024.

URI

https://host/services/data/vXX.0/metadata/deployRequest

Formats
JSON

HTTP Method
POST

Authentication

Authorization: Bearer token

deployOptions Parameters

Note:  To review the default testing behavior for deployments and approaches that can save time while still enabling you to meet
testing requirements, see Running Tests in a Deployment and Run the Same Tests in Sandbox and Production Deployments.

Parameter

Description

allowMissingFiles

Boolean. If files that are specified in  package.xml  aren’t in the  .zip  file, specifies
whether a deployment can still succeed. Don’t set this argument for deployment to
production orgs.

autoUpdatePackage

Reserved for future use.

checkOnly

ignoreWarnings

Boolean. Defaults to  false. Set to  true  to perform a test deployment (validation) of
components without saving the components in the target org. A validation enables you
to verify the results of tests that would be generated in a deployment, but doesn’t commit
any changes. After a validation finishes with passing tests, it can qualify for deployment
without rerunning tests. See Deploy a Recently Validated Component Set Without Tests.

Boolean. Indicates whether a deployment is allowed to complete successfully despite
one or more warnings (true) or not (false). Defaults to  false.

The DeployMessage object for a warning contains the following values:

- problemType—Warning

- problem—The text of the warning.

If a warning occurs and  ignoreWarnings  is set to  true, the  success  field in
DeployMessage is true. If ignoreWarnings  is set to false, success  is set to
false  and the warning is treated like an error.

performRetrieve

Reserved for future use.


REST Resources

Deploy Metadata with Apex Testing Using REST

Parameter

purgeOnDelete

rollbackOnError

runTests

singlePackage

testLevel

Description

Boolean. If  true, the deleted components in the  destructiveChanges.xml
manifest file aren't stored in the Recycle Bin. Instead, they become immediately eligible
for deletion.

This option only works in Developer Edition or sandbox orgs. It doesn't work in production
orgs.

Boolean. Indicates whether any failure causes a complete rollback (true) or not (false).
If  false, whatever actions can be performed without errors are performed, and errors
are returned for the remaining actions. This parameter must be set to  true  if you’re
deploying to a production org. The default is  false.

String[]. A list of Apex tests to run during deployment. Specify the class name, one name
per instance. The class name can also specify a namespace with a dot notation. For more
information, see Running a Subset of Tests in a Deployment.

To use this option, set  testLevel  to  RunSpecifiedTests.

Boolean. Indicates whether the specified  .zip  file points to a directory structure with
a single package (true) or a set of packages (false).

TestLevel (enumeration of type string). Optional. Specifies which tests are run as part of
a deployment. The test level is enforced regardless of the types of components that are
present in the deployment package. Valid values are:

- NoTestRun—No tests are run. This test level applies only to deployments to

development environments, such as sandbox, Developer Edition, or trial organizations.
This test level is the default for development environments.

- RunSpecifiedTests—Only the tests that you specify in the  runTests
option are run. Code coverage requirements differ from the default coverage
requirements when using this test level. Each class and trigger in the deployment
package must be covered by the executed tests for a minimum of 75% code coverage.
This coverage is computed for each class and triggers individually and is different
than the overall coverage percentage.

- RunRelevantTests (beta)—Only tests relevant to the deployment payload are
run. Salesforce automatically identifies the relevant tests based on an analysis of the
deployment payload and the payload dependencies. For fine-grained control, you
can annotate test classes so that they either run regardless of the deployment payload,
or run when modified, referenced components are included in the deployment. See
@IsTest Annotation in the Apex Developer Guide. Each class and trigger in the
deployment package must be covered by the executed tests for a minimum of 75%
code coverage. This coverage is computed for each class and trigger individually and
is different from the overall coverage percentage.

- RunLocalTests—All tests in your org are run, except the ones that originate
from installed managed and unlocked packages. This test level is the default for
production deployments that include Apex classes or triggers.

- RunAllTestsInOrg—All tests are run. The tests include all tests in your org,

including tests of managed packages.


REST Resources

Deploy Metadata with Apex Testing Using REST

Parameter

Description

If you don’t specify a test level, the default test execution behavior is used. See Running
Tests in a Deployment.

Apex tests that run as part of a deployment always run synchronously and serially.

Request Body: Deploy Metadata

When you deploy metadata, your request includes both the deployment parameters and the .zip file containing the component directories
and the manifest.

This example POST request creates a  deployRequest  object that initiates a deployment.

- The POST request header is set to  Content-Type: multipart/form-data  and defines a  boundary delimiter to

encapsulate different subparts of the request. In this example, the boundary delimiter is
--------------------------BOUNDARY.

- The boundary delimiter precedes each subpart, and the delimiter itself is preceded by two extra  --. In the first subpart, a JSON

request creates a  deployOptions  child object for passing the deployment parameters.

- The second subpart specifies the .zip file that contains the manifest and the component directories.

- The second subpart ends with the boundary delimiter preceded by two  --. The delimiter is followed by another two  --, which

indicate the end of the request body.

POST /services/data/v48.0/metadata/deployRequest
Authorization: Bearer 00D....
Content-Type: multipart/form-data; boundary=--------------------------BOUNDARY

----------------------------BOUNDARY
Content-Disposition: form-data; name="json"
Content-Type: application/json

{

"deployOptions" :

{
"allowMissingFiles" : false,
"autoUpdatePackage" : false,
"checkOnly" : false,
"ignoreWarnings" : false,
"performRetrieve" : false,
"purgeOnDelete" : false,
"rollbackOnError" : false,
"runTests" : null,
"singlePackage" : true,
"testLevel" : "RunAllTestsInOrg"
}

}

----------------------------BOUNDARY
Content-Disposition: form-data; name="file"; filename="deploy.zip"
Content-Type: application/zip


REST Resources

Deploy Metadata with Apex Testing Using REST

//Contents of deploy.zip
----------------------------BOUNDARY--

Response Body: Deploy Metadata

When an HTTP status code of  201  (Created) is returned, your request has succeeded and resulted in the creation of a deployment that
is being processed.

{ "id" : "0Afxx00000001VPCAY",

"deployOptions" :

{ "checkOnly" : false,

"singlePackage" : false,
"allowMissingFiles" : false,
"performRetrieve" : false,
"autoUpdatePackage" : false,
"rollbackOnError" : true,
"ignoreWarnings" : false,
"purgeOnDelete" : false,
"runAllTests" : false },

"deployResult" :

{ "id" : "0Afxx00000001VPCAY",

"success" : false,
"checkOnly" : false,
"ignoreWarnings" : false,
"rollbackOnError" : true,
"status" : "Pending",
"runTestsEnabled" : false,
"done" : false } }

deployResult Parameters

Parameter

id

canceledBy

Description

ID. ID of the component being deployed.

ID. The ID of the user who canceled the deployment.

canceledByName

String. The full name of the user who canceled the deployment.

checkOnly

completedDate

createdBy

createdByName

createdDate

details

Boolean. Indicates whether this deployment is used to check the validity of the deployed
files without changing the org (true) or not (false). A check-only deployment
doesn’t deploy any components or change the organization in any way.

DateTime. Timestamp for when the deployment process ended.

ID. The ID of the user who created the deployment.

String. The full name of the user who created the deployment.

DateTime. Timestamp for when the deploy request was received.

DeployDetails. Provides the details of a deployment that is in-progress or ended if
?includeDetails=true  is added as a query to the GET request.


REST Resources

Deploy Metadata with Apex Testing Using REST

Parameter

done

Description

Boolean. Indicates whether the server finished processing the deploy request for the
specified  id.

errorMessage

String. Message corresponding to the values in the errorStatusCode  field, if any.

errorStatusCode

ignoreWarnings

String. If an error occurred during the deploy request, a status code is returned, and the
message corresponding to the status code is returned in  errorMessagefield.

Boolean. Optional. Defaults to false. Specifies whether a deployment continues even
if the deployment generates warnings. Don’t set this argument to  true  for
deployments to production organizations.

lastModifiedDate

DateTime. Timestamp of the last update for the deployment process.

numberComponentErrors

numberComponentsTotal

Int. The number of components deployed in the deployment process. Use this value
with the numberComponentsTotal  value to get an estimate of the deployment’s
progress.

Int. The total number of components in the deployment. Use this value with the
numberComponentsDeployed  value to get an estimate of the deployment’s
progress.

numberTestErrors

Int. The number of Apex tests that have generated errors during this deployment.

numberTestsCompleted

The number of completed Apex tests for this deployment. Use this value with the
numberTestsTotal  value to get an estimate of the deployment’s test progress.

numberTestsTotal

runTestsEnabled

rollbackOnError

startDate

stateDetail

status

Int. The total number of Apex tests for this deployment. Use this value with the
numberTestsCompleted  value to get an estimate of the deployment’s test
progress. The value in this field isn’t accurate until the deployment has started running
tests for the components being deployed.

Boolean. Indicates whether Apex tests were run as part of this deployment (true) or
not (false). Tests are either automatically run as part of a deployment or can be set
to run in the deployOptions child object.

Boolean. Defaults to  true. Indicates whether any failure causes a complete rollback
(true) or not (false). If  false, whatever set of actions can be performed without
errors are performed, and errors are returned for the remaining actions. This parameter
must be set to  true  if you’re deploying to a production org.

DateTime. Timestamp for when the deployment process began.

String. Indicates which component is being deployed or which Apex test class is running.

Indicates the current state of the deployment. The valid values are:

- Pending

- InProgress

- FinalizingDeploy

- FinalizingDeployFailed

- Succeeded

- SucceededPartial


REST Resources

Check the Status of Your Deployment Using REST Resources

Parameter

Description

- Failed

- Canceling

- Canceled

success

Boolean. Indicates whether the deployment was successful (true) or not (false).

Check the Status of Your Deployment Using REST Resources

Check the status of your deployment by using passing the deployment request ID in the URL The response body is similar to that returned
by the original deployment request, but it includes information about the deployment in progress.

URI

https://host/services/data/vXX.0/metadata/deployRequest/deployRequestId

To include more details in the response, use:

https://host/services/data/vXX.0/metadata/deployRequest/deployRequestId?includeDetails=true

Formats
JSON

HTTP Method

GET

Authentication

Authorization: Bearer token

Response Body: Deploy Metadata

The following example shows the response when  ?includeDetails=true  is added as a query to the GET request.

{

"id" : "0Afxx00000000lWCAQ"
"url" :

"https://host/services/data/vXX.0/metadata/deployRequest/0Afxx00000000lWCAQ?includeDetails=true",

"deployResult" :

{
"checkOnly" : "false",
"ignoreWarnings" : "false",
"rollbackOnError" : "false",

"status : "InProgress",
"numberComponentsDeployed" : "10",
"numberComponentsTotal" : "1032",
"numberComponentErrors" : "0",
"numberTestsCompleted" : "45",
"numberTestsTotal" : "135",
"numberTestErrors" : "0",
"details" : {

"componentFailures" : [],


REST Resources

Deploy a Recently Validated Component Set Without Tests

"componentSuccesses" : [],

"retrieveResult" : null,
"runTestResults" : {
"numRun" : 0,
"successes" : [ … ],
"failures" : []
}

},

"createdDate" : "2017-10-10T08:22Z",
"startDate" : "2017-10-10T08:22Z",
"lastModifiedDate" : "2017-10-10T08:44Z",
"completedDate" : "2017-10-10T08:44Z",

"errorStatusCode" : null,
"errorMessage" : null,
"stateDetail" : "Processing Type: Apex Component",

"createdBy" : "005xx0000001Sv1m",
"createdByName" : "stephanie stevens",
"canceledBy" : null,
"canceledByName" : null,
"isRunTestsEnabled" : null
}

"deployOptions": {

"allowMissingFiles" : false,
"autoUpdatePackage" : false,
"checkOnly" : true,
"ignoreWarnings" : false,
"performRetrieve" : false,
"purgeOnDelete" : false,
"rollbackOnError" : false,
"runTests" : null,
"singlePackage" : true,
"testLevel" : "RunAllTestsInOrg"
}

}

Expect an HTTP status code of  200  (OK) to be returned.

Deploy a Recently Validated Component Set Without Tests

You can deploy components to production in less time by skipping the execution of Apex tests when testing requirements have already
been met.

- The components have been validated successfully for the target environment within the last 10 days.

- As part of the validation, Apex tests in the target org have passed.

- Code coverage requirements are met.

– If all tests in the org or all local tests are run, overall code coverage is at least 75%, and Apex triggers have some coverage.

– If specific tests are run with the RunSpecifiedTests test level, each class and trigger to be deployed is covered by at least

75% individually.


REST Resources

Deploy a Recently Validated Component Set Without Tests

This operation is equivalent to performing a quick deployment of a recent validation on the Deployment Status page in the Salesforce
user interface.

To validate but not deploy a set of components when using the  deployRequest  resource, set the  checkOnly  parameter of
deployOptions  to  true. Note the deployment request ID in the response. Use this ID (associated with a successful validation)
later to deploy the component set without repeating the validation.

URI

https://host/services/data/vXX.0/metadata/deployRequest/validatedDeployRequestId

Formats
JSON

HTTP Method
POST

Authentication

Authorization: Bearer token

Request Body: Deploy a Recently Validated Component Set Without Tests

Note:  The HTTP method for deploying a recently validated component set is POST, not PATCH. Using PATCH would create a new
deployment.

{

}

"validatedDeployRequestId" : "0Afxx00000000lWCAQ"

If there is no corresponding deployment package that meets the validation requirements, you receive an HTTP status code of 404  (Not
Found). If the validated deployment package is found, the HTTP status code returned is  201 (Created).

Response Body: Deploy a Recently Validated Component Set Without Tests

Note:  The response body from the deployment without validation request includes a new request ID, because it is separate from
the earlier request for a validation-only deployment.

{

"validatedDeployRequestId" : "0Afxx00000000lWCAQ"
"id" : "0Afxx00000000lWMEM"

"url" : "https://host/services/data/vXX.0/metadata/deployRequest/0Afxx00000000lWMEM",

"deployOptions" :

{
"allowMissingFiles" : false,
"autoUpdatePackage" : false,
"checkOnly" : true,
"ignoreWarnings" : false,
"performRetrieve" : false,
"purgeOnDelete" : false,
"rollbackOnError" : false,
"runTests" : null,
"singlePackage" : true,
"testLevel" : "RunAllTestsInOrg"


REST Resources

}

}

Cancel a Deployment in Progress Using REST

When an HTTP status code of  201  (Created) is returned, your request has succeeded and resulted in the creation of a deployment that
is being processed. In the preceding example response body, the ID of the validation-only deployment request is
0Afxx00000000lWCAQ; the ID of the deployment without validation request is  0Afxx00000000lWMEM.

Cancel a Deployment in Progress Using REST

You can request a cancellation of a deployment that's already in progress. Make the cancellation request by patching the status of an
ongoing deployRequest. The cancellation is processed asynchronously. For API versions 65.0 and higher, deployments with a status
of Finalizing Deploy, can't be cancelled. For API versions below 65.0, attempts to cancel a deployment may fail if the deployment
has started committing data. Alternatively, it's possible that the cancellation will succeed, but data from the deployment is also committed.

URI

https://host/services/data/vXX.0/metadata/deployRequest/deployRequestId

Formats
JSON

HTTP Method
PATCH

Authentication

Authorization: Bearer token

Request Body: Request Deployment Cancellation

The JSON request body for a deployment cancellation includes a PATCH to the status of the original  deployRequest.

{

"deployResult":

{
"status" : "Canceling"
}

}

Response Body: Request Deployment Cancellation

Because the cancellation request is processed asynchronously, the status shown in the response body can be either  Canceling  or
Canceled.

{

"id" : "0Afxx00000000lWCAQ"

"url" : “https://host/services/data/vXX.0/metadata/deployRequest/0Afxx00000000lWCAQ",

"deployResult":

{
"checkOnly" : "false",
"ignoreWarnings" : "false",
"rollbackOnError" : "false",
"status : "Canceling", // or Canceled


REST Resources

Deploy Metadata with REST API in Salesforce CLI

"numberComponentsDeployed" : "10",
"numberComponentsTotal" : "1032",
"numberComponentErrors" : "0",
"numberTestsCompleted" : "45",
"numberTestsTotal" : "135",
"numberTestErrors" : "0",
"details" : {

"componentFailures" : [],
"componentSuccesses" : [],

"retrieveResult" : null,
"runTestResults” : {
"numRun" : 0,
"successes" : [ … ],
"failures" : []

}

},

"createdDate" : "2017-10-10T08:22Z",
"startDate" : "2017-10-10T08:22Z",
"lastModifiedDate" : "2017-10-10T08:44Z",
"completedDate" : "2017-10-10T08:44Z",
"errorStatusCode" : null,
"errorMessage" : null,
"stateDetail" : "Processing Type: Apex Component",
"createdBy" : "005xx0000001Sv1m",
"createdByName" : "steve stevens",
"canceledBy" : null,
"canceledByName" : null,
"isRunTestsEnabled" : null
}

}

When an HTTP status code of  202  (Accepted) is returned, your cancellation request is in progress or successful.

Deploy Metadata with REST API in Salesforce CLI

By default, the Salesforce CLI  project deploy start  command uses the Metadata SOAP
API to deploy source to your org. You can use the Metadata REST API instead by setting a CLI
configuration value or environment variable. Compared with SOAP API, REST API offers faster
deployment.

Use the  org-metadata-rest-deploy  Salesforce CLI runtime configuration variable or
SF_ORG_METADATA_REST_DEPLOY  environment variable to set REST API as the default. For
more information, see the Salesforce DX Setup Guide.

This example uses the configuration value to set the default for your current project:

USER PERMISSIONS

To work with Metadata API
from Salesforce CLI:
- Modify Metadata

Through Metadata API
Functions

Or

Modify All Data

sf config set org-metadata-rest-deploy true


REST Resources

Deploy Metadata with REST API in Salesforce CLI

To set the default globally for all your projects, use the  --global  flag:

sf config set org-metadata-rest-deploy true --global

Note:  Only commands that deploy source, such as project deploy start, support REST API. Commands that retrieve source, such
as project retrieve start, always use SOAP API.

Here are the deploy limits. Limits can change without notice.

Feature

Maximum compressed .zip folder size1(SOAP API)

Maximum uncompressed folder size2(SOAP API)

Maximum number of files in AppExchange packages (REST and SOAP API)

Maximum number of files in packages (REST and SOAP API)

Limit

Approximately 39 MB

Approximately 600 MB

35,000

10,000

1 Metadata API base-64 encodes components after they’re compressed. The resulting .zip file can't exceed 50 MB. Base-64 encoding
increases the size of the payload by approximately 22%, so your compressed payload can't exceed approximately 39 MB before encoding.
2 When deploying an unzipped project, all files in the project are compressed first. The maximum size of uncompressed components in
an uncompressed project is 600 MB or less, depending on the files’ compression ratio. If the files have a high compression ratio, you can
migrate a total of approximately 600 MB because the compressed size would be under 39 MB. However, if the components can't be
compressed much, like binary static resources, you can migrate less than 600 MB.


CHAPTER 7

Error Handling

Metadata API calls return error information that your client application can use to identify and resolve runtime errors.

Metadata API provides these types of error handling.

- Since the Metadata API uses the enterprise or partner WSDLs to authenticate, it uses SOAP fault messages defined in those WSDLs
for errors resulting from badly formed messages, failed authentication, or similar problems. Each SOAP fault has an associated
ExceptionCode. For more details, see Error Handling in the SOAP API Developer Guide.

- For errors with the asynchronous create(), update(), and delete() calls, see the error status code in the  statusCode  field in the

AsyncResult object for the associated component.

- For errors with the synchronous CRUD calls, see the error status code in the  statusCode  field of the Error object corresponding

to each error in the array returned by the  errors  field of the appropriate result object. For example, the result object of
createMetadata() is SaveResult.

- For errors with deploy(), see the  problem  and  success  fields in the DeployMessage object for the associated component.

- For errors with retrieve(), see the  problem  field in the RetrieveMessage object for the associated component.

For sample code, see Step 3: Walk Through the Java Sample Code on page 16.

Error Handling for Session Expiration

When you sign on via the  login()  call, a new client session begins and a corresponding unique session ID is generated. Sessions
automatically expire after the amount of time specified in the Security Controls setup area of the Salesforce application (default two
hours). When your session expires, the exception code INVALID_SESSION_ID is returned. If this happens, you must invoke the login()
call again. For more information about  login(), see the SOAP API Developer Guide.


METADATA API CONTEXT MCP TOOL (BETA)


## CHAPTER 8 Quick Start: Metadata API Context MCP Tool

In this chapter ...

- Prerequisites: Set Up
Salesforce Hosted
MCP Servers (Beta)

- 

- 

- 

Step 1: Configure a
MCP Client

Step 2: Test Your
Connection to the
MCP Server

Step 3 [Optional]:
Configure a Rule

The Metadata API Context MCP tool provides contextual information
about Salesforce metadata types to help generate accurate
Salesforce metadata files when working with the Metadata API.

For a given metadata type, this tool gives you:

- complete field definitions

EDITIONS

Available in: Developer,
sandbox, and scratch orgs
that have API enabled.

- valid values

- constraints

- examples

It's a useful resource for creating valid Salesforce metadata XML files when you need to generate them
programmatically, or want to ensure accuracy.

Server Name

Tool Name

Tool Description

Table 1: MCP Details

platform/salesforce-api-context

get_metadata_api_context

Provides contextual information
about Salesforce metadata types
to help generate accurate
Salesforce metadata files. This
tool gives you complete field
definitions, valid values,
constraints, and examples for
metadata types. It is a useful
resource for creating valid
Salesforce metadata files when
you need to generate them
programmatically, or want to
ensure accuracy.

This MCP tool is part of the Salesforce API Context MCP Server, which is hosted in Salesforce.

With this feature, you might make API calls to your org. API usage counts against your org’s API quota.

Metadata API Context MCP Tool is a beta service that is subject to the Beta Services Terms at Agreements
- Salesforce.com or a written Unified Pilot Agreement if executed by Customer, and applicable terms in
the Product Terms Directory. Use of this beta service is at the Customer's sole discretion.


Quick Start: Metadata API Context MCP Tool

Prerequisites: Set Up Salesforce Hosted MCP Servers (Beta)

Prerequisites: Set Up Salesforce Hosted MCP Servers (Beta)

The Salesforce API Context MCP server is one of many Salesforce Hosted MCP Servers. To use the Salesforce API Context MCP server, you
must first set up the Salesforce Hosted MCP Server.

Enable the Beta

To enable this beta, follow these steps as an admin user with the Customize Application permission.

1. From Setup, in the Quick Find box, enter  User Interface, and then select User Interface.

2. On the User Interface page, select Enable MCP Service (Beta), click Save.

3.

(Optional) To enable the Salesforce Hosted MCP Servers beta in a scratch org, first create the org with the SalesforceHostedMCP
feature. See Scratch Org Features.

Note:  Selecting Enable MCP Service (Beta) asserts that you accept the Beta Services Terms provided at the Agreements and
Terms.

Create an External Client App

External client apps enable third-party applications to integrate with Salesforce using APIs and security protocols.

In this Quick Start, we provide the steps to use Cursor as your MCP client. Cursor is an AI-driven coding editor that supports MCP. To use
Cursor as your MCP client, you must install Node.js. After installing Node.js, confirm that your installation was successful by running the
commands  node -v  and  npm -v  from the command line.

1. From Setup, in the Quick Find box, enter  external client, and then select External Client App Manager.

2. Click New External Client App.

3. Fill out the Basic Information section.

4. Expand the section labeled API (Enable OAuth Settings) and click the Enable OAuth checkbox.

5.

In Callback URL, enter http://localhost:8080/oauth/callback.

For other clients, consult the provider’s documentation for the callback URL.

6.

In OAuth Scopes, add the Manage user data via APIs (api), Access the Salesforce API Platform (sfap_api) and Perform
requests at any time (refresh_token, offline_access) scopes. If you’re using prompt templates, add the Access Einstein GPT
services (einstein_gpt_api) scope.

7. Under Security:

a. Select Issue JSON Web Token (JWT)-based access tokens for named users.

b. Select Require Proof Key for Code Exchange (PKCE) extension for Supported Authorization Flows.

c. Deselect all other options.

8. Click Create.

9. Click Settings, then click Consumer Key and Secret under OAuth Settings to get the consumer key.

Store the consumer key for later use.

Important:  Check the Salesforce mcp-hosted repository for the latest updates on the Salesforce Hosted MCP Servers beta.


Quick Start: Metadata API Context MCP Tool

Log Into Your Target Org

Log Into Your Target Org

When you configure your MCP client and initiate its authentication, it will open a web browser to authenticate into your org via OAuth.
To prepare for this, additional steps are sometimes needed for the authentication to succeed. Since the MCP spec doesn't have special
provisions for systems like Salesforce with multiple tenants, we recommend the following steps:

1. Log out of all other Salesforce orgs.

2. Using your default browser, log into the org that you want to access from your MCP client.

This should be the org in which you created the External Client App in the previous section.

3. Keep the browser open, since the MCP client will open a new tab in that browser window in a later step.

Step 1: Configure a MCP Client

Configure a client to connect to MCP servers hosted in your Salesforce org. In this quick start guide, we provide guidance on how to
configure Agentforce Vibes, Cursor, and Claude.

Configure Agentforce Vibes

The Agentforce Vibes extension is an AI-powered developer tool that's available as an easy-to-install Visual Studio Code extension.

1.

Install the Agentforce Vibes VS Code Extension

2. From the VS Code Activity Bar, click the Agentforce icon (

).

3. To open the MCP Servers interface, click the icon (

) in the top-right corner of the Agentforce panel.

The MCP Servers interface is divided into three main tabs:

- Marketplace: Discover and install pre-configured MCP servers (if enabled).

- Remote Servers: Connect to existing MCP servers via URL endpoints.

- Installed: Manage your connected MCP servers.

4.

In the MCP interface, click the Remote Servers tab.

5. To open up the  a4d_mcp_settings.json  file, select Edit Configuration.

6. Update the  a4d_mcp_settings.json  file and include this code.

{

"mcpServers": {

"salesforce-api-context": {

"command": "npx",
"args": [
"-y",
"mcp-remote@0.1.18",

"https://api.salesforce.com/platform/mcp/v1-beta.2/platform/salesforce-api-context",

"8080",
"--static-oauth-client-info",
"{\"client_id\":\"YOUR_CONSUMER_KEY\",\"client_secret\":\"\"}"

]

}


Quick Start: Metadata API Context MCP Tool

Configure Cursor in Developer Mode

}

}

7. Replace placeholder values in the  a4d_mcp_settings.json  file.

a. Replace YOUR_CONSUMER_KEY with the consumer key that you saved from your external client app setup.

Note:  The client_secret is an empty string. Leave this string blank.

b.

If you're connecting to a scratch or sandbox org, change the URL to
https://api.salesforce.com/platform/mcp/v1-beta.2/sandbox/platform/salesforce-api-context.

Agentforce attempts to connect to the server and display the connection status. Verify the connection using the status indicators. For
more details, review the Managed Connected Servers, or the Troubleshoot Connection Issues sections in Connect to Remote MCP Servers
in the Agentforce Vibes Extension Guide.

Configure Cursor in Developer Mode

Cursor is an AI-driven coding editor that supports MCP.

1. Select Cursor > Settings > Cursor Settings > MCP

2. Click New MCP Server.

This creates a file called  mcp.json.

3. Replace the contents of  mcp.json  file with this code.

{

"mcpServers": {

"salesforce-api-context": {

"command": "npx",
"args": [
"-y",
"mcp-remote@0.1.18",

"https://api.salesforce.com/platform/mcp/v1-beta.2/platform/salesforce-api-context",

"8080",
"--static-oauth-client-info",
"{\"client_id\":\"YOUR_CONSUMER_KEY\",\"client_secret\":\"\"}"

]

}

}

}

4. Replace placeholder values in the  mcp.json  file.

a. Replace YOUR_CONSUMER_KEY with the consumer key that you saved from your external client app setup.

Note:  The client_secret is an empty string. Leave this string blank.

b.

If you're connecting to a scratch or sandbox org, change the URL to
https://api.salesforce.com/platform/mcp/v1-beta.2/sandbox/platform/salesforce-api-context.


Quick Start: Metadata API Context MCP Tool

Configure Claude Desktop in Developer Mode

You can now test the client's connection to the MCP server.

1. From Cursor, select Settings, and then select Cursor Settings.

2. From the Cursor Settings page, select MCP & Integrations.

3.

In the MCP Tools section, locate salesforce_api_context. Confirm that get_metadata_api_context  is enabled.

Configure Claude Desktop in Developer Mode

Claude is an AI assistant that you configure to connect to Salesforce Hosted MCP Servers. Configure Claude using a special Claude Desktop
Extensions file.

1. Download salesforce-hosted-mcp-servers.mcpb from this GitHub repository. This is the extension file for Salesforce

Hosted MCP Servers.

2. Double-click the salesforce-hosted-mcp-servers.mcpb file. The Claude desktop client opens and shows the Salesforce

extension.

3. Click Install.

4.

5.

In Server Name, enter  platform/salesforce-api-context.

In Consumer Key, paste the consumer key that you saved from the external client app, then click Save.

A toggle to enable the extension appears.

6. Enable the extension using the toggle.

If you encounter an error, quit and restart Claude.

You can now test the client's connection to the MCP server.

Step 2: Test Your Connection to the MCP Server

Use simple prompts to test your client’s connection to the Salesforce API Context MCP server you configured.

EXAMPLE 1

In your client's chat field, enter the prompt "Query the get_metadata_api_context MCP tool to get the metadata context for the
CustomTab Metadata Type".

The MCP client should respond with information about the CustomTab Metadata Type.

EXAMPLE 2

In your client's chat field, enter the prompt "Can you create a new custom object to track Projects with the following fields: Start Date
(date), End Date (date), and Budget (number). Use the get_metadata_api_context MCP tool as context when creating each metadata
type."

The MCP client should respond with information about the CustomObject and CustomField Metadata Types. The MCP client uses this
context to generate the proper metadata XML files.


Quick Start: Metadata API Context MCP Tool

Step 3 [Optional]: Configure a Rule

Step 3 [Optional]: Configure a Rule

To help the MCP server function optimally, you can create a rule that guides your AI assistant, such as Agentforce Vibes or Cursor Agent,
to call the Metadata API Context MCP tool. An AI rule is a plain-text file like Markdown that provides specific instructions, context, or
constraints to your AI assistant.

Use this example rule to ensure that the Metadata API Context MCP tool is called to provide AI with additional context when generating
metadata XML files. This helps ensure the structural integrity of the metadata XML files generated, and minimize errors during deployment.

# Rule: Metadata Context and XML Structure

**Description:** To guarantee the creation of accurate and deployable Salesforce metadata
files, you must call the get_metadata_api_context MCP tool. This step provides comprehensive
contextual information—including complete field definitions, valid values, and

constraints—that is essential for correctly determining the required entity shape and
creating a valid Metadata XML structure.

**Guidelines:**
- Before generating the XML structure for any Salesforce Metadata Type, the
get_metadata_api_context MCP tool must be called.
- The returned information—which includes field definitions, valid values, constraints,
and examples—must be used to correctly determine the required shape of the entity.
- The resulting Metadata XML structure must strictly adhere to the determined shape to
leverage the complete field definitions and constraints provided by the tool.
- Following these constraints is mandatory to ensure the resulting XML file is valid and
will pass Salesforce validation upon deployment.

For more details about configuring AI rules, see:

- Agentforce Vibes Extension: Agentforce Rules

- Cursor Docs: Rules


REFERENCE


## CHAPTER 9 File-Based Calls

Use file-based calls to deploy or retrieve XML components.

- deploy()

- deployRecentValidation()

- retrieve()

deploy()

Uses file representations of components to create, update, or delete those components in a Salesforce org.

Syntax

AsyncResult = metadatabinding.deploy(base64 zipFile, DeployOptions deployOptions)

Usage

Use this call to take file representations of components and deploy them into an org by creating, updating, or deleting the components
they represent.

Note:  To migrate Data 360 metadata from a sandbox org to a parent sandbox or a production org, use DevOps data kit instead
of this call.

Here are the deploy limits. Limits can change without notice.

Feature

Maximum compressed .zip folder size1

Maximum uncompressed folder size2

Limit

Approximately 39 MB

Approximately 600 MB

Maximum number of files included in a first-generation managed package (1GP). Only
1GP packages that have passed AppExchange Security Review can contain this number
of files.

35,000

Maximum number of files included in an unlocked or second-generation managed
package

10,000

1 Metadata API base-64 encodes components after they’re compressed. The resulting .zip file can't exceed 50 MB. Base-64 encoding
increases the size of the payload by approximately 22%, so your compressed payload can't exceed approximately 39 MB before encoding.


File-Based Calls

deploy()

2The maximum size of uncompressed components in an uncompressed project is 600 MB (629,145,600 bytes) or less, depending on
the files’ compression ratio. The size limit in bytes is calculated as 600 x 1024 x 1024.

If the files have a high compression ratio, you can migrate a total of approximately 600 MB because the compressed size is under 39 MB.
However, if the components can't be compressed much, like binary static resources, you can migrate less than 600 MB.

In API version 29.0, Salesforce improved the deployment status properties and removed the requirement to use  checkStatus()
after a  deploy()  call to get information about deployments. Salesforce continues to support the use of  checkStatus()  when
using  deploy()  with API version 28.0 or earlier.

Deploy Components to an Org

The  package.xml  file is a project manifest that lists all the components that you want to retrieve or deploy. You can use
package.xml  to add components. To delete components, add another manifest file. See Deleting Components from an Organization.

For API version 29.0 or later, here’s how to deploy (create or update) packaged or unpackaged components.

1.

2.

Issue a  deploy()  call to start the asynchronous deployment. An AsyncResult object is returned. Note the value in the id field,
and use it for the next step.

Issue a checkDeployStatus() call in a loop until the done field of the returned DeployResult contains  true, which means
that the call is completed. The DeployResult object contains information about an in-progress or completed deployment started
using the  deploy()  call. When calling checkDeployStatus(), pass in the id value from the AsyncResult object from the
first step.

For API version 28.0 or earlier, here’s how to deploy (create or update) packaged or unpackaged components.

1.

2.

Issue a deploy()  call to start the asynchronous deployment. An AsyncResult object is returned. If the call is completed, the done
field contains  true. Most often, the call isn’t completed quickly enough to be noted in the first result. If it’s completed, note the
value in the id field returned, and skip the next step.

If the call isn’t complete, issue a checkStatus() call in a loop. In the loop, use the value in the id field of the AsyncResult object
returned by the deploy()  call in the previous step. Check the AsyncResult object, which is returned until the done field contains
true. The time taken to complete a  deploy()  call depends on the size of the zip file being deployed. Therefore, use a longer
wait time between iterations as the size of the zip file increases.

3.

Issue a checkDeployStatus() call to obtain the results of the  deploy()  call, using the id value returned in the first step.

Note: The deployment process locks write-access to resources getting deployed until deployment completes. During deployment,
changes made to locked resources or related items can result in errors. Salesforce recommends deployments during off-peak
usage time and limiting or postponing changes to your org while deployment is in progress.

Check the Status of a Deployment

Check the status of a deployment using Metadata API or from Setup. You can check the status of deployments that are in progress or
completed in the last 30 days.

To check the status of a deployment using Metadata API, see checkDeployStatus() on page 76.

To check the status of a deployment from Setup, enter  Deployment Status  in the Quick Find box, then select Deployment
Status.

When running a deployment, the Deployment Status page shows you the real-time progress of your current deployment. This page
contains charts that provide a visual representation of the overall deployment progress. The first chart shows how many components
have been deployed out of the total and includes the number of components with errors. For example, this chart indicates that 302
components were processed successfully out of 450 and there were 45 components with errors.


File-Based Calls

deploy()

After all components have been deployed without errors, Apex tests start running, if necessary or enabled. A second chart shows how
many Apex tests have run out of the total number of tests and the number of errors returned. In addition, the chart shows the name of
the currently running test. For example, in this chart, 77 tests have completed execution out of a total of 120, and 1 test failed.

You can initiate multiple deployments, but only one deployment can run at a time. The other deployments remain in the queue waiting
to run after the current deployment finishes. Queued deployments are listed under Pending Deployments and are not necessarily
executed in the order in which they were submitted. To execute deployments in a particular order, submit them one at a time after the
previous deployment has completed successfully.

Cancel a Deployment

Cancel a deployment using the Metadata API or from Setup. You can cancel a deployment while it’s in progress or in the queue. For API
versions 65.0 and higher, you can't cancel deployments with a status of Finalizing Deploy. For API versions below 65.0, attempts
to cancel a deployment may fail if the deployment has started committing data. Alternatively, it's possible that the cancellation will
succeed, but data from the deployment is also committed.

To cancel a deployment using Metadata API, see cancelDeploy().

To cancel a deployment from Setup, enter  Deployment Status  in the quick find box, then select Deployment Status. Click
Cancel next to the deployment you want to cancel. The deployment has the status of  Cancel Requested until the cancellation
completes. A canceled deployment is listed in the Failed section.

Permissions

Your client application must be logged in with the Modify Metadata Through Metadata API Functions or Modify All Data permission.

Note:  If a user requires access to metadata but not to data, enable the Modify Metadata Through Metadata API Functions
permission. Otherwise, enable the Modify All Data permission.


File-Based Calls

deploy()

Arguments

Name

zipFile

Type

base64

Description

Base 64-encoded binary data. Client applications must encode the binary data as base64.

deployOptions

DeployOptions

Encapsulates options for determining which packages or files are deployed.

DeployOptions

The following deployment options can be selected for this call:

Name

Type

Description

allowMissingFiles

boolean

autoUpdatePackage

boolean

checkOnly

boolean

If files that are specified in package.xml aren’t in the .zip
file, specifies whether a deployment can still succeed.

Don’t set this argument for deployment to production orgs.

If a file is in the .zip file but not specified in package.xml,
specifies whether the file is automatically added to the package.
A retrieve()  is issued with the updated package.xml
that includes the  .zip  file.

Don’t set this argument for deployment to production orgs.

Defaults to false. Set to true  to perform a test deployment
(validation) of components without saving the components
in the target org. A validation enables you to verify the results
of tests that would be generated in a deployment, but doesn’t
commit any changes. After a validation finishes with passing
tests, sometimes it can qualify for deployment without
rerunning tests. See deployRecentValidation().

If you change a field type from Master-Detail to Lookup or vice
versa, the change isn’t supported when using the
checkOnly  option to test a deployment. This change isn’t
supported for test deployments to avoid permanently altering
your data. If a change that isn’t supported for test deployments
is included in a deployment package, the test deployment fails
and issues an error.

If your deployment package changes a field type from
Master-Detail to Lookup or vice versa, you can still validate the
changes before you deploy to production. Perform a full
deployment to another test sandbox. A full deployment
includes a validation of the changes as part of the deployment
process.

A Metadata API deployment that includes Master-Detail
relationships deletes all detail records in the Recycle Bin in the
following cases.


File-Based Calls

deploy()

Name

Type

Description

ignoreWarnings

boolean

performRetrieve

boolean

purgeOnDelete

boolean

1. For a deployment with a new Master-Detail field, soft delete

(send to the Recycle Bin) all detail records before
proceeding to deploy the Master-Detail field, or the
deployment fails. During the deployment, detail records
are permanently deleted from the Recycle Bin and can’t
be recovered.

2. For a deployment that converts a Lookup field relationship

to a Master-Detail relationship, detail records must
reference a master record or be soft-deleted (sent to the
Recycle Bin) for the deployment to succeed. However, a
successful deployment permanently deletes any detail
records in the Recycle Bin.

Indicates whether deployments with warnings complete
successfully (true) or not (false). Defaults to  false.

The DeployMessage object for a warning contains the following
values:

- problemType—Warning

- problem—The text of the warning

If a warning occurs and ignoreWarnings is set to true,
the  success  field in DeployMessage is  true. If
ignoreWarnings  is set to  false,  success  is set to
false  and the warning is treated like an error.

This field is available in API version 18.0 and later. Before version
18.0, there was no distinction between warnings and errors.
All problems were treated as errors and prevented a successful
deployment.

Indicates whether a  retrieve()  call is performed
immediately after the deployment (true) or not (false).
Set to  true  to retrieve whatever was deployed.

If  true, the deleted components in the
destructiveChanges.xml  manifest file aren't stored
in the Recycle Bin. Instead, they become immediately eligible
for deletion.

This field is available in API version 22.0 and later.

This option only works in Developer Edition or sandbox orgs.
It doesn’t work in production orgs.

When you delete a roll-up summary field using Metadata API,
the field isn't saved in the Recycle Bin. The field is purged even
if you don’t set the  purgeOnDelete  deployment option
to  true.


File-Based Calls

deploy()

Name

rollbackOnError

Type

boolean

runAllTests

boolean

runTests

string[]

singlePackage

boolean

testLevel

TestLevel (enumeration of type
string)

Description

Indicates whether any failure causes a complete rollback
(true) or not (false). If  false, whatever actions can be
performed without errors are performed, and errors are
returned for the remaining actions. This parameter must be
set to  true  if you’re deploying to a production org. The
default is  false.

(Deprecated and only available in API version 33.0 and earlier.)
This field defaults to false. Set to true  to run all Apex tests
after deployment, including tests that originate from installed
managed packages.

Apex tests that run as part of a deployment always run
synchronously and serially.

A list of Apex tests to run during deployment. Specify the class
name, one name per instance. The class name can also specify
a namespace with a dot notation. For more information, see
Running a Subset of Tests in a Deployment.

To use this option, set  testLevel  to
RunSpecifiedTests.

Indicates whether the specified .zip  file points to a directory
structure with a single package (true) or a set of packages
(false).

Optional. Specifies which tests are run as part of a deployment.
The test level is enforced regardless of the types of components
that are present in the deployment package. Valid values are:

- NoTestRun—No tests are run. This test level applies

only to deployments to development environments, such
as sandbox, Developer Edition, or trial organizations. This
test level is the default for development environments.

- RunSpecifiedTests—Only the tests that you specify

in the  runTests  option are run. Code coverage
requirements differ from the default coverage requirements
when using this test level. Each class and trigger in the
deployment package must be covered by the executed
tests for a minimum of 75% code coverage. This coverage
is computed for each class and trigger individually and is
different than the overall coverage percentage.

- RunRelevantTests  (beta)—Only tests relevant to
the deployment payload are run. Salesforce automatically
identifies the relevant tests based on an analysis of the
deployment payload and the payload dependencies. For
fine-grained control, you can annotate test classes so that
they either run regardless of the deployment payload, or
run when modified, referenced components are included


File-Based Calls

deploy()

Name

Type

Description

in the deployment. See @IsTest Annotation in the Apex
Developer Guide. Each class and trigger in the deployment
package must be covered by the executed tests for a
minimum of 75% code coverage. This coverage is
computed for each class and trigger individually and is
different from the overall coverage percentage.

- RunLocalTests—All tests in your org are run, except
the ones that originate from installed managed and
unlocked packages. This test level is the default for
production deployments that include Apex classes or
triggers.

- RunAllTestsInOrg—All tests are run. The tests

include all tests in your org, including tests of managed
packages.

If you don’t specify a test level, the default test execution
behavior is used. See Running Tests in a Deployment.

Apex tests that run as part of a deployment always run
synchronously and serially.

This field is available in API version 34.0 and later.

Response

AsyncResult

Sample Code—Java

This sample shows how to deploy components in a zip file. See the retrieve() sample code for details on how to retrieve a zip file.

package com.doc.samples;

import java.io.*;

import java.rmi.RemoteException;

import com.sforce.soap.metadata.AsyncResult;
import com.sforce.soap.metadata.DeployDetails;
import com.sforce.soap.metadata.MetadataConnection;
import com.sforce.soap.metadata.DeployOptions;
import com.sforce.soap.metadata.DeployResult;
import com.sforce.soap.metadata.DeployMessage;
import com.sforce.soap.metadata.RunTestsResult;
import com.sforce.soap.metadata.RunTestFailure;
import com.sforce.soap.metadata.CodeCoverageWarning;
import com.sforce.soap.enterprise.LoginResult;
import com.sforce.soap.enterprise.EnterpriseConnection;
import com.sforce.ws.ConnectionException;


File-Based Calls

deploy()

import com.sforce.ws.ConnectorConfig;

/**

* Deploy a zip file of metadata components.
* Prerequisite: Have a deploy.zip file that includes a package.xml manifest file that
* details the contents of the zip file.
*/

public class DeploySample {

// binding for the metadata WSDL used for making metadata API calls
private MetadataConnection metadataConnection;

static BufferedReader rdr = new BufferedReader(new InputStreamReader(System.in));

private static final String ZIP_FILE = "deploy.zip";

// one second in milliseconds
private static final long ONE_SECOND = 1000;
// maximum number of attempts to deploy the zip file
private static final int MAX_NUM_POLL_REQUESTS = 50;

public static void main(String[] args) throws Exception {

final String USERNAME = "user@company.com";
// This is only a sample. Hard coding passwords in source files is a bad practice.

final String PASSWORD = "password";
final String URL = "https://login.salesforce.com/services/Soap/c/29.0";

DeploySample sample = new DeploySample(USERNAME, PASSWORD, URL);
sample.deployZip();

}

public DeploySample(String username, String password, String loginUrl)

throws ConnectionException {

createMetadataConnection(username, password, loginUrl);

}

public void deployZip()

throws RemoteException, Exception

{

byte zipBytes[] = readZipFile();
DeployOptions deployOptions = new DeployOptions();
deployOptions.setPerformRetrieve(false);
deployOptions.setRollbackOnError(true);
AsyncResult asyncResult = metadataConnection.deploy(zipBytes, deployOptions);
String asyncResultId = asyncResult.getId();

// Wait for the deploy to complete
int poll = 0;
long waitTimeMilliSecs = ONE_SECOND;
DeployResult deployResult = null;
boolean fetchDetails;
do {

Thread.sleep(waitTimeMilliSecs);
// double the wait time for the next iteration


File-Based Calls

deploy()

waitTimeMilliSecs *= 2;
if (poll++ > MAX_NUM_POLL_REQUESTS) {

throw new Exception("Request timed out. If this is a large set " +

"of metadata components, check that the time allowed by " +
"MAX_NUM_POLL_REQUESTS is sufficient.");

}

// Fetch in-progress details once for every 3 polls
fetchDetails = (poll % 3 == 0);

deployResult = metadataConnection.checkDeployStatus(asyncResultId, fetchDetails);

System.out.println("Status is: " + deployResult.getStatus());
if (!deployResult.isDone() && fetchDetails) {

printErrors(deployResult, "Failures for deployment in progress:\n");

}

}
while (!deployResult.isDone());

if (!deployResult.isSuccess() && deployResult.getErrorStatusCode() != null) {

throw new Exception(deployResult.getErrorStatusCode() + " msg: " +

deployResult.getErrorMessage());

}

if (!fetchDetails) {

// Get the final result with details if we didn't do it in the last attempt.
deployResult = metadataConnection.checkDeployStatus(asyncResultId, true);

}

if (!deployResult.isSuccess()) {

printErrors(deployResult, "Final list of failures:\n");
throw new Exception("The files were not successfully deployed");

}

System.out.println("The file " + ZIP_FILE + " was successfully deployed");

}

/**

* Read the zip file contents into a byte array.
* @return byte[]
* @throws Exception - if cannot find the zip file to deploy
*/

private byte[] readZipFile()

throws Exception

{

// We assume here that you have a deploy.zip file.
// See the retrieve sample for how to retrieve a zip file.
File deployZip = new File(ZIP_FILE);
if (!deployZip.exists() || !deployZip.isFile())

throw new Exception("Cannot find the zip file to deploy. Looking for " +

deployZip.getAbsolutePath());

FileInputStream fos = new FileInputStream(deployZip);
ByteArrayOutputStream bos = new ByteArrayOutputStream();
int readbyte = -1;


File-Based Calls

deploy()

while ((readbyte = fos.read()) != -1) {

bos.write(readbyte);

}
fos.close();
bos.close();
return bos.toByteArray();

}

/**

* Print out any errors, if any, related to the deploy.
* @param result - DeployResult
*/

private void printErrors(DeployResult result, String messageHeader)
{

DeployDetails deployDetails = result.getDetails();

StringBuilder errorMessageBuilder = new StringBuilder();
if (deployDetails != null) {

DeployMessage[] componentFailures = deployDetails.getComponentFailures();
for (DeployMessage message : componentFailures) {

String loc = (message.getLineNumber() == 0 ? "" :

("(" + message.getLineNumber() + "," +

message.getColumnNumber() + ")"));

if (loc.length() == 0

&& !message.getFileName().equals(message.getFullName())) {

loc = "(" + message.getFullName() + ")";

}
errorMessageBuilder.append(message.getFileName() + loc + ":" +

message.getProblem()).append('\n');

}
RunTestsResult rtr = deployDetails.getRunTestResult();
if (rtr.getFailures() != null) {

for (RunTestFailure failure : rtr.getFailures()) {

String n = (failure.getNamespace() == null ? "" :

(failure.getNamespace() + ".")) + failure.getName();

errorMessageBuilder.append("Test failure, method: " + n + "." +

failure.getMethodName() + " -- " +
failure.getMessage() + " stack " +
failure.getStackTrace() + "\n\n");

}

}
if (rtr.getCodeCoverageWarnings() != null) {

for (CodeCoverageWarning ccw : rtr.getCodeCoverageWarnings()) {

errorMessageBuilder.append("Code coverage issue");
if (ccw.getName() != null) {

String n = (ccw.getNamespace() == null ? "" :

(ccw.getNamespace() + ".")) + ccw.getName();

errorMessageBuilder.append(", class: " + n);

}
errorMessageBuilder.append(" -- " + ccw.getMessage() + "\n");

}

}

}


File-Based Calls

Deleting Components from an Organization

if (errorMessageBuilder.length() > 0) {

errorMessageBuilder.insert(0, messageHeader);
System.out.println(errorMessageBuilder.toString());

}

}

private void createMetadataConnection(

final String username,
final String password,
final String loginUrl) throws ConnectionException {

final ConnectorConfig loginConfig = new ConnectorConfig();
loginConfig.setAuthEndpoint(loginUrl);
loginConfig.setServiceEndpoint(loginUrl);
loginConfig.setManualLogin(true);
LoginResult loginResult = (new EnterpriseConnection(loginConfig)).login(

username, password);

final ConnectorConfig metadataConfig = new ConnectorConfig();
metadataConfig.setServiceEndpoint(loginResult.getMetadataServerUrl());
metadataConfig.setSessionId(loginResult.getSessionId());
this.metadataConnection = new MetadataConnection(metadataConfig);

}

}

1. Deleting Components from an Organization

To delete components, perform a deployment with the  deploy()  call by using a destructive changes manifest file that lists the
components to remove from your organization. You can perform a deployment that only deletes components, or a deployment
that deletes and adds components. In API version 33.0 and later, you can specify components to delete before and after other
components are added or updated. In earlier API versions, if deletions and additions are specified for the same deployment, the
deploy()  call performs the deletions first.

2.

3.

checkDeployStatus()
Checks the status of declarative metadata call  deploy().

cancelDeploy()
Cancels a deployment that hasn’t completed yet.

SEE ALSO:

Running Tests in a Deployment

Run Relevant Apex Tests in a Deployment (Beta)

Deleting Components from an Organization

To delete components, perform a deployment with the  deploy()  call by using a destructive changes manifest file that lists the
components to remove from your organization. You can perform a deployment that only deletes components, or a deployment that
deletes and adds components. In API version 33.0 and later, you can specify components to delete before and after other components
are added or updated. In earlier API versions, if deletions and additions are specified for the same deployment, the  deploy()  call
performs the deletions first.


File-Based Calls

Deleting Components from an Organization

Deleting Components in a Deployment

To delete components, use the same procedure as with deploying components, but also include a delete manifest file that’s named
destructiveChanges.xml  and list the components to delete in this manifest. The format of this manifest is the same as
package.xml  except that wildcards aren’t supported.

Note:  You can’t use  destructiveChanges.xml  to delete items that are associated with an active Lightning page, such
as a custom object, a component on the page, or the page itself. First, you must remove the page's action override by deactivating
it in the Lightning App Builder.

The following sample  destructiveChanges.xml  file names a single custom object to be deleted:

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>MyCustomObject__c</members>
<name>CustomObject</name>

</types>

</Package>

To deploy the destructive changes, you must also have a  package.xml  file that lists no components to deploy, includes the API
version, and is in the same directory as  destructiveChanges.xml:

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<version>66.0</version>

</Package>

Note:

- To bypass the Recycle Bin, set the purgeOnDelete option to  true.

- When you delete a roll-up summary field using Metadata API, the field isn't saved in the Recycle Bin. The field is purged even

if you don’t set the  purgeOnDelete  deployment option to  true.

- If you try to delete some components that don’t exist in the organization, the rest of the deletions are still attempted.

Adding and Deleting Components in a Single Deployment

You can perform a deployment that specifies components to delete in  destructiveChanges.xml  and components to add or
update in package.xml. The process is the same as with performing a delete-only deployment except that package.xml contains
the components to add or update.

By default, deletions are processed before component additions. In API version 33.0 and later, you can specify components to be deleted
before and after component additions. The process is the same as with performing a delete-only deployment except that the name of
the deletion manifest file is different.

- To delete components before adding or updating other components, create a manifest file that’s named

destructiveChangesPre.xml  and include the components to delete.

- To delete components after adding or updating other components, create a manifest file that’s named

destructiveChangesPost.xml  and include the components to delete.

The ability to specify when deletions are processed is useful when you’re deleting components with dependencies. For example, if a
custom object is referenced in an Apex class, you can’t delete it unless you modify the Apex class first to remove the dependency on
the custom object. In this example, you can perform a single deployment that updates the Apex class to clear the dependency and then


File-Based Calls

checkDeployStatus()

deletes the custom object by using  destructiveChangesPost.xml. The following are samples of the  package.xml  and
destructiveChangesPost.xml  manifests that would be used in this example.

Sample  package.xml, which specifies the class to update:

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>SampleClass</members>
<name>ApexClass</name>

</types>
<version>66.0</version>

</Package>

Sample  destructiveChangesPost.xml, which specifies the custom object to delete after the class update:

<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">

<types>

<members>MyCustomObject__c</members>
<name>CustomObject</name>

</types>

</Package>

Post destructive changes are processed before running any tests.

When deleting Apex classes or triggers, Salesforce recommends that as part of the deployment, you run all local tests from the namespace
in order to detect any remaining references to the deleted class or trigger.

Note:  The API version that the deployment uses is the API version that’s specified in  package.xml.

checkDeployStatus()

Checks the status of declarative metadata call  deploy().

Syntax

DeployResult = metadatabinding.checkDeployStatus(ID id, includeDetails boolean);

Usage

checkDeployStatus  is used as part of the process for deploying packaged or unpackaged components to an organization:

1.

2.

Issue a  deploy()  call to start the asynchronous deployment. An AsyncResult object is returned. Note the value in the id field,
and use it for the next step.

Issue a checkDeployStatus() call in a loop until the done field of the returned DeployResult contains  true, which means
that the call is completed. The DeployResult object contains information about an in-progress or completed deployment started
using the  deploy()  call. When calling checkDeployStatus(), pass in the id value from the AsyncResult object from the
first step.

In API version 29.0, Salesforce improved the deployment status properties and removed the requirement to use  checkStatus()
after a  deploy()  call to get information about deployments. Salesforce continues to support the use of  checkStatus()  when
using  deploy()  with API version 28.0 or earlier.


File-Based Calls

cancelDeploy()

Sample Code—Java

See the deploy()  sample code for sample usage of this call.

Arguments

Name

id

Type

ID

includeDetails

boolean

Response

DeployResult

Description

ID obtained from an AsyncResult object returned by deploy() or a subsequent checkStatus() call.

Sets the DeployResult object to include DeployDetails information ((true) or not (false).
The default is  false. Available in API version 29.0 and later.

cancelDeploy()

Cancels a deployment that hasn’t completed yet.

Syntax

CancelDeployResult = metadatabinding.cancelDeploy(string id)

Usage

Use the cancelDeploy()  operation to cancel a deployment in your org started by the deploy() operation, which includes deployments
started by the Lightning Platform Migration Tool and the Lightning Platform IDE. The deployment can be in a queue waiting to get
started, or can be in progress. For API versions 65.0 and higher, deployments with a status of  Finalizing Deploy, can't be
cancelled. For API versions below 65.0, attempts to cancel a deployment may fail if the deployment has started committing data.
Alternatively, it's possible that the cancellation will succeed, but data from the deployment is also committed.

This operation takes the ID of the deployment you want to cancel and returns a CancelDeployResult object. When the deployment is in
the queue and hasn’t started yet, calling cancelDeploy()  cancels the deployment immediately. When the deployment has started
and is in progress, sometimes it doesn’t get canceled immediately, so call checkDeployStatus() to check the status of the cancellation.

Cancel a deployment using these steps.

1. Obtain the ID of the deployment you want to cancel. For example, you can obtain the ID from the deploy() call in the AsyncResult
object id field. Alternatively, you can obtain the ID in the Salesforce user interface from Setup by entering Deployment Status
in the  Quick Find  box, selecting Deployment Status, and then noting the ID of a deployment started by the API.

2.

Issue a  cancelDeploy()  call to start the cancellation process. This call returns a  CancelDeployResult  object.

3. Check the value in the  done  field of the returned  CancelDeployResult. If the  done  field value is  true, the deployment
has been canceled and you’re done. If the  done  field value is  false, the cancellation is in progress. To check the cancellation
status, follow these steps.

a. Call checkDeployStatus() using the deployment ID you obtained earlier.


File-Based Calls

cancelDeploy()

b.

In the returned DeployResult object, check the  status  field. If the status is  Canceling, the cancellation is still in progress,
and repeat steps a and b. Otherwise, if the status is  Canceled, the deployment has been canceled and you’re done.

The  deploy()  operation throws these API faults.

INVALID_ID_FIELD with the message  Invalid deploy ID

The specified ID argument doesn't correspond to a valid deployment.

INVALID_ID_FIELD with the message  Deployment already completed

The specified deployment has already completed.

INVALID_ID_FIELD with the message  You cannot cancel the deployment while finalizing is in
progress

The specified deployment can't be canceled. Applies to API version 65.0 and later.

Version

Available in API version 30.0 and later.

Permissions

Your client application must be logged in with the Modify Metadata Through Metadata API Functions or Modify All Data permission.

Note:  If a user requires access to metadata but not to data, enable the Modify Metadata Through Metadata API Functions on
page 7 permission. Otherwise, enable the Modify All Data permission.

Arguments

Name

id

Type

string

Description

The ID of the deployment to cancel.

Response

CancelDeployResult

Sample Code—Java

This sample shows how to cancel a deployment. The sample calls  cancelDeploy()  by passing it a given deployment ID. Next, it
checks whether the cancellation has completed, and if not, calls  checkDeployStatus  in a loop.

public void cancelDeploy(String asyncId) throws Exception {

// Issue the deployment cancellation request
CancelDeployResult result = metadataConnection.cancelDeploy(asyncId);

// If the deployment cancellation completed, write a message to the output.
if (result.isDone()) {

System.out.println("Your deployment was canceled successfully!");

}
else {

// The deployment cancellation is still in progress, so get a new status
DeployResult deployResult = metadataConnection.checkDeployStatus(asyncId, false);


File-Based Calls

deployRecentValidation()

// Check whether the deployment is done. If not done, this means
// that the cancellation is still in progress and the status is Canceling.

while (!deployResult.isDone()) {

// Assert that the deployment status is Canceling
assert deployResult.getStatus() == DeployStatus.Canceling;
// Wait 2 seconds
Thread.sleep(2000);
// Get the deployment status again
deployResult = metadataConnection.checkDeployStatus(asyncId, false);

}

// The deployment is done. Write the status to the output.
// (When the deployment is done, the cancellation should have completed
// and the status should be Canceled. However, in very rare cases,
// the deployment can complete before it is canceled.)
System.out.println("Final deploy status = >" + deployResult.getStatus());

}

}

deployRecentValidation()

Deploys a recently validated component set without running Apex tests.

Syntax

string = metadatabinding.deployRecentValidation(ID validationID)

Usage

Use  deployRecentValidation()  to deploy your components to production in less time by skipping the execution of Apex
tests. Ensure that the following requirements are met before deploying a recent validation.

- The components have been validated successfully for the target environment within the last 10 days.

- As part of the validation, Apex tests in the target org have passed.

- Code coverage requirements are met.

– If all tests in the org or all local tests are run, overall code coverage is at least 75%, and Apex triggers have some coverage.

– If specific tests are run with the  RunSpecifiedTests  test level, each class and trigger that was deployed is covered by at

least 75% individually.

This call is equivalent to performing a quick deployment of a recent validation on the Deployment Status page in the Salesforce user
interface.

Before you call  deployRecentValidation(), your organization must have a validation that was recently run. You can run a
validation on a set of components by calling deploy() with the  checkOnly  property of the  deployOptions  parameter set to
true. Note the ID that you obtained from the  deploy()  call. You’ll use this ID for the  deployRecentValidation()  call in
the next step.


File-Based Calls

deployRecentValidation()

After you’ve run a validation successfully, use these steps to quick-deploy the validation to the same target environment.

1. To start an asynchronous quick deployment, call deployRecentValidation()  and pass it the ID of a recent validation. This
ID is obtained from the previous deploy() call. The deployRecentValidation()  call returns the ID of the quick deployment.
Note this value. You’ll use it in the next step.

2. Check for the completion of the call. This process is similar to that of deploy(). Issue a checkDeployStatus() call in a loop until the

done field of the returned DeployResult contains  true, which means that the call is completed. The DeployResult object contains
information about an in-progress or completed deployment that was started by using the  deployRecentValidation()
call. When calling checkDeployStatus(), pass in the ID value that you obtained in the first step.

Version

Available in API version 33.0 and later.

Arguments

Name

Type

Description

validationID

string

The ID of a recent validation.

Response

Type: string

The ID of the quick deployment.

Sample Code—Java

package com.salesforce.test.metadata;

import java.rmi.RemoteException;

import com.sforce.soap.metadata.CodeCoverageWarning;
import com.sforce.soap.metadata.DeployDetails;
import com.sforce.soap.metadata.DeployMessage;
import com.sforce.soap.metadata.DeployResult;
import com.sforce.soap.metadata.MetadataConnection;
import com.sforce.soap.metadata.RunTestFailure;
import com.sforce.soap.metadata.RunTestsResult;
import com.sforce.soap.partner.Connector;
import com.sforce.ws.ConnectionException;
import com.sforce.ws.ConnectorConfig;

/**

* Quick-deploy a recent validation.
* Prerequisite: A successful validation (check-only deploy) has been done in the org

recently.

*/

public class DeployRecentValidationSample {

// binding for the metadata WSDL used for making metadata API calls


File-Based Calls

deployRecentValidation()

private MetadataConnection metadataConnection;

// one second in milliseconds
private static final long ONE_SECOND = 1000;
// maximum number of attempts to deploy the zip file
private static final int MAX_NUM_POLL_REQUESTS = 50;

public static void main(String[] args) throws Exception {

final String USERNAME = args[0];
final String PASSWORD = args[1];
final String URL = args[2];

final String recentValidationId = args[3];

DeployRecentValidationSample sample = new DeployRecentValidationSample(

sample.deployRecentValidation(recentValidationId);

USERNAME, PASSWORD, URL);

}

public DeployRecentValidationSample(String username, String password, String loginUrl)

throws ConnectionException {

createMetadataConnection(username, password, loginUrl);

}

public void deployRecentValidation(String recentValidationId)

throws RemoteException, Exception

{

String asyncResultId = metadataConnection.deployRecentValidation(recentValidationId);

// Wait for the deploy to complete
int poll = 0;
long waitTimeMilliSecs = ONE_SECOND;
DeployResult deployResult = null;
boolean fetchDetails;
do {

Thread.sleep(waitTimeMilliSecs);
// double the wait time for the next iteration
waitTimeMilliSecs *= 2;
if (poll++ > MAX_NUM_POLL_REQUESTS) {

throw new Exception("Request timed out. If this is a large set " +

"of metadata components, check that the time allowed by " +
"MAX_NUM_POLL_REQUESTS is sufficient.");

}

// Fetch in-progress details once for every 3 polls
fetchDetails = (poll % 3 == 0);

deployResult = metadataConnection.checkDeployStatus(asyncResultId, fetchDetails);

System.out.println("Status is: " + deployResult.getStatus());
if (!deployResult.isDone() && fetchDetails) {

printErrors(deployResult, "Failures for deployment in progress:\n");

}


File-Based Calls

deployRecentValidation()

}
while (!deployResult.isDone());

if (!deployResult.isSuccess() && deployResult.getErrorStatusCode() != null) {

throw new Exception(deployResult.getErrorStatusCode() + " msg: " +

deployResult.getErrorMessage());

}

if (!fetchDetails) {

// Get the final result with details if we didn't do it in the last attempt.
deployResult = metadataConnection.checkDeployStatus(asyncResultId, true);

}

if (!deployResult.isSuccess()) {

printErrors(deployResult, "Final list of failures:\n");
throw new Exception("The files were not successfully deployed");

}

System.out.println("The recent validation " + recentValidationId +

" was successfully deployed");

}

/**

* Print out any errors, if any, related to the deploy.
* @param result - DeployResult
*/

private void printErrors(DeployResult result, String messageHeader)
{

DeployDetails deployDetails = result.getDetails();

StringBuilder errorMessageBuilder = new StringBuilder();
if (deployDetails != null) {

DeployMessage[] componentFailures = deployDetails.getComponentFailures();
for (DeployMessage message : componentFailures) {

String loc = (message.getLineNumber() == 0 ? "" :

("(" + message.getLineNumber() + "," +

message.getColumnNumber() + ")"));

if (loc.length() == 0

&& !message.getFileName().equals(message.getFullName())) {

loc = "(" + message.getFullName() + ")";

}
errorMessageBuilder.append(message.getFileName() + loc + ":" +

message.getProblem()).append('\n');

}
RunTestsResult rtr = deployDetails.getRunTestResult();
if (rtr.getFailures() != null) {

for (RunTestFailure failure : rtr.getFailures()) {

String n = (failure.getNamespace() == null ? "" :

(failure.getNamespace() + ".")) + failure.getName();

errorMessageBuilder.append("Test failure, method: " + n + "." +

failure.getMethodName() + " -- " +
failure.getMessage() + " stack " +
failure.getStackTrace() + "\n\n");

}


File-Based Calls

retrieve()

}
if (rtr.getCodeCoverageWarnings() != null) {

for (CodeCoverageWarning ccw : rtr.getCodeCoverageWarnings()) {

errorMessageBuilder.append("Code coverage issue");
if (ccw.getName() != null) {

String n = (ccw.getNamespace() == null ? "" :

(ccw.getNamespace() + ".")) + ccw.getName();

errorMessageBuilder.append(", class: " + n);

}
errorMessageBuilder.append(" -- " + ccw.getMessage() + "\n");

}

}

}

if (errorMessageBuilder.length() > 0) {

errorMessageBuilder.insert(0, messageHeader);
System.out.println(errorMessageBuilder.toString());

}

}

private void createMetadataConnection(

final String username,
final String password,
final String loginUrl) throws ConnectionException {

final ConnectorConfig loginConfig = new ConnectorConfig();
loginConfig.setUsername(username);
loginConfig.setPassword(password);
loginConfig.setAuthEndpoint(loginUrl);

Connector.newConnection(loginConfig);

final ConnectorConfig metadataConfig = new ConnectorConfig();
metadataConfig.setServiceEndpoint(

loginConfig.getServiceEndpoint().replace("/u/", "/m/"));

metadataConfig.setSessionId(loginConfig.getSessionId());
this.metadataConnection = com.sforce.soap.metadata.Connector.

newConnection(metadataConfig);

}

}

retrieve()

The  retrieve()  call retrieves XML file representations of components in an organization.

Syntax

AsyncResult = metadatabinding.retrieve(RetrieveRequest)


File-Based Calls

Usage

retrieve()

Use this call to retrieve file representations of components in an organization.

Here are the deploy limits. Limits can change without notice.

Feature

Maximum compressed .zip folder size1

Maximum uncompressed folder size2

Maximum number of files in AppExchange packages

Maximum number of files in packages

Limit

Approximately 39 MB

Approximately 600 MB

35,000

10,000

Note:  You can perform a retrieve() call for a big object only if its index is defined. If a big object is created in Setup and doesn’t
yet have an index defined, you can’t retrieve it.

1 Metadata API base-64 encodes components after they’re compressed. The resulting .zip file can't exceed 50 MB. Base-64 encoding
increases the size of the payload by approximately 22%, so your compressed payload can't exceed approximately 39 MB before encoding.
2 When deploying an unzipped project, all files in the project are compressed first. The maximum size of uncompressed components in
an uncompressed project is 600 MB or less, depending on the files’ compression ratio. If the files have a high compression ratio, you can
migrate a total of approximately 600 MB because the compressed size would be under 39 MB. However, if the components can't be
compressed much, like binary static resources, you can migrate less than 600 MB.

In API version 31.0 and later, the process of making a  retrieve()  call has been simplified. You no longer have to call checkStatus()
after a retrieve()  call to obtain the status of the retrieve operation. Instead, make calls to checkRetrieveStatus() only. If the retrieve
operation is in progress, call checkRetrieveStatus() again until the retrieve operation is completed. The checkStatus() call is still supported
in versions API version 30.0 or earlier, but isn’t available in API version 31.0 and later.

For API version 31.0 or later, retrieve packaged or unpackaged components by using the following steps.

1.

2.

Issue a  retrieve()  call to start the asynchronous retrieval. An AsyncResult object is returned. Note the value in the id field, and
use it for the next step.

Issue a checkRetrieveStatus() call, and pass in the id value from the AsyncResult object from the first step. Check the value of the
done field of the returned RetrieveResult. If it’s  true, the call is completed, and you proceed to the next step. Otherwise, repeat
this step to call checkRetrieveStatus() again until the done field is  true.

3. Retrieve the zip file (zipFile) field and other desired fields from RetrieveResult, which the final call to checkRetrieveStatus() returned

in the previous step.

For API version 30.0 or earlier, retrieve packaged or unpackaged components by using the following steps.

1.

2.

Issue a  retrieve()  call to start the asynchronous retrieval. An AsyncResult object is returned. If the call is completed, the done
field contains  true. Most often, the call isn’t completed quickly enough to be noted in the result. If it’s completed, note the value
in the id field returned, and skip the next step.

If the call isn’t completed, issue a checkStatus() call in a loop using the value in the id field of the AsyncResult object, returned by
the  retrieve()  call in the previous step. Check the AsyncResult object returned until the done field contains  true. The time
taken to complete a  retrieve()  call depends on the size of the zip file being deployed, so use a longer wait time between
iterations as the size of the zip file increases.

3.

Issue a checkRetrieveStatus() call to obtain the results of the  retrieve()  call, using the id value returned in the first step.

For examples of manifest files, see Sample package.xml Manifest Files.


File-Based Calls

Permissions

retrieve()

Your client application must be logged in with the Modify Metadata Through Metadata API Functions or Modify All Data permission.

Note:  If a user requires access to metadata but not to data, enable the Modify Metadata Through Metadata API Functions on
page 7 permission. Otherwise, enable the Modify All Data permission.

Arguments

Name

Type

Description

retrieveRequest

RetrieveRequest

Encapsulates options for determining which packages or files are retrieved.

Response

AsyncResult

Sample Code—Java

This sample shows how to retrieve components into a zip file. See the deploy()  sample code for details on how to deploy a zip file.

Note:  This sample requires API version 34.0 or later.

package com.doc.samples;

import java.io.*;
import java.util.*;
import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.rmi.RemoteException;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import com.sforce.soap.metadata.AsyncResult;
import com.sforce.soap.metadata.MetadataConnection;
import com.sforce.soap.enterprise.EnterpriseConnection;
import com.sforce.soap.metadata.RetrieveMessage;
import com.sforce.soap.metadata.RetrieveRequest;
import com.sforce.soap.metadata.RetrieveResult;
import com.sforce.soap.metadata.RetrieveStatus;
import com.sforce.soap.enterprise.LoginResult;
import com.sforce.ws.ConnectionException;
import com.sforce.ws.ConnectorConfig;
import com.sforce.soap.metadata.PackageTypeMembers;

public class RetrieveSample {


File-Based Calls

retrieve()

// Binding for the metadata WSDL used for making metadata API calls
private MetadataConnection metadataConnection;

static BufferedReader rdr = new BufferedReader(new InputStreamReader(System.in));

// one second in milliseconds
private static final long ONE_SECOND = 1000;
// maximum number of attempts to retrieve the results
private static final int MAX_NUM_POLL_REQUESTS = 50;

// manifest file that controls which components get retrieved
private static final String MANIFEST_FILE = "package.xml";

private static final double API_VERSION = 31.0;

public static void main(String[] args) throws Exception {

final String USERNAME = "user@company.com";
// This is only a sample. Hard coding passwords in source files is a bad practice.

final String PASSWORD = "password";
final String URL = "https://login.salesforce.com/services/Soap/c/31.0";

RetrieveSample sample = new RetrieveSample(USERNAME, PASSWORD, URL);
sample.retrieveZip();

}

public RetrieveSample(String username, String password, String loginUrl)

throws ConnectionException {

createMetadataConnection(username, password, loginUrl);

}

private void retrieveZip() throws RemoteException, Exception
{

RetrieveRequest retrieveRequest = new RetrieveRequest();
// The version in package.xml overrides the version in RetrieveRequest
retrieveRequest.setApiVersion(API_VERSION);
setUnpackaged(retrieveRequest);

// Start the retrieve operation
AsyncResult asyncResult = metadataConnection.retrieve(retrieveRequest);
String asyncResultId = asyncResult.getId();

// Wait for the retrieve to complete
int poll = 0;
long waitTimeMilliSecs = ONE_SECOND;
RetrieveResult result = null;
do {

Thread.sleep(waitTimeMilliSecs);
// Double the wait time for the next iteration
waitTimeMilliSecs *= 2;
if (poll++ > MAX_NUM_POLL_REQUESTS) {

throw new Exception("Request timed out. If this is a large set " +


File-Based Calls

retrieve()

"of metadata components, check that the time allowed " +
"by MAX_NUM_POLL_REQUESTS is sufficient.");

}
result = metadataConnection.checkRetrieveStatus(

asyncResultId, true);

System.out.println("Retrieve Status: " + result.getStatus());

} while (!result.isDone());

if (result.getStatus() == RetrieveStatus.Failed) {

throw new Exception(result.getErrorStatusCode() + " msg: " +

result.getErrorMessage());

} else if (result.getStatus() == RetrieveStatus.Succeeded) {

// Print out any warning messages
StringBuilder buf = new StringBuilder();
if (result.getMessages() != null) {

for (RetrieveMessage rm : result.getMessages()) {

buf.append(rm.getFileName() + " - " + rm.getProblem());

}

}
if (buf.length() > 0) {

System.out.println("Retrieve warnings:\n" + buf);

}

// Write the zip to the file system
System.out.println("Writing results to zip file");
ByteArrayInputStream bais = new ByteArrayInputStream(result.getZipFile());
File resultsFile = new File("retrieveResults.zip");
FileOutputStream os = new FileOutputStream(resultsFile);
try {

ReadableByteChannel src = Channels.newChannel(bais);
FileChannel dest = os.getChannel();
copy(src, dest);

System.out.println("Results written to " + resultsFile.getAbsolutePath());

} finally {

os.close();

}

}

}

/**

* Helper method to copy from a readable channel to a writable channel,
* using an in-memory buffer.
*/

private void copy(ReadableByteChannel src, WritableByteChannel dest)

throws IOException

{

// Use an in-memory byte buffer
ByteBuffer buffer = ByteBuffer.allocate(8092);
while (src.read(buffer) != -1) {

buffer.flip();
while(buffer.hasRemaining()) {

dest.write(buffer);


File-Based Calls

retrieve()

}
buffer.clear();

}

}

private void setUnpackaged(RetrieveRequest request) throws Exception
{

// Edit the path, if necessary, if your package.xml file is located elsewhere
File unpackedManifest = new File(MANIFEST_FILE);
System.out.println("Manifest file: " + unpackedManifest.getAbsolutePath());

if (!unpackedManifest.exists() || !unpackedManifest.isFile())

throw new Exception("Should provide a valid retrieve manifest " +

"for unpackaged content. " +
"Looking for " + unpackedManifest.getAbsolutePath());

// Note that we populate the _package object by parsing a manifest file here.
// You could populate the _package based on any source for your
// particular application.
com.sforce.soap.metadata.Package p = parsePackage(unpackedManifest);
request.setUnpackaged(p);

}

private com.sforce.soap.metadata.Package parsePackage(File file) throws Exception {

try {

InputStream is = new FileInputStream(file);
List<PackageTypeMembers> pd = new ArrayList<PackageTypeMembers>();
DocumentBuilder db =

DocumentBuilderFactory.newInstance().newDocumentBuilder();

Element d = db.parse(is).getDocumentElement();
for (Node c = d.getFirstChild(); c != null; c = c.getNextSibling()) {

if (c instanceof Element) {

Element ce = (Element)c;
//
NodeList namee = ce.getElementsByTagName("name");
if (namee.getLength() == 0) {

// not
continue;

}
String name = namee.item(0).getTextContent();
NodeList m = ce.getElementsByTagName("members");
List<String> members = new ArrayList<String>();
for (int i = 0; i < m.getLength(); i++) {

Node mm = m.item(i);
members.add(mm.getTextContent());

}
PackageTypeMembers pdi = new PackageTypeMembers();
pdi.setName(name);
pdi.setMembers(members.toArray(new String[members.size()]));
pd.add(pdi);

}

}
com.sforce.soap.metadata.Package r = new com.sforce.soap.metadata.Package();
r.setTypes(pd.toArray(new PackageTypeMembers[pd.size()]));


File-Based Calls

RetrieveRequest

r.setVersion(API_VERSION + "");
return r;

} catch (ParserConfigurationException pce) {

throw new Exception("Cannot create XML parser", pce);

} catch (IOException ioe) {

throw new Exception(ioe);

} catch (SAXException se) {

throw new Exception(se);

}

}

private void createMetadataConnection(final String username,
final String password, final String loginUrl)
throws ConnectionException {

final ConnectorConfig loginConfig = new ConnectorConfig();
loginConfig.setAuthEndpoint(loginUrl);
loginConfig.setServiceEndpoint(loginUrl);
loginConfig.setManualLogin(true);
LoginResult loginResult = (new EnterpriseConnection(loginConfig)).login(

username, password);

final ConnectorConfig metadataConfig = new ConnectorConfig();
metadataConfig.setServiceEndpoint(loginResult.getMetadataServerUrl());
metadataConfig.setSessionId(loginResult.getSessionId());
this.metadataConnection = new MetadataConnection(metadataConfig);

}

//The sample client application retrieves the user's login credentials.
// Helper function for retrieving user input from the console
String getUserInput(String prompt) {

System.out.print(prompt);
try {

return rdr.readLine();

}
catch (IOException ex) {

return null;

}

}

}

RetrieveRequest

The  RetrieveRequest  parameter specified on a  retrieve()  call encapsulates options for determining which packages or
files are retrieved.

The  RetrieveRequest  object consists of the following properties:

Name

apiVersion

Type

double

Description

Required. The API version for the retrieve request. The API
version determines the fields retrieved for each metadata type.


File-Based Calls

checkRetrieveStatus()

Name

Type

Description

For example, an icon field was added to the
CustomTab on page 838  for API version 14.0. If you
retrieve components for version 13.0 or earlier, the components
don't include the icon

field. In API version 31.0 and later, the API version that’s
specified in  package.xml  is used for the  retrieve()
call and overrides the version in the  apiVersion field. If
the version isn't specified in  package.xml, the version in
this field is used.

A list of package names to be retrieved. If you're retrieving only
unpackaged components, don't specify a name here. You can
retrieve packaged and unpackaged components in the same
retrieve.

This field is for reference only, don't use it to retrieve packaged
metadata for development.

A list of component types to retrieve dependencies for.
Currently, the only allowed value for this parameter is  Bot.

Use this parameter if any requested metadata components are
of type  Bot.

Make up to 25 retrieve requests using this parameter per day.
A single retrieve request using this parameter can request
dependencies for up to 100 components.

This field is available in API version 64.0 and later.

Specifies whether only a single package is being retrieved
(true) or not (false). If  false, then more than one
package is being retrieved.

A list of file names to be retrieved. If a value is specified for this
property,  packageNames  must be set to  null  and
singlePackage  must be set to  true.

packageNames

string[]

rootTypesWithDependencies

string[]

singlePackage

boolean

specificFiles

string[]

unpackaged

Package

A list of components to retrieve that aren't in a package.

checkRetrieveStatus()

Checks the status of the declarative metadata call  checkRetrieveStatus()  and returns the zip file contents.

Syntax

In API version 34.0 and later:

RetrieveResult = metadatabinding.checkRetrieveStatus(ID id, boolean includeZip);


File-Based Calls

checkRetrieveStatus()

In API version 33.0 and earlier:

RetrieveResult = metadatabinding.checkRetrieveStatus(ID id);

Usage

Use  checkRetrieveStatus()  to check the progress of the metadata retrieve() operation. The RetrieveResult object that
this method returns indicates when the asynchronous  retrieve()  call is completed. If the retrieval is completed, RetrieveResult
contains the zip file contents by default. Use the following process to retrieve metadata components with the  retrieve()  call.

1.

2.

Issue a  retrieve()  call to start the asynchronous retrieval. An AsyncResult object is returned. Note the value in the id field, and
use it for the next step.

Issue a checkRetrieveStatus() call, and pass in the id value from the AsyncResult object from the first step. Check the value of the
done field of the returned RetrieveResult. If it’s  true, the call is completed, and you proceed to the next step. Otherwise, repeat
this step to call checkRetrieveStatus() again until the done field is  true.

3. Retrieve the zip file (zipFile) field and other desired fields from RetrieveResult, which the final call to checkRetrieveStatus() returned

in the previous step.

In API version 31.0 and later, the process of making a  retrieve()  call has been simplified. You no longer have to call checkStatus()
after a retrieve()  call to obtain the status of the retrieve operation. Instead, make calls to checkRetrieveStatus() only. If the retrieve
operation is in progress, call checkRetrieveStatus() again until the retrieve operation is completed. The checkStatus() call is still supported
in versions API version 30.0 or earlier, but isn’t available in API version 31.0 and later.

Retrieving the Zip File in a Second Process

By default,  checkRetrieveStatus()  returns the zip file on the last call to this operation when the retrieval is completed
(RetrieveResult.isDone() == true)  and then deletes the zip file from the server. Subsequent calls to
checkRetrieveStatus()  for the same retrieve operation can’t retrieve the zip file after it has been deleted. Starting with API
version 34.0, pass a boolean value for the includeZip  argument of checkRetrieveStatus()  to indicate whether to retrieve
the zip file. The  includeZip  argument gives you the option to retrieve the file in a separate process after the retrieval operation is
completed. For example, a service polls the retrieval status by calling  checkRetrieveStatus(id, false)  in a loop. This call
returns the status of the retrieval operation, but doesn’t retrieve the zip file. After the retrieval operation is completed, another process,
such as a background file transfer service, calls  checkRetrieveStatus(id, true)  to retrieve the zip file. This last call causes
the zip file to be deleted from the server.

// First process: Poll the retrieval but don’t retrieve the zip file.
AsyncResult asyncResult = metadataConnection.retrieve(retrieveRequest);
String asyncResultId = asyncResult.getId();
// Wait for the retrieve to complete
int poll = 0;
long waitTimeMilliSecs = ONE_SECOND;
RetrieveResult result = null;
do {

Thread.sleep(waitTimeMilliSecs);
// Check the status but don’t retrieve zip file.
result = metadataConnection.checkRetrieveStatus(asyncResultId, false);

} while (!result.isDone());

// Second process: Retrieve the zip file.
// For example, this process can be a background file transfer service.
// Retrieve the zip file.
result = metadataConnection.checkRetrieveStatus(asyncResultId, true);


File-Based Calls

checkRetrieveStatus()

// Get the zip file from the RetrieveResult (result) variable
if (result.getStatus() == RetrieveStatus.Succeeded) {

ByteArrayInputStream bais = new ByteArrayInputStream(result.getZipFile());
// ...

}

Sample Code—Java

See the retrieve() sample code for sample usage of this call.

Arguments

Name

id

Type

ID

includeZip

boolean

Response

RetrieveResult

Description

ID obtained from an AsyncResult object returned by a retrieve() call or a subsequent RetrieveResult
object returned by a checkRetrieveStatus() call.

Set to true  to retrieve the zip file. You can retrieve the zip file only after the retrieval operation
is completed. After the zip file is retrieved, it’s deleted from the server. Set to  false  to check
the status of the retrieval without attempting to retrieve the zip file. If set to null, this argument
defaults to  true, which means that the zip file is retrieved on the last call to
checkRetrieveStatus()  when the retrieval has finished.

This argument is available in API version 34.0 and later.


## CHAPTER 10 CRUD-Based Calls

Use CRUD-based calls to work with metadata components in a manner similar to how synchronous API calls in the enterprise WSDL act
upon objects.

createMetadata()
Adds one or more new metadata components to your organization synchronously.

readMetadata()
Returns one or more metadata components from your organization synchronously.

updateMetadata()
Updates one or more metadata components in your organization synchronously.

upsertMetadata()
Creates or updates one or more metadata components in your organization synchronously.

deleteMetadata()
Deletes one or more metadata components from your organization synchronously.

renameMetadata()
Renames a metadata component in your organization synchronously.

create()
Deprecated. Adds one or more new metadata components to your organization asynchronously. This call is removed as of API version
31.0 and is available in earlier versions only. Use  createMetadata()  instead.

delete()
Deprecated. Deletes one or more components from your organization asynchronously. This call is removed as of API version 31.0
and is available in earlier versions only. Use  deleteMetadata()  instead.

update()
Deprecated. Updates one or more components in your organization asynchronously. This call is removed as of API version 31.0 and
is available in earlier versions only. Use  updateMetadata()  or  renameMetadata()  instead.

createMetadata()

Adds one or more new metadata components to your organization synchronously.

Syntax

SaveResult[] = metadatabinding.createMetadata(

Metadata[] metadata);


CRUD-Based Calls

Usage

createMetadata()

Use the  createMetadata()  call to create any component that extends Metadata. All components must be of the same type in
the same call. For more details, see Metadata Components and Types.

This call executes synchronously, which means that the call returns only when the operation completes.

Starting in API version 34.0, this call supports the AllOrNoneHeader header. By default, if AllOrNoneHeader isn’t used in API version 34.0
and later, this call can save a partial set of records for records with no errors (equivalent to  AllOrNoneHeader=false). In API
version 33.0 and earlier, the default behavior is to only save all records when there are no failures in any record in the call (equivalent to
AllOrNoneHeader=true).

Version

Available in API version 30.0 and later.

Permissions

Your client application must be logged in with the Modify Metadata Through Metadata API Functions or Modify All Data permission.

Note:  If a user requires access to metadata but not to data, enable the Modify Metadata Through Metadata API Functions on
page 7 permission. Otherwise, enable the Modify All Data permission.

Required Fields

The metadata components being created determine required fields. For more information about specific component types, see Metadata
Components and Types.

Valid Data Values

You must supply values that are valid for the field’s data type, such as integers for integer fields (not alphabetic characters). In your client
application, follow the data formatting rules specified for your programming language and development tool. (Your development tool
handles the appropriate mapping of data types in SOAP messages.)

String Values

When storing values in string fields, the API trims any leading and trailing whitespace. For example, if the value of a label field is entered
as  "MyObject ", the value is stored in the database as  "MyObject".

Basic Steps for Creating Metadata Components

Follow this process to create metadata components.

1. Design an array, and populate it with the components that you want to create. All components must be of the same type.

2. Call  createMetadata()  with the component array passed in as an argument.

3. A  SaveResult  object is returned for each component you tried to create. It contains information about whether the operation

was successful, the name of the component created, and any errors returned if the operation wasn’t successful.


CRUD-Based Calls

createMetadata()

Sample Code—Java

public void createCustomObjectSync() {

try {

CustomObject co = new CustomObject();
String name = "MyCustomObject1";
co.setFullName(name + "__c");
co.setDeploymentStatus(DeploymentStatus.Deployed);
co.setDescription("Created by the Metadata API");
co.setEnableActivities(true);
co.setLabel(name + " Object");
co.setPluralLabel(co.getLabel() + "s");
co.setSharingModel(SharingModel.ReadWrite);

CustomField nf = new CustomField();
nf.setType(FieldType.Text);
nf.setLabel(co.getFullName() + " Name");
co.setNameField(nf);

SaveResult[] results = metadataConnection

.createMetadata(new Metadata[] { co });

for (SaveResult r : results) {

if (r.isSuccess()) {

System.out.println("Created component: " + r.getFullName());

} else {

System.out

.println("Errors were encountered while creating "

for (Error e : r.getErrors()) {

+ r.getFullName());

System.out.println("Error message: " + e.getMessage());
System.out.println("Status code: " + e.getStatusCode());

}

}

}

} catch (ConnectionException ce) {

ce.printStackTrace();

}

}

Arguments

Name

Type

Description

metadata

Metadata[]

Array of one or more metadata components.

Limit: 10. (For CustomMetadata on page 734 and CustomApplication on page 702 only, the
limit is 200.)

You must submit arrays of only one type of component. For example, you can submit an array
of 10 custom objects or 10 profiles, but not a mix of both types.


CRUD-Based Calls

Response

SaveResult[]

readMetadata()

readMetadata()

Returns one or more metadata components from your organization synchronously.

Syntax

ReadResult = metadataConnection.readMetadata(string metadataType, string[] fullNames);

Usage

Use the  readMetadata()  call to retrieve any component that extends Metadata. All components must be of the same type in the
same call. For more details, see Metadata Components and Types.

This call executes synchronously, which means that the call returns only when the operation completes.

Version

Available in API version 30.0 and later.

Permissions

Your client application must be logged in with the Modify Metadata Through Metadata API Functions or Modify All Data permission.

Note:  If a user requires access to metadata but not to data, enable the Modify Metadata Through Metadata API Functions on
page 7 permission. Otherwise, enable the Modify All Data permission.

Basic Steps for Reading Metadata Components

Use the following process to read metadata components:

1. Determine the metadata type of the components you want to read and the fullName of each component to read.

The full names must match one or more full names returned by the listMetadata()  call, which includes namespace prefixes.
If you obtain the  fullName  from a package manifest file, and the component has a namespace prefix, prepend the namespace
prefix to the  fullName. Use this syntax:  namespacePrefix__ComponentName. For example, for the custom object
component  MyCustomObject__c  and the namespace  MyNS, the  fullName is  MyNS__MyCustomObject__c. For
more information about the fullName field, see Metadata.

You can read only components of the same type in a single call.

2.

Invoke the readMetadata()  call. For the first argument, pass in the name of the metadata type. The metadata type must match
one of the values returned by the  describeMetadata()  call. For the second argument, pass in an array of full names
corresponding to the components you wish to get.

3. A  ReadResult  is returned that contains an array of  Metadata  components. Cast each returned  Metadata  object to the

metadata type you specified in the call to get the component’s properties.


CRUD-Based Calls

updateMetadata()

Sample Code—Java

public void readCustomObjectSync() {

try {

ReadResult readResult = metadataConnection

.readMetadata("CustomObject", new String[] {

"MyCustomObject1__c", "MyCustomObject2__c" });

Metadata[] mdInfo = readResult.getRecords();
System.out.println("Number of component info returned: "

+ mdInfo.length);

for (Metadata md : mdInfo) {

if (md != null) {

CustomObject obj = (CustomObject) md;
System.out.println("Custom object full name: "

+ obj.getFullName());

System.out.println("Label: " + obj.getLabel());
System.out.println("Number of custom fields: "

+ obj.getFields().length);

System.out.println("Sharing model: "

+ obj.getSharingModel());

} else {

System.out.println("Empty metadata.");

}

}

} catch (ConnectionException ce) {

ce.printStackTrace();

}

}

Arguments

Name

Type

Description

metadataType

string

The metadata type of the components to read.

fullNames

string[]

Array of full names of the components to read.

Limit: 10. (For CustomMetadata on page 734 and CustomApplication on page 702 only, the
limit is 200.)

You must submit arrays of only one type of component. For example, you can submit an array
of 10 custom objects or 10 profiles, but not a mix of both types.

Response

ReadResult

updateMetadata()

Updates one or more metadata components in your organization synchronously.