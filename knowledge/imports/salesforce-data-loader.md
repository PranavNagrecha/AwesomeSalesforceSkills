

## Data Loader Guide
## Version 66.0, Spring ’26
Last updated: February 27, 2026

## ©
Copyright 2000–2026 Salesforce, Inc. All rights reserved. Salesforce is a registered trademark of Salesforce, Inc., as are other
names and marks. Other marks appearing herein may be trademarks of their respective owners.

## CONTENTS
Chapter 1: Data Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Chapter 2: When to Use Data Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
Chapter  3:  Install  Data  Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
Download and Install Data Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
Considerations for Installing Data Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 6
Uninstall Data Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
Chapter  4:  Configure  Data  Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
Enable  Bulk  API. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
Data Loader Behavior with Bulk API Enabled. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
Enable Bulk API 2.0. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13
Keep  Account  Teams. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
Log  In  with  Hardware  2FA. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14
Create a Secure Connection with an External Client App. . . . . . . . . . . . . . . . . . . . . . . . . . . 15
Chapter 5: Using Data Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
Data Types Supported by Data Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17
Export Data from Salesforce. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
Define Data Loader Field Mappings. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19
Insert, Update, or Delete Data Using Data Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 20
Perform  Mass  Updates. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 21
Perform  Mass  Deletes. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 21
Upload  Attachments. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
Upload Files and Links with Data Loader. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 22
Review  Data  Loader  Output  Files. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
Data  Import  Dates. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
View  the  Data  Loader  Log  File. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
Configure the Data Loader Log File. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 24
Chapter 6: Run in Batch Mode (Windows Only). . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
Installed Directories and Files. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
Encrypt from the Command Line. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
Upgrade Your Batch Mode Interface. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
Run  Batch  File  With  Windows  Command-Line  Interface. . . . . . . . . . . . . . . . . . . . . . . . . . . 28
Configure  Batch  Processes. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 29
Data  Loader  Process  Configuration  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 30
Data  Loader  Command-Line  Operations  and  Exit  Codes. . . . . . . . . . . . . . . . . . . . . . . . . . 38
Configure Database Access. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 39

Spring  Framework. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
Access External Data with Data Access Objects. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
SQL  Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
Map  Columns. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
Run  Individual  Batch  Processes. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 44
Chapter 7: Command-Line Quick Start (Windows Only) . . . . . . . . . . . . . . . . . . . . . . . 46
Data Loader Command Line Introduction. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 47
Prerequisites. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 47
Step One: Create the Encryption Key File. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 47
Step Two: Create the Encrypted Password. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
Step Three: Create the Field Mapping File. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 49
Step Four: Create the Configuration File. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 49
Step  Five:  Import  the  Data. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 51
Chapter 8: Data Loader Third-Party Licenses. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 53
Index. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 54
## Contents

CHAPTER 1Data Loader
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
Data Loader is a client application for the bulk import or export of
data. Use it to insert, update, delete, or export Salesforce records.
When importing data, Data Loader reads, extracts, and loads data
from comma-separated values (CSV) files or from a database
connection. When exporting, Data Loader outputs CSV files.
Important: Download the latest version of Data Loader.
Salesforce doesn't support older versions.
Data Loader can be used on either MacOS or Windows, and offers
these key features.
## •
An easy-to-use wizard interface for interactive use
## •
An alternative command-line interface for automated batch operations (Windows only)
## •
Support for large files with up to 150 million records when used with Bulk API 2.0
## •
Drag-and-drop field mapping
## •
Support for all objects, including custom objects
## •
Process data in both Salesforce and Database.com
## •
Detailed success and error log files in CSV format
## •
A built-in CSV file viewer
You can use Data Loader in two different ways:
## •
User interface—Specify configuration parameters and CSV files used for import and export, and
define field mappings that map field names in your import file to field names in Salesforce.
## •
Command line (Windows only)—Specify the configuration, data sources, mappings, and actions in
files. The command line enables you to set up Data Loader for automated processing.
## 1

CHAPTER 2When to Use Data Loader
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
Data Loader complements the web-based import wizards that are
accessible from the Setup menu in the online application.
Refer to the following guidelines to determine which method best
suits your business needs:
## Use Data Loader When:
## •
Data loader supports CSV files with a maximum 150,000,000
records. If you must load more than 150 million records, we
recommend you work with a Salesforce partner or visit the
AppExchange for a suitable partner product.
## •
You must load into an object that isn’t yet supported by Data Import Wizard.
## •
Your data includes complex field mappings that you must load consistently on a regular basis.
## •
You want to schedule regular data loads, such as nightly imports.
## •
You want to export your data for backup purposes.
## Use Data Import Wizard When:
## •
You’re loading less than 50,000 records.
## •
The object you must import is supported by import wizards. To see what objects they support, from
Setup, enter DataImportWizard in the QuickFind box, then select Import Wizard.
## •
You want to prevent duplicates by uploading records according to account name and site, contact
email address, or lead email address.
## •
Your target object has fewer than 50 fields.
## •
Your data doesn’t include complex field mappings.
## 2

CHAPTER 3Install Data Loader
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
Use Data Loader to insert, update, delete, and export Salesforce
records.
In this chapter ...
•Download and Install
## Data Loader
•Considerations for
## Installing Data
## Loader
•Uninstall Data Loader
## 3

Download and Install Data Loader
## USER PERMISSIONS
To use Data Loader:
•API Enabled
## AND
The appropriate user
permission for the
operation you’re doing,
for example, Create on
accounts to insert new
accounts
## AND
Bulk API Hard Delete
(only if you configure
Data Loader to use Bulk
API to hard-delete
records)
Data Loader is available for MacOS and Windows operating systems. Download to install and
configure the app on your local machine.
Data Loader is updated in every Salesforce Release. The major version number corresponds to the
currently available API version.
1.Install Java Runtime Environment (JRE) version 17 or later for your operating system. Tips for
downloading JRE:
## •
Download the JRE java package, or a JDK package that contains a JRE.
## •
If unsure of the version to choose, select the latest.
## •
Make sure to select a download that matches your operating system and CPU architecture.
## •
Some examples of sites that make JRE available include Azul Zulu (documentation), or
## Adoptium Eclipse Temurin (documentation).
2.Set your JAVA_HOME environment variable to point to the directory in which you installed the
## JRE.
3.Download the most recent version of Data Loader at
https://developer.salesforce.com/tools/data-loader.
4.Optionally, verify that the downloaded Data Loader zip file is signed by Salesforce. On macOS
or Windows, run the command jarsigner-verifydataloader_v<version>.zip. Replace <version> with
the version string in the download's filename. For example,
jarsigner-verifydataloader_v58.0.3.zip
5.After the download completes, open the .zip file and select Extract All.
6.On Windows, in the Data Loader folder, run the install.bat file.
7.On MacOS, in the Data Loader folder, run the installer.command file.
a.On MacOS 15, if there's an error that installer.command can't be opened, open the macOS Privacy & Security panel. Scroll
to the Security section, then click Open Anyway next to "install.command" was blocked to protect your Mac". Click Open
Anyway on the Open "install.command"? window.
b.On MacOS earlier than version 15, an error is shown when you first double-click install.command after extracting zip file content.
Ignore the error and click OK.
## 4
Download and Install Data LoaderInstall Data Loader

c.On macOS earlier than version 15, ignore any error regarding an unidentified developer message. Press the Control key while
clicking the installer.command file, and select Open from the menu. An error is shown:
Ignore the error and click Open.
8.Specify a directory for the Data Loader installation. Overwrite the contents if there’s an existing Data Loader directory.
9.Answer the prompts and decide your preferences to complete the installation.
To open Data Loader, use the Data Loader desktop icon, or find it from the Start menu (Windows) or in your Applications folder (macOS).
You can also run dataloader.app (macOS) or dataloader.bat (Windows) from the installation folder.
If you want to retain your settings after installing a new version of data loader, move config.properties from the configs sub-folder
of the previously installed version to the configs sub-folder of the newly installed version.
## 5
Download and Install Data LoaderInstall Data Loader

Considerations for Installing Data Loader
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
## USER PERMISSIONS
To use Data Loader:
•API Enabled
## AND
The appropriate user
permission for the
operation you’re doing,
for example, Create on
accounts to insert new
accounts
## AND
Bulk API Hard Delete
(only if you configure
Data Loader to use Bulk
API to hard-delete
records)
Before you download and install Data Loader, understand the installation and login considerations.
Each release of Data Loader has its own list of supported operating systems and hardware
requirements.
System Requirements for Windows
Data Loader is signed for Windows. See Salesforce Data Loader and the Salesforce Release Notes
for the most current information.
Note:  Salesforce no longer bundles Java with the Data Loader for Windows installer.
Download and install Java Runtime Environment (JRE) on your Windows computer.
System Requirements for macOS
See Salesforce Data Loader and the Salesforce Release Notes for the most current information.
## Installation Considerations
Over time, several versions of the Data Loader client application have been available for download.
Some earlier versions were called “AppExchange Data Loader” or “Sforce Data Loader.” You can run
different versions at the same time on one computer. However, don’t install more than one copy
of the same version. If you’ve installed the latest version and want to install it again, first remove
the version on your computer.
As of Data Loader v56.0.0, if the latest version of Data Loader isn’t compatible with your org's current
API version, your installed version of Data Loader automatically attempts to use the previous API
version to resolve compatibility with your org. For example, if your org doesn’t support API v56.0,
Data Loader v56.0.0 tries making requests with API v55.0.
Download Data Loader from the Tools section of the Salesforce Developer website.
Note:  Install Java Runtime Environment (JRE) version 17 or later, before installing Data Loader.
Tip: If you experience login issues in the command-line interface after upgrading Data Loader, try encrypting your password again
to solve the problem.
Note:  The Data Loader command-line interface is supported for Windows only.
To change the source code, download the open-source version of Data Loader from https://github.com/forcedotcom/dataloader.
## Login Considerations
## •
When using Data Loader from the command line or UI, you can log using either OAuth 2.0 Web Server Flow (Data Loader version
v64.0.1 and later) or password authentication. See OAuth Authentication for more information.
## •
If your organization restricts IP addresses, logins from untrusted IPs are blocked until they’re activated. Salesforce automatically sends
you an activation email that you can use to log in. The email contains a security token that you add to the end of your password. For
example, if your password is mypassword, and your security token is XXXXXXXXXX, you must enter
mypasswordXXXXXXXXXX to log in.
## 6
Considerations for Installing Data LoaderInstall Data Loader

## •
Salesforce Communities users always log in using OAuth 2.0 Web Server Flow (Data Loader v64.1.0 and later). To enable OAuth for
Digital Experiences, modify the config.properties.
## –
Change the portion in bold in the following line to the login URL of the site. Don’t add a forward slash (/) to the end of the line.
sfdc.oauth.Production.server=https\://login.salesforce.com
For example:
sfdc.oauth.Production.server=https\://MyDomainName.my.site.com/test
## –
Change the portion in bold in the following line to the hostname of the site.
sfdc.oauth.Production.redirecturi=https\://login.salesforce.com/services/oauth2/success
For example:
sfdc.oauth.Production.redirecturi=
https\:/MyDomainName.my.site.com/services/oauth2/success
The config.properties file is in the configs default configuration directory, which is installed in these locations.
## –
macOS: /Users/{userName}/dataloader/version/configs
## –
Windows: C:\Users\{userName}\dataloader\version\configs
## Uninstall Data Loader
You can uninstall Data Loader from your Windows or macOS machine.
Uninstall Data Loader from Windows
1.Locate and delete the Data Loader installation folder. The default installation folder is
\Users\<username>\dataloader\<version>.
2.Delete the Data Loader desktop icon link.
3.Delete the Data Loader link from the Windows Start menu.
Uninstall Data Loader from macOS
1.Locate and delete the Data Loader installation folder. The default installation folder is
/Users/<username>/dataloader/<version>.
2.Delete the Data Loader link from the Desktop folder.
3.Delete the Data Loader link from the Applications folder.
## 7
Uninstall Data LoaderInstall Data Loader

