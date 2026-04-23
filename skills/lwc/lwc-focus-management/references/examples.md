# LWC Focus Management — Examples

## Example 1: Modal Component With Restore

```js
import { LightningElement, api } from 'lwc';
export default class ConfirmDialog extends LightningElement {
  _opener;
  @api open() {
    this._opener = document.activeElement;
    this._isOpen = true;
  }
  renderedCallback() {
    if (this._isOpen && !this._focused) {
      this.template.querySelector('[data-focus="first"]')?.focus();
      this._focused = true;
    }
  }
  handleClose() {
    this._isOpen = false;
    this._focused = false;
    Promise.resolve().then(() => this._opener?.focus?.());
  }
}
```

**Why:** saves the opener; restores on close; respects the render timing.

---

## Example 2: Error Summary Focus

After `handleSubmit()` validates and finds errors:

```js
this.errors = [...];
Promise.resolve().then(() => {
  const summary = this.template.querySelector('[data-focus="error-summary"]');
  summary?.focus();
});
```

The summary element has `role="alert"` so the screen reader announces it
automatically.

---

## Example 3: Parent Triggering Focus In Child

Parent:
```html
<c-address-form data-focus="primary"></c-address-form>
```
Parent's renderedCallback:
```js
this.template.querySelector('c-address-form').focus();
```
Child exposes:
```js
@api focus() {
  this.template.querySelector('lightning-input')?.focus();
}
```

---

## Anti-Pattern: Global querySelector

A component used `document.querySelector('lightning-input')` to find its
own input. In Spring '24 this silently returned null as shadow DOM became
stricter. Fix: `this.template.querySelector` always.
