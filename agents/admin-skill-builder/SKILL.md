---
name: admin-skill-builder
description: "Use to build Admin and BA role skills for any Salesforce cloud. Triggers: 'build an admin skill for', 'create a BA skill about', 'add admin coverage for'. NOT for Dev, Data, or Architect skills — use the role-specific builder agents for those."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - admin
  - ba
  - skill-builder
  - automation
inputs:
  - skill name and topic
  - cloud and role from MASTER_QUEUE.md row
outputs:
  - validated admin or BA skill package ready for commit
dependencies:
  - content-researcher
  - validator
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---