CHAPTER 4Configure Data Loader
Use the Settings menu to change the Data Loader default operation settings.
In this chapter ...
Connect to Salesforce using OAuth 2.0. See Create a Secure Connection with an External Client App.
•Enable Bulk API
1.To start Data Loader, double-click the Data Loader icon on your Desktop or in your Applications
folder.
•Enable Bulk API 2.0
•Keep Account Teams
2.Select Settings > Settings.
•Log In with Hardware
## 2FA
3.Edit the fields as needed.
DescriptionField
•Create a Secure
Connection with an
## External Client App
The maximum import batch size is 200 records
for SOAP API and 10000 records for Bulk API. If
## Importbatchsize
the Use SOAPAPI option is selected, then
both ImportBatchSize and Export
BatchSize are used. If the Use Bulk
API option is selected, then only Import
BatchSize is used. If the Use Bulk
API 2.0 option is selected, then neither
batch size is used because Bulk API 2.0 handles
batch size automatically.
For more information about working with Bulk
API batches, see General Guidelines for Data
Loads in the Bulk API 2.0 and Bulk API Developer
## Guide.
Select this option to insert blank mapped values
as null values during data operations. When
## Insertnullvalues
you’re updating records, this option instructs
Data Loader to overwrite existing data in
mapped fields.
This option isn’t available if either the Use
BulkAPI or the Use BulkApi 2.0
option is selected.Empty field values are ignored
when you update records using either API. To
set a field value to null when either API option
is selected, use a field value of #N/A in the
import CSV file.
Specify the ID of the assignment rule to use for
inserts, updates, and upserts. This option applies
## Assignmentrule
to inserts, updates, and upserts on cases and
leads. The assignment rule overrides Owner
values in your CSV file.
## 8

DescriptionField
Enter the URL of the Salesforce server with which
you want to communicate. For example, if you’re
## Serverhost
loading data into a sandbox, change the URL to
https://MyDomainName--SandboxName.sandbox.my.salesforce.com.
By default, Salesforce resets the URL after login
to the one specified in Serverhost. To turn
off this automatic reset, disable this option.
ResetURL on Login
Compression enhances the performance of Data
Loader and is turned on by default. Disabling
## Compression
compression is helpful when debugging the
underlying SOAP messages. To turn off
compression, enable this option.
Specify how many seconds Data Loader waits
to receive a response back from the server before
returning an error for the request.
## Timeout
For a single SOAP export or SOAP query
operation (if the Use SOAPAPI option is
ExportBatchSize
selected), records are returned from Salesforce
in batches of this size. Larger values can improve
performance but use more memory on the
client.
The default is 500; the minimum is 200, and the
maximum is 2,000. There’s no guarantee that
the requested batch size requested is the actual
batch size; changes are sometimes made to
maximize performance.
Select this option to generate success and error
files when exporting data.
## Generatestatusfilesfor
exports
Select this option to force files to open in UTF-8
encoding, even if they were saved in a different
format.
Readall CSVswithUTF-8
encoding
Select this option to force files to be written in
UTF-8 encoding.
Writeall CSVswithUTF-8
encoding
Select this option to support the date formats
dd/MM/yyyy and dd/MM/yyyy
HH:mm:ss.
## Use Europeandateformat
Select this option to truncate data in the
following types of fields when loading that data
## Allowfieldtruncation
into Salesforce: Email, Multi-select Picklist, Phone,
Picklist, Text, and Text (Encrypted).
## 9
## Configure Data Loader

DescriptionField
In Data Loader versions 14.0 and earlier, Data
Loader truncates values for fields of those types
if they’re too large. In Data Loader version 15.0
and later, the load operation fails if a value is
specified that is too large.
Selecting this option allows you to specify that
the previous behavior, truncation, be used
instead of the new behavior in Data Loader
versions 15.0 and later. This option is selected
by default and has no effect in versions 14.0 and
earlier.
This option isn’t available if either the Use
BulkAPI or the Use BulkApi 2.0
option is selected. In that case, the load
operation fails for the row if a value is specified
that is too large for the field.
Select this option if your CSV file uses commas
to delimit records.
Allowcommaas a CSV delimiter
Select this option if your CSV file uses tab
characters to delimit records.
Allowtab as a CSV delimiter
Select this option if your CSV file uses a character
other than a comma or tab to delimit records.
Allowothercharactersas CSV
delimiters
The characters in this field are used only if the
Allow other characters as CSV delimiters
## Otherdelimiters(enter
multiplevalueswithno
separator;for example,!+?)
option is selected. For example, if you use the |
(pipe) character to delimit data records, enter
that character in this field.
Select this option to use Bulk API to insert,
update, upsert, delete, and hard-delete records.
Use BulkAPI
Bulk API is optimized to load or delete many
records asynchronously. It’s faster than the
default SOAP-based API due to parallel
processing and fewer network round-trips.
You can hard delete records when you configure
Data Loader to Use BulkAPI. Keep in mind
that hard-deleted records are immediately
deleted and can’t be recovered from the Recycle
## Bin.
If Use BulkAPI is selected, you can use
serial processing instead of parallel processing.
Enableserialmodefor BulkAPI
Processing in parallel can cause database
contention. When contention is severe, the load
## 10
## Configure Data Loader

DescriptionField
can fail. Serial mode processes batches one at a
time, and can be a solution to database
contention (locking). However, it can increase
the processing time for a load.
This option is only available if the Use Bulk
API option is selected.
If Use BulkAPI is selected, you can use
Bulk API to upload zip files containing binary
UploadBulkAPI Batchas Zip
## File
attachments, such as Attachment records or
Salesforce CRM Content.
Select this option to use Bulk API 2.0 to insert,
update, upsert, delete, and hard-delete records.
Use BulkAPI 2.0
Bulk API 2.0 is optimized to load or delete many
records asynchronously. It’s faster than the
default SOAP-based API due to parallel
processing and fewer network round-trips.
Supports all OAuth 2.0 flows supported by other
Salesforce REST APIs. Bulk API 2.0's design is more
consistent and better integrated with other
Salesforce APIs. Bulk API 2.0 also has the
advantage of future innovation.
You can hard-delete records when you configure
Data Loader to Use BulkAPI 2.0. Keep
in mind that hard-deleted records are
immediately deleted and can’t be recovered
from the Recycle Bin.
Select this option to specify a default time zone.
If a date value doesn’t include a time zone, this
value is used.Valid values are any time zone
TimeZone
identifier that can be passed to the Java
getTimeZone(java.lang.String)
method. The value can be a full name such as
America/Los_Angeles, or a custom ID
such as GMT-8:00.
## •
If no value is specified, the time zone of the
computer where Data Loader is installed is
used.
## •
If an incorrect value is entered, GMT is used
as the time zone and this fact is noted in the
Data Loader log.
The host name of the proxy server, if applicable.Proxyhost
The proxy server port.Proxyport
## 11
## Configure Data Loader

DescriptionField
The username for proxy server authentication.Proxyusername
The password for proxy server authentication.Proxypassword
The name of the Windows domain used for
NTLM authentication.
ProxyNTLMdomain
If your last operation failed, you can use this
setting to begin where the last successful
operation finished.
Startat row
4.Click OK to save your settings.
Data Loader settings are saved in the properties.csv file. To find the path to the settings file,
select Settings from the Settings menu, then click Help in the upper right of the Settings window. The
path to the settings file is shown at the bottom of the Help window. Click the file name to view its
contents.
## 12
## Configure Data Loader

Enable Bulk API
Bulk API is optimized to load or delete a large number of records asynchronously. It’s faster than the SOAP-based API due to parallel
processing and fewer network round-trips. By default, Data Loader uses the SOAP-based API to process records.
To configure Data Loader to use Bulk API for inserting, updating, upserting, deleting, and hard deleting records:
1.To start Data Loader, double-click the Data Loader icon on your Desktop or in your Applications folder.
2.Choose Settings > Settings.
3.Select the Use BulkAPI option.
4.Click OK.
## Note:
## •
You can also select the Enableserialmodefor BulkAPI option. Processing in parallel can cause database
contention. When contention is severe, the load can fail. Serial mode processes batches one at a time, however it can increase
the processing time for a load.
## •
Caution: You can hard delete records when you configure Data Loader to Use BulkAPI. Keep in mind that hard-deleted
records are immediately deleted and can’t be recovered from the Recycle Bin.
Data Loader Behavior with Bulk API Enabled
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
Enabling the Bulk API in Data Loader lets you load or delete a large number of records faster than
using the default SOAP-based API. However, there are some differences in behavior in Data Loader
when you enable the Bulk API. One important difference is that it allows you to execute a hard
delete if you have the permission and license.
The following settings are not available on the Settings > Settings page in Data Loader when the
Use BulkAPI option is selected:
DescriptionSetting
This option enables Data Loader to insert blank mapped values as null
values during data operations when the Bulk API is disabled. Empty field
values are ignored when you update records using the Bulk API. To set
Insert null values
a field value to null when the Use BulkAPI option is selected,
use a field value of #N/A.
This option directs Data Loader to truncate data for certain field types
when the Bulk API is disabled. A load operation fails for the row if a value
Allow field truncation
is specified that is too large for the field when the Use BulkAPI
option is selected.
Enable Bulk API 2.0
Select this option to use Bulk API 2.0 to insert, update, upsert, delete, and hard-delete records. Bulk API 2.0 is optimized to load or delete
many records asynchronously. Supports all OAuth 2.0 flows supported by other Salesforce REST APIs. Bulk API 2.0's design is more
consistent and better integrated with other Salesforce APIs. Bulk API 2.0 also has the advantage of future innovation. By default, Data
Loader uses the SOAP-based API to process records.
## 13
Enable Bulk APIConfigure Data Loader

To configure Data Loader to use Bulk API 2.0 for inserting, updating, upserting, deleting, and hard deleting records:
1.To start Data Loader, double-click the Data Loader icon on your Desktop or in your Applications folder.
2.Choose Settings > Settings.
3.Select the Use BulkAPI 2.0 option.
4.Click OK.
Note:  Caution: You can hard delete records when you configure Data Loader to Use BulkAPI 2.0. Keep in mind that
hard-deleted records are immediately deleted and can’t be recovered from the Recycle Bin.
## Keep Account Teams
Configure Data Loader to keep Account Teams when mass updating Account Owners.
To keep Account Teams intact when mass-updating account owners
1.Use Data Loader version 56.0.3 or later.
2.Close Data Loader. It's important to make the following changes only with Data Loader closed.
3.Open the config.properties file.
The config.properties file is in the configs default configuration directory, which is installed in these locations.
## •
macOS: /Users/{userName}/dataloader/version/configs
## •
Windows: C:\Users\{userName}\dataloader\version\configs
4.In the config.properties file, set the property sfdc.useBulkApi=false
5.In the config.properties file, set the property process.keepAccountTeam=true
6.Save and close the config.properties file.
7.To start Data Loader, double-click the Data Loader icon on your Desktop or in your Applications folder.
Note:  To keep Account Teams intact, the uploaded .csv file must have the same value for all Current Account owner records.
Likewise, the New Account Owner records must all have the same value. Otherwise, the operation fails and the Account Owners
are not updated. For example, if the current Account owner of all records is "John Doe" and the new Account owner of all records
is "Jane Smith" in a csv file, the operation succeeds if there are no other issues. However, if all records have "John Doe" as the
current Account owner and the new Account owner of all but one record is "Jane Smith", the operation fails.
Log In with Hardware 2FA
Learn how to log in to Data Loader with OAuth and hardware 2FA.
You must create a Salesforce External Client App before using OAuth and two-factor authentication (2FA). See Create a Secure Connection
with an External Client App.
To log in using OAuth and 2FA:
1.Choose an action from Data Loader's main menu (for example, Insert, Update, Export).
2.In the Step 1: Log In screen, select OAuth, and select your Environment.
3.Click Log in.
4.To complete the login process, follow the instructions in the Login from Browser window. By clicking the Link to Verification Page,
you’re guided through a 2FA login sequence in your browser. You can use a hardware key, if necessary.
## 14
Keep Account TeamsConfigure Data Loader

