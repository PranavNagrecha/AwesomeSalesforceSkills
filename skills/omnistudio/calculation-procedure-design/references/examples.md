# Calculation Procedure — Examples

## Example 1: Simple Regional Pricing Matrix

**Matrix: `RegionalPriceMatrix_v3`**

| Region | ProductTier | BasePrice | DiscountPct |
|---|---|---|---|
| NA | Gold | 100 | 0.10 |
| NA | Silver | 80 | 0.05 |
| NA | * | 60 | 0.00 |
| EU | Gold | 110 | 0.10 |
| EU | * | 75 | 0.00 |
| * | * | 50 | 0.00 |

**Procedure steps:**

1. Matrix lookup → `BasePrice`, `DiscountPct`.
2. Expression: `NetPrice = BasePrice * (1 - DiscountPct)`.
3. Output `NetPrice`.

## Example 2: Range Matrix (Insurance Rating)

**Matrix: `AutoRatingMatrix_v7`** — range on `DriverAge`, `PriorClaims`.

| DriverAgeMin | DriverAgeMax | PriorClaimsMin | PriorClaimsMax | BaseRate |
|---|---|---|---|---|
| 16 | 24 | 0 | 0 | 1.80 |
| 16 | 24 | 1 | 99 | 2.50 |
| 25 | 64 | 0 | 0 | 1.00 |
| 25 | 64 | 1 | 2 | 1.25 |
| 25 | 64 | 3 | 99 | 1.75 |
| 65 | 120 | 0 | 99 | 1.20 |

Ranges are non-overlapping and inclusive.

## Example 3: Procedure With Expression Set

Steps:

1. Constant `MinPremium = 250`.
2. Matrix lookup → `BaseRate`.
3. Aggregation: `PolicyPremium = sum(VehiclePremiums)`.
4. Expression set: `FinalPremium = max(PolicyPremium, MinPremium)`.
5. Output `FinalPremium`.

## Example 4: Effective-Dated Version Switch

Two active versions: `v6` (effective through 2026-06-30) and `v7`
(effective from 2026-07-01). Procedure looks up the matrix by quote
issue date, not "today", so back-dated quotes use the correct rates.

## Example 5: Test-Mode Fixture

```json
[
  { "input": { "region": "NA", "tier": "Gold" },
    "expect": { "NetPrice": 90 } },
  { "input": { "region": "EU", "tier": "Silver" },
    "expect": { "NetPrice": 75 } },
  { "input": { "region": "APAC", "tier": "Gold" },
    "expect": { "NetPrice": 50 } }
]
```

Run after every activation.
