# Examples — Calculation Procedures

---

## Example 1: Insurance Premium Calculation with Tiered Rate Matrix

**Context:** An insurance carrier sells auto policies with premiums that vary by driver age bracket, vehicle class, and coverage tier. Rates change quarterly. The pricing team manages rates in a spreadsheet today and wants to load them into Salesforce without deploying code each quarter.

**Problem:** Without a Calculation Matrix, each rate combination is hardcoded in Apex or a Flow formula resource. Every rate revision requires a change set, testing, and approval — typically a two-week cycle. Mid-quarter corrections are blocked by the deployment window.

**Solution:**

1. Create a Calculation Matrix named `AutoPremiumRates` with these columns:

   | Column | Type | Role |
   |--------|------|------|
   | `DriverAgeBracket` | Text | Input |
   | `VehicleClass` | Text | Input |
   | `CoverageTier` | Text | Input |
   | `AnnualBaseRate` | Decimal | Output |
   | `RiskMultiplier` | Decimal | Output |

2. Load rows for the current quarter. Set `StartDateTime` to the first day of the quarter and `EndDateTime` to the last day (23:59:59 UTC). Set `Rank = 1`. Activate the version.

3. Create a Calculation Procedure named `ComputeAutoPremium` with these variables:

   ```
   Input variables:
     DriverAgeBracket  (Text)
     VehicleClass      (Text)
     CoverageTier      (Text)
     BaseCoverageAmount (Decimal)

   Output variables:
     AnnualBaseRate    (Decimal)
     RiskMultiplier    (Decimal)
     FinalPremium      (Decimal)
   ```

4. Add a Decision Matrix Lookup step. Map input variables to matrix input columns. Map `AnnualBaseRate` and `RiskMultiplier` matrix outputs to the corresponding procedure variables.

5. Add an Assignment step to compute the final premium:

   ```
   FinalPremium = BaseCoverageAmount * AnnualBaseRate * RiskMultiplier
   ```

6. Activate the procedure version.

7. Call from OmniScript using the Calculation Procedure action element, passing `DriverAgeBracket`, `VehicleClass`, `CoverageTier`, and `BaseCoverageAmount` as inputs. Bind `FinalPremium` to the quote record.

**Why it works:** The matrix version handles all rate lookup logic. When rates change next quarter, the pricing team creates a new matrix version with the new `StartDateTime`, loads new rows, and activates it — no deployment needed. The procedure remains unchanged.

---

## Example 2: Product Pricing with Quantity Discounts

**Context:** A manufacturer applies tiered quantity discounts on top of a base price. Discounts vary by product line and quantity bracket. Sales reps need real-time pricing in a CPQ-style OmniScript.

**Problem:** A single Apex class calculated discounts by walking through a series of `if/else` brackets. Adding a new product line or changing a bracket required Apex development and deployment. The class also had no test for edge cases like exact bracket boundary values.

**Solution:**

1. Create a Calculation Matrix named `QuantityDiscounts` with columns:

   | Column | Type | Role |
   |--------|------|------|
   | `ProductLine` | Text | Input |
   | `QuantityMin` | Decimal (Range Start) | Input |
   | `QuantityMax` | Decimal (Range End) | Input |
   | `DiscountPercent` | Decimal | Output |

2. Load rows:

   ```
   ProductLine=Hardware, QuantityMin=1,  QuantityMax=9,   DiscountPercent=0.00
   ProductLine=Hardware, QuantityMin=10, QuantityMax=49,  DiscountPercent=0.05
   ProductLine=Hardware, QuantityMin=50, QuantityMax=999, DiscountPercent=0.10
   ProductLine=Software, QuantityMin=1,  QuantityMax=4,   DiscountPercent=0.00
   ProductLine=Software, QuantityMin=5,  QuantityMax=24,  DiscountPercent=0.08
   ```

   Activate the matrix version.

3. Create a Calculation Procedure named `ComputeLineItemPrice` with input variables `ProductLine` (Text), `Quantity` (Decimal), `ListPrice` (Decimal). Output variables: `DiscountPercent` (Decimal), `NetPrice` (Decimal).

4. Add a Decision Matrix Lookup step mapping `ProductLine` and `Quantity` as inputs. Map the `DiscountPercent` output column to the `DiscountPercent` procedure variable.

5. Add an Assignment step:

   ```
   NetPrice = ListPrice * (1 - DiscountPercent)
   ```

6. Call this procedure from the Integration Procedure that hydrates the quote line in the OmniScript.

**Why it works:** Range-based input columns let a single row match any quantity within the bracket. Sales operations updates the matrix rows when discount schedules change. No Apex changes, no deployment cycle.

---

## Anti-Pattern: Hardcoding Rates in Assignment Steps

**What practitioners do:** Instead of using a Calculation Matrix for rate lookups, they build a tree of Condition steps with Assignment steps that hardcode each rate value inside the Condition branches.

**What goes wrong:** Each rate change requires editing the Calculation Procedure, creating a new version, and activating it. This requires someone with OmniStudio admin access to update business-owned data. It also makes the procedure version history noisy — version 1, 2, 3 are just rate-table changes rather than logic changes. If there are many rates, the Condition tree becomes unmanageable and the built-in test harness requires separate test runs per branch.

**Correct approach:** Encode rates in a Calculation Matrix. The procedure contains only business logic (how to calculate); the matrix contains business data (what the rates are). This separation allows business users to own rate management without touching procedure versions.