Create a Secure Connection with an External Client App
Use a Salesforce external client app to create a secure connection from Data Loader to your Salesforce org.
These instructions are for Data Loader version 64.0.2 or later.
Before configuring Data Loader, create an external client app with OAuth enabled. See Configure the External Client OAuth Settings.
Configure the app with these settings:
## •
Use the callback URL http://localhost:7171/OauthRedirect. If you choose a different port number, be sure to note
it.
## •
Select Require Proof Key for Code Exchange (PKCE) extension for Supported Authorization Flows to require Proof Key for
## Code Exchange.
## •
Deselect Require secret for Web Server Flow to avoid storing the Consumer Secret in Data Loader.
## •
For OAuth scopes, select Perform requests at any time (refresh_token, offline_access) and Manage user data via APIs (api).
After you create the client app, use it to get the information you need to configure Data Loader.
1.From Setup, in the Quick Find box, enter externalclient, and then select External Client App Manager.
2.Select the external client app you created, then select the Settings tab.
3.In the OAuth Settings section, click Consumer Key and Secret.
This opens the Consumer Details page.
4.In Data Loader, select Settings > Settings.
5.In Authentication host domain URL for Production, enter your org's base URL.
The base My Domain URL has the format https://mycompany.my.salesforce.com. For a sandbox org, enter the
sandbox URL in Authentication host domain URL for Sandbox.
6.In the Consumer Details page, copy the Consumer Key.
## •
Paste it into External Client App Consumer Key (Production) for a production org.
## •
Paste it into External Client App Consumer Key (Sandbox) for a sandbox org.
Leave the External Client App Consumer Secret fields empty.
7.If you specified a port other than 7171 for the external client app's callback URL, enter that port number in OAuth PKCE callback
port.
8.Click OK.
Data Loader can now use OAuth 2.0 Web Server Flow to authenticate when logging into a Salesforce org.
9.From Setup, in the Quick Find box, enter OAuth and select Connected Apps OAuth Usage to view a list of apps with OAuth
access.
10.Click Block to block the Dataloader Partner and Dataloader Bulk connected apps.
## 15
Create a Secure Connection with an External Client AppConfigure Data Loader

CHAPTER 5Using Data Loader
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
Using Data Loader, you can perform various operations which
include exporting data, defining field mappings, inserting, updating,
and deleting data, performing mass updates and mass deletes,
uploading attachments and content, and reviewing output files.
In this chapter ...
•Data Types
Supported by Data
## Loader
•Export Data from
## Salesforce
•Define Data Loader
## Field Mappings
•Insert, Update, or
## Delete Data Using
## Data Loader
•Upload Attachments
•Upload Files and
Links with Data
## Loader
•Review Data Loader
## Output Files
•Data Import Dates
•View the Data Loader
## Log File
•Configure the Data
## Loader Log File
## 16

Data Types Supported by Data Loader
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
Data Loader supports these data types.
## •
## Base64
String path to file (converts the file to a base64–encoded array). Base64 fields are only used to
insert or update attachments and Salesforce CRM Content. For more information, see Upload
Attachments on page 22 and Upload Content with the Data Loader on page 22.
## •
## Boolean
## –
True values (case insensitive) = yes, y, true, on, 1
## –
False values (case insensitive) = no, n, false, off, 0
## •
## Date Formats
We recommend you specify dates in the format yyyy-MM-ddTHH:mm:ss.SSS+/-HHmm.
## –
yyyy is the four-digit year
## –
MM is the two-digit month (01-12)
## –
dd is the two-digit day (01-31)
## –
HH is the two-digit hour (00-23)
## –
mm is the two-digit minute (00-59)
## –
ss is the two-digit seconds (00-59)
## –
SSS is the three-digit milliseconds (000-999)
## –
+/-HHmm is the Zulu (UTC) time zone offset
The following date formats are also supported:
## –
yyyy-MM-dd'T'HH:mm:ss.SSS'Z'
## –
yyyy-MM-dd'T'HH:mm:ss.SSSPacificStandardTime
## –
yyyy-MM-dd'T'HH:mm:ss.SSSPacificStandardTime
## –
yyyy-MM-dd'T'HH:mm:ss.SSSPST
## –
yyyy-MM-dd'T'HH:mm:ss.SSSPST
## –
yyyy-MM-dd'T'HH:mm:ss.SSSGMT-08:00
## –
yyyy-MM-dd'T'HH:mm:ss.SSSGMT-08:00
## –
yyyy-MM-dd'T'HH:mm:ss.SSS-800
## –
yyyy-MM-dd'T'HH:mm:ss.SSS-800
## –
yyyy-MM-dd'T'HH:mm:ss
## –
yyyy-MM-ddHH:mm:ss
## –
yyyyMMdd'T'HH:mm:ss
## –
yyyy-MM-dd
## –
MM/dd/yyyyHH:mm:ss
## –
MM/dd/yyyy
## –
yyyyMMdd
Note these tips for date formats.
## 17
Data Types Supported by Data LoaderUsing Data Loader

## –
To enable date formats that begin with the day rather than the month, select the Use Europeandateformat box in
the Settings dialog. European date formats are dd/MM/yyyy and dd/MM/yyyyHH:mm:ss.
## –
If your computer's locale is east of Greenwich Mean Time (GMT), we recommend that you change your computer setting to
GMT in order to avoid date adjustments when inserting or updating records.
## –
Only dates within a certain range are valid. The earliest valid date is 1700-01-01T00:00:00Z GMT, or just after midnight on January
1, 1700. The latest valid date is 4000-12-31T00:00:00Z GMT, or just after midnight on December 31, 4000. These values are offset
by your time zone. For example, in the Pacific time zone, the earliest valid date is 1699-12-31T16:00:00, or 4:00 PM on December
## 31, 1699.
## •
## Double
Standard double string
## •
## ID
A Salesforce ID is a case-sensitive 15-character or case–insensitive 18-character alphanumeric string that uniquely identifies a particular
record.
Tip:  To ensure data quality, make sure that all Salesforce IDs you enter in Data Loader are in the correct case.
## •
## Integer
Standard integer string
## •
## String
All valid XML strings; invalid XML characters are removed.
Export Data from Salesforce
## USER PERMISSIONS
To export records:
•Read on the records
To export all records:
•Read on the records
Extract data from a Salesforce object using Data Loader.
1.To start Data Loader, double click the Data Loader icon on your Desktop or in your Applications
folder.
2.Click Export. If you want to also export archived activity records and soft-deleted records, click
Export All instead.
3.Enter your Salesforce username and password, and click Log in.
4.When you’re logged in, click Next. (You are not asked to log in again until you log out or close
the program.)
If your organization restricts IP addresses, logins from untrusted IPs are blocked until they’re activated. Salesforce automatically sends
you an activation email that you can use to log in. The email contains a security token that you add to the end of your password. For
example, if your password is mypassword, and your security token is XXXXXXXXXX, you must enter
mypasswordXXXXXXXXXX to log in.
5.Choose an object. For example, select the Account object. If your object name isn’t listed, select Show all objects to see all the
objects that you can access. The objects are listed by localized label name, with the developer name in parentheses. For object
descriptions, see the Salesforce Object Reference.
6.Select the CSV file to export the data to. You can choose an existing file or create a file.
If you select an existing file, the export replaces its contents. To confirm the action, click Yes, or choose another file by clicking No.
7.Click Next.
## 18
Export Data from SalesforceUsing Data Loader

8.Create a SOQL query for the data export. For example, select Id and Name in the query fields, and click Finish. As you follow the
next steps, the CSV viewer displays all the Account names and their IDs. SOQL is the Salesforce Object Query Language. Similar to
the SELECT command in SQL, with SOQL, you can specify the source object, a list of fields to retrieve, and conditions for selecting
rows in the source object.
## •
Choose the fields you want to export.
## •
Optionally, select conditions to filter your dataset. If you do not select any conditions, all the data to which you have read access
is returned.
## •
Review the generated query and edit if necessary.
Tip:  You can use a SOQL relationship query to include fields from a related object. For example:
SelectName,Pricebook2Id,Pricebook2.Name,Product2Id,Product2.ProductCodeFROM
PricebookEntryWHEREIsActive= true
## Or:
SelectId, LastName,Account.NameFROMContact
When using relationship queries in the Data Loader, the fully specified field names are case-sensitive. For example, using
ACCOUNT.NAME instead of Account.Name does not work.
Data Loader doesn’t support nested queries or querying child objects. For example, queries similar to the following return an
error:
SELECTAmount,Id, Name,(SELECTQuantity,ListPrice,
PriceBookEntry.UnitPrice,PricebookEntry.Name,
PricebookEntry.product2.FamilyFROMOpportunityLineItems)
FROMOpportunity
Also, Data Loader doesn’t support queries that use polymorphic relationships. For example, the following query results in an
error:
SELECTId, Owner.Name,Owner.Type,Owner.Id,SubjectFROMCase
9.Click Finish, then click Yes to confirm.
A progress information window reports the status of the operation. After the operation completes, a confirmation window summarizes
your results.
10.To view the CSV file. click View Extraction, or to close, click OK.
## Note:
## •
Data Loader currently does not support exporting attachments. As a workaround, use the weekly export feature in the online
application to export attachments.
## •
If you select compound fields for export in the Data Loader, they cause error messages. To export values, use individual field
components.
## Define Data Loader Field Mappings
When you insert, delete, or update files, use Data Loader's Mapping Dialog window to associate Salesforce fields with the columns of
your CSV file.
## 19
Define Data Loader Field MappingsUsing Data Loader

