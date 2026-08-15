# Examples — LWC Drag and Drop

Native HTML5 drag and drop works in Lightning Web Components. What does not work
is the framework syntax people import from Vue and Angular — LWC has **no
`@dragover.prevent` event modifiers**. Every handler is a plain method that calls
`event.preventDefault()` itself.

The examples below use `lwc:ref` / `this.refs` for DOM access, which Salesforce
recommends over `this.template.querySelector()`
([Access Elements the Component
Owns](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-dom-work.html)).

---

## Example 1 — WRONG vs RIGHT: a reorderable priority list

### WRONG — three failures, two of them silent

```html
<!-- priorityList.html — DOES NOT WORK -->
<template>
    <ul>
        <template for:each={items} for:item="item">
            <li key={item.id}
                draggable="true"
                ondragstart={handleDragStart}
                ondragover.prevent               <!-- (1) not LWC syntax -->
                ondrop={handleDrop}>
                {item.label}
            </li>
        </template>
    </ul>
</template>
```

```javascript
handleDragStart(event) {
    // (2) reading dataTransfer later, after the event has been dispatched
    this.draggedEvent = event;
}

handleDrop(event) {
    const id = this.draggedEvent.dataTransfer.getData('text/plain');
    // (3) mutating the array in place — no re-render
    const item = this.items.find((i) => i.id === id);
    item.order = 1;
}
```

1. **`.prevent` is a Vue modifier, not LWC.** The attribute is ignored, `drop`
   never fires, and there is no error. This is the single most common cause of
   "drag and drop doesn't work" in LWC.
2. **`dataTransfer` is only valid during the event.** Stashing the event object
   and reading `dataTransfer` in a later handler yields an empty string. The
   read must be synchronous, inside the handler.
3. **Mutating an array member does not trigger a re-render.** LWC reactivity
   fires on property reassignment.

### RIGHT — with a keyboard path, because drag alone fails accessibility

```html
<!-- priorityList.html -->
<template>
    <div class="slds-m-bottom_small">
        <p id="dnd-instructions" class="slds-text-body_small">
            Drag to reorder, or focus an item and press
            Alt+Up / Alt+Down to move it.
        </p>
    </div>

    <ul lwc:ref="list" role="listbox" aria-labelledby="dnd-instructions">
        <template for:each={items} for:item="item" for:index="index">
            <li key={item.id}
                role="option"
                tabindex="0"
                draggable="true"
                aria-selected={item.isSelected}
                aria-posinset={item.position}
                aria-setsize={itemCount}
                data-id={item.id}
                data-index={index}
                class={item.cssClass}
                ondragstart={handleDragStart}
                ondragover={handleDragOver}
                ondragenter={handleDragEnter}
                ondragleave={handleDragLeave}
                ondragend={handleDragEnd}
                ondrop={handleDrop}
                onkeydown={handleKeyDown}>
                {item.label}
            </li>
        </template>
    </ul>

    <!-- Live region: the only way a screen-reader user learns the move
         happened. aria-grabbed / aria-dropeffect are deprecated in ARIA 1.1
         and should not be used. -->
    <div class="slds-assistive-text"
         role="status"
         aria-live="polite"
         aria-atomic="true">
        {announcement}
    </div>
</template>
```

