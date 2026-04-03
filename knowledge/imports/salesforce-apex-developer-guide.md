# Salesforce Apex Developer Guide
Source: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/
Downloaded: 2026-04-03

## APEX DEVELOPER GUIDE

Apex is a strongly typed, object-oriented programming language that allows developers to execute flow and transaction control
statements on the Salesforce Platform server, in conjunction with calls to the API. This guide introduces you to the Apex development
process and provides valuable information on learning, writing, deploying and testing Apex.

For reference information on Apex classes, interfaces, exceptions and so on, see Apex Reference Guide.

## Apex Release Notes

Use the Salesforce Release Notes to learn about the most recent updates and changes to Apex.

## Getting Started with Apex

Learn about the Apex development lifecycle. Follow a step-by-step tutorial to create an Apex class and trigger, and deploy them to
a production organization.

## Writing Apex

Apex is like Java for Salesforce. It enables you to add and interact with data in the Lightning Platform persistence layer. It uses classes,
data types, variables, and if-else statements. You can make it execute based on a condition, or have a block of code execute repeatedly.

## Running Apex

You can access many features of the Salesforce user interface programmatically in Apex, and you can integrate with external SOAP
and REST Web services. You can run Apex code using a variety of mechanisms. Apex code runs in atomic transactions.

## Debugging, Testing, and Deploying Apex

Develop your Apex code in a sandbox and debug it with the Developer Console and debug logs. Unit-test your code, then distribute
it to customers using packages.

### Apex Reference

In Summer ’21 and later versions, Apex reference content is moved to a separate guide called the Apex Reference Guide.

## Appendices

## Apex Release Notes

Use the Salesforce Release Notes to learn about the most recent updates and changes to Apex.

For Apex updates and changes that impact the Salesforce Platform, see the Apex Release Notes.

For new and changed Apex classes, methods, exceptions and interfaces, see Apex: New and Changed Items in the Salesforce Release
Notes.

## Getting Started with Apex

Learn about the Apex development lifecycle. Follow a step-by-step tutorial to create an Apex class and trigger, and deploy them to a
production organization.

### Introducing Apex

Apex code is the first multitenant, on-demand programming language for developers interested in building the next generation of
business applications. Apex revolutionizes the way developers create on-demand applications.

### Apex Development Process

In this chapter, you’ll learn about the Apex development lifecycle, and which organization and tools to use to develop Apex. You’ll
also learn about testing and deploying Apex code.

### Apex Quick Start

This step-by-step tutorial shows how to create a simple Apex class and trigger, and how to deploy these components to a production
organization.

### Introducing Apex

Apex code is the first multitenant, on-demand programming language for developers interested in building the next generation of
business applications. Apex revolutionizes the way developers create on-demand applications.

While many customization options are available through the Salesforce user interface, such as the ability to define new fields, objects,
workflow, and approval processes, developers can also use the SOAP API to issue data manipulation commands such as  delete(),
update() or  upsert(), from client-side programs.

These client-side programs, typically written in Java, JavaScript, .NET, or other programming languages, grant organizations more flexibility
in their customizations. However, because the controlling logic for these client-side programs is not located on Salesforce servers, they
are restricted by the performance costs of making multiple round-trips to the Salesforce site to accomplish common business transactions,
and by the cost and complexity of hosting server code, such as Java or .NET, in a secure and robust environment.

1. What is Apex?

Apex is a strongly typed, object-oriented programming language that allows developers to execute flow and transaction control
statements on Salesforce servers in conjunction with calls to the API. Using syntax that looks like Java and acts like database stored
procedures, Apex enables developers to add business logic to most system events, including button clicks, related record updates,
and Visualforce pages. Apex code can be initiated by Web service requests and from triggers on objects.

2. Understanding Apex Core Concepts

Apex code typically contains many things that you're familiar with from other programming languages.

3. When Should I Use Apex?

Salesforce provides the ability to customize prebuilt apps to fit your organization. For complex business processes, you can implement
custom functionality and user interfaces with a variety of tools, including Apex and Lightning Components.

4. How Does Apex Work?

All Apex runs entirely on-demand on the Lightning Platform. Developers write and save Apex code to the platform, and end users
trigger the execution of the Apex code via the user interface.

5. Developing Code in the Cloud

The Apex programming language is saved and runs in the cloud—the multitenant platform. Apex is tailored for data access and
data manipulation on the platform, and it enables you to add custom business logic to system events. While it provides many benefits
for automating business processes on the platform, it is not a general purpose programming language.

Apex is a strongly typed, object-oriented programming language that allows developers to execute flow and transaction control
statements on Salesforce servers in conjunction with calls to the API. Using syntax that looks like Java and acts like database stored
procedures, Apex enables developers to add business logic to most system events, including button clicks, related record updates, and
Visualforce pages. Apex code can be initiated by Web service requests and from triggers on objects.

You can add Apex to most system events.

As a language, Apex is:

Integrated

Apex provides built-in support for common Lightning Platform idioms, including:

• Data manipulation language (DML) calls, such as  INSERT,  UPDATE, and  DELETE, that include built-in  DmlException

handling

• Inline Salesforce Object Query Language (SOQL) and Salesforce Object Search Language (SOSL) queries that return lists of sObject

records

• Looping that allows for bulk processing of multiple records at a time

• Locking syntax that prevents record update conflicts

• Custom public API calls that can be built from stored Apex methods

• Warnings and errors issued when a user tries to edit or delete a custom object or field that is referenced by Apex

Apex is based on familiar Java idioms, such as variable and expression syntax, block and conditional statement syntax, loop syntax,
object and array notation. Where Apex introduces new elements, it uses syntax and semantics that are easy to understand and
encourage efficient use of the Lightning Platform. Therefore, Apex produces code that is both succinct and easy to write.

Data focused

Apex is designed to thread together multiple query and DML statements into a single unit of work on the Salesforce server. Developers
use database stored procedures to thread together multiple transaction statements on a database server in a similar way. Like other
database stored procedures, Apex does not attempt to provide general support for rendering elements in the user interface.

Rigorous

Apex is a strongly typed language that uses direct references to schema objects such as object and field names. It fails quickly at
compile time if any references are invalid. It stores all custom field, object, and class dependencies in metadata to ensure that they
are not deleted while required by active Apex code.

Hosted

Apex is interpreted, executed, and controlled entirely by the Lightning Platform.

Multitenant aware

Like the rest of the Lightning Platform, Apex runs in a multitenant environment. So, the Apex runtime engine is designed to guard
closely against runaway code, preventing it from monopolizing shared resources. Any code that violates limits fails with
easy-to-understand error messages.

Easy to test

Apex provides built-in support for unit test creation and execution. It includes test results that indicate how much code is covered,
and which parts of your code could be more efficient. Salesforce ensures that all custom Apex code works as expected by executing
all unit tests prior to any platform upgrades.

Versioned

You can save your Apex code against different versions of the API. This enables you to maintain behavior.

Apex is included in Performance Edition, Unlimited Edition, Developer Edition, Enterprise Edition, and Database.com.

Understanding Apex Core Concepts

Apex code typically contains many things that you're familiar with from other programming languages.

Programming elements in Apex

The section describes the basic functionality of Apex, as well as some of the core concepts.

Using Version Settings

In the Salesforce user interface you can specify a version of the Salesforce API against which to save your Apex class or trigger. This setting
indicates not only the version of SOAP API to use, but which version of Apex as well. You can change the version after saving. Every class
or trigger name must be unique. You can’t save the same class or trigger against different versions.

You can also use version settings to associate a class or trigger with a particular version of a managed package that is installed in your
organization from AppExchange. This version of the managed package continues to be used by the class or trigger if later versions of
the managed package are installed, unless you manually update the version setting. To add an installed managed package to the settings
list, select a package from the list of available packages. The list is only displayed if you have an installed managed package that is not
already associated with the class or trigger.

For more information about using version settings with managed packages, see About Package Versions in Salesforce Help.

Naming Variables, Methods and Classes

You can’t use any of the Apex reserved keywords when naming variables, methods, or classes. These include words that are part of Apex
and the Lightning Platform, such as  list,  test, or  account, as well as reserved keywords.

Using Variables and Expressions

Apex is a strongly-typed language, that is, you must declare the data type of a variable when you first refer to it. Apex data types include
basic types such as Integer, Date, and Boolean, as well as more advanced types such as lists, maps, objects, and sObjects.

Variables are declared with a name and a data type. You can assign a value to a variable when you declare it. You can also assign values
later. Use the following syntax when declaring variables:

datatype variable_name [ = value];

Tip:  The semi-colon at the end of preceding codeblock is not optional. You must end all statements with a semi-colon.

The following are examples of variable declarations:

// The following variable has the data type of Integer with the name Count,
// and has the value of 0.
Integer Count = 0;
// The following variable has the data type of Decimal with the name Total. Note
// that no value has been assigned to it.
Decimal Total;
// The following variable is an account, which is also referred to as an sObject.
Account MyAcct = new Account();

In Apex, all primitive data type arguments, such as Integer or String, are passed into methods by value. This fact means that any changes
to the arguments exist only within the scope of the method. When the method returns, the changes to the arguments are lost.

Non-primitive data type arguments, such as sObjects, are passed into methods by reference. Therefore, when the method returns, the
passed-in argument still references the same object as before the method call. Within the method, the reference can't be changed to
point to another object, but the values of the object's fields can be changed.

Using Statements

A statement is any coded instruction that performs an action.

In Apex, statements must end with a semicolon and can be one of these types:

• Assignment, such as assigning a value to a variable

• Conditional (if-else)

• Loops:

– Do-while

– While

– For

• Locking

• Data Manipulation Language (DML)

• Transaction Control

• Method Invoking

• Exception Handling

A block is a series of statements that are grouped with curly braces and can be used in any place where a single statement is allowed.
For example:

if (true) {

System.debug(1);
System.debug(2);

} else {

System.debug(3);
System.debug(4);

}

In cases where a block consists of only one statement, the curly braces can be left off. For example:

if (true)

System.debug(1);

else

System.debug(2);

Using Collections

Apex has the following types of collections:

• Lists (arrays)

• Maps

• Sets

A list is a collection of elements, such as Integers, Strings, objects, or other collections. Use a list when the sequence of elements is
important. You can have duplicate elements in a list.

The first index position in a list is always 0.

To create a list:

• Use the  new  keyword

• Use the  List  keyword followed by the element type contained within  <> characters.

Use the following syntax for creating a list:

List <datatype> list_name

[= new List<datatype>();] |
[=new List<datatype>{value [, value2. . .]};] |
;

The following example creates a list of Integer, and assigns it to the variable  My_List. Remember, because Apex is strongly typed,
you must declare the data type of  My_List  as a list of Integer.

List<Integer> My_List = new List<Integer>();

For more information, see Lists on page 28.

A set is a collection of unique, unordered elements. It can contain primitive data types, such as String, Integer, Date, and so on. It can
also contain more complex data types, such as sObjects.

To create a set:

• Use the  new  keyword

• Use the  Set  keyword followed by the primitive data type contained within  <> characters

Use the following syntax for creating a set:

Set<datatype> set_name

[= new Set<datatype>();] |
[= new Set<datatype>{value [, value2. . .] };] |
;

The following example creates a set of String. The values for the set are passed in using the curly braces  {}.

Set<String> My_String = new Set<String>{'a', 'b', 'c'};

For more information, see Sets on page 31.

A map is a collection of key-value pairs. Keys can be any primitive data type. Values can include primitive data types, as well as objects
and other collections. Use a map when finding something by key matters. You can have duplicate values in a map, but each key must
be unique.

To create a map:

• Use the  new  keyword

• Use the  Map  keyword followed by a key-value pair, delimited by a comma and enclosed in  <>  characters.

Use the following syntax for creating a map:

Map<key_datatype, value_datatype> map_name

[=new Map<key_datatype, value_datatype>();] |
[=new Map<key_datatype, value_datatype>
{key1_value => value1_value
[, key2_value => value2_value. . .]};] |
;

The following example creates a map that has a data type of Integer for the key and String for the value. In this example, the values for
the map are being passed in between the curly braces  {}  as the map is being created.

Map<Integer, String> My_Map = new Map<Integer, String>{1 => 'a', 2 => 'b', 3 => 'c'};

For more information, see Maps on page 31.

Using Branching

An  if  statement is a true-false test that enables your application to do different things based on a condition. The basic syntax is as
follows:

if (Condition){
// Do this if the condition is true
} else {
// Do this if the condition is not true
}

For more information, see Conditional (If-Else) Statements on page 53.

Using Loops

While the  if  statement enables your application to do things based on a condition, loops tell your application to do the same thing
again and again based on a condition. Apex supports the following types of loops:

• Do-while

• While

• For

A Do-while loop checks the condition after the code has executed.

A While loop checks the condition at the start, before the code executes.

A For loop enables you to more finely control the condition used with the loop. In addition, Apex supports traditional For loops where
you set the conditions, as well as For loops that use lists and SOQL queries as part of the condition.

For more information, see Loops on page 57.

When Should I Use Apex?

Salesforce provides the ability to customize prebuilt apps to fit your organization. For complex business processes, you can implement
custom functionality and user interfaces with a variety of tools, including Apex and Lightning Components.

Apex

Use Apex if you want to:

• Create Web services.

• Create email services.

• Perform complex validation over multiple objects.

• Create complex business processes that aren’t supported by Flow Builder.

• Create custom transactional logic (logic that occurs over the entire transaction, not just with a single record or object).

• Attach custom logic to another operation, such as saving a record, so that it occurs whenever the operation is executed, regardless

of whether it originates in the user interface, a Visualforce page, or from SOAP API.

Lightning Components

Develop Lightning components to customize Lightning Experience, the Salesforce mobile app, or to build your own standalone apps.
You can also use out-of-the-box components to speed up development.

As of Spring ’19 (API version 45.0), you can build Lightning components using two programming models: the Lightning Web Components
model, and the original Aura Components model. Lightning web components are custom HTML elements built using HTML and modern
JavaScript. Lightning web components and Aura components can coexist and interoperate on a page. Configure Lightning web
components and Aura components to work in Lightning App Builder and Experience Builder. Admins and end users don’t know which
programming model was used to develop the components. To them, they’re simply Lightning components.

We recommend using the Lightning Web Components (LWC) model to create custom user interfaces. LWC follows W3C web standards,
and you can build and package components using standard JavaScript syntax. With LWC, you can work easily with Salesforce data using
Apex and Lightning Data Service.

For more information, see the LWC Dev Guide.

Visualforce

Visualforce consists of a tag-based markup language that gives developers a more powerful way of building applications and customizing
the Salesforce user interface. With Visualforce you can:

• Build wizards and other multistep processes.

• Create your own custom flow control through an application.