1.To automatically match fields with columns, click Auto-Match Fields to Columns. The Data Loader populates the list at the bottom
of the window based on the similarity of field and column names. For a delete operation, automatic matching works only on the ID
field.
2.To manually match fields with columns, click and drag fields from the list of Salesforce fields at the top to the list of CSV column
header names at the bottom. For example, if you are inserting new Account records where your CSV file contains the names of new
accounts, click and drag the Name field to the right of the NAME column header field.
3.Optionally, click Save Mapping to save this mapping for future use. Specify a name for the SDL mapping file. If you select an existing
file, the export replaces its contents. To confirm the action, click Yes, or choose another file by clicking No.
4.Click OK to use your mapping for the current operation.
Insert, Update, or Delete Data Using Data Loader
## USER PERMISSIONS
Create on the recordTo insert records:
Edit on the recordTo update records:
Create or Edit on the recordTo upsert records:
Delete on the recordTo delete records:
Delete on the recordTo hard delete records:
Modify All DataTo mass delete records:
Use the Data Loader wizards to add, modify, or delete records. The upsert wizard combines inserting and updating a record. If a record
in your file matches an existing record, the existing record is updated with the values in your file. If no match is found, a new record is
created. When you hard-delete records, the deleted records are not stored in the Recycle Bin and are eligible for deletion. For more
information, see Configure Data Loader.
1.To start Data Loader, double click the Data Loader icon on your Desktop or in your Applications folder.
2.Click Insert, Update, Upsert, Delete, or Hard Delete. These commands are also listed in the File menu.
3.Enter your Salesforce username and password. To log in, click Log in. When you are logged in, click Next. (Until you log out or close
the program, you are not asked to log in again.)
If your organization restricts IP addresses, logins from untrusted IPs are blocked until they’re activated. Salesforce automatically sends
you an activation email that you can use to log in. The email contains a security token that you add to the end of your password. For
example, if your password is mypassword, and your security token is XXXXXXXXXX, you must enter
mypasswordXXXXXXXXXX to log in.
4.Choose an object. For example, if you are inserting Account records, select Account. If your object name does not display in the
default list, select Show all objects to see a complete list of the objects that you can access. The objects are listed by localized label
name, with the developer name noted in parentheses.
Note:  Data Loader deletes records based on the IDs in the CSV file, not the object selected.
5.To select your CSV file, click Browse. For example, if you are inserting Account records, you could specify a CSV file called
insertaccounts.csv containing a Name column for the names of the new accounts.
## 20
Insert, Update, or Delete Data Using Data LoaderUsing Data Loader

6.Click Next. After the object and CSV file are initialized, click OK.
7.If you are performing an upsert, your CSV file must contain a column of ID values for matching against existing records. The column
is either an external ID (a custom field with the External ID attribute) or ID (the Salesforce record ID).
a.From the dropdown list, select which field to use for matching. If the object has no external ID fields, ID is used. Click Next to
continue.
b.If your file includes the external IDs of an object that has a relationship to your chosen object, enable that external ID for record
matching by selecting its name from the dropdown list. If you make no selection, you can use the related object’s ID field for
matching by mapping it in the next step. Click Next to continue.
8.Define how the columns in your CSV file map to Salesforce fields. To select an existing field mapping, click Choose an Existing
Map. To create or modify a map, click Create or Edit a Map. Click Next.
9.For each operation, the Data Loader generates two unique CSV log files. One file name starts with “success,” and the other starts
with “error.” Click Browse to specify a directory for these files.
10.To complete the operation, click Finish, and then click Yes to confirm. As the operation proceeds, a progress information window
reports the status of the data movement.
11.To view your success or error files, click View Successes or View Errors. To close the wizard, click OK .
## Tip:
## •
If you are updating or deleting large amounts of data, review Perform Mass Updates and Perform Mass Deletes for tips and
best practices.
## •
There is a 5-minute limit to process 100 records when the Bulk API is enabled. If it takes longer than 10 minutes to process a
file, the Bulk API places the remainder of the file back in the queue for later processing. If the Bulk API continues to exceed the
10-minute limit on subsequent attempts, the file is placed back in the queue and reprocessed up to 10 times before the
operation is permanently marked as failed. Even if the processing fails, some records could have completed successfully, so
check the results. If you get a timeout error when loading a file, split your file into smaller files and try again.
## Perform Mass Updates
Use data Loader to update a large number of records at one time.
1.Obtain your data by performing an export of the objects you wish to update, or by running a report. Make sure your report includes
the record ID.
2.As a backup measure, save an extra copy of the generated CSV file.
3.Open your working file in a CSV editor such as Excel, and update your data.
4.Launch Data Loader, then click Update. Note that matching is done according to record ID.
5.After the operation, review your success and error log files.
6.If you made a mistake, use the backup file to update the records to their previous values.
## Perform Mass Deletes
## USER PERMISSIONS
To mass delete records:
•Modify All Data
Use Data Loader to delete a large number of records at one time. The total number of records you
can delete depends on which API you've configured Data Loader to use.
1.As a backup measure, export the records you wish to delete, being sure to select all fields. Save
an extra copy of the generated CSV file.
## 21
Perform Mass UpdatesUsing Data Loader

2.Next, export the records you wish to delete, this time using only the record ID as the desired criterion.
3.Launch the Data Loader and follow the delete or hard delete wizard. Map only the record ID column.
4.After the operation, review your success and error log files.
## Upload Attachments
Use Data Loader to upload attachments to Salesforce.
Before uploading attachments, note the following:
## •
If you intend to upload with Bulk API, verify that Upload Bulk API Batch as Zip File on the Settings > Settings page is enabled.
## •
If you are migrating attachments from a source Salesforce org to a target org, begin by requesting a data export for the source org.
On the Schedule Export page, select Include Attachments to include the Attachment.csv file in your export. You can use
this CSV file to upload the attachments. .
Confirm that the CSV file you want to use for attachment importing contains these required columns. Each column represents a Salesforce
field. The CSV file can also include other optional Attachment fields, such as Description.
## •
ParentId—Salesforce ID of the parent record
## •
Name—Name of the attachment file, such as myattachment.jpg
## •
Body—Absolute path to the attachment on your local drive
Make sure that the values in the Body column contain the full path of the attachments on your computer. For example, if an attachment
named myattachment.jpg is the folder C:\Export, Body must specify C:\Export\myattachment.jpg. Your CSV
file looks like this example:
ParentId,Name,Body
50030000000VDowAAG,attachment1.jpg,C:\Export\attachment1.jpg
701300000000iNHAAY,attachment2.doc,C:\Export\files\attachment2.doc
50030000000VJowBBG,attachment_word_document.doc,C:\Export\attachment_word_document.doc
Proceed with an insert or upsert operation (see Insert, Update, or Delete Data Using Data Loader on page 20). For the select data objects
step, select Show all Salesforce objects and the attachment object name in the list.
Upload Files and Links with Data Loader
Use Data Loader to bulk upload files and links into Salesforce.
Before uploading documents or links, note the following.
## •
If you intend to upload with Bulk API, verify that UploadBulkAPI Batchas Zip File on the Settings > Settings
page is enabled.
## •
When you upload a document from your local drive using Data Loader, specify the path in the VersionData and
PathOnClient fields in the CSV file. VersionData identifies the location and extracts the format, and PathOnClient
identifies the type of document being uploaded.
## •
When you upload a link using the Data Loader, specify the URL in ContentUrl. Don’t use PathOnClient or VersionData
to upload links.
## •
If you’re updating content that you’ve already uploaded:
## –
Perform the Insert function.
## 22
Upload AttachmentsUsing Data Loader

## –
Include a ContentDocumentId column with an 18-character ID. Salesforce uses this information to determine that you’re
updating content. When you map the ContentDocumentId, the updates are added to the content file. If you don’t include
the ContentDocumentId, the content is treated as new, and the content file isn’t updated. Visit ContentDocument to learn more.
1.Create a CSV file with the following fields.
DescriptionField
The file nameTitle
(Optional.) The file or link description. If there are commas in the description, use double quotes around
the text.
## Description
The complete file path on your local drive (for uploading documents only). Files are converted to base64
encoding on upload. This action adds approximately 30% to the file size.
VersionData
The complete file path on your local drive (for uploading documents only).PathOnClient
The URL (for uploading links only).ContentUrl
(Optional). The file owner, defaults to the user uploading the file.OwnerId
The library ID.FirstPublishLocationId
The record type ID.
To determine the RecordTypeId values for your organization using Data Loader, follow the steps in
Exporting Data. The following is a sample SOQL query:
SelectId, NameFROMRecordTypeWHERESobjectType= 'ContentVersion'
RecordTypeId
Optional tagTagsCsv
A sample CSV file is:
Title,Description,VersionData,PathOnClient,OwnerId,FirstPublishLocationId,RecordTypeId,TagsCsv
testfile,"Thisis a testfile,use for bulk
upload",c:\files\testfile.pdf,c:\files\testfile.pdf,005000000000000,058700000004Cd0,012300000008o2sAQG,one
2.Upload the CSV file for the ContentVersion object (see Insert, Update, or Delete Data Using Data Loader on page 20). All documents
and links are available in the specified library.
## Review Data Loader Output Files
After an import or export, Data Loader generates two CSV output files that contain the results of the operation. One file name begins
with success, and the other starts with error. Both files have the extension .csv. Use the Data Loader CSV file viewer to open
the files. Specify the folder containing success and error CSV files in the Finish step of an operation.
Note:  Export operations don’t generate a success file by default. To generate a success file when exporting data, check Generate
status files for exports in the Advanced Settings dialog.
1.Choose View > View CSV.
2.Specify the number of rows to view. Each row in the CSV file corresponds to one Salesforce record. The default is 1,000.
## 23
Review Data Loader Output FilesUsing Data Loader

3.To view a specific CSV file, click Open CSV. To view the last success file, click Open Success. To view the last error file, click Open
## Error.
4.To open the file in an external program, such as Excel, click Open in External Program.
The success file contains the successfully loaded records, including a column with the newly generated record IDs. The error file
contains the rejected records, with a column that describes why the load failed. If the object you’re exporting has a column named
“success” or “error”, your output file columns could display incorrect information. To avoid this problem, rename the columns.
5.To return to the CSV Chooser window, click Close. To exit the window, click OK. To generate success files when exporting data,
select Generatestatusfilesfor exports.
## Data Import Dates
Limits for importing data with Data Loader.
The following limits apply to data imported using Data Loader.
Only dates within a certain range are valid. The earliest valid date is 1700-01-01T00:00:00Z GMT, or just after midnight on January 1,
- The latest valid date is 4000-12-31T00:00:00Z GMT, or just after midnight on December 31, 4000. These values are offset by your
time zone. For example, in the Pacific time zone, the earliest valid date is 1699-12-31T16:00:00, or 4:00 PM on December 31, 1699.
When using Data Loader version 28.0 and later, the maximum field size for imported CSV files is 32,000 characters.
View the Data Loader Log File
If you need to investigate a problem with Data Loader, or if requested by Salesforce Customer Support, you can access log files that track
the operations and network connections made by Data Loader.
## •
The log file, sdl.log, contains a detailed chronological list of Data Loader log entries. Log entries marked “INFO” are procedural
items, such as logging in to and out of Salesforce. Log entries marked “ERROR” are problems such as a submitted record missing a
required field. The log file can be opened with commonly available text editor programs, such as Microsoft Notepad.
## •
If you are using Data Loader for Windows, view the log file by entering %TEMP%\sdl.log in either the Run dialog or the Windows
Explorer address bar.
## •
If you are using Data Loader for Mac OSX, view the log file by opening the terminal and entering open$TMPDIR/sdl.log.
## •
If you are having login issues from the UI, you need to obtain a new security token.
Configure the Data Loader Log File
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
You can customize the Data Loader log file for advanced troubleshooting and tracking.
log-conf.xml
The log-conf.xml file is included with the Data Loader installer version 35.0 and later. To
change the location of the log-conf.xml file, specify the full path, incuding the full file name, in the
LOG4J_CONFIGURATION_FILE environment variable.
## •
In Windows, the log-conf.xml file is at
C:\Users\{userName}\dataloader\version\configs
## 24
Data Import DatesUsing Data Loader