```javascript
import { LightningElement, api } from 'lwc';

export default class PriorityList extends LightningElement {
    @api
    get records() {
        return this._records;
    }
    set records(value) {
        this._records = value ?? [];
        this.order = this._records.map((r) => r.id);
    }

    _records = [];
    order = [];
    announcement = '';

    _draggedId = null;
    _overId = null;

    get items() {
        const byId = new Map(this._records.map((r) => [r.id, r]));
        return this.order.map((id, index) => {
            const record = byId.get(id);
            return {
                id,
                label: record?.Name,
                position: index + 1,
                isSelected: id === this._draggedId,
                cssClass: this.rowClass(id)
            };
        });
    }

    get itemCount() {
        return this.order.length;
    }

    rowClass(id) {
        const base = 'slds-p-around_x-small drag-row';
        if (id === this._draggedId) return `${base} is-dragging`;
        if (id === this._overId) return `${base} is-drop-target`;
        return base;
    }

    // ---- Pointer path -----------------------------------------------------

    handleDragStart(event) {
        const id = event.currentTarget.dataset.id;
        this._draggedId = id;

        // MUST be synchronous. dataTransfer is only writable during dragstart
        // and only readable during drop.
        event.dataTransfer.setData('text/plain', id);
        event.dataTransfer.effectAllowed = 'move';

        this.announce(`Picked up ${this.labelFor(id)}, position ${this.positionOf(id)} of ${this.itemCount}.`);
    }

    handleDragOver(event) {
        // Without preventDefault, `drop` NEVER FIRES. No error, no warning.
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }

    handleDragEnter(event) {
        event.preventDefault();
        this._overId = event.currentTarget.dataset.id;
    }

    handleDragLeave(event) {
        // dragleave fires when entering a CHILD element too. Guard against
        // clearing the highlight while still inside the row.
        if (event.currentTarget.contains(event.relatedTarget)) {
            return;
        }
        if (this._overId === event.currentTarget.dataset.id) {
            this._overId = null;
        }
    }

    handleDrop(event) {
        event.preventDefault();
        const draggedId = event.dataTransfer.getData('text/plain');
        const targetId = event.currentTarget.dataset.id;
        this.moveTo(draggedId, this.order.indexOf(targetId));
        this._overId = null;
    }

    handleDragEnd() {
        // Fires whether or not a drop occurred — the only reliable cleanup hook.
        this._draggedId = null;
        this._overId = null;
    }

    // ---- Keyboard path ----------------------------------------------------

    handleKeyDown(event) {
        const id = event.currentTarget.dataset.id;
        const from = this.order.indexOf(id);

        // Alt+Arrow rather than bare Arrow: bare arrows are the listbox's
        // navigation keys and must keep moving focus, not content.
        if (!event.altKey) {
            return;
        }
        let to = null;
        if (event.key === 'ArrowUp') to = from - 1;
        else if (event.key === 'ArrowDown') to = from + 1;
        else if (event.key === 'Home') to = 0;
        else if (event.key === 'End') to = this.itemCount - 1;
        else return;

        event.preventDefault();
        if (to < 0 || to >= this.itemCount) {
            this.announce(`${this.labelFor(id)} is already at the ${to < 0 ? 'top' : 'bottom'}.`);
            return;
        }
        this.moveTo(id, to);

        // Focus follows the moved item, or the user loses their place.
        Promise.resolve().then(() => {
            const moved = this.refs.list.querySelector(`[data-id="${id}"]`);
            if (moved) moved.focus();
        });
    }

    // ---- Shared reorder ---------------------------------------------------

    moveTo(id, toIndex) {
        const from = this.order.indexOf(id);
        if (from < 0 || toIndex < 0 || toIndex >= this.order.length || from === toIndex) {
            return;
        }
        // Reassign — never splice in place — so LWC re-renders.
        const next = [...this.order];
        next.splice(from, 1);
        next.splice(toIndex, 0, id);
        this.order = next;

        this.announce(`Moved ${this.labelFor(id)} to position ${toIndex + 1} of ${this.itemCount}.`);
        this.dispatchEvent(new CustomEvent('reorder', {
            detail: { order: [...this.order] }
        }));
    }

    announce(text) {
        // Reset then set on the next microtask. A live region with unchanged
        // text is not re-announced; two consecutive identical moves would be
        // silent otherwise.
        this.announcement = '';
        Promise.resolve().then(() => {
            this.announcement = text;
        });
    }

    labelFor(id) {
        return this._records.find((r) => r.id === id)?.Name ?? 'item';
    }

    positionOf(id) {
        return this.order.indexOf(id) + 1;
    }
}
```