• Define navigation patterns and data-specific rules for optimal, efficient application interaction.

For more information, see the Visualforce Developer's Guide.

SOAP API

Use standard SOAP API calls when you want to add functionality to a composite application that processes only one type of record at a
time and does not require any transactional control (such as setting a Savepoint or rolling back changes).

For more information, see the SOAP API Developer Guide.

How Does Apex Work?

All Apex runs entirely on-demand on the Lightning Platform. Developers write and save Apex code to the platform, and end users trigger
the execution of the Apex code via the user interface.

Apex is compiled, stored, and run entirely on the Lightning Platform

When a developer writes and saves Apex code to the platform, the platform application server first compiles the code into an abstract
set of instructions that can be understood by the Apex runtime interpreter, and then saves those instructions as metadata.

When an end user triggers the execution of Apex, perhaps by clicking a button or accessing a Visualforce page, the platform application
server retrieves the compiled instructions from the metadata and sends them through the runtime interpreter before returning the
result. The end user observes no differences in execution time from standard platform requests.

Developing Code in the Cloud

The Apex programming language is saved and runs in the cloud—the multitenant platform. Apex is tailored for data access and data
manipulation on the platform, and it enables you to add custom business logic to system events. While it provides many benefits for
automating business processes on the platform, it is not a general purpose programming language.

Apex cannot be used to:

• Render elements in the user interface other than error messages

• Change standard functionality—Apex can only prevent the functionality from happening, or add additional functionality

• Create temporary files

• Spawn threads

Tip:  All Apex code runs on the Lightning Platform, which is a shared resource used by all other organizations. To guarantee
consistent performance and scalability, the execution of Apex is bound by governor limits that ensure no single Apex execution
impacts the overall service of Salesforce. This means all Apex code is limited by the number of operations (such as DML or SOQL)
that it can perform within one process.

All Apex requests return a collection that contains from 1 to 50,000 records. You cannot assume that your code only works on a
single record at a time. Therefore, you must implement programming patterns that take bulk processing into account. If you don’t,
you may run into the governor limits.

SEE ALSO:

Trigger and Bulk Request Best Practices

### Apex Development Process

In this chapter, you’ll learn about the Apex development lifecycle, and which organization and tools to use to develop Apex. You’ll also
learn about testing and deploying Apex code.

What is the Apex Development Process?
To develop Apex, get a Developer Edition account, write and test your code, then deploy your code.

Choose a Salesforce Org for Apex Development
You can develop Apex in a sandbox, scratch org, or Developer Edition org, but not directly in a production org. With so many choices,
here’s some help to determine which org type is right for you and how to create it.

Choose a Development Environment for Writing Apex
There are several development environments for developing Apex code. Choose the environment that meets your needs.

Learning Apex
After you have your developer account, there are many resources available to you for learning about Apex

Writing Tests
Testing is the key to successful long-term development and is a critical component of the development process. We strongly
recommend that you use a test-driven development process, that is, test development that occurs at the same time as code
development.

Deploying Apex to a Sandbox Organization
Sandboxes create copies of your Salesforce org in separate environments. Use them for development, testing, and training without
compromising the data and applications in your production org. Sandboxes are isolated from your production org, so operations
that you perform in your sandboxes don’t affect your production org.

Deploy Apex to a Salesforce Production Organization
After you’ve finished all of your unit tests and verified that your Apex code is executing properly, the final step is deploying Apex to
your Salesforce production organization.

Adding Apex Code to a AppExchange App
You can include an Apex class or trigger in an app that you’re creating for AppExchange.

What is the Apex Development Process?

To develop Apex, get a Developer Edition account, write and test your code, then deploy your code.

We recommend the following process for developing Apex:

1. Choose a Salesforce Org for Apex development.

2. Learn more about Apex.

3. Write your Apex.

4. While writing Apex, you should also be writing tests.

5. Optionally deploy your Apex to a sandbox organization and do final unit tests.

6. Deploy your Apex to your Salesforce production organization.

In addition to deploying your Apex, once it is written and tested, you can also add your classes and triggers to a AppExchange App
package.

Choose a Salesforce Org for Apex Development

You can develop Apex in a sandbox, scratch org, or Developer Edition org, but not directly in a production org. With so many choices,
here’s some help to determine which org type is right for you and how to create it.

Sandboxes (Recommended)

A sandbox is a copy of your production org’s metadata in a separate environment, with varying amounts of data depending on the
sandbox type. A sandbox provides a safe space for developers and admins to experiment with new features and validate changes before
deploying code to production. Developer and Developer Pro sandboxes with source tracking enabled can take advantage of many of
the features of our Salesforce DX source-driven development tools, including Salesforce CLI, Code Builder, and DevOps Center. See Create
a Sandbox in Salesforce Help.

Scratch Orgs (Recommended)

A scratch org is a source-driven and temporary deployment of Salesforce code and metadata. A scratch org is fully configurable, allowing
you to emulate different Salesforce editions with different features and settings. Scratch orgs have a maximum 30-day lifespan, with the
default set at 7 days. For information on using and creating scratch orgs, see Scratch Orgs in the Salesforce DX Developer Guide.

Developer Edition (DE) Orgs

A DE org is a free org that provides access to many of the features available in an Enterprise Edition org. Developer Edition orgs can
become out-of-date over time and have limited storage. Developer Edition orgs don’t have source tracking enabled and can’t be used
as development environments in DevOps Center. Developer Edition orgs expire if they aren't logged into regularly. You can sign up for
as many Developer Edition orgs as you like on the Developer Edition Signup page.

Trial Edition Orgs

Trial editions usually expire after 30 days, so they’re great for evaluating Salesforce functionality but aren’t intended for use as a permanent
development environment. Although Apex triggers are available in trial editions, they’re disabled when you convert to any other edition.
Deploy your code to another org before conversion to retain your Apex triggers. Salesforce offers several product- and industry-specific
free trial orgs.

Production Orgs (Not Supported)

A production org is the final destination for your code and applications, and has live users accessing your data. You can't develop Apex
in your Salesforce production org, and we recommend that you avoid directly modifying any code or metadata directly in production.
Live users accessing the system while you're developing can destabilize your data or corrupt your application.

Choose a Development Environment for Writing Apex

There are several development environments for developing Apex code. Choose the environment that meets your needs.

Agentforce for Developers

Agentforce for Developers is an AI-powered developer tool that generates Apex code from natural language prompts and automatically
suggests code completions as you type. Use Agentforce for Developers to easily create unit test cases for your Apex code and get to the
required Apex test coverage.

Agentforce for Developers extension (salesforcedx-einstein-gpt) is a part of the Salesforce Expanded Pack. Agentforce for Developers is
enabled by default in VS Code. For more information, see Set Up Agentforce for Developers.

• To access Agentforce for Developers from inside an Apex file in the VS Code editor, see Generate Apex Code.

• To use AI-based autocomplete to accept suggestions for Apex code as you write it, see Inline Auto Completion.

• To use Agentforce for Developers to quickly generate unit tests, see Test Case Generation.

Salesforce Extensions for Visual Studio Code and Code Builder

The Salesforce Extensions for Visual Studio Code and Code Builder are tools for developing on the Salesforce platform in the lightweight,
extensible VS Code editor. These tools provide features for working with development orgs (scratch orgs, sandboxes, and developer
edition orgs), Apex, Lightning components, and Visualforce.

Code Builder is a browser-based version of the desktop experience, with everything installed and configured. It provides all the goodness
of the desktop experience, but provides you with the flexibility to work anywhere, from any computer.

Developer Console

The Developer Console is an integrated development environment (IDE) built into Salesforce. Use it to create, debug, and test Apex
classes and triggers.

To open the Developer Console from Lightning Experience: Click the quick access menu (

), then click Developer Console.

To open the Developer Console from Salesforce Classic: Click  Your Name > Developer Console.

The Developer Console supports these tasks:

• Writing code—You can add code using the source code editor. Also, you can browse packages in your organization.

• Compiling code—When you save a trigger or class, the code is automatically compiled. Any compilation errors are reported.

• Debugging—You can view debug logs and set checkpoints that aid in debugging.

• Testing—You can execute tests of specific test classes or all tests in your organization, and you can view test results. Also, you can

inspect code coverage.

• Checking performance—You can inspect debug logs to locate performance bottlenecks.

• SOQL queries—You can query data in your organization and view the results using the Query Editor.

• Color coding and autocomplete—The source code editor uses a color scheme for easier readability of code elements and provides

autocompletion for class and method names.

Salesforce Setup Code Editors

In Salesforce Setup, you can view and edit Apex classes and triggers.

All classes and triggers are compiled when they’re saved, and any syntax errors are flagged. You can’t save your code until it compiles
without errors. The Salesforce user interface also numbers the lines in the code, and uses color coding to distinguish different elements,
such as comments, keywords, literal strings, and so on.

• From Setup in the Quick Find box, enter Apex, and select an Apex class or trigger. To edit it, click Edit beside the class or trigger

name.

• To create a trigger on an object, from Setup in the Quick Find box, enter Object  and click Object Manager. Click the object name

and click Triggers. Click New and enter your code.

Note:  You can’t use the Salesforce Setup code editors to modify Apex in a Salesforce production org.

Additional Editors

Alternatively, you can use any text editor, such as Notepad, to write Apex code. Then either copy and paste the code into your application,
or use one of the API calls to deploy it.

To develop an Apex IDE of your own, use SOAP API methods for compiling triggers and classes, and executing test methods. Use Metadata
API methods for deploying code to production environments. For more information, see Deploying Apex on page 748.

SEE ALSO:

Salesforce Help: Find Object Management Settings

Learning Apex

After you have your developer account, there are many resources available to you for learning about Apex

Apex Trailhead Content

Beginning and intermediate programmers

Several Trailhead modules provide tutorials on learning Apex. Use these modules to learn the fundamentals of Apex and how you can
use it on the Salesforce Platform. Use Apex to add custom business logic through triggers, unit tests, asynchronous Apex, REST Web
services, and Lightning components.

• Quick Start: Apex

• Apex Basics & Database

• Apex Triggers

• Apex Integration Services

• Apex Testing

• Asynchronous Apex

Salesforce Developers Apex Developer Center

Beginning and advanced programmers

The Apex Developer Center has links to several resources including articles about the Apex programming language. These resources
provide a quick introduction to Apex and include best practices for Apex development.

Code Samples and SDKs

Beginning and advanced programmers

Open-source code samples and SDKs, reference code, and best practices can be found at Code samples and SDKs. A library of concise,
meaningful examples of Apex code for common use cases, following best practices, can be found at Apex-recipes.

Training Courses

Training classes are also available from Salesforce Trailhead Academy. Grow and validate your skills with Salesforce Credentials.

In This Guide (Apex Developer Guide)

Beginning programmers can look at the following:

• Introducing Apex, and in particular:

– Documentation Conventions

– Core Concepts

– Quick Start Tutorial

• Classes, Objects, and Interfaces

• Testing Apex

• Execution Governors and Limits

In addition, advanced programmers can look at:

• Trigger and Bulk Request Best Practices

• Advanced Apex Programming Example

• Understanding Apex Describe Information

• Asynchronous Execution (@future  Annotation)

• Batch Apex and Apex Scheduler

Writing Tests

Testing is the key to successful long-term development and is a critical component of the development process. We strongly recommend
that you use a test-driven development process, that is, test development that occurs at the same time as code development.

To facilitate the development of robust, error-free code, Apex supports the creation and execution of unit tests. Unit tests are class
methods that verify whether a particular piece of code is working properly. Unit test methods take no arguments, commit no data to
the database, and send no emails. Such methods are flagged with the @IsTest  annotation in the method definition. Unit test methods
must be defined in test classes, that is, classes annotated with  @IsTest.

Note:  The  @IsTest annotation on methods is equivalent to the  testMethod  keyword. As best practice, Salesforce
recommends that you use @IsTest  rather than testMethod. The testMethod  keyword may be versioned out in a future
release.

In addition, before you deploy Apex or package it for the AppExchange, the following must be true.

• Unit tests must cover at least 75% of your Apex code, and all of those tests must complete successfully.

Note the following.

– When deploying Apex to a production organization, each unit test in your organization namespace is executed by default.

– Calls to  System.debug  aren’t counted as part of Apex code coverage.

– Test methods and test classes aren’t counted as part of Apex code coverage.

– While only 75% of your Apex code must be covered by tests, don’t focus on the percentage of code that is covered. Instead,
make sure that every use case of your application is covered, including positive and negative cases, as well as bulk and single
records. This approach ensures that 75% or more of your code is covered by unit tests.

• Every trigger must have some test coverage.

• All classes and triggers must compile successfully.

For more information on writing tests, see Testing Apex on page 713.

Deploying Apex to a Sandbox Organization

Sandboxes create copies of your Salesforce org in separate environments. Use them for development, testing, and training without
compromising the data and applications in your production org. Sandboxes are isolated from your production org, so operations that
you perform in your sandboxes don’t affect your production org.

To deploy Apex from a local project in the Salesforce extension for Visual Studio Code to a Salesforce organization, see Salesforce
Extensions for Visual Studio Code.

You can also use the  deploy()  Metadata API call to deploy your Apex from a developer organization to a sandbox organization.

A useful API call is  runTests(). In a development or sandbox organization, you can run the unit tests for a specific class, a list of
classes, or a namespace.

You can also use Salesforce CLI. See Develop Against Any Org for details.

For more information, see Deploying Apex.

Deploy Apex to a Salesforce Production Organization

After you’ve finished all of your unit tests and verified that your Apex code is executing properly, the final step is deploying Apex to your
Salesforce production organization.

1. To deploy Apex from a local project in Visual Studio Code editor to a Salesforce organization, see Salesforce Extensions for Visual

Studio Code and Code Builder.

Also, you can deploy Apex through change sets in the Salesforce user interface. For more information and for additional deployment
options, see Deploying Apex on page 748, and Build and Release Your App.

Adding Apex Code to a AppExchange App

You can include an Apex class or trigger in an app that you’re creating for AppExchange.

Any Apex that is included as part of a package must have at least 75% cumulative test coverage. Each trigger must also have some test
coverage. When you upload your package to AppExchange, all tests are run to ensure that they run without errors. In addition, tests
with the@isTest(OnInstall=true)  annotation run when the package is installed in the installer's organization. You can specify
which tests should run during package install by annotating them with  @isTest(OnInstall=true). This subset of tests must
pass for the package install to succeed.

For more information, see the Second-Generation Managed Packaging Developer Guide.

### Apex Quick Start

This step-by-step tutorial shows how to create a simple Apex class and trigger, and how to deploy these components to a production
organization.

When you have a Developer Edition or sandbox organization, you can learn some of the core concepts of Apex. After reviewing the
basics, you’re ready to write your first Apex program—a simple class, trigger, and unit test.

