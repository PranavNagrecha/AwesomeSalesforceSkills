# Baseline comparison protocol

For each release-cohort scenario, run:

A. host/model with raw evidence and no SfSkills product context;
B. host/model with selected SfSkills knowledge but no evidence framework;
C. full SfSkills framework;
D. previous SfSkills release, when available.

Keep evidence, model, host, temperature/settings, and time budget as equivalent as possible. Compare required-finding recall, unsupported claims, status, safety, context cost, duration, and human usefulness.

The goal is to prove which layer adds value. If B performs as well as C, simplify the framework. If C adds latency without quality, remove or change the subagent/context design.