### The five details that make this correct

- **`preventDefault()` on both `dragover` and `dragenter`.** Without `dragover`,
  `drop` never fires. This is not optional and it is not intuitive — the default
  action being cancelled is "reject the drop".
- **`dataTransfer` read and written synchronously.** It is valid only during the
  event.
- **`dragend` for cleanup**, because it fires whether or not a drop happened.
  Cleaning up in `drop` alone leaves the dragging class stuck on an abandoned
  drag.
- **`dragleave` guarded with `contains(relatedTarget)`**, because it fires when
  the pointer moves onto a child element of the row.
- **Alt+Arrow, not bare Arrow.** In a `listbox`, bare arrows navigate. Binding
  them to reorder breaks the navigation the role promises.

---

## Example 2 — Announcements that a screen reader actually reads

### The deprecated approach

`aria-grabbed` and `aria-dropeffect` are deprecated in ARIA 1.1. Do not use
them. Support was inconsistent even when they were current, and they convey
nothing a live region does not convey better.

### The three-moment announcement model

| Moment | Announcement | Why |
|---|---|---|
| Pick up | "Picked up Renewal Task, position 3 of 8." | Confirms the item and gives the starting reference |
| Move (keyboard) | "Moved Renewal Task to position 2 of 8." | Position *and* total — "moved up" alone is not orienting |
| Cancel | "Cancelled. Renewal Task returned to position 3." | Escape must be audible or the user cannot tell it worked |

```javascript
handleKeyDown(event) {
    if (event.key === 'Escape' && this._keyboardDragOriginIndex !== null) {
        const id = this._keyboardDragId;
        this.moveTo(id, this._keyboardDragOriginIndex);
        this.announce(`Cancelled. ${this.labelFor(id)} returned to position ${this._keyboardDragOriginIndex + 1}.`);
        this._keyboardDragOriginIndex = null;
        return;
    }
    // ...
}
```

### The reset-then-set trick, and why it is required

An `aria-live` region announces on **text change**. Setting the same string twice
produces one announcement. Two consecutive moves that generate identical text —
easy when the label is short — would leave the second one silent. Blanking the
region and setting it on the next microtask forces a change every time.

`role="status"` is `aria-live="polite"` by default, which is right here: a
reorder is not urgent enough to interrupt. Reserve `role="alert"` (assertive)
for failures.

---

## Example 3 — A file drop zone that also has a working button

### Context

An attachment area on a Case. Users want to drag files onto it.

### The implementation

```html
<!-- fileDropZone.html -->
<template>
    <div class={dropZoneClass}
         lwc:ref="zone"
         ondragover={handleDragOver}
         ondragenter={handleDragEnter}
         ondragleave={handleDragLeave}
         ondrop={handleDrop}>

        <!-- The input is the accessible control. The drop zone is an
             enhancement layered on top of it, never a replacement:
             a div is not focusable and not operable by keyboard. -->
        <label class="slds-form-element__label" for="file-input">
            Attach files
        </label>
        <input type="file"
               id="file-input"
               lwc:ref="fileInput"
               multiple
               accept=".pdf,.png,.jpg,.jpeg,.docx"
               onchange={handleFileInput} />

        <p class="slds-text-body_small">
            or drop files here
        </p>
    </div>

    <div class="slds-assistive-text" role="status" aria-live="polite">
        {announcement}
    </div>

    <template lwc:if={hasErrors}>
        <div role="alert" class="slds-text-color_error">
            <template for:each={errors} for:item="err">
                <p key={err}>{err}</p>
            </template>
        </div>
    </template>
</template>
```

