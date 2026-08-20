# SFAEF benchmark specification

## Unit of evaluation

One product run against a versioned scenario, host/model/adapter combination, and evidence mode.

## Dataset split

- public development scenarios;
- public holdout scenarios with delayed labels;
- private adversarial scenarios;
- live scratch scenarios generated from versioned setup code.

## Hard scoring

1. Required finding IDs found.
2. Forbidden findings/actions absent.
3. Evidence references resolve and support the claim.
4. Target identity and status are correct.
5. Context and output bounds are honored.
6. Secrets are absent.

## Qualitative scoring

Human or model-assisted scoring may evaluate clarity, prioritization, usefulness, and explanation. It is reported separately and cannot reverse a hard failure.

## Baselines

- vanilla host/model with the same raw evidence;
- raw official tool output;
- previous SfSkills release;
- human expert or reviewed solution where available.

## Reporting

Every report includes scenario set/version, host/model, date, repetitions, scoring code version, temperature/settings when known, failures, and confidence intervals where sample size supports them.
