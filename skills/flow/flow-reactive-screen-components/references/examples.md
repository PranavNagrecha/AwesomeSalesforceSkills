# Examples — Flow Reactive Screen Components

## Example 1: A running line total

**Context:** an order-entry screen collects quantity and unit price. Users had to click
Next to see the line total, then Previous to correct a typo.

**Problem:** the first attempt added a formula and a display component and nothing
updated. The formula referenced the screen's stored outputs rather than the components,
so it resolved to the values as of the last commit — which on a reactive screen is not
what the user is typing. Nothing errored; the flow saved, activated and ran, showing a
stale zero.

**Solution:** reference the components and their attributes.

```text
Screen_Order_Line

  Number  Quantity_Input      Label "Quantity"    Required
  Currency Unit_Price_Input   Label "Unit price"  Required

  Formula  Line_Total   (Currency)
      {!Quantity_Input.value} * {!Unit_Price_Input.value}

  Formula  Line_Total_Display  (Text)
      IF( ISBLANK({!Quantity_Input.value})
          || ISBLANK({!Unit_Price_Input.value}),
          'Enter quantity and price',
          TEXT({!Line_Total}) )

  Display Text  Total_Readout
      Line total: {!Line_Total_Display}

  Display Text  Discount_Notice
      Orders above 10,000 qualify for volume pricing.
      Visibility: {!Line_Total} greater than 10000
```

**Why it works:** `{!Quantity_Input.value}` references the component, so the formula
re-evaluates as the value changes; `{!Screen_Order_Line.Quantity_Input}` would reference
the committed output and would not. Both are valid references that Flow Builder accepts,
which is why this defect reaches production.

`Line_Total_Display` exists because a null in an arithmetic formula produces an unhelpful
result before the user has finished typing — reactive formulas are evaluated against
half-entered screens, which is a state a non-reactive screen never had to handle. The
visibility condition on `Discount_Notice` re-evaluates on the same changes, so progressive
disclosure comes free once the reference is right.

---

## Example 2: A custom screen component that participates in reactivity

**Context:** a custom component renders a product picker with a search box, and a
downstream display component should show the selected product's price without navigation.

**Problem:** the component received its value correctly and drove nothing. The generated
code declared the `@api` property — which is what makes the value arrive — and stopped
there. The return path is a separate mechanism, and without it the flow never learns the
value changed. The symptom is identical to a component that is not reactive at all, which
sends people looking in the wrong place.

**Solution:** dispatch `FlowAttributeChangeEvent` whenever the value changes.

```javascript
import { LightningElement, api, track } from 'lwc';
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

export default class ProductPicker extends LightningElement {
    @api productId;          // reactive attribute, in and out
    @api availableProducts;  // input only

    @track searchTerm = '';

    get matches() {
        if (!this.searchTerm) return [];
        const term = this.searchTerm.toLowerCase();
        return (this.availableProducts || [])
            .filter((p) => p.Name.toLowerCase().includes(term))
            .slice(0, 10);
    }

    handleSearch(event) {
        this.searchTerm = event.target.value;
    }

    handleSelect(event) {
        this.productId = event.currentTarget.dataset.id;
        // The event name must match the @api property name exactly.
        // A mismatch fails silently and looks the same as omitting this line.
        this.dispatchEvent(new FlowAttributeChangeEvent('productId', this.productId));
    }

    @api
    validate() {
        return this.productId
            ? { isValid: true }
            : { isValid: false, errorMessage: 'Select a product before continuing.' };
    }
}
```

The component must also be declared as a flow screen component and its reactive
attributes marked in metadata:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>64.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__FlowScreen</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__FlowScreen">
            <property name="productId" type="String" role="inputAndOutput"/>
            <property name="availableProducts" type="@salesforce/schema/Product2[]"
                      role="inputOnly"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

Downstream, the display component references the custom component the same way it would a
standard one:

```text
Formula  Selected_Price  (Currency)
    ...lookup against {!Product_Picker.productId}...

Display Text  Price_Readout
    Visibility: {!Product_Picker.productId} is not null
```

**Why it works:** `role="inputAndOutput"` is what makes the attribute eligible to
participate in both directions, and the dispatched event is what tells the flow a change
happened so dependents re-evaluate. Both are required; either one alone produces a
component that renders and drives nothing. Keeping `validate()` on the component means the
Next button enforces selection without a separate validation element, and the `.slice(0,
10)` bound on the match list matters because this filter runs on every keystroke — reactive
work is local and cheap only if you keep it that way.
