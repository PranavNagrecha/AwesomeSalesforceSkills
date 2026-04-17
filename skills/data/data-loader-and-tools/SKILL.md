---
name: data-loader-and-tools
description: "Use this skill when selecting or configuring Salesforce data load tools: Data Loader, Data Import Wizard, Workbench, Salesforce Inspector, or Salesforce CLI for import/export. Trigger keywords: data loader configuration, import wizard, bulk data load, workbench SOQL, salesforce inspector, data export, csv import salesforce, data migration tool selection. NOT for Bulk API development — use the integration or apex skills for Bulk API coding."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - data-loader
  - data-import-wizard
  - workbench
  - salesforce-inspector
  - bulk-api
  - data-migration
  - csv-import
  - data-export
  - tool-selection
triggers:
  - "which tool should I use to import 10000 contacts into Salesforce"
  - "how do I configure Data Loader for scheduled bulk imports in headless mode"
  - "is Workbench still the best tool for running SOQL queries in Salesforce"
  - "what is the difference between Data Import Wizard and Data Loader"
  - "do I need a special permission to hard delete records with Data Loader"
  - "is Salesforce Inspector an official Salesforce product I can use in production"
  - "how do I set the batch size for a Bulk API 2.0 Data Loader job"
inputs:
  - Record count estimate
  - Object type(s) being loaded
  - Operation type (insert, update, upsert, delete, hard delete)
  - Scheduling or automation requirement (yes/no)
  - Authentication context (human interactive vs. headless/CI)
outputs:
  - Tool recommendation with justification
  - Configuration checklist
  - Pre-operation security checklist
  - Relevant limits and gotchas
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Data Loader and Tools

## Overview

Salesforce provides several tools for loading, exporting, and inspecting data. Choosing the wrong tool for the job is one of the most common causes of failed data migrations, governor limit errors, and security gaps. This skill covers **tool selection, configuration, and safe operation** — it does NOT cover writing Bulk API integrations in Apex or custom code.

## Tool Comparison

| Tool | Use When | Max Records | API Mode | Official? |
|------|----------|-------------|----------|-----------|
| Data Import Wizard | <50K, supported objects, no automation | 50,000 | SOAP | Yes |
| Data Loader | >50K, all objects, automation | 150M | Bulk API 2.0 | Yes |
| Workbench | Ad-hoc SOQL, REST Explorer | Small | REST/SOAP | Yes (sunset) |
| Salesforce Inspector | Quick record lookup | Tiny | REST | No (open-source) |
| Salesforce CLI | Scripted/CI export-import | Variable | Multiple | Yes |

### Data Import Wizard

The Data Import Wizard is the **preferred tool for small, standard-object loads** (<50,000 records). It is browser-based, requires no installation, and includes field-mapping assistance. Supported objects are limited: Leads, Accounts, Contacts, Campaign Members, Cases, Solutions, and Person Accounts (when enabled). It does not support scheduling or command-line automation.

### Data Loader (v66.0, Spring '26)

Data Loader is a desktop application available for macOS and Windows. It supports **all standard and custom objects** and scales to approximately 150 million records via Bulk API 2.0. Key configuration notes:

- **Bulk API 2.0 mode** (default for large loads): batching is managed automatically by Salesforce — do not set manual batch sizes.
- **SOAP mode**: batch size is configurable (max 200 per batch); use only when you need synchronous error feedback for small loads.
- **Bulk API v1 mode** (legacy): 10,000 records per batch; deprecated in favor of v2.
- Hard delete operations require the **"Bulk API Hard Delete"** permission on the running user's profile or permission set, regardless of which API mode is used.
- Credentials in `process-conf.xml` must use OAuth tokens or encrypted passwords — never plaintext passwords in config files.
- Command-line / headless mode (`process.bat` / `process.sh`) is the right choice for scheduled or automated loads.

### Workbench

Workbench (workbench.developerforce.com) is an officially provided browser-based tool useful for ad-hoc SOQL queries, REST API exploration, metadata retrieval, and small record operations. **Salesforce has announced a sunset trajectory for Workbench.** Official replacements are:

- **VS Code + Salesforce Extensions** for metadata work and SOQL execution
- **Salesforce CLI** (`sf data query`) for scripted SOQL
- **Code Builder** for browser-based development

Use Workbench for exploratory, non-production tasks only. Do not build automated workflows that depend on it.

### Salesforce Inspector / Inspector Reloaded

Salesforce Inspector and its community fork Inspector Reloaded are **open-source Chrome browser extensions**. They are **not official Salesforce products** and are not supported by Salesforce Support. They are useful for quick single-record inspection, field API name lookup, and ad-hoc SOQL in the browser. They should never be used for bulk operations, production data changes, or in environments with strict security review requirements (ISV packages, regulated industries).

### Salesforce CLI

The Salesforce CLI (`sf` / `sfdx`) supports data operations via `sf data import`, `sf data export`, `sf data query`, and related commands. It is the right choice for **CI/CD pipelines, scripted migrations, and developer sandbox seeding**. It supports JSON and CSV formats and can target specific API versions.

## Security Considerations

- The **"Bulk API Hard Delete"** permission must be explicitly granted — it is not included in standard admin profiles by default. Audit who holds this permission before enabling it broadly.
- `process-conf.xml` files used by Data Loader in headless mode frequently end up committed to version control with plaintext passwords or usernames. Use encrypted passwords (`encrypt.bat`/`encrypt.sh`) or OAuth 2.0 JWT flow instead.
- Salesforce Inspector and third-party extensions have read/write access to your org's data through your browser session. Evaluate their use against your org's security policies, especially in production.

## Recommended Workflow

1. **Estimate record count and identify target objects.** If under 50,000 records and the object is in the supported list (Leads, Accounts, Contacts, Cases, etc.), use the Data Import Wizard and stop here.
2. **Determine operation type.** Insert, update, upsert, and delete are supported by all tools. Hard delete requires the Bulk API Hard Delete permission — verify it is granted before proceeding.
3. **Select the tool.** For >50K records, all objects, or automated/scheduled runs, use Data Loader in Bulk API 2.0 mode. For scripted/CI contexts use Salesforce CLI. Reserve Workbench for exploratory ad-hoc queries only.
4. **Configure credentials securely.** For Data Loader headless mode, use `encrypt.sh`/`encrypt.bat` to encrypt the password or configure OAuth JWT. Never store plaintext passwords in `process-conf.xml`.
5. **Run a sample load in sandbox.** Execute against a representative 1,000-record subset first. Inspect the success and error CSV outputs before scaling up.
6. **Execute full load and monitor.** For Bulk API 2.0 jobs, monitor job status in Setup > Bulk Data Load Jobs. Capture the error CSV and resolve all failures before closing the migration window.
7. **Validate and archive.** Run post-load record counts and spot-check field values. Archive the success/error CSVs and `process-conf.xml` (with no credentials) for audit purposes.

## Official Sources Used

- https://help.salesforce.com/s/articleView?id=sf.loader_when_to_use.htm&type=5
- https://help.salesforce.com/s/articleView?id=sf.loader_configuring_bulk_api.htm&type=5
- https://help.salesforce.com/s/articleView?id=platform.replacement_workbench_tools.htm&type=5
- https://help.salesforce.com/s/articleView?id=sf.data_import_wizard.htm&type=5