Because Apex is similar to Java, you can recognize much of the functionality.

This tutorial is based on a custom object called Book that is created in the first step. This custom object is updated through a trigger.

This Hello World sample requires custom objects. You can either create these objects on your own, or download the objects and Apex
code as an unmanaged package from AppExchange. To obtain the sample assets in your org, install the Apex Tutorials Package. This
package also contains sample code and objects for the Shipping Invoice example.

Note:  There’s a more complex Shipping Invoice example that you can also walk through. That example illustrates many more
features of the language.

1. Create a Custom Object

In this step, you create a custom object called Book with one custom field called Price.

2. Add an Apex Class

In this step, you add an Apex class that contains a method for updating the book price. This method is called by the trigger that
you’ll be adding in the next step.

3. Add an Apex Trigger

In this step, you create a trigger for the Book__c  custom object that calls the applyDiscount  method of the MyHelloWorld
class that you created in the previous step.

4. Add a Test Class

In this step, you add a test class with one test method. You also run the test and verify code coverage. The test method exercises
and validates the code in the trigger and class. Also, it enables you to reach 100% code coverage for the trigger and class.

5. Deploy Components to Production

In this step, you deploy the Apex code and the custom object you created previously to your production organization using change
sets.

Create a Custom Object

In this step, you create a custom object called Book with one custom field called Price.

Prerequisites:

A Salesforce account in a sandbox Professional, Enterprise, Performance, or Unlimited Edition org, or an account in a Developer org.

For more information about creating a sandbox org, see “Sandbox Types and Templates” in Salesforce Help. To sign up for a free Developer
org, see the Developer Edition Environment Sign Up Page.

1. Log in to your sandbox or Developer org.

2. From your management settings for custom objects, if you’re using Salesforce Classic, click New Custom Object, or if you’re using

Lightning Experience, select Create > Custom Object.

3. Enter  Book  for the label.

4. Enter  Books  for the plural label.

5. Click Save.

Ta dah! You’ve now created your first custom object. Now let’s create a custom field.

6.

In the Custom Fields & Relationships section of the Book detail page, click New.

7. Select Number for the data type and click Next.

8. Enter  Price  for the field label.

9. Enter 16 in the length text box.

10. Enter 2 in the decimal places text box, and click Next.

11. Click Next to accept the default values for field-level security.

12. Click Save.

You've created a custom object called Book, and added a custom field to that custom object. Custom objects already have some standard
fields, like Name and CreatedBy, and allow you to add other fields that are more specific to your implementation. For this tutorial, the
Price field is part of our Book object, and the Apex class you’ll write in the next step accesses it.

SEE ALSO:

Salesforce Help: Find Object Management Settings

Add an Apex Class

In this step, you add an Apex class that contains a method for updating the book price. This method is called by the trigger that you’ll
be adding in the next step.

Prerequisites:

• A Salesforce account in a sandbox Professional, Enterprise, Performance, or Unlimited Edition org, or an account in a Developer org.

• The Book custom object.

1. From Setup, enter “Apex Classes” in the  Quick Find  box, then select Apex Classes and click New.

2.

In the class editor, enter this class definition:

public class MyHelloWorld {

}

The previous code is the class definition to which you’ll be adding one method in the next step. Apex code is contained in classes.
This class is defined as  public, which means the class is available to other Apex classes and triggers. For more information, see
Classes, Objects, and Interfaces on page 60.

3. Add this method definition between the class opening and closing brackets.

public static void applyDiscount(Book__c[] books) {

for (Book__c b :books){
b.Price__c *= 0.9;

}

}

This method is called  applyDiscount, and it’s both public and static. Because it’s a static method, you don't need to create an
instance of the class to access the method—you can use the name of the class followed by a dot (.) and the name of the method.
For more information, see Static and Instance Methods, Variables, and Initialization Code on page 69.

This method takes one parameter, a list of Book records, which is assigned to the variable  books. Notice the  __c  in the object
name  Book__c. This indicates that it’s a custom object that you created. Standard objects that are provided in the Salesforce
application, such as Account, don't end with this postfix.

The next section of code contains the rest of the method definition:

for (Book__c b :books){
b.Price__c *= 0.9;

}

Notice the  __c  after the field name  Price__c. This indicates that it’s a custom field that you created. Standard fields that are
provided by default in Salesforce are accessed using the same type of dot notation but without the __c, for example, Name  doesn't
end with __c  in Book__c.Name. The statement b.Price__c *= 0.9;  takes the old value of b.Price__c, multiplies
it by 0.9, which means its value is discounted by 10%, and then stores the new value into the b.Price__c  field. The *=  operator

is a shortcut. Another way to write this statement is  b.Price__c = b.Price__c * 0.9;. See Expression Operators on
page 39.

4. Click Save to save the new class. You now have this full class definition.

public class MyHelloWorld {

public static void applyDiscount(Book__c[] books) {

for (Book__c b :books){
b.Price__c *= 0.9;

}

}

}

You now have a class that contains some code that iterates over a list of books and updates the Price field for each book. This code is
part of the  applyDiscount  static method called by the trigger that you’ll create in the next step.

Add an Apex Trigger

In this step, you create a trigger for the Book__c  custom object that calls the applyDiscount  method of the MyHelloWorld
class that you created in the previous step.

Prerequisites:

• A Salesforce account in a sandbox Professional, Enterprise, Performance, or Unlimited Edition org, or an account in a Developer org.

• The MyHelloWorld Apex class.

A trigger is a piece of code that executes before or after records of a particular type are inserted, updated, or deleted from the Lightning
Platform database. Every trigger runs with a set of context variables that provide access to the records that caused the trigger to fire. All
triggers run in bulk; that is, they process several records at once.

1. From the object management settings for books, go to Triggers, and then click New.

2.

In the trigger editor, delete the default template code and enter this trigger definition:

trigger HelloWorldTrigger on Book__c (before insert) {

Book__c[] books = Trigger.new;

MyHelloWorld.applyDiscount(books);

}

The first line of code defines the trigger:

trigger HelloWorldTrigger on Book__c (before insert) {

It gives the trigger a name, specifies the object on which it operates, and defines the events that cause it to fire. For example, this
trigger is called HelloWorldTrigger, it operates on the  Book__c  object, and runs before new books are inserted into the database.

The next line in the trigger creates a list of book records named  books  and assigns it the contents of a trigger context variable
called  Trigger.new. Trigger context variables such as  Trigger.new  are implicitly defined in all triggers and provide access
to the records that caused the trigger to fire. In this case,  Trigger.new contains all the new books that are about to be inserted.

Book__c[] books = Trigger.new;

The next line in the code calls the method  applyDiscount  in the  MyHelloWorld  class. It passes in the array of new books.

MyHelloWorld.applyDiscount(books);

You now have all the code that is needed to update the price of all books that get inserted. However, there’s still one piece of the puzzle
missing. Unit tests are an important part of writing code and are required. In the next step, you'll see why this is so and will be able to
add a test class.

SEE ALSO:

Salesforce Help: Find Object Management Settings

Add a Test Class

In this step, you add a test class with one test method. You also run the test and verify code coverage. The test method exercises and
validates the code in the trigger and class. Also, it enables you to reach 100% code coverage for the trigger and class.

Prerequisites:

• A Salesforce account in a sandbox Professional, Enterprise, Performance, or Unlimited Edition org, or an account in a Developer org.

• The HelloWorldTrigger Apex trigger.

Note:  Testing is an important part of the development process. Before you can deploy Apex or package it for AppExchange, the
following must be true.

• Unit tests must cover at least 75% of your Apex code, and all of those tests must complete successfully.

Note the following.

– When deploying Apex to a production organization, each unit test in your organization namespace is executed by default.

– Calls to  System.debug  aren’t counted as part of Apex code coverage.

– Test methods and test classes aren’t counted as part of Apex code coverage.

– While only 75% of your Apex code must be covered by tests, don’t focus on the percentage of code that is covered. Instead,
make sure that every use case of your application is covered, including positive and negative cases, as well as bulk and
single records. This approach ensures that 75% or more of your code is covered by unit tests.

• Every trigger must have some test coverage.

• All classes and triggers must compile successfully.

1. From Setup, enter  Apex Classes  in the  Quick Find  box, then select Apex Classes and click New.

2.

In the class editor, add this test class definition, and then click Save.

@IsTest
private class HelloWorldTestClass {

@IsTest
static void validateHelloWorld() {

Book__c b = new Book__c(Name='Behind the Cloud', Price__c=100);
System.debug('Price before inserting new book: ' + b.Price__c);

// Insert book
insert b;

// Retrieve the new book
b = [SELECT Price__c FROM Book__c WHERE Id =:b.Id];
System.debug('Price after trigger fired: ' + b.Price__c);

// Test that the trigger correctly updated the price
System.assertEquals(90, b.Price__c);

}

}

This class is defined using the  @IsTest  annotation. Classes defined this way should only contain test methods and any methods
required to support those test methods. One advantage to creating a separate class for testing is that classes defined with @IsTest
don’t count against your org’s limit of 6 MB of Apex code. You can also add the  @IsTest  annotation to individual methods. For
more information, see @IsTest  Annotation on page 106 and Execution Governors and Limits.

The method  validateHelloWorld  is defined using the  @IsTest  annotation. This annotation means that if changes are
made to the database, they’re rolled back when execution completes. You don’t have to delete any test data created in the test
method.

Note:  The  @IsTest annotation on methods is equivalent to the  testMethod  keyword. As best practice, Salesforce
recommends that you use  @IsTest  rather than  testMethod. The  testMethod  keyword may be versioned out in a
future release.

First, the test method creates a book and inserts it into the database temporarily. The System.debug statement writes the value
of the price in the debug log.

Book__c b = new Book__c(Name='Behind the Cloud', Price__c=100);
System.debug('Price before inserting new book: ' + b.Price__c);

// Insert book
insert b;

After the book is inserted, the code retrieves the newly inserted book, using the ID that was initially assigned to the book when it
was inserted. The  System.debug statement then logs the new price that the trigger modified.

// Retrieve the new book
b = [SELECT Price__c FROM Book__c WHERE Id =:b.Id];
System.debug('Price after trigger fired: ' + b.Price__c);

When the  MyHelloWorld  class runs, it updates the  Price__c  field and reduces its value by 10%. The following test verifies
that the method  applyDiscount  ran and produced the expected result.

// Test that the trigger correctly updated the price
System.assertEquals(90, b.Price__c);

3. To run this test and view code coverage information, switch to the Developer Console.

4.

In the Developer Console, click Test > New Run.

5. To select your test class, click HelloWorldTestClass.

6. To add all methods in the  HelloWorldTestClass  class to the test run, click Add Selected.

7. Click Run.

The test result displays in the Tests tab. Optionally, you can expand the test class in the Tests tab to view which methods were run.
In this case, the class contains only one test method.

8. The Overall Code Coverage pane shows the code coverage of this test class. To view the percentage of lines of code in the trigger
covered by this test, which is 100%, double-click the code coverage line for HelloWorldTrigger. Because the trigger calls a method
from the  MyHelloWorld  class, this class also has coverage (100%). To view the class coverage, double-click MyHelloWorld.

9. To open the log file, in the Logs tab, double-click the most recent log line in the list of logs. The execution log displays, including

logging information about the trigger event, the call to the applyDiscount  method, and the price before and after the trigger.

By now, you’ve completed all the steps necessary for writing some Apex code with a test that runs in your development environment.
In the real world, after you tested your code and are satisfied with it, you want to deploy the code and any prerequisite components to
a production org. The next step shows you how to do this deployment for the code and custom object you created.

SEE ALSO:

Salesforce Help: Open the Developer Console

Deploy Components to Production

In this step, you deploy the Apex code and the custom object you created previously to your production organization using change
sets.

Prerequisites:

• A Salesforce account in a sandbox Performance, Unlimited, or Enterprise Edition organization.

• The HelloWorldTestClass Apex test class.

• A deployment connection between the sandbox and production organizations that allows inbound change sets to be received by

the production organization. See “Change Sets” in Salesforce Help.

• “Create and Upload Change Sets” user permission to create, edit, or upload outbound change sets.

This procedure doesn't apply to Developer organizations since change sets are available only in Performance, Unlimited, Enterprise, or
Database.com Edition organizations. If you have a Developer Edition account, you can use other deployment methods. For more
information, see Deploying Apex.

1. From Setup, enter  Outbound Changesets  in the  Quick Find  box, then select Outbound Changesets.

2.

3.

If a splash page appears, click Continue.

In the Change Sets list, click New.

4. Enter a name for your change set, for example,  HelloWorldChangeSet, and optionally a description. Click Save.

5.

In the Change Set Components section, click Add.

6. Select Apex Class from the component type dropdown list, then select the MyHelloWorld and the HelloWorldTestClass classes from

the list and click Add to Change Set.

7. To add the dependent components, click View/Add Dependencies.

8. To select all components, select the top checkbox. Click Add To Change Set.

9.

In the Change Set Detail section of the change set page, click Upload.

10. Select the target organization, in this case production, and click Upload.

11. After the change set upload completes, deploy it in your production organization.

a. Log in to your production organization.

b. From Setup, enter  Inbound Change Sets  in the  Quick Find  box, then select Inbound Change Sets.

c.

If a splash page appears, click Continue.

d.

In the change sets awaiting deployment list, click your change set's name.

e. Click Deploy.

In this tutorial, you learned how to create a custom object, how to add an Apex trigger, class, and test class. Finally, you also learned
how to test your code, and how to upload the code and the custom object using Change Sets.

## Writing Apex

Apex is like Java for Salesforce. It enables you to add and interact with data in the Lightning Platform persistence layer. It uses classes,
data types, variables, and if-else statements. You can make it execute based on a condition, or have a block of code execute repeatedly.

### Data Types and Variables

Apex uses data types, variables, and related language constructs such as enums, constants, expressions, operators, and assignment
statements.

### Control Flow Statements

Apex provides if-else statements, switch statements, and loops to control the flow of code execution. Statements are generally
executed line by line, in the order they appear. With control flow statements, you can make Apex code execute based on a certain
condition, or have a block of code execute repeatedly.

### Working with Data in Apex

You can add and interact with data in the Lightning Platform persistence layer. The sObject data type is the main data type that
holds data objects. You’ll use Data Manipulation Language (DML) to work with data, and use query languages to retrieve data, such
as the (), among other things.

### Document Your Apex Code

ApexDoc is a standardized comment format that makes it easier for humans, documentation generators, and AI agents to understand
your codebase. We recommend using ApexDoc comments to facilitate code collaboration and increase long-term code maintainability.
Based on the JavaDoc standard, ApexDoc provides specifications, such as specialized tags and guidelines, that are tailored to Apex
and the Salesforce ecosystem.

### Data Types and Variables

Apex uses data types, variables, and related language constructs such as enums, constants, expressions, operators, and assignment
statements.

1. Data Types

In Apex, all variables and expressions have a data type, such as sObject, primitive, or enum.

2. Primitive Data Types

Apex uses the same primitive data types as SOAP API, except for higher-precision Decimal type in certain cases.

3. Collections

Collections in Apex can be lists, sets, or maps.

4. Enums

An enum is an abstract data type with values that each take on exactly one of a finite set of identifiers that you specify. Enums are
typically used to define a set of possible values that don’t otherwise have a numerical order. Typical examples include the suit of a
card, or a particular season of the year.

5. Variables

Local variables are declared with Java-style syntax.

6. Constants

Apex constants are variables whose values don’t change after being initialized once. Constants can be defined using the  final
keyword.

7. Expressions and Operators

An expression is a construct made up of variables, operators, and method invocations that evaluates to a single value.

8. Assignment Statements

An assignment statement is any statement that places a value into a variable.

9. Rules of Conversion

In general, Apex requires you to explicitly convert one data type to another. For example, a variable of the Integer data type cannot
be implicitly converted to a String. You must use the  string.format  method. However, a few data types can be implicitly
converted, without using a method.

Data Types

In Apex, all variables and expressions have a data type, such as sObject, primitive, or enum.

• A primitive, such as an Integer, Double, Long, Date, Datetime, String, ID, or Boolean (see Primitive Data Types on page 24)

• An sObject, either as a generic sObject or as a specific sObject, such as an Account, Contact, or MyCustomObject__c (see Working

with sObjects on page 132 in Chapter 4.)

• A collection, including:

– A list (or array) of primitives, sObjects, user defined objects, objects created from Apex classes, or collections (see Lists on page

28)

– A set of primitives (see Sets on page 31)

– A map from a primitive to a primitive, sObject, or collection (see Maps on page 31)

• A typed list of values, also known as an enum (see Enums on page 33)

• Objects created from user-defined Apex classes (see Classes, Objects, and Interfaces on page 60)

• Objects created from system supplied Apex classes

• Null (for the  null  constant, which can be assigned to any variable)

Methods can return values of any of the listed types, or return no value and be of type Void.

Type checking is strictly enforced at compile time. For example, the parser generates an error if an object field of type Integer is assigned
a value of type String. However, all compile-time exceptions are returned as specific fault codes, with the line number and column of
the error. For more information, see Debugging Apex on page 671.

Primitive Data Types

Apex uses the same primitive data types as SOAP API, except for higher-precision Decimal type in certain cases.

All Apex variables, whether they’re class member variables or method variables, are initialized to  null. Make sure that you initialize
your variables to appropriate values before using them. For example, initialize a Boolean variable to  false.

Apex primitive data types include:

Data Type

Blob

Description

A collection of binary data stored as a single object. You can convert this data type to String or from
String using the toString  and valueOf  methods, respectively. Blobs can be accepted as Web
service arguments, stored in a document (the body of a document is a Blob), or sent as attachments.
For more information, see Crypto Class. Salesforce supports Blob manipulation only with Apex class
methods that are supplied by Salesforce.

Data Type

Boolean

Date

Description

A value that can only be assigned  true,  false, or  null. For example:

Boolean isWinner = true;

A value that indicates a particular day. Unlike Datetime values, Date values contain no information
about time. Always create date values with a system static method.

You can add or subtract an Integer value from a Date value, returning a Date value. Addition and
subtraction of Integer values are the only arithmetic functions that work with Date values. You can’t
perform arithmetic functions that include two or more Date values. Instead, use the Date methods.

Use the  String.valueOf()  method to obtain the date without an appended timestamp.
Using an implicit string conversion with a Date value results in the date with the timestamp appended.

Datetime

A value that indicates a particular day and time, such as a timestamp. Always create datetime values
with a system static method.

You can add or subtract an Integer or Double value from a Datetime value, returning a Date value.
Addition and subtraction of Integer and Double values are the only arithmetic functions that work
with Datetime values. You can’t perform arithmetic functions that include two or more Datetime
values. Instead, use the Datetime methods.

Decimal

A number that includes a decimal point. Decimal is an arbitrary precision number. Currency fields
are automatically assigned the type Decimal.

If you don’t explicitly set the number of decimal places for a Decimal, the item from which the Decimal
is created determines the Decimal’s scale. Scale is a count of decimal places. Use the  setScale
method to set a Decimal’s scale.

• If the Decimal is created as part of a query, the scale is based on the scale of the field returned

from the query.

• If the Decimal is created from a String, the scale is the number of characters after the decimal

point of the String.

• If the Decimal is created from a non-decimal number, the number is first converted to a String.

The scale is then set using the number of characters after the decimal point.

Note:  Two Decimal objects that are numerically equivalent but differ in scale (such as 1.1
and 1.10) generally don’t have the same hashcode. Use caution when such Decimal objects
are used in Sets or as Map keys.

Double

A 64-bit number that includes a decimal point. Doubles have a minimum value of -263 and a maximum
value of 263-1. For example:

Double pi = 3.14159;
Double e = 2.7182818284D;

Scientific notation (e) for Doubles isn’t supported.

ID

Any valid 18-character Lightning Platform record identifier. For example:

ID id='00300000003T2PGAA0';

Data Type

Description

Integer

Long

Object

If you set  ID  to a 15-character value, Apex converts the value to its 18-character representation. All
invalid  ID  values are rejected with a runtime exception.

A 32-bit number that doesn’t include a decimal point. Integers have a minimum value of
-2,147,483,648 and a maximum value of 2,147,483,647. For example:

Integer i = 1;

A 64-bit number that doesn’t include a decimal point. Longs have a minimum value of -263 and a
maximum value of 263-1. Use this data type when you need a range of values wider than the range
provided by Integer. For example:

Long l = 2147483648L;

Any data type that is supported in Apex. Apex supports primitive data types (such as Integer),
user-defined custom classes, the sObject generic type, or an sObject specific type (such as Account).
All Apex data types inherit from Object.

You can cast an object that represents a more specific data type to its underlying data type. For
example:

Object obj = 10;
// Cast the object to an integer.
Integer i = (Integer)obj;
System.assertEquals(10, i);

The next example shows how to cast an object to a user-defined type—a custom Apex class named
MyApexClass  that is predefined in your organization.

Object obj = new MyApexClass();
// Cast the object to the MyApexClass custom type.
MyApexClass mc = (MyApexClass)obj;
// Access a method on the user-defined class.
mc.someClassMethod();

String

Any set of characters surrounded by single quotes. For example,

String s = 'The quick brown fox jumped over the lazy dog.';

String size: The limit on the number of characters is governed by the heap size limit.

Empty Strings and Trailing Whitespace: sObject String field values follow the same rules as in
SOAP API: they can never be empty (only  null), and they can never include leading and trailing
whitespace. These conventions are necessary for database storage.

Conversely, Strings in Apex can be null or empty and can include leading and trailing whitespace,
which can be used to construct a message.

The Solution sObject field SolutionNote operates as a special type of String. If you have HTML Solutions
enabled, any HTML tags used in this field are verified before the object is created or updated. If invalid
HTML is entered, an error is thrown. Any JavaScript used in this field is removed before the object is

Data Type

Description

created or updated. In the following example, when the Solution displays on a detail page, the
SolutionNote field has H1 HTML formatting applied to it:

trigger t on Solution (before insert) {

Trigger.new[0].SolutionNote ='<h1>hello</h1>';

}

In the following example, when the Solution displays on a detail page, the SolutionNote field only
contains  HelloGoodbye:

trigger t2 on Solution (before insert) {
Trigger.new[0].SolutionNote =

'<javascript>Hello</javascript>Goodbye';

}

For more information, see “HTML Solutions Overview” in Salesforce Help.

EscapeSequences: All Strings in Apex use the same escape sequences as SOQL strings:  \b
(backspace),  \t (tab),  \n  (line feed),  \f  (form feed),  \r  (carriage return),  \"  (double quote),
\'  (single quote), and  \\  (backslash).

Comparison Operators: Unlike Java, Apex Strings support using the comparison operators  ==,
!=, <, <=, >, and >=. Because Apex uses SOQL comparison semantics, results for Strings are collated
according to the context user’s locale and aren’t case-sensitive. For more information, see Expression
Operators.

String Methods: As in Java, Strings can be manipulated with several standard methods. For more
information, see String Class.

Apex classes and triggers saved (compiled) using API version 15.0 and higher produce a runtime
error if you assign a String value that is too long for the field.

Time

A value that indicates a particular time. Always create time values with a system static method. See
Time Class.

In addition, two non-standard primitive data types can’t be used as variable or method types, but do appear in system static methods:

• AnyType. The  valueOf  static method converts an sObject field of type AnyType to a standard primitive. AnyType is used within

the Lightning Platform database exclusively for sObject fields in field history tracking tables.

• Currency. The  Currency.newInstance  static method creates a literal of type Currency. This method is for use solely within
SOQL and SOSL  WHERE  clauses to filter against sObject currency fields. You can’t instantiate Currency in any other type of Apex.

For more information on the AnyType data type, see Field Types in the Object Reference for Salesforce.

Versioned Behavior Changes

In API version 16 (Summer ’09) and later, Apex uses the higher-precision Decimal data type in certain types such as currency.

SEE ALSO:

Expression Operators

Class Methods

Object Reference for the Salesforce Platform: Primitive Data Types

Collections

Collections in Apex can be lists, sets, or maps.

Note:  There is no limit on the number of items a collection can hold. However, there is a general limit on heap size.

Lists
A list is an ordered collection of elements that are distinguished by their indices. List elements can be of any data type—primitive
types, collections, sObjects, user-defined types, and built-in Apex types.

Sets
A set is an unordered collection of elements that do not contain any duplicates. Set elements can be of any data type—primitive
types, collections, sObjects, user-defined types, and built-in Apex types.

Maps
A map is a collection of key-value pairs where each unique key maps to a single value. Keys and values can be any data type—primitive
types, collections, sObjects, user-defined types, and built-in Apex types.

Parameterized Typing
Apex, in general, is a statically-typed programming language, which means users must specify the data type for a variable before
that variable can be used.

SEE ALSO:

Execution Governors and Limits

Lists

A list is an ordered collection of elements that are distinguished by their indices. List elements can be of any data type—primitive types,
collections, sObjects, user-defined types, and built-in Apex types.

This table is a visual representation of a list of Strings:

Index 0

'Red'

Index 1

'Orange'

Index 2

'Yellow'

Index 3

'Green'

Index 4

'Blue'

Index 5

'Purple'

The index position of the first element in a list is always 0.

Lists can contain any collection and can be nested within one another and become multidimensional. For example, you can have a list
of lists of sets of Integers. A list can contain up to seven levels of nested collections inside it, that is, up to eight levels overall.

To declare a list, use the  List  keyword followed by the primitive data, sObject, nested list, map, or set type within <> characters. For
example:

// Create an empty list of String
List<String> my_list = new List<String>();
// Create a nested list
List<List<Set<Integer>>> my_list_2 = new List<List<Set<Integer>>>();

To access elements in a list, use the  List methods provided by Apex. For example:

List<Integer> myList = new List<Integer>(); // Define a new list
myList.add(47);

// Adds a second element of value 47 to the end

// of the list

Integer i = myList.get(0);
myList.set(0, 1);
myList.clear();

// Retrieves the element at index 0

// Adds the integer 1 to the list at index 0

// Removes all elements from the list

For more information, including a complete list of all supported methods, see List Class.

Using Array Notation for One-Dimensional Lists

When using one-dimensional lists of primitives or objects, you can also use more traditional array notation to declare and reference list
elements. For example, you can declare a one-dimensional list of primitives or objects by following the data type name with the []
characters:

String[] colors = new List<String>();

These two statements are equivalent to the previous:

List<String> colors = new String[1];

String[] colors = new String[1];

To reference an element of a one-dimensional list, you can also follow the name of the list with the element's index position in square
brackets. For example:

colors[0] = 'Green';

Even though the size of the previous String  array is defined as one element (the number between the brackets in new String[1]),
lists are elastic and can grow as needed provided that you use the  List add  method to add new elements. For example, you can
add two or more elements to the  colors  list. But if you’re using square brackets to add an element to a list, the list behaves like an
array and isn’t elastic, that is, you won’t be allowed to add more elements than the declared array size.

All lists are initialized to  null. Lists can be assigned values and allocated memory using literal notation. For example:

Example

Description

List<Integer> ints = new Integer[0];

Defines an Integer list of size zero with no elements

List<Integer> ints = new Integer[6];

Defines an Integer list with memory allocated for six Integers

List Sorting
You can sort list elements and the sort order depends on the data type of the elements.

You can sort list elements and the sort order depends on the data type of the elements.

Using the List.sort  method, you can sort elements in a list. Sorting is in ascending order for elements of primitive data types, such
as strings. The sort order of other more complex data types is described in the chapters covering those data types.

You can sort custom types (your Apex classes) if they implement the  Comparable  interface. Alternatively, a class implementing the
Comparator  interface can be passed as a parameter to the  List.sort  method. For more information on the sort order used for
sObjects, see Sorting Lists of sObjects.

This example shows how to sort a list of strings and verifies that the colors are in ascending order in the list.

List<String> colors = new List<String>{

'Yellow',
'Red',
'Green'};

colors.sort();
System.assertEquals('Green', colors.get(0));
System.assertEquals('Red', colors.get(1));
System.assertEquals('Yellow', colors.get(2));

For the Visualforce SelectOption control, sorting is in ascending order based on the value and label fields. See this next section for the
sequence of comparison steps used for SelectOption.

Default Sort Order for SelectOption

The  List.sort  method sorts SelectOption elements in ascending order using the value and label fields, and is based on this
comparison sequence.

1. The value field is used for sorting first.

2.

If two value fields have the same value or are both empty, the label field is used.

The disabled field isn’t used for sorting.

For text fields, the sort algorithm uses the Unicode sort order. Also, empty fields precede non-empty fields in the sort order.

In this example, a list contains three SelectOption elements. Two elements, United States and Mexico, have the same value field (‘A’).
The  List.sort  method sorts these two elements based on the label field, and places Mexico before United States, as shown in the
output. The last element in the sorted list is Canada and is sorted on its value field ‘C’, which comes after ‘A’.

List<SelectOption> options = new List<SelectOption>();
options.add(new SelectOption('A','United States'));
options.add(new SelectOption('C','Canada'));
options.add(new SelectOption('A','Mexico'));
System.debug('Before sorting: ' + options);
options.sort();
System.debug('After sorting: ' + options);

The output of the debug statements shows the contents of the list, both before and after the sort.

DEBUG|Before sorting: (System.SelectOption[value="A", label="United States",
disabled="false"],

System.SelectOption[value="C", label="Canada", disabled="false"],
System.SelectOption[value="A", label="Mexico", disabled="false"])

DEBUG|After sorting: (System.SelectOption[value="A", label="Mexico", disabled="false"],

System.SelectOption[value="A", label="United States", disabled="false"],
System.SelectOption[value="C", label="Canada", disabled="false"])

A set is an unordered collection of elements that do not contain any duplicates. Set elements can be of any data type—primitive types,
collections, sObjects, user-defined types, and built-in Apex types.

This table represents a set of strings that uses city names:

'San Francisco'

'New York'

'Paris'

'Tokyo'

Sets can contain collections that can be nested within one another. For example, you can have a set of lists of sets of Integers. A set can
contain up to seven levels of nested collections inside it, that is, up to eight levels overall.

To declare a set, use the  Set  keyword followed by the primitive data type name within <> characters. For example:

Set<String> myStringSet = new Set<String>();

The following example shows how to create a set with two hardcoded string values.

// Defines a new set with two elements
Set<String> set1 = new Set<String>{'New York', 'Paris'};

To access elements in a set, use the system methods provided by Apex. For example:

// Define a new set
Set<Integer> mySet = new Set<Integer>();
// Add two elements to the set
mySet.add(1);
mySet.add(3);
// Assert that the set contains the integer value we added
System.assert(mySet.contains(1));
// Remove the integer value from the set
mySet.remove(1);

The following example shows how to create a set from elements of another set.

// Define a new set that contains the
// elements of the set created in the previous example
Set<Integer> mySet2 = new Set<Integer>(mySet);
// Assert that the set size equals 1
// Note: The set from the previous example contains only one value
System.assert(mySet2.size() == 1);

For more information, including a complete list of all supported set system methods, see Set Class.

Note the following limitations on sets:

• Unlike Java, Apex developers do not need to reference the algorithm that is used to implement a set in their declarations (for example,

HashSet  or  TreeSet). Apex uses a hash structure for all sets.

• A set is an unordered collection—you can’t access a set element at a specific index. You can only iterate over set elements.

• The iteration order of set elements is deterministic, so you can rely on the order being the same in each subsequent execution of

the same code.

Maps

A map is a collection of key-value pairs where each unique key maps to a single value. Keys and values can be any data type—primitive
types, collections, sObjects, user-defined types, and built-in Apex types.

This table represents a map of countries and currencies:

Country (Key)

'United States'

'Japan'

Currency (Value)

'Dollar'

'Yen'

'France'

'Euro'

'England'

'Pound'

'India'

'Rupee'

Map keys and values can contain any collection, and can contain nested collections. For example, you can have a map of Integers to
maps, which, in turn, map Strings to lists. Map keys can contain up to seven levels of nested collections, that is, up to eight levels overall.

To declare a map, use the  Map  keyword followed by the data types of the key and the value within  <> characters. For example:

Map<String, String> country_currencies = new Map<String, String>();
Map<ID, Set<String>> m = new Map<ID, Set<String>>();

You can use the generic or specific sObject data types with maps. You can also create a generic instance of a map.

As with lists, you can populate map key-value pairs when the map is declared by using curly brace ({}) syntax. Within the curly braces,
specify the key first, then specify the value for that key using  =>. For example:

Map<String, String> MyStrings = new Map<String, String>{'a' => 'b', 'c' =>
'd'.toUpperCase()};

In the first example, the value for the key  a  is  b, and the value for the key  c  is  D.

To access elements in a map, use the Map methods provided by Apex. This example creates a map of integer keys and string values. It
adds two entries, checks for the existence of the first key, retrieves the value for the second entry, and finally gets the set of all keys.

Map<Integer, String> m = new Map<Integer, String>(); // Define a new map
m.put(1, 'First entry');
m.put(2, 'Second entry');
System.assert(m.containsKey(1)); // Assert that the map contains a key
String value = m.get(2);
System.assertEquals('Second entry', value);
Set<Integer> s = m.keySet();
map

// Insert a new key-value pair in the map

// Insert a new key-value pair in the map

// Retrieve a value, given a particular key

// Return a set that contains all of the keys in the

For more information, including a complete list of all supported Map methods, see Map Class.

Map Considerations

• Unlike Java, Apex developers don’t need to reference the algorithm that is used to implement a map in their declarations (for example,

HashMap  or  TreeMap). Apex uses a hash structure for all maps.

• The iteration order of map elements is deterministic. You can rely on the order being the same in each subsequent execution of the

same code. However, we recommend to always access map elements by key.

• A map key can hold the  null  value.

• Adding a map entry with a key that matches an existing key in the map overwrites the existing entry with that key with the new

entry.

• Map keys of type String are case-sensitive. Two keys that differ only by the case are considered unique and have corresponding

distinct Map entries. Subsequently, the Map methods, including  put,  get,  containsKey, and  remove  treat these keys as
distinct.

• Uniqueness of map keys of user-defined types is determined by the equals  and  hashCode  methods, which you provide in

your classes. Uniqueness of keys of all other non-primitive types, such as sObject keys, is determined by comparing the objects’ field
values. Use caution when you use an sObject as a map key because when the sObject is changed, it no longer maps to the same

value. For information and examples, see
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_map_sobject_considerations.htm

• A Map object is serializable into JSON only if it uses one of the following data types as a key.

– Boolean

– Date

– DateTime

– Decimal

– Double

– Enum

– Id

– Integer

– Long

– String

– Time

Parameterized Typing

Apex, in general, is a statically-typed programming language, which means users must specify the data type for a variable before that
variable can be used.

This is legal in Apex:

Integer x = 1;

This is not legal, if  x  has not been defined earlier:

x = 1;

Lists, maps and sets are parameterized in Apex: they take any data type Apex supports for them as an argument. That data type must be
replaced with an actual data type upon construction of the list, map or set. For example:

List<String> myList = new List<String>();

Subtyping with Parameterized Lists

In Apex, if type  T  is a subtype of  U, then  List<T>  would be a subtype of  List<U>. For example, the following is legal:

List<String> slst = new List<String> {'alpha', 'beta'};
List<Object> olst = slst;

Enums

An enum is an abstract data type with values that each take on exactly one of a finite set of identifiers that you specify. Enums are typically
used to define a set of possible values that don’t otherwise have a numerical order. Typical examples include the suit of a card, or a
particular season of the year.

Although each value corresponds to a distinct integer value, the enum hides this implementation. Hiding the implementation prevents
any possible misuse of the values to perform arithmetic and so on. After you create an enum, variables, method arguments, and return
types can be declared of that type.

Note:  Unlike Java, the enum type itself has no constructor syntax.

To define an enum, use the enum  keyword in your declaration and use curly braces to demarcate the list of possible values. For example,
the following code creates an enum called  Season:

public enum Season {WINTER, SPRING, SUMMER, FALL}

By creating the enum  Season, you have also created a new data type called  Season. You can use this new data type as you would
any other data type. For example:

Season southernHemisphereSeason = Season.WINTER;

public Season getSouthernHemisphereSeason(Season northernHemisphereSeason) {

if (northernHemisphereSeason == Season.SUMMER) return southernHemisphereSeason;

//...

}

You can also define a class as an enum. When you create an enum class, do not use the  class  keyword in the definition.

public enum MyEnumClass { X, Y }

You can use an enum in any place you can use another data type name. If you define a variable whose type is an enum, any object you
assign to it must be an instance of that enum class.

Any  webservice  method can use enum types as part of their signature. In this case, the associated WSDL file includes definitions
for the enum and its values, which the API client can use.

Apex provides the following system-defined enums:

• System.StatusCode

This enum corresponds to the API error code that is exposed in the WSDL document for all API operations. For example:

StatusCode.CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY
StatusCode.INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY

The full list of status codes is available in the WSDL file for your organization. For more information about accessing the WSDL file
for your organization, see Downloading Salesforce WSDLs and Client Authentication Certificates in Salesforce Help.

• System.XmlTag:

This enum returns a list of XML tags used for parsing the result XML from a  webservice  method. For more information, see
XmlStreamReader Class.

• System.ApplicationReadWriteMode: This enum indicates if an organization is in 5 Minute Upgrade read-only mode

during Salesforce upgrades and downtimes. For more information, see System.getApplicationReadWriteMode().

• System.LoggingLevel:

This enum is used with the system.debug  method, to specify the log level for all debug  calls. For more information, see System
Class.

• System.RoundingMode:

This enum is used by methods that perform mathematical operations to specify the rounding behavior for the operation. Typical
examples are the Decimal  divide  method and the Double  round  method. For more information, see Rounding Mode.

• System.SoapType:

This enum is returned by the field describe result  getSoapType  method. For more information, see SOAPType Enum.

• System.DisplayType:

This enum is returned by the field describe result  getType  method. For more information, see DisplayType Enum.

• System.JSONToken:

This enum is used for parsing JSON content. For more information, see JsonToken Enum.

• ApexPages.Severity:

This enum specifies the severity of a Visualforce message. For more information, see ApexPages.Severity Enum.

• Dom.XmlNodeType:

This enum specifies the node type in a DOM document.

Note:  System-defined enums cannot be used in Web service methods.

All enum values, including system enums, have common methods associated with them. For more information, see Enum Methods.

You cannot add user-defined methods to enum values.

Variables

Local variables are declared with Java-style syntax.

For example:

Integer i = 0;
String str;
List<String> strList;
Set<String> s;
Map<ID, String> m;

As with Java, multiple variables can be declared and initialized in a single statement, using comma separation. For example:

Integer i, j, k;

Variable Naming Rules

When naming variables, follow these rules.

• Variable names are case-insensitive.

• Variable names can contain only letters (A-Z or a-z), numbers (0-9), and underscores (_). Spaces and other special characters, including

dollar signs ($) and hyphens (-), aren’t allowed.

• Variable names must begin with a letter (A-Z or a-z). Names can’t begin with a number (0-9) or an underscore (_).

• Variable names can’t end with an underscore (_).

• Varable names can’t contain consecutive underscores (_ _).

• Reserved keywords can’t be used as variable names.

• Variable names can have a maximum length of 255 characters.

• Salesforce doesn't recommend sharing the same name between a variable and either its class or a method in its class, although it

is permitted to do so.

Null Variables and Initial Values

If you declare a variable and don't initialize it with a value, it will be  null. In essence,  null  means the absence of a value. You can
also assign null  to any variable declared with a primitive type. For example, both of these statements result in a variable set to null:

Boolean x = null;
Decimal d;

Many instance methods on the data type will fail if the variable is  null. In this example, the second statement generates an exception
(NullPointerException)

Date d;
d.addDays(2);

All variables are initialized to null  if they aren’t assigned a value. For instance, in the following example, i, and k  are assigned values,
while the integer variable  j  and the boolean variable  b  are set to  null  because they aren’t explicitly initialized.

Integer i = 0, j, k = 1;
Boolean b;

Note:  A common pitfall is to assume that an uninitialized boolean variable is initialized to  false  by the system. This isn’t the
case. Like all other variables, boolean variables are null if not assigned a value explicitly.

Variable Scope

Variables can be defined at any point in a block, and take on scope from that point forward. Sub-blocks can’t redefine a variable name
that has already been used in a parent block, but parallel blocks can reuse a variable name. For example:

Integer i;
{

// Integer i; This declaration is not allowed

}

for (Integer j = 0; j < 10; j++);
for (Integer j = 0; j < 10; j++);

Case Sensitivity

To avoid confusion with case-insensitive SOQL and SOSL queries, Apex is also case-insensitive. This means:

• Variable and method names are case-insensitive. For example:

Integer I;
//Integer i;

• References to object and field names are case-insensitive. For example:

Account a1;
ACCOUNT a2;

• SOQL and SOSL statements are case- insensitive. For example:

Account[] accts = [sELect ID From ACCouNT where nAme = 'fred'];

Note:  You’ll learn more about sObjects, SOQL, and SOSL later in this guide.

Also note that Apex uses the same filtering semantics as SOQL, which is the basis for comparisons in the SOAP API and the Salesforce
user interface. The use of these semantics can lead to some interesting behavior. For example, if an end-user generates a report based
on a filter for values that come before 'm' in the alphabet (that is, values < 'm'), null fields are returned in the result. The rationale for this
behavior is that users typically think of a field without a value as just a space character, rather than its actual null  value. Consequently,
in Apex, the following expressions all evaluate to  true:

String s;
System.assert('a' == 'A');
System.assert(s < 'b');
System.assert(!(s > 'b'));

Note:  Although  s < 'b'  evaluates to  true in the example above,  'b.'compareTo(s) generates an error because
you’re trying to compare a letter to a  null  value.

SEE ALSO:

Naming Conventions

Constants

Apex constants are variables whose values don’t change after being initialized once. Constants can be defined using the final keyword.

The  final  keyword means that the variable can be assigned at most once, either in the declaration itself, or with a static initializer
method if the constant is defined in a class. This example declares two constants. The first is initialized in the declaration statement. The
second is assigned a value in a static block by calling a static method.

public class myCls {

static final Integer PRIVATE_INT_CONST = 200;
static final Integer PRIVATE_INT_CONST2;

public static Integer calculate() {

return 2 + 7;

}

static {

PRIVATE_INT_CONST2 = calculate();

}

}

For more information, see Using the  final  Keyword on page 85.

Expressions and Operators

An expression is a construct made up of variables, operators, and method invocations that evaluates to a single value.

Expressions
An expression is a construct made up of variables, operators, and method invocations that evaluates to a single value.

Expression Operators
Expressions can be joined to one another with operators to create compound expressions.

Safe Navigation Operator
Use the safe navigation operator (?.) to replace explicit, sequential checks for null references. This operator short-circuits expressions
that attempt to operate on a null value and returns null instead of throwing a NullPointerException.

Null Coalescing Operator
The  ??  operator returns its right-hand side operand when its left-hand side operand is null. Similar to the safe navigation operator
(?.), the null coalescing operator (??) replaces verbose and explicit checks for null references in code.

Operator Precedence
Operators are interpreted in order, according to rules.

Comments
Both single and multiline comments are supported in Apex code.

SEE ALSO:

Expanding sObject and List Expressions

Expressions

An expression is a construct made up of variables, operators, and method invocations that evaluates to a single value.

In Apex, an expression is always one of the following types:

• A literal expression. For example:

1 + 1

• A new sObject, Apex object, list, set, or map. For example:

new Account(<field_initializers>)
new Integer[<n>]
new Account[]{<elements>}
new List<Account>()
new Set<String>{}
new Map<String, Integer>()
new myRenamingClass(string oldName, string newName)

• Any value that can act as the left-hand of an assignment operator (L-values), including variables, one-dimensional list positions, and

most sObject or Apex object field references. For example:

Integer i
myList[3]
myContact.name
myRenamingClass.oldName

• Any sObject field reference that is not an L-value, including:

– The ID of an sObject in a list (see Lists)

– A set of child records associated with an sObject (for example, the set of contacts associated with a particular account). This type

of expression yields a query result, much like SOQL and SOSL queries.

• A SOQL or SOSL query surrounded by square brackets, allowing for on-the-fly evaluation in Apex. For example:

Account[] aa = [SELECT Id, Name FROM Account WHERE Name ='Acme'];
Integer i = [SELECT COUNT() FROM Contact WHERE LastName ='Weissman'];
List<List<SObject>> searchList = [FIND 'map*' IN ALL FIELDS RETURNING Account (Id, Name),

Contact, Opportunity, Lead];

For information, see SOQL and SOSL Queries on page 169.

• A static or instance method invocation. For example:

System.assert(true)
myRenamingClass.replaceNames()
changePoint(new Point(x, y));

Expression Operators

Expressions can be joined to one another with operators to create compound expressions.

Apex supports the following operators:

Operator

Syntax

Description

=

+=

*=

x = y

x += y

x *= y

Assignment operator (Right associative). Assigns the value of  y  to the L-value
x. The data type of  x  must match the data type of  y  and can’t be  null.

Addition assignment operator (Right associative). Adds the value of  y  to the
original value of  x  and then reassigns the new value to  x. See  +  for additional
information.  x  and  y  can’t be  null.

Multiplication assignment operator (Right associative). Multiplies the value of
y  with the original value of  x  and then reassigns the new value to  x.

Note:  x  and  y  must be Integers or Doubles or a combination.

x  and  y  can’t be  null.

-=

x -= y

Subtraction assignment operator (Right associative). Subtracts the value of  y
from the original value of  x  and then reassigns the new value to  x.

Note:  x  and  y  must be Integers or Doubles or a combination.

x  and  y  can’t be  null.

/=

x /= y

Division assignment operator (Right associative). Divides the original value of x
with the value of  y  and then reassigns the new value to  x.

|=

&=

x |= y

x &= y

<<=

x <<= y

>>=

x >>= y

Note:  x  and  y  must be Integers or Doubles or a combination.

x  and  y  can’t be  null.

OR assignment operator (Right associative). If  x, a Boolean, and  y, a Boolean,
are both false, then  x  remains false. Otherwise  x  is assigned the value of true.  x
and  y  can’t be  null.

AND assignment operator (Right associative). If  x, a Boolean, and  y, a Boolean,
are both true, then  x  remains true. Otherwise  x  is assigned the value of false.  x
and  y  can’t be  null.

Bitwise shift left assignment operator. Shifts each bit in  x  to the left by  y  bits
so that the high-order bits are lost and the new right bits are set to 0. This value is
then reassigned to  x.

Bitwise shift right signed assignment operator. Shifts each bit in x  to the right
by  y  bits so that the low-order bits are lost and the new left bits are set to 0 for

Operator

Syntax

Description

>>>=

x >>>= y

? :

x ? y : z

&&

x && y

positive values of  y  and 1 for negative values of  y. This value is then reassigned to
x.

Bitwise shift right unsigned assignment operator. Shifts each bit in  x  to the
right by  y  bits so that the low-order bits are lost and the new left bits are set to 0
for all values of  y. This value is then reassigned to  x.

Ternary operator (Right associative). This operator acts as a short-hand for
if-then-else statements. If  x, a Boolean, is true,  y  is the result. Otherwise  z  is the
result.

Note:  x  can’t be  null.

AND logical operator (Left associative). If x, a Boolean, and y, a Boolean, are both
true, then the expression evaluates to true. Otherwise the expression evaluates to
false.

Note:

• &&  has precedence over  ||

• This operator exhibits short-circuiting behavior, which means  y  is evaluated

only if  x is true.

• x  and  y  can’t be  null.

||

x || y

OR logical operator (Left associative). If  x, a Boolean, and  y, a Boolean, are both
false, then the expression evaluates to false. Otherwise the expression evaluates to
true.

Note:

• &&  has precedence over  ||

• This operator exhibits short-circuiting behavior, which means  y  is evaluated

only if  x is false.

• x and  y  can’t be  null.

==

x == y

Equality operator. If the value of x  equals the value of y, the expression evaluates
to true. Otherwise the expression evaluates to false.

Note:

• Unlike Java,  ==  in Apex compares object value equality not reference

equality, except for user-defined types. Therefore:

– String comparison using  ==  is case-insensitive and is performed

according to the locale of the context user

– ID comparison using  ==  is case-sensitive and doesn’t distinguish

between 15-character and 18-character formats

– User-defined types are compared by reference, which means that
two objects are equal only if they reference the same location in
memory. You can override this default comparison behavior by

Operator

Syntax

Description

providing  equals  and  hashCode  methods in your class to
compare object values instead.

• For sObjects and sObject arrays, ==  performs a deep check of all sObject
field values before returning its result. Likewise for collections and built-in
Apex objects.

• For records, every field must have the same value for  ==  to evaluate to

true.

• x  or  y  can be the literal  null.

• The comparison of any two values can never result in  null.

• SOQL and SOSL use  = for their equality operator and not  ==. Although
Apex and SOQL and SOSL are strongly linked, this unfortunate syntax
discrepancy exists because most modern languages use =  for assignment
and  ==  for equality. The designers of Apex deemed it more valuable to
maintain this paradigm than to force developers to learn a new
assignment operator. As a result, Apex developers must use  ==  for
equality tests in the main body of the Apex code, and  =  for equality in
SOQL and SOSL queries.

===

x === y

<

x < y

Exact equality operator. If x  and y  reference the exact same location in memory
the expression evaluates to true. Otherwise the expression evaluates to false.

Less than operator. If x  is less than y, the expression evaluates to true. Otherwise
the expression evaluates to false.

Note:

• Unlike other database stored procedures, Apex doesn’t support tri-state
Boolean logic and the comparison of any two values can never result in
null.

• If  x  or  y  equal  null  and are Integers, Doubles, Dates, or Datetimes,

the expression is false.

• A non-null  String or ID value is always greater than a  null value.

• If  x and  y  are IDs, they must reference the same type of object.

Otherwise a runtime error results.

• If  x  or  y  is an ID and the other value is a String, the String value is

validated and treated as an ID.

• x  and  y  can’t be Booleans.

• The comparison of two strings is performed according to the locale of

the context user and is case-insensitive.

>

x > y

Greater than operator. If  x  is greater than  y, the expression evaluates to true.
Otherwise the expression evaluates to false.

Note:

• The comparison of any two values can never result in  null.

Operator

Syntax

Description

• If  x  or  y  equal  null  and are Integers, Doubles, Dates, or Datetimes,

the expression is false.

• A non-null  String or ID value is always greater than a  null  value.

• If  x  and  y  are IDs, they must reference the same type of object.

Otherwise a runtime error results.

• If  x  or  y  is an ID and the other value is a String, the String value is

validated and treated as an ID.

• x  and  y  can’t be Booleans.

• The comparison of two strings is performed according to the locale of

the context user and is case-insensitive.

<=

x <= y

Less than or equal to operator. If  x  is less than or equal to  y, the expression
evaluates to true. Otherwise the expression evaluates to false.

Note:

• The comparison of any two values can never result in  null.

• If  x  or  y  equal  null  and are Integers, Doubles, Dates, or Datetimes,

the expression is false.

• A non-null  String or ID value is always greater than a  null  value.

• If  x  and  y  are IDs, they must reference the same type of object.

Otherwise a runtime error results.

• If  x  or  y  is an ID and the other value is a String, the String value is

validated and treated as an ID.

• x  and  y  can’t be Booleans.

• The comparison of two strings is performed according to the locale of

the context user and is case-insensitive.

>=

x >= y

Greater than or equal to operator. If  x  is greater than or equal to  y, the
expression evaluates to true. Otherwise the expression evaluates to false.

Note:

• The comparison of any two values can never result in  null.

• If  x  or  y  equal  null  and are Integers, Doubles, Dates, or Datetimes,

the expression is false.

• A non-null  String or ID value is always greater than a  null  value.

• If  x  and  y  are IDs, they must reference the same type of object.

Otherwise a runtime error results.

• If  x  or  y  is an ID and the other value is a String, the String value is

validated and treated as an ID.

• x  and  y  can’t be Booleans.

• The comparison of two strings is performed according to the locale of

the context user and is case-insensitive.

Operator

Syntax

Description

!=

x != y

Inequality operator. If the value of x  doesn’t equal the value of y, the expression
evaluates to true. Otherwise the expression evaluates to false.

!==

x !== y

+

x + y

-

x - y

Note:

• String comparison using  !=  is case-insensitive

• Unlike Java,  !=  in Apex compares object value equality not reference

equality, except for user-defined types.

• For sObjects and sObject arrays, !=  performs a deep check of all sObject

field values before returning its result.

• For records,  != evaluates to true if the records have different values for

any field.

• User-defined types are compared by reference, which means that two
objects are different only if they reference different locations in memory.
You can override this default comparison behavior by providing equals
and hashCode  methods in your class to compare object values instead.

• x  or  y can be the literal  null.

• The comparison of any two values can never result in  null.

Exact inequality operator. If  x  and  y  don’t reference the exact same location in
memory, the expression evaluates to true. Otherwise the expression evaluates to
false.

Addition operator. Adds the value of  x  to the value of  y  according to the
following rules:

• If  x  and  y  are Integers or Doubles, the operator adds the value of  x  to the

value of  y. If a Double is used, the result is a Double.

• If  x  is a Date and  y  is an Integer, returns a new Date that is incremented by

the specified number of days.

• If  x  is a Datetime and  y  is an Integer or Double, returns a new Date that is
incremented by the specified number of days, with the fractional portion
corresponding to a portion of a day.

• If  x  is a String and  y  is a String or any other type of non-null  argument,

concatenates  y  to the end of  x.

Subtraction operator. Subtracts the value of  y  from the value of  x  according to
the following rules:

• If  x  and  y  are Integers or Doubles, the operator subtracts the value of  y  from

the value of  x. If a Double is used, the result is a Double.

• If  x  is a Date and  y  is an Integer, returns a new Date that is decremented by

the specified number of days.

• If  x  is a Datetime and  y  is an Integer or Double, returns a new Date that is
decremented by the specified number of days, with the fractional portion
corresponding to a portion of a day.

Operator

Syntax

Description

*

/

!

-

++

--

&

|

^

^=

<<

>>

x * y

x / y

!x

-x

x++

++x

x--

--x

x & y

x | y

x ^ y

x ^= y

x << y

x >> y

>>>

x >>> y

~

~x

()

(x)

Multiplication operator. Multiplies  x, an Integer or Double, with  y, another
Integer or Double. If a double is used, the result is a Double.

Division operator. Divides x, an Integer or Double, by y, another Integer or Double.
If a double is used, the result is a Double.

Logical complement operator. Inverts the value of a Boolean so that true becomes
false and false becomes true.

Unary negation operator. Multiplies the value of  x, an Integer or Double, by -1.
The positive equivalent +  is also syntactically valid but doesn’t have a mathematical
effect.

Increment operator. Adds 1 to the value of  x, a variable of a numeric type. If
prefixed (++x), the expression evaluates to the value of x after the increment. If
postfixed (x++), the expression evaluates to the value of x before the increment.

Decrement operator. Subtracts 1 from the value of x, a variable of a numeric type.
If prefixed (--x), the expression evaluates to the value of x after the decrement. If
postfixed (x--), the expression evaluates to the value of x before the decrement.

Bitwise AND operator. ANDs each bit in  x  with the corresponding bit in  y  so
that the result bit is set to 1 if both of the bits are set to 1.

Bitwise OR operator. ORs each bit in  x  with the corresponding bit in  y  so that
the result bit is set to 1 if at least one of the bits is set to 1.

Bitwise exclusive OR operator. Exclusive ORs each bit in x  with the corresponding
bit in  y  so that the result bit is set to 1 if exactly one of the bits is set to 1 and the
other bit is set to 0.

Bitwise exclusive OR operator. Exclusive ORs each bit in x  with the corresponding
bit in  y  so that the result bit is set to 1 if exactly one of the bits is set to 1 and the
other bit is set to 0. Assigns the result of the exclusive OR operation to  x.

Bitwise shift left operator. Shifts each bit in  x  to the left by  y  bits so that the
high-order bits are lost and the new right bits are set to 0.

Bitwise shift right signed operator. Shifts each bit in  x  to the right by  y  bits so
that the low-order bits are lost and the new left bits are set to 0 for positive values
of  y  and 1 for negative values of  y.

Bitwise shift right unsigned operator. Shifts each bit in  x  to the right by  y  bits
so that the low-order bits are lost and the new left bits are set to 0 for all values of
y.

Bitwise Not or Complement operator. Toggles each binary digit of x, converting
0 to 1 and 1 to 0. Boolean values are converted from  True  to  False  and vice
versa.

Parentheses. Elevates the precedence of an expression  x  so that it’s evaluated
first in a compound expression.

Operator

Syntax

Description

?.

x?.y

Safe navigation operator. Short-circuits expressions that attempt to operate on
a null value, and returns null instead of throwing a NullPointerException. If the
left-hand side of the chain expression evaluates to null, the right-hand side of the
chain expression isn’t evaluated.

Safe Navigation Operator

Use the safe navigation operator (?.) to replace explicit, sequential checks for null references. This operator short-circuits expressions
that attempt to operate on a null value and returns null instead of throwing a NullPointerException.

Important:  Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain
terms to avoid any effect on customer implementations.

If the left-hand-side of the chain expression evaluates to null, the right-hand-side isn’t evaluated. Use the safe navigation operator (?.)
in method, variable, and property chaining. The part of the expression that isn’t evaluated can include variable references, method
references, or array expressions.

Note:  All Apex types are implicitly nullable and can hold a null value returned from the operator.

Examples

• This example first evaluates  a, and returns null if  a  is null. Otherwise the return value is  a.b.

a?.b // Evaluates to: a == null ? null : a.b

• This example returns null if  a[x] evaluates to null. If  a[x]  doesn’t evaluate to null and  aMethod()  returns null, then this

expression throws a NullPointerException.

a[x]?.aMethod().aField // Evaluates to null if a[x] == null

• This example returns null if  a[x].aMethod()  evaluates to null.

a[x].aMethod()?.aField

• This example indicates that the type of the expression is the same whether the safe navigation operator is used in the expression or

not.

Integer x = anObject?.anIntegerField; // The expression is of type Integer because the

field is of type Integer

• This example shows a single statement replacing a block of code that checks for nulls.

// Previous code checking for nulls
String profileUrl = null;
if (user.getProfileUrl() != null) {

profileUrl = user.getProfileUrl().toExternalForm();

}

// New code using the safe navigation operator
String profileUrl = user.getProfileUrl()?.toExternalForm();

• This example shows a single-row SOQL query using the safe navigation operator.

// Previous code checking for nulls
results = [SELECT Name FROM Account WHERE Id = :accId];
if (results.size() == 0) { // Account was deleted

return null;

}
return results[0].Name;

// New code using the safe navigation operator
return [SELECT Name FROM Account WHERE Id = :accId]?.Name;

Table 1: Safe Navigation Operator Use-Cases

Allowed use-case

Example

More information

Method or variable or parameter chains

aObject?.aMethod();

Can be used as a top-level statement.

Using parentheses, for example in a cast.

((T)a1?.b1)?.c1()

SObject chaining

String s =
contact.Account?.BillingCity;

SOQL Queries

String s = [SELECT LastName
FROM Contact]?.LastName;

The operator skips the method chain up to
the first closing parenthesis. By adding the
operator after the parenthesis, the code
safeguards the whole expression. If the
operator is used elsewhere, and not after
the parenthesis, the whole cast expression
isn’t be safeguarded. For example, the
behavior of

//Incorrect use of safe
navigation operator
((T)a1?.b1).c1()

is equivalent to:

T ref = null;
if (a1 != null) {
ref = (T)a1.b1;
}
result = ref.c1();

An SObject expression evaluates to null
when the relationship is null. The behavior
is equivalent to  String s =
contact.Account.BillingCity.

If the SOQL query returns no objects, then
the expression evaluates to null. The
behavior is equivalent to:

List<Contact> contacts =
[SELECT LastName FROM
Contact];
String s;
if (contacts.size() == 0) {

Allowed use-case

Example

More information

s = null; // New behavior
when using Safe Navigation.
Earlier, this would throw

an exception. }
else if (contacts.size() ==
1) {

s =

contacts.get(0).LastName; }
else { // contacts.size() >
1 throw new
QueryException(...); }

You can’t use the Safe Navigation Operator in certain cases. Attempting to use the operator in these ways causes an error during
compilation:

• Types and static expressions with dots. For example:

– Namespaces

– {Namespace}.{Class}

– Trigger.new

– Flow.interview.{flowName}

– {Type}.class

• Static variable access, method calls, and expressions. For example:

– AClass.AStaticMethodCall()

– AClass.AStaticVariable

– String.format('{0}', 'hello world')

– Page.{pageName}

• Assignable expressions. For example:

– foo?.bar = 42;

– ++foo?.bar;

• SOQL bind expressions. For example:

class X { public String query = 'xyz';}
X x = new X();
List<Account> accounts = [SELECT Name FROM Account WHERE Name = :X?.query]
List<List<SObject>> moreAccounts = [FIND :X?.query IN ALL FIELDS

RETURNING Account(Name)];

• With  addError()  on SObject scalar fields. For example:

Contact c;
c.LastName?.addError('The field must have a value');

Note:  You can use the operator with  addError()  on SObjects, including lookup and master-detail fields.

Null Coalescing Operator

The ??  operator returns its right-hand side operand when its left-hand side operand is null. Similar to the safe navigation operator (?.),
the null coalescing operator (??) replaces verbose and explicit checks for null references in code.

The null coalescing operator is a binary operator in the form a ?? b  that returns a  if a  isn’t null, and otherwise returns b. The operator
is left-associative. The left-hand operand is evaluated only one time. The right-hand operand is only evaluated if the left-hand operand
is null.

You must ensure type compatibility between the operands. For example, in the expression:  objectZ result = objectA ??
objectB, both  objectA  and  objectB must be instances of objectZ to avoid a compile-time error.

Here’s a comparison that illustrates the operator usage. Before the Null Coalescing Operator, you used:

Integer notNullReturnValue = (anInteger != null) ? anInteger : 100;

With the Null Coalescing Operator, use:

Integer notNullReturnValue = anInteger ?? 100;

While using the null coalescing operator, always keep operator precedence in mind. In some cases, using parentheses is necessary to
obtain the desired results. For example, the expression top ?? 100 - bottom ?? 0 evaluates to top ?? (100 - bottom
?? 0)  and not to  (top ?? 100) - (bottom ?? 0).

Apex supports assignment of a single resultant record from a SOQL query, but throws an exception if there are no rows returned by the
query. The null coalescing operator can be used to gracefully deal with the case where the query doesn’t return any rows. If a SOQL
query is used as the left-hand operand of the operator and rows are returned, then the null coalescing operator returns the query results.
If no rows are returned, the null coalescing operator returns the right-hand operand.

Warning:  Salesforce recommends against using multiple SOQL queries in a single statement that also uses the null coalescing
operator.

These examples work with Account objects.

Account defaultAccount = new Account(name = 'Acme');
// Left operand SOQL is empty, return defaultAccount from right operand:
Account a = [SELECT Id FROM Account

WHERE Id = '001000000FAKEID'] ?? defaultAccount;

Assert.areEqual(defaultAccount, a);

// If there isn't a matching Account or the Billing City is null, replace the value
string city = [Select BillingCity

From Account
Where Id = '001xx000000001oAAA']?.BillingCity;

System.debug('Matches count: ' + city?.countMatches('San Francisco') ?? 0 );

Usage

There are some restrictions on using the null coalescing operator.

• You can’t use the null coalescing operator as the left side of an assignment operator in an assignment.

– foo??bar = 42;// This is not a valid assignment

– foo??bar++; // This is not a valid assignment

• SOQL bind expressions don’t support the null coalescing operator.

class X { public String query = 'xyz';}
X x = new X();
List<Account> accounts = [SELECT Name FROM Account WHERE Name = :X??query]
List<List<SObject>> moreAccounts = [FIND :X??query IN ALL FIELDS

RETURNING Account(Name)];

SEE ALSO:

Operator Precedence

Using SOQL Queries That Return One Record

Operator Precedence

Operators are interpreted in order, according to rules.

Apex uses the following operator precedence rules:

Precedence

Operators

Description

{} () ++ --

Grouping and prefix increments and decrements

~ ! -x +x (type) new

Unary operators, additive operators, type cast and object
creation

* /

+ -

<< >> >>>

Multiplication and division

Addition and subtraction

Shift Operators

< <= > >= instanceof

Greater-than and less-than comparisons, reference tests

== !=

Comparisons: equal and not-equal

&

^

|

&&

||

??

?:

Bitwise AND

Bitwise XOR

Bitwise OR

Logical AND

Logical OR

Null Coalescing

Ternary

= += -= *= /= &= <<= >>= >>>=

Assignment operators

Comments

Both single and multiline comments are supported in Apex code.

Tip:  We recommend using the standardized ApexDoc comment format to increase code readability, collaboration, and long-term
maintainability. For the full specifications, see Document Your Apex Code on page 245.

• To create a single line comment, use //. All characters on the same line to the right of the //  are ignored by the parser. For example:

Integer i = 1; // This comment is ignored by the parser

• To create a multiline comment, use  /*  and  */  to demarcate the beginning and end of the comment block. For example:

Integer i = 1; /* This comment can wrap over multiple

lines without getting interpreted by the
parser. */

Assignment Statements

An assignment statement is any statement that places a value into a variable.

An assignment statement generally takes one of two forms:

[LValue] = [new_value_expression];
[LValue] = [[inline_soql_query]];

In the forms above, [LValue]  stands for any expression that can be placed on the left side of an assignment operator. These include:

• A simple variable. For example:

Integer i = 1;
Account a = new Account();
Account[] accts = [SELECT Id FROM Account];

• A de-referenced list element. For example:

ints[0] = 1;
accts[0].Name = 'Acme';

• An sObject field reference that the context user has permission to edit. For example:

Account a = new Account(Name = 'Acme', BillingCity = 'San Francisco');

// IDs cannot be set prior to an insert call
// a.Id = '00300000003T2PGAA0';

// Instead, insert the record. The system automatically assigns it an ID.
insert a;

// Fields also must be writable for the context user
// a.CreatedDate = System.today(); This code is invalid because
//

createdDate is read-only!

// Since the account a has been inserted, it is now possible to
// create a new contact that is related to it
Contact c = new Contact(LastName = 'Roth', Account = a);

// Notice that you can write to the account name directly through the contact
c.Account.Name = 'salesforce.com';

Assignment is always done by reference. For example:

Account a = new Account();
Account b;
Account[] c = new Account[]{};
a.Name = 'Acme';
b = a;
c.add(a);

// These asserts should now be true. You can reference the data
// originally allocated to account a through account b and account list c.
System.assertEquals(b.Name, 'Acme');
System.assertEquals(c[0].Name, 'Acme');

Similarly, two lists can point at the same value in memory. For example:

Account[] a = new Account[]{new Account()};
Account[] b = a;
a[0].Name = 'Acme';
System.assert(b[0].Name == 'Acme');

In addition to  =, other valid assignment operators include  +=,  *=,  /=,  |=,  &=,  ++, and  --. See Expression Operators on page 39.

Rules of Conversion

In general, Apex requires you to explicitly convert one data type to another. For example, a variable of the Integer data type cannot be
implicitly converted to a String. You must use the  string.format  method. However, a few data types can be implicitly converted,
without using a method.

Numbers form a hierarchy of types. Variables of lower numeric types can always be assigned to higher types without explicit conversion.
The following is the hierarchy for numbers, from lowest to highest:

1.

Integer

2. Long

3. Double

4. Decimal

Note:  Once a value has been passed from a number of a lower type to a number of a higher type, the value is converted to the
higher type of number.

Note that the hierarchy and implicit conversion is unlike the Java hierarchy of numbers, where the base interface number is used and
implicit object conversion is never allowed.

In addition to numbers, other data types can be implicitly converted. The following rules apply:

• IDs can always be assigned to Strings.

• Strings can be assigned to IDs. However, at runtime, the value is checked to ensure that it is a legitimate ID. If it is not, a runtime

exception is thrown.

• The  instanceOf  keyword can always be used to test whether a string is an ID.

Additional Considerations for Data Types

Data Types of Numeric Values

Numeric values represent Integer values unless they are appended with L for a Long or with .0 for a Double or Decimal. For example,
the expression  Long d = 123;  declares a Long variable named d and assigns it to an Integer numeric value (123), which is
implicitly converted to a Long. The Integer value on the right hand side is within the range for Integers and the assignment succeeds.
However, if the numeric value on the right hand side exceeds the maximum value for an Integer, you get a compilation error. In this
case, the solution is to append L to the numeric value so that it represents a Long value which has a wider range, as shown in this
example:  Long d = 2147483648L;.

Overflow and Underflow of Data Type Values

Arithmetic computations that produce values larger than the maximum value of the current type are said to overflow and values
lower than the minimum value of the current type are said to be underflow. Apex doesn’t throw an exception for overflow and
underflow of data type values. For example,  Integer i = 2147483647 + 1; yields a value of –2147483648 because
2147483647 is the maximum value for an Integer, so adding one to it wraps the value around to the minimum negative value for
Integers: –2147483648. Similarly, subtracting one from the minimum integer -2,147,483,648 wraps the value around to the maximum
value for Integers: 2,147,483,647.

If arithmetic computations generate results larger than the maximum value for the current type, the end result will be incorrect
because the computed values that are larger than the maximum will overflow. For example, the expression Long MillsPerYear
= 365 * 24 * 60 * 60 * 1000;  results in an incorrect result because the products of Integers on the right hand side
are larger than the maximum Integer value and they overflow. As a result, the final product isn't the expected one. You can avoid
this by ensuring that the type of numeric values or variables you are using in arithmetic operations are large enough to hold the
results. In this example, append L to numeric values to make them Long so the intermediate products will be Long as well and no
overflow occurs. The following example shows how to correctly compute the amount of milliseconds in a year by multiplying Long
numeric values.

Long MillsPerYear = 365L * 24L * 60L * 60L * 1000L;
Long ExpectedValue = 31536000000L;
System.assertEquals(MillsPerYear, ExpectedValue);

Loss of Fractions in Divisions

When dividing numeric Integer or Long values, the fractional portion of the result, if any, is removed before performing any implicit
conversions to a Double or Decimal. For example, Double d = 5/3;  returns 1.0 because the actual result (1.666...) is an Integer
and is rounded to 1 before being implicitly converted to a Double. To preserve the fractional value, ensure that you are using Double
or Decimal numeric values in the division. For example,  Double d = 5.0/3.0;  returns 1.6666666666666667 because 5.0
and 3.0 represent Double values, which results in the quotient being a Double as well and no fractional value is lost.

Conversion of Date to Datetime

Apex supports both implicit and explicit casting of Date values to Datetime, with the time component being zeroed out in the
resulting Datetime value.

### Control Flow Statements

Apex provides if-else statements, switch statements, and loops to control the flow of code execution. Statements are generally executed
line by line, in the order they appear. With control flow statements, you can make Apex code execute based on a certain condition, or
have a block of code execute repeatedly.

Conditional (If-Else) Statements
The conditional statement in Apex works similarly to Java.

Switch Statements
Apex provides a  switch  statement that tests whether an expression matches one of several values and branches accordingly.

Loops
Apex supports five types of procedural loops.

Conditional (If-Else) Statements

The conditional statement in Apex works similarly to Java.

if ([Boolean_condition])

// Statement 1

else

// Statement 2

The  else  portion is always optional, and always groups with the closest  if. For example:

Integer x, sign;
// Your code
if (x <= 0) if (x == 0) sign = 0; else sign = -1;

is equivalent to:

Integer x, sign;
// Your code
if (x <= 0) {

if (x == 0) {

sign = 0;

} else {

sign = -1;

}

}

Repeated  else if  statements are also allowed. For example:

if (place == 1) {

medal_color = 'gold';

} else if (place == 2) {

medal_color = 'silver';

} else if (place == 3) {

medal_color = 'bronze';

} else {

medal_color = null;

}

Switch Statements

Apex provides a  switch  statement that tests whether an expression matches one of several values and branches accordingly.

The syntax is:

switch on expression {

when value1 { // when block 1

// code block 1

}
when value2 { // when block 2

// code block 2

}
when value3 { // when block 3

// code block 3

}
when else {

// default block, optional

// code block 4

}

}

The  when  value can be a single value, multiple values, or sObject types. For example:

when value1 {
}

when value2, value3 {
}

when TypeName VariableName {
}

The  switch  statement evaluates the expression and executes the code block for the matching  when value. If no value matches, the
when else  code block is executed. If there isn’t a  when else block, no action is taken.

Note:  There is no fall-through. After the code block is executed, the  switch  statement exits.

Apex  switch  statement expressions can be one of the following types.

• Integer

• Long

• sObject

• String

• Enum

When Blocks

Each  when  block has a value that the expression is matched against. These values can take one of the following forms.

• when  literal  {} (a when block can have multiple, comma-separated literal clauses)

• when SObjectType  identifier  {}

• when  enum_value  {}

The value  null  is a legal value for all types.

Each  when  value must be unique. For example, you can use the literal  x  only in one  when  block clause. A  when  block is matched
one time at most.

When Else Block

If no  when  values match the expression, the  when else  block is executed.

Note:  Salesforce recommends including a when else  block, especially with enum types, although it isn’t required. When you
build a  switch  statement using enum values provided by a managed package, your code might not behave as expected if a

new version of the package contains additional enum values. You can prevent this problem by including a  when else  block
to handle unanticipated values.

If you include a  when else  block, it must be the last block in the  switch  statement.

Examples with Literals

You can use literal when  values for switching on Integer, Long, and String types. String clauses are case-sensitive. For example, “orange”
is a different value than “ORANGE.”

Single Value Example

The following example uses integer literals for  when  values.

switch on i {
when 2 {

System.debug('when block 2');

}
when -3 {

System.debug('when block -3');

}
when else {

System.debug('default');

}

}

Null Value Example

Because all types in Apex are nullable, a  when  value can be  null.

switch on i {
when 2 {

System.debug('when block 2');

}
when null {

System.debug('bad integer');

}
when else {

System.debug('default ' + i);

}

}

Multiple Values Examples

The Apex  switch  statement doesn’t fall-through, but a  when  clause can include multiple literal values to match against. You can
also nest Apex  switch  statements to provide multiple execution paths within a  when  clause.

switch on i {

when 2, 3, 4 {

System.debug('when block 2 and 3 and 4');

}
when 5, 6 {

System.debug('when block 5 and 6');

}
when 7 {

System.debug('when block 7');

}

when else {

System.debug('default');

}

}

Method Example

Instead of switching on a variable expression, the following example switches on the result of a method call.

switch on someInteger(i) {

when 2 {

System.debug('when block 2');

}
when 3 {

System.debug('when block 3');

}
when else {

System.debug('default');

}

}

Example with sObjects

Switching on an sObject value allows you to implicitly perform instanceof  checks and casting. For example, consider the following
code that uses if-else statements.

if (sobject instanceof Account) {

Account a = (Account) sobject;
System.debug('account ' + a);

} else if (sobject instanceof Contact) {

Contact c = (Contact) sobject;
System.debug('contact ' + c);

} else {

System.debug('default');

}

You can replace and simplify this code with the following  switch  statement.

switch on sobject {
when Account a {

System.debug('account ' + a);

}
when Contact c {

System.debug('contact ' + c);

}
when null {

System.debug('null');

}
when else {

System.debug('default');

}

}

Note:  You can use only one sObject type per  when block.

Example with Enums

A switch  statement that uses enum when  values doesn’t require a when else  block, but it is recommended. You can use multiple
enum values per  when  block clause.

switch on season {
when WINTER {

System.debug('boots');

}
when SPRING, SUMMER {

System.debug('sandals');

}
when else {

System.debug('none of the above');

}

}

Loops

Apex supports five types of procedural loops.

These types of procedural loops are supported:

• do {statement} while (Boolean_condition);

• while (Boolean_condition) statement;

• for (initialization; Boolean_exit_condition; increment) statement;

• for (variable : array_or_set) statement;

• for (variable : [inline_soql_query]) statement;

All loops allow for loop control structures:

• break;  exits the entire loop

• continue;  skips to the next iteration of the loop

1. Do-While Loops

2. While Loops

3. For Loops

Do-While Loops

The Apex  do-while  loop repeatedly executes a block of code as long as a particular Boolean condition remains true. Its syntax is:

do {

code_block

} while (condition);

Note:  Curly braces ({}) are always required around a  code_block.

As in Java, the Apex do-while  loop does not check the Boolean condition statement until after the first loop is executed. Consequently,
the code block always runs at least once.

As an example, the following code outputs the numbers 1 - 10 into the debug log:

Integer count = 1;

do {

System.debug(count);
count++;

} while (count < 11);

While Loops

The Apex  while  loop repeatedly executes a block of code as long as a particular Boolean condition remains true. Its syntax is:

while (condition) {
code_block

}

Note:  Curly braces ({}) are required around a  code_block  only if the block contains more than one statement.

Unlike  do-while, the  while  loop checks the Boolean condition statement before the first loop is executed. Consequently, it is
possible for the code block to never execute.

As an example, the following code outputs the numbers 1 - 10 into the debug log:

Integer count = 1;

while (count < 11) {

System.debug(count);
count++;

}

For Loops

Apex supports three variations of the  for  loop:

• The traditional  for loop:

for (init_stmt; exit_condition; increment_stmt) {

code_block

}

• The list or set iteration  for loop:

for (variable : list_or_set) {

code_block

}

where  variable  must be of the same primitive or sObject type as  list_or_set.

• The SOQL  for loop:

for (variable : [soql_query]) {

code_block

}

for (variable_list : [soql_query]) {

code_block

}

Both  variable  and  variable_list  must be of the same sObject type as is returned by the  soql_query.

Note:  Curly braces ({}) are required around a  code_block  only if the block contains more than one statement.

Each is discussed further in the sections that follow.

Traditional For Loops

List or Set Iteration for Loops

Iterating Collections

Traditional For Loops

The traditional  for  loop in Apex corresponds to the traditional syntax used in Java and other languages. Its syntax is:

for (init_stmt; exit_condition; increment_stmt) {

code_block

}

When executing this type of  for  loop, the Apex runtime engine performs the following steps, in order:

1. Execute the  init_stmt  component of the loop. Note that multiple variables can be declared and/or initialized in this statement,

separated by commas.

2. Perform the  exit_condition  check. If true, the loop continues. If false, the loop exits.

3. Execute the  code_block.

4. Execute the  increment_stmt  statement.

5. Return to Step 2.

As an example, the following code outputs the numbers 1 - 10 into the debug log. Note that an additional initialization variable,  j, is
included to demonstrate the syntax:

for (Integer i = 0, j = 0; i < 10; i++) {

System.debug(i+1);

}

List or Set Iteration for Loops

The list or set iteration  for  loop iterates over all the elements in a list or set. Its syntax is:

for (variable : list_or_set) {

code_block

}

where  variable  must be of the same primitive or sObject type as  list_or_set.

When executing this type of  for  loop, the Apex runtime engine assigns  variable  to each element in  list_or_set, and
runs the  code_block  for each value.

For example, the following code outputs the numbers 1 - 10 to the debug log:

Integer[] myInts = new Integer[]{1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

for (Integer i : myInts) {

System.debug(i);

}

Iterating Collections

Collections can consist of lists, sets, or maps. Modifying a collection's elements while iterating through that collection is not supported
and causes an error. Do not directly add or remove elements while iterating through the collection that includes them.

Adding Elements During Iteration

To add elements while iterating a list, set or map, keep the new elements in a temporary list, set, or map and add them to the original
after you finish iterating the collection.

Removing Elements During Iteration

To remove elements while iterating a list, create a new list, then copy the elements you wish to keep. Alternatively, add the elements
you wish to remove to a temporary list and remove them after you finish iterating the collection.

Note:  The  List.remove  method performs linearly. Using it to remove elements has time and resource implications.

To remove elements while iterating a map or set, keep the keys you wish to remove in a temporary list, then remove them after you
finish iterating the collection.

### Classes, Objects, and Interfaces

Apex classes are modeled on their counterparts in Java. You’ll define, instantiate, and extend classes, and you’ll work with interfaces,
Apex class versions, properties, and other related class concepts.

1. Classes

As in Java, you can create classes in Apex. A class is a template or blueprint from which objects are created. An object is an instance
of a class.

2.

Interfaces
An interface is like a class in which none of the methods have been implemented—the method signatures are there, but the body
of each method is empty. To use an interface, another class must implement it by providing a body for all of the methods contained
in the interface.

3. Keywords

Apex provides the keywords  final,  instanceof,  super,  this,  transient,  with sharing  and  without
sharing.

4. Annotations

An Apex annotation modifies the way that a method or class is used, similar to annotations in Java. Annotations are defined with
an initial  @  symbol, followed by the appropriate keyword.

5. Classes and Casting

In general, all type information is available at run time. This means that Apex enables casting, that is, a data type of one class can be
assigned to a data type of another class, but only if one class is a subclass of the other class. Use casting when you want to convert
an object from one data type to another.

6. Differences Between Apex Classes and Java Classes

Apex classes and Java classes work in similar ways, but there are some significant differences.

7. Class Definition Creation

Use the class editor to create a class in Salesforce.

8. Namespace Prefix

The Salesforce application supports the use of namespace prefixes. Namespace prefixes are used in managed AppExchange packages
to differentiate custom object and field names from names used by other organizations.

9. Apex Code Versions

To aid backwards-compatibility, classes and triggers are stored with the version settings for a specific Salesforce API version.

10. Lists of Custom Types and Sorting

Lists can hold objects of your user-defined types (your Apex classes). Lists of user-defined types can be sorted.

11. Using Custom Types in Map Keys and Sets

You can add instances of your own Apex classes to maps and sets.

Classes

As in Java, you can create classes in Apex. A class is a template or blueprint from which objects are created. An object is an instance of a
class.

For example, the  PurchaseOrder  class describes an entire purchase order, and everything that you can do with a purchase order.
An instance of the  PurchaseOrder  class is a specific purchase order that you send or receive.

All objects have state and behavior, that is, things that an object knows about itself, and things that an object can do. The state of a
PurchaseOrder object—what it knows—includes the user who sent it, the date and time it was created, and whether it was flagged as
important. The behavior of a PurchaseOrder object—what it can do—includes checking inventory, shipping a product, or notifying a
customer.

A class can contain variables and methods. Variables are used to specify the state of an object, such as the object's  Name  or  Type.
Since these variables are associated with a class and are members of it, they are commonly referred to as member variables. Methods
are used to control behavior, such as  getOtherQuotes  or  copyLineItems.

A class can contain other classes, exception types, and initialization code.

An interface is like a class in which none of the methods have been implemented—the method signatures are there, but the body of
each method is empty. To use an interface, another class must implement it by providing a body for all of the methods contained in the
interface.

For more general information on classes, objects, and interfaces, see http://java.sun.com/docs/books/tutorial/java/concepts/index.html

In addition to classes, Apex provides triggers, similar to database triggers. A trigger is Apex code that executes before or after database
operations. See Triggers.

1. Apex Class Definition

2. Class Variables

Learn how to define Apex methods. Understand the differences between passing method arguments by value and passing method
arguments by reference.

4. Using Constructors

5. Access Modifiers

6. Static and Instance Methods, Variables, and Initialization Code

In Apex, you can have static methods, variables, and initialization code. However, Apex classes can't be static. You can also have
instance methods, member variables, and initialization code, which have no modifiers, and local variables.

7. Apex Properties

8. Extending a Class

You can extend a class to provide more specialized behavior.

9. Extended Class Example

Apex Class Definition

In Apex, you can define top-level classes (also called outer classes) as well as inner classes, that is, a class defined within another class.
You can only have inner classes one level deep. For example:

public class myOuterClass {

// Additional myOuterClass code here
class myInnerClass {

// myInnerClass code here

}

}

To define a class, specify the following:

1. Access modifiers:

• You must use one of the access modifiers (such as  public  or  global) in the declaration of a top-level class.

• You don’t have to use an access modifier in the declaration of an inner class.

2. Optional definition modifiers (such as  virtual,  abstract, and so on)

3. Required: The keyword  class  followed by the name of the class

4. Optional extensions or implementations or both

Note:  Avoid using standard object names for class names. Doing so causes unexpected results. For a list of standard objects, see
Object Reference for Salesforce.

Use the following syntax for defining classes:

private | public | global
[virtual | abstract | with sharing | without sharing]
class ClassName [implements InterfaceNameList] [extends ClassName]
{
// The body of the class
}

• The  private  access modifier declares that this class is only known locally, that is, only by this section of code. This is the default
access for inner classes—that is, if you don't specify an access modifier for an inner class, it’s considered  private. This keyword
can only be used with inner classes (or with top-level test classes marked with the  @IsTest  annotation).

• The  public  access modifier declares that this class is visible in your application or namespace.

• The global  access modifier declares that this class is known by all Apex code everywhere. All classes containing methods defined
with the  webservice  keyword must be declared as  global. If a method or inner class is declared as  global, the outer,
top-level class must also be defined as  global.

• The  with sharing  and  without sharing  keywords specify the sharing mode for this class. For more information, see

Use the with sharing, without sharing, and inherited sharing Keywords on page 89.

• The  virtual  definition modifier declares that this class allows extension and overrides. You can’t override a method with the

override  keyword unless the class has been defined as  virtual.

• The abstract  definition modifier declares that this class contains abstract methods, that is, methods that only have their signature

declared and no body defined.

Note:

• You can’t add an abstract method to a global class after the class has been uploaded in a Managed - Released package version.

• If the class in the Managed - Released package is virtual, the method that you can add to it must also be virtual and must have

an implementation.

• You can’t override a public or protected virtual method of a global class of an installed managed package.

For more information about managed packages, see Managed Package Types on page 751.

A class can implement multiple interfaces, but only extend one existing class. This restriction means that Apex doesn’t support multiple
inheritance. The interface names in the list are separated by commas. For more information about interfaces, see Interfaces on page 81.

For more information about method and variable access modifiers, see Access Modifiers on page 68.

Versioned Behavior Changes

In API version 65.0 and later, an abstract or override method requires a  protected,  public, or  global  access modifier. If one of
these access modifiers isn’t explicitly included in the method declaration, then method access defaults to  private. Private access is
invalid for these method types because the implementing class can’t access the abstract method. Therefore, if you attempt to declare
an abstract or override method without an allowed access modifier, you get the compilation error Abstract methods require
at least one of the following: global, public, protected.

In API version 61.0 and later, private methods are no longer overridden by an instance method with the same signature in a subclass.
This change is versioned, so to prevent the override, update your abstract or virtual classes that contain private methods to API version
61.0 or later. In API version 60.0 and earlier, if a subclass declares an instance method with the same signature as a private method in
one of its superclasses, the subclass method overrides the private method.

SEE ALSO:

### Documentation Typographical Conventions

Salesforce Help: Manage Apex Classes

Salesforce Help: Developer Console Functionality

Class Variables

To declare a variable, specify the following:

• Optional: Modifiers, such as  public  or  final, as well as  static.

• Required: The data type of the variable, such as String or Boolean.

• Required: The name of the variable.