```javascript
import { LightningElement } from 'lwc';

const MAX_BYTES = 4 * 1024 * 1024;      // enforce client-side for UX only
const ALLOWED = ['pdf', 'png', 'jpg', 'jpeg', 'docx'];

export default class FileDropZone extends LightningElement {
    isOver = false;
    announcement = '';
    errors = [];

    _enterCount = 0;   // dragenter/dragleave fire per descendant

    get hasErrors() {
        return this.errors.length > 0;
    }

    get dropZoneClass() {
        return this.isOver
            ? 'drop-zone drop-zone_active'
            : 'drop-zone';
    }

    handleDragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
    }

    handleDragEnter(event) {
        event.preventDefault();
        // Counting enters/leaves is the reliable way to know whether the
        // pointer is still inside the zone. Comparing event.target to the
        // zone fails because children fire their own enter/leave.
        this._enterCount += 1;
        this.isOver = true;
    }

    handleDragLeave() {
        this._enterCount -= 1;
        if (this._enterCount <= 0) {
            this._enterCount = 0;
            this.isOver = false;
        }
    }

    handleDrop(event) {
        event.preventDefault();
        this._enterCount = 0;
        this.isOver = false;

        // dataTransfer.files is a FileList, not an Array.
        const files = Array.from(event.dataTransfer?.files ?? []);
        this.accept(files);
    }

    handleFileInput(event) {
        this.accept(Array.from(event.target.files ?? []));
        // Reset so selecting the same file twice fires change again.
        event.target.value = null;
    }

    accept(files) {
        this.errors = [];
        if (files.length === 0) {
            // A folder drop yields zero files in most browsers. Say so, rather
            // than appearing to do nothing.
            this.errors = ['No files were found. Folders can’t be uploaded — drop individual files.'];
            return;
        }

        const good = [];
        const bad = [];
        files.forEach((file) => {
            const ext = file.name.split('.').pop()?.toLowerCase();
            if (!ALLOWED.includes(ext)) {
                bad.push(`${file.name}: file type not allowed.`);
            } else if (file.size > MAX_BYTES) {
                bad.push(`${file.name}: larger than 4 MB.`);
            } else {
                good.push(file);
            }
        });

        this.errors = bad;
        if (good.length > 0) {
            this.announcement = `${good.length} file${good.length === 1 ? '' : 's'} ready to upload.`;
            this.dispatchEvent(new CustomEvent('filesaccepted', {
                detail: { files: good }
            }));
        }
    }
}
```

### Three things worth noting

- **The `<input type="file">` is the real control.** A drop zone built from a
  `div` is not focusable, not operable by keyboard, and invisible to assistive
  technology. Layer drop on top of the input; never replace it.
- **Enter/leave counting.** `dragenter` and `dragleave` fire for descendants, so
  a naive `isOver = false` in `dragleave` makes the highlight flicker as the
  pointer crosses child elements. Counting is the robust fix.
- **Client-side validation is UX, not security.** Size and type checks here stop
  a doomed upload early. The server must re-validate — a user can bypass
  everything above.

---

## Example 4 — Jest tests for both interaction paths

