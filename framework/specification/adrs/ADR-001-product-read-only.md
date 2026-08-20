# ADR-001-product-read-only: Product tools remain read-only

**Status:** Accepted  
**Date:** 2026-08-19

## Context

SfSkills is evolving from a skill library into a Salesforce AI engineering framework and must make an explicit decision on this architectural boundary.

## Decision

Ordinary product agents cannot mutate Salesforce. Controlled mutation exists only in separately authorized disposable scratch-org setup code.

## Consequences

This minimizes blast radius and makes diagnostics usable in customer environments. It excludes automatic remediation from V2.

## Revisit when

Two or more shipped products produce evidence that the decision creates measurable quality, safety, usability, or maintenance problems.