## •
In macOS, the log-conf.xml file is at /Users/{userName}/dataloader/version/configs
## Configure Log Levels
Change @LOG_LEVEL@ to TRACE, DEBUG, INFO, WARN, ERROR, or FATAL for the needed level of log tracking. For Log4J log
levels, see https://logging.apache.org/log4j/2.0/manual/architecture.html.
To implement enhanced logging, use a copy of log-conf.xml.
## 25
Configure the Data Loader Log FileUsing Data Loader

CHAPTER 6Run in Batch Mode (Windows Only)
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
You can run Data Loader in batch mode from the Windows
command line. Batch mode runs a series of Data Loader processes
in a certain order using a batch file. You can rerun the same
sequence of processes using an executable .bat file.
We recommend that you set the JAVA_HOME environment
variable to the directory where Zulu OpenJDK is installed. Doing so
ensures that you can run Data Loader in batch mode from the
command line.
In this chapter ...
•Installed Directories
and Files
•Encrypt from the
## Command Line
•Upgrade Your Batch
## Mode Interface
•Run Batch File With
## Windows
Command-Line
## Interface
Note:  The Data Loader command-line interface is supported
for Windows only.
Note:  If you’re batch mode from the command line with a version earlier than 8.0, upgrade your
batch mode interface.
•Configure Batch
## Processes
•Data Loader Process
## Configuration
## Parameters
•Data Loader
Command-Line
Operations and Exit
## Codes
•Configure Database
## Access
•Map Columns
•Run Individual Batch
## Processes
## 26

Installed Directories and Files
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
In version 8.0 and later, installing the Data Loader adds several directories under the installation
directory that are needed for automated batch processing.
Note:  The Data Loader command-line interface is supported for Windows only.
## •
bin—Contains the batch files encrypt.bat for encrypting passwords and process.bat
for running batch processes.
For information on running Data Loader from the command-line, see Run Batch File With
Windows Command-Line Interface on page 28.
## •
configs—The default configuration directory. Contains the configuration files
config.properties, Loader.class, and log-conf.xml.
The config.properties file that is generated when you modify the Settings dialog in the graphical user interface is in
C:\Users\{userName}\dataloader\version\configs.
Data Loader runs the operation, file, or map listed in the configuration file that you specify. If you don’t specify a configuration
directory, the current directory is used.
## •
samples—Contains subdirectories of sample files for reference.
## File Path Convention
The file paths provided in these topics start one level below the installation directory. For example, \configs means
C:\Users\{userName}\dataloader\version\configs, provided you accepted the default installation directory. If you
installed the program in a different location, use that directory path.
Encrypt from the Command Line
Data Loader offers an encryption utility to secure passwords specified in configuration files. While Data Loader does not handle encryption
directly, data in transit is encrypted when using a secure connection such as HTTPS.
Note:  The Data Loader command-line interface is supported for Windows only.
When running Data Loader in batch mode from the command line, you must encrypt the following configuration parameters:
## •
sfdc.password
## •
sfdc.proxyPassword
1.Open a command prompt, and navigate to the bin subfolder of your Data Loader installation folder.
2.Run encrypt.bat.
3.At the command line, follow the prompts provided to execute the following actions.
## •
Generate a key: -k [pathto key file]
Generates a key file, and saves it in %userprofile%\.dataloader\dataLoader.key if the path is not specified.
Store this file with care as you use it for encryption and decryption.
## •
Encrypt text: -e <plaintext> <pathto key file>
Generates an encrypted version of the text. Provide a key file for the encryption.
## 27
Installed Directories and FilesRun in Batch Mode (Windows Only)

## •
Decrypt text: -d <encryptedtext> <pathto key file>
Decrypts the text using the key file.
## Upgrade Your Batch Mode Interface
The batch mode interface in Data Loader versions 8.0 and later aren’t backward-compatible with earlier versions. If you’re using a version
earlier than 8.0 to run batch processes, you have these options.
Note:  The Data Loader command-line interface is supported for Windows only.
## •
Maintain the old version for batch use
Do not uninstall your old version of Data Loader. Continue to use that version for batch processes. You can't take advantage of newer
features such as database connectivity, but your integrations continue to work. Optionally, install the new version alongside the old
version and dedicate the old version solely to batch processes.
## •
Generate a new config.properties file from the new GUI
If you originally generated your config.properties file from the graphical user interface, use the new version to set the
same properties and generate a new file. Use this new file with the new batch mode interface.
## •
Manually update your config.properties file
If your old config.properties file was created manually, you must manually update it for the new version. For more
information, see Installed Directories and Files on page 27.
Run Batch File With Windows Command-Line Interface
For automated batch operations, such as nightly scheduled loads and extractions, run Data Loader from the Windows command-line.
To run Data Loader from a configured Windows batch file:
Note:  The Data Loader command-line interface is supported for Windows only.
1.Include your encrypted password in the configuration file to run a batch operation. For more information, see Data Loader Command
Line Introduction on page 47 and Encrypt from the Command Line on page 27.
2.Use the process-conf.xml file to configure batch file processing. Specify the name of the process in the ProcessRunner
bean's id attribute.
For example,
<beanid="accountInsert"class="com.salesforce.dataloader.process.ProcessRunner"
scope="prototype">
3.Navigate to the Data Loader \bin directory by entering this command. Replace the file path with the path from your system.
C:\Users\{userName}\dataloader\version\bin
4.To run the batch file, use the correct command syntax for process.bat:
process.bat<configdir>[<operation>]
where:
## 28
Upgrade Your Batch Mode InterfaceRun in Batch Mode (Windows Only)

## •
<configdir> (mandatory) The absolute or relative path to the directory containing process-conf.xml. It must be
the first parameter when running process.bat.
## •
<batchprocessbeanid> (optional) The id of the batch process bean of class
com.salesforce.dataloader.process.ProcessRunner defined in the process-conf.xmlfile. If not
provided, then the value of the process.name property in the config.properties file is used.
Example:  Running process.bat using both parameters
To execute Data Loader in batch mode, we’ll use the beans, their properties and attributes specified for a ProcessRunner
bean with id="accountInsert" in the process-conf.xml file located in
C:\Users\username\dataloaderconfig directory.
process.bat"C:\Users\username\dataloaderconfig"accountInsert
Tip: If you experience login issues in the command-line interface after upgrading Data Loader, try encrypting your password again
to solve the problem.
## Configure Batch Processes
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
Use \samples\conf\process-conf.xml to configure your Data Loader processes, which
are represented by ProcessRunner beans.
Note:  The Data Loader command-line interface is supported for Windows only.
A process must have ProcessRunner as the class attribute and these properties set in the
configuration file.
## •
name—Sets the name of the ProcessRunner bean. This value is also used as the non-generic
thread name and for configuration backing files.
## •
configOverrideMap—A property of type map where each entry represents a configuration
setting: the key is the setting name; the value is the setting value.
## •
enableLastRunOutput—If set to true (the default), output files containing information about the last run, such as
sendAccountsFile_lastrun.properties, are generated and saved to the location specified by
lastRunOutputDirectory. If set to false, the files are not generated or saved.
## •
lastRunOutputDirectory—The directory location where output files containing information about the last run, such as
sendAccountsFile_lastrun.properties, are written. The default value is \conf. If enableLastRunOutput
is set to false, this value is not used because the files are not generated.
The configuration backing file stores configuration parameter values from the last run for debugging purposes, and is used to load
default configuration parameters in config.properties. The settings in configOverrideMap take precedence over the
settings in the configuration backing file. The configuration backing file is managed programmatically and does not require any manual
edits.
For the names and descriptions of available process configuration parameters, see Data Loader Process Configuration Parameters on
page 30.
## 29
Configure Batch ProcessesRun in Batch Mode (Windows Only)

## Data Loader Process Configuration Parameters
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
When running Data Loader from the command line, you can specify configuration parameters in
the process-conf.xml file. In some cases, the parameter is also represented in the UI at
## Settings > Settings.
Note:  The Data Loader command-line interface is supported for Windows only.
Tip:  A sample process-conf.xml file is in the \samples directory that’s installed
with Data Loader.
DescriptionEquivalent
## Option
in
## Settings
## Dialog
## Data
## Type
## Parameter Name
Select this option to force files to open
in UTF-8 encoding, even if they were
saved in a different format.
Sample value: true
## Read
all
CSVs
with
## UTF-8
encoding
boolean
dataAccess.readUTF8
Select this option to force files to be
written in UTF-8 encoding.
Sample value: true
## Write
all
CSVs
with
boolean
dataAccess.writeUTF8
## UTF-8
encoding
Name of the data source to use, such
as a CSV file name. For databases, use
## Not
applicable
(N/A)string
dataAccess.name
the name of the database
configuration in
database-conf.xml.
Sample value:
c:\dataloader\data\extractLead.csv
Number of records read from the
database at a time. The maximum
value is 200.
Sample value: 50
N/Ainteger
dataAccess.readBatchSize
Standard or custom data source type.
Standard types are csvWrite,
N/Astring
dataAccess.type
csvRead, databaseWrite, and
databaseRead.
Sample value: csvWrite
## 30
Data Loader Process Configuration ParametersRun in Batch Mode (Windows Only)

DescriptionEquivalent
Option in
## Settings
## Dialog
## Data
## Type
## Parameter Name
Number of records written to the database at a time.
The maximum value is 2,000. Note the implication
N/Ainteger
dataAccess.writeBatchSize
for a large parameter value: if an error occurs, all
records in the batch are rolled back. In contrast, if the
value is set to 1, each record is processed individually
(not in batch) and errors are specific to a given record.
We recommend setting the value to 1 when you
need to diagnose problems with writing to a
database.
Sample value: 500
Select this option if your CSV file uses commas to
delimit records.
## Allow
commaas
a CSV
delimiter
boolean
loader.csvComma
Select this option if your CSV file uses tab characters
to delimit records.
## Allow
tab as a
## CSV
delimiter
boolean
loader.csvTab
Select this option if your CSV file uses a character
other than a comma or tab to delimit records.
## Allow
other
characters
boolean
loader.csvOther
as CSV
delimiters
The characters in this field are used only if the Allow
other characters as CSV delimiters option is
## Other
delimiters
string
loader.csvOtherValue
selected. For example, if you use the | (pipe) character
## (enter
to delimit data records, enter that character in this
field.
multiple
values
withno
separator;
for
example,
## !+?)
Select this option to generate success and error files
when exporting data.
Sample value: true
## Generate
status
files
for
exports
boolean
process.enableExtractStatusOutput
When running Data Loader in batch mode, you can
disable the generation of output files such asN/Aboolean
process.enableLastRunOutput
## 31
Data Loader Process Configuration ParametersRun in Batch Mode (Windows Only)

DescriptionEquivalent
Option in
## Settings
## Dialog
## Data
## Type
## Parameter Name
sendAccountsFile_lastRun.properties.
Files of this type are saved by default to the conf
directory. To stop the writing of these files, set this
option to false.
Alternatively, you can change the location of the
directory where these files are saved, using
process.lastRunOutputDirectory.
Sample value: true
Name of the file that contains the encryption key.
This parameter is required in Data Loader version 43.0
## N/A
string (file
name)
process.encryptionKeyFile
and later. See Encrypt from the Command Line on
page 27.
Sample value:
c:\Users\{user}\.dataloader\dataloader.key
The initial setting for the
process.lastRunDate parameter, which can
N/Adate
process.initialLastRunDate
be used in a SQL string and is automatically updated
when a process has run successfully. For an
explanation of the date format syntax, see Date
Formats on page 17.
Format must be
yyyy-MM-ddTHH:mm:ss.SSS+/-HHmm. For
example: 2006-04-13T13:50:32.423-0700
When running Data Loader in batch mode, you can
change the location where output files such as
## N/A
string
## (directory)
process.lastRunOutputDirectory
sendAccountsFile_lastRun.properties
are written. Files of this type are saved by default to
the \conf directory. To change the location,
change the value of this option to the full path where
you want the output files written.
Alternatively, you can stop the files from being
written, using
process.enableLastRunOutput.
If your last operation failed, you can use this setting
to begin where the last successful operation finished.
Sample value: 1008
## Startat
row
number
process.loadRowToStartAt
## 32
Data Loader Process Configuration ParametersRun in Batch Mode (Windows Only)

