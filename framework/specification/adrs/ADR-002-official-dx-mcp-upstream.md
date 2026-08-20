# ADR-002-official-dx-mcp-upstream: Use official Salesforce DX MCP/CLI as upstream where practical

**Status:** Accepted  
**Date:** 2026-08-19

## Context

SfSkills is evolving from a skill library into a Salesforce AI engineering framework and must make an explicit decision on this architectural boundary.

## Decision

SfSkills implements a restricted evidence broker and product normalization rather than duplicating the full Salesforce tool surface.

## Consequences

SfSkills remains differentiated by knowledge, evidence, context, review, and QA. Upstream changes require compatibility tests.

## Revisit when

Two or more shipped products produce evidence that the decision creates measurable quality, safety, usability, or maintenance problems.