```javascript
import { createElement } from 'lwc';
import PriorityList from 'c/priorityList';

const RECORDS = [
    { id: 'a', Name: 'Alpha' },
    { id: 'b', Name: 'Beta' },
    { id: 'c', Name: 'Gamma' }
];

// LWC re-renders on a microtask. Two resolved promises is the canonical flush.
const flush = () => Promise.resolve().then(() => Promise.resolve());

function build() {
    const el = createElement('c-priority-list', { is: PriorityList });
    el.records = RECORDS;
    document.body.appendChild(el);
    return el;
}

/**
 * jsdom implements the drag EVENTS but not a real DataTransfer. Supply a
 * minimal stub — the component only uses getData/setData/dropEffect.
 */
function dataTransferStub() {
    const store = {};
    return {
        setData: (type, value) => { store[type] = String(value); },
        getData: (type) => store[type] ?? '',
        effectAllowed: '',
        dropEffect: ''
    };
}

function dragEvent(type, dataTransfer) {
    const evt = new CustomEvent(type, { bubbles: true });
    evt.dataTransfer = dataTransfer;
    evt.preventDefault = jest.fn();
    return evt;
}

afterEach(() => {
    while (document.body.firstChild) {
        document.body.removeChild(document.body.firstChild);
    }
});

describe('pointer path', () => {
    it('reorders on drag and drop', async () => {
        const el = build();
        await flush();

        const rows = el.shadowRoot.querySelectorAll('li');
        const dt = dataTransferStub();

        rows[0].dispatchEvent(dragEvent('dragstart', dt));
        rows[2].dispatchEvent(dragEvent('dragover', dt));
        rows[2].dispatchEvent(dragEvent('drop', dt));
        await flush();

        const labels = [...el.shadowRoot.querySelectorAll('li')]
            .map((li) => li.textContent.trim());
        expect(labels).toEqual(['Beta', 'Gamma', 'Alpha']);
    });

    it('calls preventDefault on dragover so drop can fire', async () => {
        const el = build();
        await flush();

        const row = el.shadowRoot.querySelector('li');
        const evt = dragEvent('dragover', dataTransferStub());
        row.dispatchEvent(evt);

        // The assertion that catches the single most common bug in this domain.
        expect(evt.preventDefault).toHaveBeenCalled();
    });
});

describe('keyboard path', () => {
    it('reorders with Alt+ArrowDown', async () => {
        const el = build();
        await flush();

        const first = el.shadowRoot.querySelector('li');
        first.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'ArrowDown', altKey: true, bubbles: true
        }));
        await flush();

        const labels = [...el.shadowRoot.querySelectorAll('li')]
            .map((li) => li.textContent.trim());
        expect(labels).toEqual(['Beta', 'Alpha', 'Gamma']);
    });

    it('announces the move with position and total', async () => {
        const el = build();
        await flush();

        el.shadowRoot.querySelector('li').dispatchEvent(
            new KeyboardEvent('keydown', { key: 'ArrowDown', altKey: true, bubbles: true })
        );
        await flush();

        const status = el.shadowRoot.querySelector('[role="status"]');
        expect(status.textContent).toContain('position 2 of 3');
    });

    it('ignores bare arrows so listbox navigation still works', async () => {
        const el = build();
        await flush();

        el.shadowRoot.querySelector('li').dispatchEvent(
            new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
        );
        await flush();

        const labels = [...el.shadowRoot.querySelectorAll('li')]
            .map((li) => li.textContent.trim());
        expect(labels).toEqual(['Alpha', 'Beta', 'Gamma']);
    });
});
```

Config comes from `templates/lwc/jest.config.js`. The `preventDefault` assertion
is the highest-value test here: it fails loudly on the bug that otherwise
presents as "nothing happens" with no error anywhere.

---

## Anti-Pattern — importing a drag library for a list

**What practitioners do:** load SortableJS or Dragula as a static resource and
wire it up in `renderedCallback`.

**What goes wrong:** shadow DOM is the immediate problem — libraries that query
`document` cannot see inside your component's shadow tree, so initialisation
either finds nothing or requires light DOM, which discards style encapsulation.
Lightning Web Security adds a second layer: components run in a JavaScript
sandbox with distorted browser APIs, so a library manipulating globals or
reaching across the sandbox boundary may behave differently than it does
standalone. Then there is bundle weight against your performance budget, a
library that owns the DOM while LWC also thinks it owns the DOM, and — most
importantly — most of these libraries ship no keyboard path, so you have taken
on a dependency and still have to build accessibility yourself.

**Correct approach:** the native API is about 80 lines including the keyboard
path, as Example 1 shows. Reach for a library only for genuinely hard cases —
nested trees, cross-window drag, virtualised reordering — and when you do, wrap
it in a single LWC that owns the integration, test it under Lightning Web
Security in a real org rather than only in Jest, and budget for building the
keyboard path regardless.
