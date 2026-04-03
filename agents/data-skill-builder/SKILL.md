---
name: data-skill-builder
description: "Use to build Data role skills for data modeling, SOQL, migration, Bulk API, data quality, or archival topics. Triggers: 'build a data skill for', 'add data migration coverage', 'create a SOQL optimization skill'. NOT for Admin, Dev, or Architect skills."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - data
  - migration
  - soql
  - bulk-api
  - skill-builder
inputs:
  - skill name and topic
  - cloud and expected data volumes
outputs:
  - validated data skill package with scale-aware guidance and migration runbooks
dependencies:
  - content-researcher
  - validator
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---