DescriptionEquivalent
Option in
## Settings
## Dialog
## Data
## Type
## Parameter Name
Name of the field mapping file to use. See Map
Columns on page 43.
Sample value:
c:\dataloader\conf\accountExtractMap.sdl
## N/A
string (file
name)
process.mappingFile
The operation to perform. See Data Loader
Command-Line Operations on page 38.
Sample value: extract
N/Astring
process.operation
The directory where “success” and “error” output files
are saved. The file names are automatically generated
## N/A
string
## (directory)
process.statusOutputDirectory
for each operation unless you specify otherwise in
process-conf.xml.
Sample value: c:\dataloader\status
The name of the CSV file that stores error data from
the last operation.
Sample value:
c:\dataloader\status\myProcessErrors.csv
## N/A
string (file
name)
process.outputError
The name of the CSV file that stores success data from
the last operation. See also
## N/A
string (file
name)
process.outputSuccess
process.enableExtractStatusOutput
on page 31.
Sample value:
c:\dataloader\status\myProcessSuccesses.csv
Select this option to support the date formats
dd/MM/yyyy and dd/MM/yyyyHH:mm:ss.
Sample value: true
## Use
## European
date
format
boolean
process.useEuropeanDates
Specify the ID of the assignment rule to use for
inserts, updates, and upserts. This option applies to
## Assignment
rule
string
sfdc.assignmentRule
inserts, updates, and upserts on cases and leads. The
assignment rule overrides Owner values in your
CSV file.
Sample value: 03Mc00000026J7w
The number of milliseconds to wait between
successive checks to determine if the asynchronous
N/Ainteger
sfdc.bulkApiCheckStatusInterval
Bulk API operation is complete or how many records
have been processed. See also
## 33
Data Loader Process Configuration ParametersRun in Batch Mode (Windows Only)

DescriptionEquivalent
Option in
## Settings
## Dialog
## Data
## Type
## Parameter Name
sfdc.useBulkApi. We recommend a value of
## 5000.
Sample value: 5000
To use serial processing instead of parallel processing
for Bulk API, select this option. Processing in parallel
## Enable
serial
boolean
sfdc.bulkApiSerialMode
can cause database contention. When contention is
modefor
BulkAPI
severe, the load can fail. Serial mode processes
batches one at a time, however it can increase the
processing time for a load. See also
sfdc.useBulkApi.
Sample value: false
Select this option to use Bulk API to upload zip files
containing binary attachments, such as Attachment
## Upload
BulkAPI
boolean
sfdc.bulkApiZipContent
records or Salesforce CRM Content. See also
sfdc.useBulkApi.
Sample value: true
## Batchas
## Zip File
The number of seconds to wait for a connection
during API calls.
Sample value: 60
N/Ainteger
sfdc.connectionTimeoutSecs
If true, enables SOAP message debugging. By default,
messages are sent to STDOUT unless you specify an
N/Aboolean
sfdc.debugMessages
alternate location in
sfdc.debugMessagesFile.
Sample value: false
## See
process.enableExtractStatusOutput
## N/A
string (file
name)
sfdc.debugMessagesFile
on page 31. Stores SOAP messages sent to or from
Salesforce. As messages are sent or received, they are
appended to the end of the file. As the file does not
have a size limit, monitor your available disk storage
appropriately.
Sample value:
\lexiloader\status\sfdcSoapTrace.log
If true, enables repeated attempts to connect to
Salesforce servers. See sfdc.maxRetries on
N/Aboolean
sfdc.enableRetries
page 36 and sfdc.minRetrySleepSecs on
page 36.
## 34
Data Loader Process Configuration ParametersRun in Batch Mode (Windows Only)

DescriptionEquivalent
Option in
## Settings
## Dialog
## Data
## Type
## Parameter Name
Sample value: true
Enter the URL of the Salesforce server with which you
want to communicate. For example, if you are loading
## Server
host
## URL
sfdc.endpoint
data into a sandbox, change the URL to
https://MyDomainName--SandboxName.sandbox.my.salesforce.com
or https://test.salesforce.com.
Sample production values:
https://MyDomainName.my.salesforce.com/services/Soap/u/53.0
and
https://login.salesforce.com/services/Soap/u/53.0
The Salesforce object used in the operation.
Sample value: Lead
N/Astring
sfdc.entity
Used in upsert operations; specifies the custom field
with the “External ID” attribute that is used as a
unique identifier for data matching.
Sample value: LegacySKU__c
N/Astring
sfdc.externalIdField
In a single export or query operation, records are
returned from Salesforce in increments of this size.
## Query
request
size
integer
sfdc.extractionRequestSize
Larger values can improve performance but use more
memory on the client.
Sample value: 500
The SOQL query for the data export.
Sample value: SELECTId, LastName,
FirstName,Rating,AnnualRevenue,
OwnerIdFROMLead
N/Astring
sfdc.extractionSOQL
Select this option to insert blank mapped values as
null values during data operations. When you are
## Insert
null
values
boolean
sfdc.insertNulls
updating records, this option instructs Data Loader
to overwrite existing data in mapped fields.
Sample value: false
In a single insert, update, upsert, or delete operation,
records moving to or from Salesforce are processed
## Batch
size
integer
sfdc.loadBatchSize
in increments of this size. The maximum is 200
records. We recommend a value from 50 through
## 100.
Sample value: 100
## 35
Data Loader Process Configuration ParametersRun in Batch Mode (Windows Only)

DescriptionEquivalent
Option in
## Settings
## Dialog
## Data
## Type
## Parameter Name
The maximum number of repeated attempts to
connect to Salesforce. See
sfdc.enableRetries on page 34.
Sample value: 3
N/Ainteger
sfdc.maxRetries
The minimum number of seconds to wait between
connection retries. The wait time increases with each
try. See sfdc.enableRetries on page 34.
Sample value: 2
N/Ainteger
sfdc.minRetrySleepSecs
Compression enhances the performance of Data
Loader and is turned on by default. If you want to
## Compression
boolean
sfdc.noCompression
disable compression when debugging the underlying
SOAP messages, enable this option.
Sample value: false
An encrypted Salesforce password that corresponds
to the username provided in sfdc.username.
## N/A
encrypted
string
sfdc.password
This parameter is required in Data Loader version 43.0
and later. See also Encrypt from the Command Line
on page 27.
Sample value: 4285b36161c65a22
The host name of the proxy server, if applicable.
Sample value:
http://myproxy.internal.company.com
## Proxy
host
## URL
sfdc.proxyHost
An encrypted password that corresponds to the proxy
username provided in sfdc.proxyUsername.
## Proxy
password
encrypted
string
sfdc.proxyPassword
See also Encrypt from the Command Line on page
## 27.
Sample value: 4285b36161c65a22
The proxy server port.
Sample value: 8000
## Proxy
port
integer
sfdc.proxyPort
The username for proxy server authentication.
Sample value: jane.doe
## Proxy
username
string
sfdc.proxyUsername
By default, Salesforce resets the URL after login to the
one specified in sfdc.endpoint. To turn off this
## Reset
URL on
## Login
boolean
sfdc.resetUrlOnLogin
## 36
Data Loader Process Configuration ParametersRun in Batch Mode (Windows Only)

DescriptionEquivalent
Option in
## Settings
## Dialog
## Data
## Type
## Parameter Name
automatic reset, disable this option by setting it to
false.
Valid values: true (default), false
Specify how many seconds Data Loader waits to
receive a response back from the server before
returning an error for the request.
Sample value: 540
## Timeout
integer
sfdc.timeoutSecs
If a date value does not include a time zone, this value
is used.Valid values are any time zone identifier that
## Time
## Zone
string
sfdc.timezone
can be passed to the Java
getTimeZone(java.lang.String)
method. The value can be a full name such as
America/Los_Angeles, or a custom ID such
as GMT-8:00.
## •
If no value is specified, the time zone of the
computer where Data Loader is installed is used.
## •
If an incorrect value is entered, GMT is used as
the time zone and this fact is noted in the Data
Loader log.
You can retrieve the default value by running the
TimeZone.getDefault() method in Java.
This value is the time zone on the computer where
Data Loader is installed.
Select this option to truncate data in the following
types of fields when loading that data into Salesforce:
## Allow
field
truncation
boolean
sfdc.truncateFields
Email, Multi-select Picklist, Phone, Picklist, Text, and
Text (Encrypted).
In Data Loader versions 14.0 and earlier, Data Loader
truncates values for fields of those types if they are
too large. In Data Loader version 15.0 and later, the
load operation fails if a value is specified that is too
large.
Selecting this option allows you to specify that the
previous behavior, truncation, be used instead of the
new behavior in Data Loader versions 15.0 and later.
This option is selected by default and has no effect
in versions 14.0 and earlier.
This option is not available if the Use BulkAPI
option is selected. In that case, the load operation
## 37
Data Loader Process Configuration ParametersRun in Batch Mode (Windows Only)

DescriptionEquivalent
Option in
## Settings
## Dialog
## Data
## Type
## Parameter Name
fails for the row if a value is specified that is too large
for the field.
Sample value: true
Select this option to use Bulk API to insert, update,
upsert, delete, and hard-delete records. Bulk API is
## Use Bulk
## API
boolean
sfdc.useBulkApi
optimized to load or delete many records
asynchronously. It’s faster than the default
SOAP-based API due to parallel processing and fewer
network round-trips. See also
sfdc.bulkApiSerialMode.
Sample value: true
Salesforce username. See sfdc.password.
Sample value: jdoe@mycompany.com
N/Astring
sfdc.username
Data Loader Command-Line Operations and Exit Codes
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
When running Data Loader in batch mode from the command line, several operations are supported.
An operation represents the flow of data between Salesforce and an external data source, such as
a CSV file or database. You can use these operations and refer to these exit codes.
## Operations
Note:  The Data Loader command-line interface is supported for Windows only.
Note:  Enter values in the process.operation parameter in lowercase.
DescriptionOperation
Uses the Salesforce Object Query Language to export a set of
records from Salesforce. The exported data is written to a data
source. Soft-deleted records are not included.
extract
Uses SOQL to export a set of records from Salesforce, including
existing and soft-deleted records. The exported data is written to
a data source.
extract_all
Loads data from a data source into Salesforce as new records.insert
Loads data from a data source into Salesforce, and updates
existing records with matching ID fields.
update
## 38
Data Loader Command-Line Operations and Exit CodesRun in Batch Mode (Windows Only)

