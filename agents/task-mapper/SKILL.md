---
name: task-mapper
description: "Use to map the complete task universe for a Salesforce Cloud × Role cell and populate MASTER_QUEUE.md with TODO rows. Triggers: 'map tasks for Sales Cloud Admin', 'populate the queue for Service Cloud Dev', 'research what a BA does in Experience Cloud'. NOT for building skills — only maps what needs to be built."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - research
  - task-mapping
  - queue-management
  - automation
inputs:
  - cloud name
  - role (Admin/BA/Dev/Data/Architect)
  - RESEARCH row from MASTER_QUEUE.md
outputs:
  - TODO rows inserted into MASTER_QUEUE.md for every confirmed gap
  - updated progress summary in MASTER_QUEUE.md
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---
