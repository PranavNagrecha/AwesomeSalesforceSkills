# LLM Anti-Patterns — Commerce Inventory Data

Common mistakes AI coding assistants make when generating or advising on Salesforce Omnichannel Inventory (OCI) management.

---

## Anti-Pattern 1: Sending More Than 100 SKUs in a Single batchInventoryUpdate Call

**What the LLM generates:** Integration code that collects all updated SKUs from a WMS event and sends them in a single `batchInventoryUpdate` API call regardless of count.

**Why it happens:** LLMs generate straightforward API calls without modeling per-call payload limits. They assume the API accepts arbitrary batch sizes.

**Correct pattern:** Always chunk SKU-location update payloads at ≤100 items per call. Implement a batching loop that iterates through the full SKU list in 100-item slices, making one API call per slice.

**Detection hint:** If integration code calls batchInventoryUpdate with a list that could contain more than 100 items in production (e.g., a full daily restock event), batching is missing.

---

## Anti-Pattern 2: Scheduling High-Frequency Full IMPEX Imports

**What the LLM generates:** A scheduler configuration that runs OCI full inventory IMPEX imports every 5 or 15 minutes to keep Commerce storefront availability synchronized with WMS.

**Why it happens:** LLMs optimize for data freshness without modeling the IMPEX spacing constraint. They treat IMPEX like a standard file-based data sync that can run arbitrarily frequently.

**Correct pattern:** Full OCI IMPEX imports must have sufficient spacing between runs to avoid data corruption. Full IMPEX is designed for daily (nightly) batch snapshots. For near-real-time inventory updates, use `batchInventoryUpdate` triggered by WMS webhook events.

**Detection hint:** If a scheduler runs full OCI IMPEX more frequently than once per hour, the spacing constraint is being violated and data corruption risk is present.

---

## Anti-Pattern 3: Conflating OCI Inventory with FSL Field Inventory

**What the LLM generates:** Code or instructions that use OCI APIs for Field Service Lightning technician parts management, or vice versa — recommending FSL inventory objects for Commerce storefront availability.

**Why it happens:** LLMs associate "Salesforce inventory" with a single system. They do not model the bifurcation between OCI (Commerce storefront availability) and FSL inventory (technician dispatch parts).

**Correct pattern:** OCI is for Commerce product availability display and reservation management. FSL inventory tracks parts and materials for field technician dispatch. Use OCI for storefront; use FSL for field service. If a product exists in both, integrate via middleware using batchInventoryUpdate to push FSL stock changes to OCI.

**Detection hint:** If OCI API calls appear in FSL work order or technician dispatch code, or FSL objects appear in Commerce availability logic, the systems are being conflated.

---

## Anti-Pattern 4: Displaying Individual Warehouse Stock to Buyers

**What the LLM generates:** A Commerce availability component that queries OCI by individual Location (warehouse) and displays per-warehouse stock counts to the buyer.

**Why it happens:** LLMs model location-based inventory as warehouse-level data because that is how WMS systems work. They do not model that OCI exposes availability at the Location Group level for Commerce.

**Correct pattern:** Commerce storefronts display availability aggregated at the Location Group level. Individual warehouse stock levels are not surfaced to buyers. Design the storefront availability display using Location Group availability, not individual Location queries.

**Detection hint:** If the availability display query filters by specific Location identifiers (warehouses) rather than Location Groups, the storefront is bypassing OCI's intended aggregation model.

---

## Anti-Pattern 5: Uploading Uncompressed IMPEX Files Over 100 MB

**What the LLM generates:** IMPEX upload code that sends uncompressed CSV files regardless of size.

**Why it happens:** LLMs do not consistently model the gzip compression requirement triggered by the 100 MB size threshold.

**Correct pattern:** OCI IMPEX files over 100 MB must be gzip-compressed before upload. Apply gzip compression as a standard step in the IMPEX pipeline regardless of file size to ensure the production path (large catalog = large file) is always tested with compression active.

**Detection hint:** If the IMPEX upload script does not include compression logic and the catalog has more than a few thousand SKUs, production files will likely exceed 100 MB without compression.