DescriptionOperation
Loads data from a data source into Salesforce. Existing records with a matching custom
external ID field are updated. Records without matches are inserted as new records.
upsert
Loads data from a data source into Salesforce, and deletes existing records with matching
ID fields. Deleted records are moved to the Recycle Bin.
delete
Loads data from a data source into Salesforce, and deletes existing records with matching
ID fields without first storing them in the Recycle Bin.
hard_delete
## Exit Codes
To help you find the cause of an error, Data Loader version 62 and later uses these exit codes.
DescriptionExit Code
Successful execution.0
Note: If the property
process.batchMode.exitWithErrorOnFailedRows is set to false
(default is false) in the Data Loader config.properties file, then the
execution can succeed, even if one or more rows fails to upload.
Client-side error occurred.1
Server-side error occurred.2
Error in executing the operation.3
Operation succeeded but failed to upload one or more rows due to an error in data. This
exit code is only used if the property
## 4
process.batchMode.exitWithErrorOnFailedRows is set to true (default
is false) in the Data Loader config.properties file.
## Configure Database Access
When you run Data Loader in batch mode from the command line, use \samples\conf\database-conf.xml to configure
database access objects, which you use to extract data directly from a database.
Note:  The Data Loader command-line interface is supported for Windows only.
DatabaseConfig Bean
The top-level database configuration object is the DatabaseConfig bean, which has these properties.
## •
sqlConfig—The SQL configuration bean for the data access object that interacts with a database.
## •
dataSource—The bean that acts as database driver and authenticator. It must refer to an implementation of
javax.sql.DataSource such as org.apache.commons.dbcp.BasicDataSource.
## 39
Configure Database AccessRun in Batch Mode (Windows Only)

This code is an example of a DatabaseConfig bean:
<beanid="AccountInsert"
class="com.salesforce.dataloader.dao.database.DatabaseConfig"
scope="singleton">
<propertyname="sqlConfig"ref="accountInsertSql"/>
## </bean>
DataSource
The DataSource bean sets the physical information needed for database connections. It contains the following properties:
## •
driverClassName—The fully qualified name of the implementation of a JDBC driver.
## •
password—The password for logging in to the database.
## •
url—The string for physically connecting to the database.
## •
username—The username for logging in to the database.
Depending on your implementation, additional information is required. For example, use
org.apache.commons.dbcp.BasicDataSource when database connections are pooled.
The following code is an example of a DataSource bean:
<beanid="oracleRepDataSource"
class="org.apache.commons.dbcp.BasicDataSource"
destroy-method="close"
scope="prototype">
<propertyname="driverClassName"value="oracle.jdbc.driver.OracleDriver"/>
<propertyname="url"value="jdbc:oracle:thin:@myserver.salesforce.com:1521:TEST"/>
## <propertyname="username"value="test"/>
## <propertyname="password"value="test"/>
## </bean>
Versions of Data Loader from API version 25.0 onwards do not come with an Oracle JDBC driver. Using Data Loader to connect to an
Oracle data source without a JDBC driver installed results in a “Cannot load JDBC driver class” error. To add the Oracle JDBC driver to
## Data Loader:
## •
Download the latest JDBC driver from
http://www.oracle.com/technetwork/database/features/jdbc/index-091264.html.
## •
Copy the JDBC .jar file to dataloaderinstallfolder/java/bin.
## Spring Framework
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
The Spring Framework allows you to use XML files to configure beans. Each bean represents an
instance of an object; the parameters correspond to each object's setter methods.
Note:  The Data Loader command-line interface is supported for Windows only.
Note:  The Data Loader configuration files are based on the Spring Framework, which is an
open-source, full-stack Java/J2EE application framework.
A typical bean has these attributes.
## •
class—Specifies the implementation class for the bean instance.
## •
id—Uniquely identifies the bean to XmlBeanFactory, which is the class that gets objects
from an XML configuration file.
## 40
Spring FrameworkRun in Batch Mode (Windows Only)

For more information on the Spring Framework, see the official documentation and the support forums. Note that Salesforce cannot
guarantee the availability or accuracy of external websites.
Access External Data with Data Access Objects
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
When running Data Loader in batch mode from the command line, several data access objects are
supported. allows access to an external data source outside of Salesforce. A data access object can
implement a read interface (DataReader), a write interface (DataWriter), or both.
Note:  The Data Loader command-line interface is supported for Windows only.
Here's a list of object names and descriptions.
## •
csvRead—Allows the reading of a comma or tab-delimited file. There must be a header row at
the top of the file that describes each column.
## •
csvWrite—Allows writing to a comma-delimited file. A header row is added to the top of the
file based on the column list provided by the caller.
## •
databaseRead—Allows the reading of a database. Use database-conf.xml to configure
database access.
## •
databaseWrite—Allows writing to a database. Use database-conf.xml to configure database access.
SQL Configuration
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
When running Data Loader in batch mode from the command line, the SqlConfig class contains
configuration parameters for accessing specific data in the database.
Note:  The Data Loader command-line interface is supported for Windows only.
As shown in these code samples, queries and inserts are different but very similar. The bean must
be of type com.salesforce.dataloader.dao.database.SqlConfig and have
these properties.
## •
sqlString
The SQL code to be used by the data access object.
The SQL can contain replacement parameters that make the string dependent on configuration
or operation variables. Replacement parameters must be delimited on both sides by “@” characters. For example,
@process.lastRunDate@.
## •
sqlParams
A property of type map that contains descriptions of the replacement parameters specified in sqlString. Each entry represents
one replacement parameter: the key is the replacement parameter's name, the value is the fully qualified Java type to be used when
the parameter is set on the SQL statement. Note that “java.sql” types are sometimes required, such as java.sql.Date instead
of java.util.Date. For more information, see the official JDBC API documentation.
## •
columnNames
Used when queries (SELECT statements) return a JDBC ResultSet. Contains column names for the data outputted by executing
the SQL. The column names are used to access and return the output to the caller of the DataReader interface.
## 41
Access External Data with Data Access ObjectsRun in Batch Mode (Windows Only)

