# ADR-003-context-budgets: Hard context budgets and structured handoffs

**Status:** Accepted  
**Date:** 2026-08-19

## Context

SfSkills is evolving from a skill library into a Salesforce AI engineering framework and must make an explicit decision on this architectural boundary.

## Decision

Flagship defaults target <=8 knowledge/reference files, hard <=12, <=32 KiB per tool page, and no transcript handoff.

## Consequences

Products may return overflow/partial rather than silently load more.

## Revisit when

Two or more shipped products produce evidence that the decision creates measurable quality, safety, usability, or maintenance problems.