SQL Query Bean Example
<beanid="accountMasterSql"
class="com.salesforce.dataloader.dao.database.SqlConfig"
singleton="true">
<propertyname="sqlString"/>
## <value>
SELECTdistinct
'012x00000000Ij7'recordTypeId,
accounts.account_number,
org.organization_name,
concat(concat(parties.address1,' '), parties.address2)billing_address,
locs.city,
locs.postal_code,
locs.state,
locs.country,
parties.sic_code
from
ar.hz_cust_accountsaccounts,
ar.hz_organization_profilesorg,
ar.hz_partiesparties,
ar.hz_party_sitesparty_sites,
ar.hz_locationslocs
where
accounts.PARTY_ID= org.PARTY_ID
and parties.PARTY_ID= accounts.PARTY_ID
and party_sites.PARTY_ID= accounts.PARTY_ID
and locs.LOCATION_ID= party_sites.LOCATION_ID
and (locs.last_update_date> @process.lastRunDate@OR
accounts.last_update_date> @process.lastRunDate@
## </value>
## </property>
<propertyname="columNames">
## <list>
<value>recordTypeId</value>
## <value>account_number</value>
## <value>organization_name</value>
## <value>billing_address</value>
## <value>city</value>
## <value>postal_code</value>
## <value>state</value>
## <value>country</value>
## <value>sic_code</value>
## </list>
## </property>
<propertyname="sqlParams">
## <map>
<entrykey="process.lastRunDate"value="java.sql.Date"/>
## </map>
## </property>
## </bean>
## 42
SQL ConfigurationRun in Batch Mode (Windows Only)

SQL Insert Bean Example
<beanid="partiesInsertSql"
class="com.salesforce.dataloader.dao.database.SqlConfig"
singleton="true">
<propertyname="sqlString"/>
## <value>
## INSERTINTOREP.INT_PARTIES(
## BILLING_ADDRESS,SIC_CODE)
VALUES(@billing_address@,@sic_code@)
## </value>
## </property>
<propertyname="sqlParams"/>
## <map>
<entrykey="billing_address"value="java.lang.String"/>
<entrykey="sic_code"value="java.lang.String"/>
## </map>
## </property>
## </bean>
## Map Columns
When running Data Loader in batch mode from the command line, you must create a properties file that maps values between Salesforce
and data access objects.
Note:  The Data Loader command-line interface is supported for Windows only.
1.Create a mapping file and give it an extension of .sdl.
2.Observe the following syntax:
## •
On each line, pair a data source with its destination.
## •
In an import file, put the data source on the left, an equals sign (=) as a separator, and the destination on the right. In an export
file, put the destination on the left, an equals sign (=) as a separator, and the data source on the right.
## •
Data sources can be either column names or constants. Constants can be specified for insert, update, and upsert operations.
Surround constants with double quotation marks, as in “sampleconstant”. Values without quotation marks are treated as column
names.
## •
Destinations must be column names.
## •
You can map constants by surrounding them with double quotation marks, as in:
"Canada"=BillingCountry
3.In your configuration file, use the parameter process.mappingFile to specify the name of your mapping file.
Note:  If your field name contains a space, you must escape the space by prepending it with a backslash (\). For example:
Account\Name=Name
Column Mapping Example for Data Insert
## 43
Map ColumnsRun in Batch Mode (Windows Only)

The Salesforce fields are on the right.
SLA__C=SLA__c
BILLINGCITY=BillingCity
## SYSTEMMODSTAMP=
OWNERID=OwnerId
CUSTOMERPRIORITY__C=CustomerPriority__c
ANNUALREVENUE=AnnualRevenue
DESCRIPTION=Description
BILLINGSTREET=BillingStreet
SHIPPINGSTATE=ShippingState
Column Mapping Example for Data Export
The Salesforce fields are on the left.
## Id=account_number
## Name=name
## Phone=phone
Column Mapping for Constant Values
Data Loader supports the ability to assign constants to fields when you insert, update, and upsert data. If you have a field that must
contain the same value for each record, you must specify that constant in the .sdl mapping file instead of specifying the field and
value in the CSV file or the export query.
The constant must be enclosed in double quotation marks. For example, if you're importing data, the syntax is
## "constantvalue"=field1.
If you have multiple fields that must contain the same value, you must specify the constant and the field names separated by commas.
For example, if you're importing data, the syntax is "constantvalue"=field1,field2.
Here's an example of an .sdl file for inserting data. The Salesforce fields are on the right. The first two lines map a data source to a
destination field, and the last three lines map a constant to a destination field.
Name=Name
NumEmployees=NumberOfEmployees
"Aerospace"=Industry
"California"=BillingState,ShippingState
"New"=Customer_Type__c
A constant must contain at least one alphanumeric character.
Note:  If you specify a constant value that contains spaces, you must escape the spaces by prepending each with a backslash (\).
For example:
"Food\&\ Beverage"=Industry
## Run Individual Batch Processes
You can run one batch process at a time.
To start an individual batch process, use \bin\process.bat. The command-line requires the following parameters.
## •
Configuration directory—The default is \conf.
## 44
Run Individual Batch ProcessesRun in Batch Mode (Windows Only)

To use an alternate directory, create a directory and add these files to it.
## –
If your process is not interactive, copy process-conf.xml from \samples\conf.
## –
If your process requires database connectivity, copy database-conf.xml from \samples\conf.
## –
Copy config.properties from \conf.
## •
Process name—The name of the ProcessRunner bean from \samples\conf\process-conf.xml.
## Process Example
process../confaccountMasterProcess
Note:  To view tips and instructions, add -help to the command contained in process.bat.
Note:  You can configure external process launchers, such as the Windows XP Scheduled Task Wizard, to run processes on a
schedule.
## 45
Run Individual Batch ProcessesRun in Batch Mode (Windows Only)

CHAPTER 7Command-Line Quick Start (Windows Only)
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
In this chapter ...
Note:  The Data Loader command-line interface is supported
for Windows only.
•Data Loader
## Command Line
## Introduction
This quick start shows you how to use the Data Loader
command-line functionality to import data.
•Prerequisites
•Step One: Create the
## Encryption Key File
•Step Two: Create the
## Encrypted Password
•Step Three: Create
the Field Mapping
## File
•Step Four: Create the
## Configuration File
•Step Five: Import the
## Data
## 46

## Data Loader Command Line Introduction
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
In addition to using Data Loader interactively to import and export data, you can run it from the
command line. You can use commands to automate the import and export of data.
Note:  The Data Loader command-line interface is supported for Windows only.
This quick start shows you how to use the Data Loader command-line functionality to import data.
Follow these steps.
## •
Step 1: Create the encryption key
## •
Step 2: Create the encrypted password for your login username
## •
Step 3: Create the Field Mapping File
## •
Step 4: Create a process-conf.xml file that contains the import configuration settings
## •
Step 5: Run the process and import the data
## SEE ALSO:
## Prerequisites
## Prerequisites
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
Prerequisites for this quick start.
Note:  The Data Loader command-line interface is supported for Windows only.
## •
Data Loader installed on the computer that runs the command-line process.
## •
The Java Runtime Environment (JRE) installed on the computer that runs the command-line
process.
## •
Familiarity with importing and exporting data by using the Data Loader interactively through
the user interface. This makes it easier to understand how the command-line functionality
works.
Tip:  When you install Data Loader, sample files are installed in the samples directory
under the user’s directory, for example,
C:\Users\{userName}\dataloader\version\samples\. Examples of files
that are used in this quick start are in the \samples\conf directory.
## SEE ALSO:
## Data Loader Command Line Introduction
Step One: Create the Encryption Key File
Step One: Create the Encryption Key File
When you use Data Loader from the command line, there's no user interface. Therefore, you provide the information that you enter in
the user interface in a text file named process-conf.xml. For example, you add the username and password that Data Loader
uses to log in to Salesforce.
## 47
Data Loader Command Line IntroductionCommand-Line Quick Start (Windows Only)

Note:  The Data Loader command-line interface is supported for Windows only.
Note:  The password must be encrypted before you add it to the process-conf.xml file, and creating the key is the first
step in that process.
1.Open a command prompt window by selecting Start > All Programs > Accessories > Command Prompt. Alternatively, you can
click Start > Run, enter cmd in the Open field, and click OK.
2.In the command window, enter cd\ to navigate to the root directory of the drive where Data Loader is installed.
3.Navigate to the Data Loader \bin directory by entering this command. Replace the file path with the path from your system.
C:\Users\{userName}\dataloader\version\bin
4.Create an encryption key file by entering the following command. Replace [pathto key file] with the key file path.
encrypt.bat—k [pathto key file]
For example:
C:\Users\jjang\Dataloader\v45\bin>encrypt.bat-k
Keyfile"C:\Users\jjang\.dataloader\dataloader.key"was created!
C:\Users\jjang\Dataloader\v45\bin>
Note:  To see a list of command-line options for encrypt.bat, enter encrypt.bat on the command line.
5.Note the key file path. In this example, the path is C:\Users\{userName}\.dataloader\dataLoader.key.
The encryption utility encrypts passwords but not data. HTTPS with TLS 1.0 or later encrypts data transmitted by the Apex Data Loader.
## SEE ALSO:
## Data Loader Command Line Introduction
Step Two: Create the Encrypted Password
Step Two: Create the Encrypted Password
Create the encrypted password using the key file that you generated in the previous step. Skip this step if you're using OAuth for login
authentication.
Note:  The Data Loader command-line interface is supported for Windows only.
1.In the same command prompt window, enter the following command.
encrypt.bat–e <password><Salesforce_Security_Token> <key filepath>
Replace <password> with the password that you use to log in to Salesforce in Data Loader combined with your org's security
token (no space in between). Replace <key filepath> with the file path you created in the previous step.
For example, if your Data Loader password is myP4sswordsRock and your org's security token is
00DE0X0A0M0PeLE!AQcAQH0dMHEXAM, then the command is:
encrypt.bat-e myP4sswordsRock00DE0X0A0M0PeLE!AQcAQH0dMHEXAM
C:\Users\jjang\.dataloader\dataLoader.key
## 48
Step Two: Create the Encrypted PasswordCommand-Line Quick Start (Windows Only)

2.Copy the generated encrypted password string. You use this value in a later step.
## SEE ALSO:
## Data Loader Command Line Introduction
Step Three: Create the Field Mapping File
Step Three: Create the Field Mapping File
In this step, you create a mapping file with an .sdl file extension. In each line of the mapping file, pair a data source with its destination.
Note:  The Data Loader command-line interface is supported for Windows only.
## •
Copy the following to a text file and save it with a name of accountInsertMap.sdl. This code is a data insert, so the data
source is on the left of the equals sign and the destination field is on the right.
#Mappingvalues
#ThuMay 26 16:19:33GMT 2011
Name=Name
NumberOfEmployees=NumberOfEmployees
Industry=Industry
For complex mappings, you can use the Data Loader user interface to map source and destination fields and then save those
mappings to an .sdl file. It’s done on the Mapping dialog box by clicking Save Mapping.
## SEE ALSO:
## Data Loader Command Line Introduction
Step Four: Create the Configuration File
Step Four: Create the Configuration File
The process-conf.xml file contains the information that Data Loader requires to process the data. Each <bean> in the
process-conf.xml file refers to a single process such as an insert, upsert, or export. Therefore, this file can contain multiple
processes.
Note:  The Data Loader command-line interface is supported for Windows only.
In this step, you edit the file to insert accounts into Salesforce.
1.Make a copy of the process-conf.xml file from the \samples\conf directory. Be sure to maintain a copy of the original
because it contains examples of other types of Data Loader processing such as upserts and exports.
2.Open the file in a text editor, and replace the contents with the following XML.
Note:  Remove sfdc.password if you're using OAuth for login authentication.
<!DOCTYPEbeansPUBLIC"-//SPRING//DTDBEAN//EN"
## "http://www.springframework.org/dtd/spring-beans.dtd">
## <beans>
<beanid="accountInsert"
## 49
Step Three: Create the Field Mapping FileCommand-Line Quick Start (Windows Only)

class="com.salesforce.dataloader.process.ProcessRunner"
scope="prototype">
<description>accountInsertjob getsthe accountrecordfromthe
CSV file
and insertsit intoSalesforce.</description>
<propertyname="name"value="accountInsert"/>
<propertyname="configOverrideMap">
## <map>
<entrykey="sfdc.debugMessages"value="false"/>
<entrykey="sfdc.debugMessagesFile"
value="C:\DLTest\Log\accountInsertSoapTrace.log"/>
## <entrykey="sfdc.endpoint"
value="https://servername.salesforce.com"/>
<entrykey="sfdc.username"value="admin@Org.org"/>
<!--Passwordbelowhas beenencryptedusingkey file,
therefore,it willnot workwithoutthe key setting:
process.encryptionKeyFile.
The passwordis not a validencryptedvalue,
pleasegeneratethe realvalueusingthe encrypt.batutility
## -->
## <entrykey="sfdc.password"value="e8a68b73992a7a54"/>
<entrykey="process.encryptionKeyFile"
value="c:\Users\{user}\.dataloader\dataLoader.key"/>
<entrykey="sfdc.timeoutSecs"value="600"/>
<entrykey="sfdc.loadBatchSize"value="200"/>
<entrykey="sfdc.entity"value="Account"/>
## <entrykey="process.operation"value="insert"/>
<entrykey="process.mappingFile"
value="C:\DLTest\CommandLine\Config\accountInsertMap.sdl"/>
<entrykey="dataAccess.name"
value="C:\DLTest\In\insertAccounts.csv"/>
<entrykey="process.outputSuccess"
value="c:\DLTest\Log\accountInsert_success.csv"/>
<entrykey="process.outputError"
value="c:\DLTest\Log\accountInsert_error.csv"/>
<entrykey="dataAccess.type"value="csvRead"/>
<entrykey="process.initialLastRunDate"
value="2005-12-01T00:00:00.000-0800"/>
## </map>
## </property>
## </bean>
## </beans>
3.Modify the following parameters in the process-conf.xml file. For more information about the process configuration
parameters, see Data Loader Process Configuration Parameters on page 30.
## •
sfdc.endpoint—Enter the URL of the Salesforce instance for your organization; for example,
https://yourInstance.salesforce.com/.
## •
sfdc.username—Enter the username Data Loader uses to log in.
## •
sfdc.password—Enter the encrypted password value that you created in step 2.
## •
process.mappingFile—Enter the path and file name of the mapping file.
## •
dataAccess.Name—Enter the path and file name of the data file that contains the accounts that you want to import.
## 50
Step Four: Create the Configuration FileCommand-Line Quick Start (Windows Only)

## •
sfdc.debugMessages—Currently set to false. Set it to true for troubleshooting. If set to true, debug messages
are captured in the file specified by sfdc.debugMessagesFile.
Note:  Debug messages can contain sensitive information such as session id.
## •
sfdc.debugMessagesFile—Enter the path and file name of the command-line log file.
## •
process.outputSuccess—Enter the path and file name of the success log file.
## •
process.outputError—Enter the path and file name of the error log file.
Warning:  Use caution when using different XML editors to edit the process-conf.xml file. Some editors add XML
tags to the beginning and end of the file, which causes the import to fail.
4.To perform operations in a sandbox org, set the following parameters.
## •
sfdc.oauth.environment—Enter the value Sandbox.
## •
sfdc.endpoint.Sandbox—Enter the value test.salesforce.com.
## SEE ALSO:
## Data Loader Command Line Introduction
Step Five: Import the Data
Step Five: Import the Data
## USER PERMISSIONS
Create on the recordTo insert records:
Edit on the recordTo update records:
Create or Edit on the recordTo upsert records:
Delete on the recordTo delete records:
Delete on the recordTo hard delete records:
Now that all the pieces are in place, you can run Data Loader from the command line and insert some new accounts.
Note:  The Data Loader command-line interface is supported for Windows only.
1.Copy the following data to a file named accountInsert.csv. It’s account data that you import into your organization.
Name,Industry,NumberOfEmployees
Dickensonplc,Consulting,120
GenePoint,Biotechnology,265
ExpressLogisticsand Transport,Transportation,12300
GrandHotels& ResortsLtd,Hospitality,5600
2.In the command prompt window, enter the following command:
process.bat"<filepathto process-conf.xml>"<processname>
## 51
Step Five: Import the DataCommand-Line Quick Start (Windows Only)

## •
Replace <file path to process-conf.xml> with the path to the directory containing process-conf.xml.
## •
Replace <process name> with the process specified in process-conf.xml.
Your command looks something like this:
process.bat"C:\DLTest\CommandLine\Config"accountInsert
After the process runs, the command prompt window displays success and error messages. You can also check the log files:
insertAccounts_success.csv and insertAccounts_error.csv. After the process runs successfully, the
insertAccounts_success.csv file contains the records that you imported, along with the ID and status of each record.
For more information about the status files, see Review Data Loader Output Files on page 23.
## SEE ALSO:
## Data Loader Command Line Introduction
## 52
Step Five: Import the DataCommand-Line Quick Start (Windows Only)

CHAPTER 8Data Loader Third-Party Licenses
## EDITIONS
Available in: both Salesforce
Classic (not available in all
orgs) and Lightning
## Experience
Available in: Enterprise,
## Performance, Unlimited,
and Developer editions
Data Loader version information for Salesforce releases and API
versions.
For information about third-party licenses included with the
installation of Data Loader, see Data Loader release page on GitHub.
Note:  Salesforce is not responsible for the availability or
content of third-party websites.
## 53

## INDEX
## D
## Data Loader
date formats17
## 54