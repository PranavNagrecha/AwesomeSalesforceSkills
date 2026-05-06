# Examples — LWC Drag and Drop

## Example 1: Minimal kanban with two columns

```html
<template>
    <div class="board">
        <template for:each={columns} for:item="col">
            <div key={col.id}
                 class={col.cssClass}
                 data-col-id={col.id}
                 ondragover={handleDragOver}
                 ondragenter={handleDragEnter}
                 ondragleave={handleDragLeave}
                 ondrop={handleDrop}>
                <h3>{col.label}</h3>
                <template for:each={col.cards} for:item="card">
                    <div key={card.id}
                         class="card"
                         draggable="true"
                         data-card-id={card.id}
                         data-source-col={col.id}
                         ondragstart={handleDragStart}
                         ondragend={handleDragEnd}>
                        {card.title}
                    </div>
                </template>
            </div>
        </template>
    </div>
</template>
```

```js
import { LightningElement, track } from 'lwc';

const MIME = 'application/x-acme-card';

export default class Kanban extends LightningElement {
    @track columns = [
        { id: 'todo',  label: 'To Do',  cards: [{id:'a',title:'A'},{id:'b',title:'B'}] },
        { id: 'doing', label: 'Doing',  cards: [] },
        { id: 'done',  label: 'Done',   cards: [] }
    ];
    draggedId = null;
    overColId = null;

    handleDragStart(e) {
        const id = e.currentTarget.dataset.cardId;
        const source = e.currentTarget.dataset.sourceCol;
        this.draggedId = id;
        e.dataTransfer.setData(MIME, JSON.stringify({ id, source }));
        e.dataTransfer.effectAllowed = 'move';
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    handleDragEnter(e) {
        this.overColId = e.currentTarget.dataset.colId;
        this.recalcColumnClasses();
    }

    handleDragLeave(e) {
        if (this.overColId === e.currentTarget.dataset.colId) {
            this.overColId = null;
            this.recalcColumnClasses();
        }
    }

    handleDrop(e) {
        e.preventDefault();
        const targetCol = e.currentTarget.dataset.colId;
        const raw = e.dataTransfer.getData(MIME);
        if (!raw) return;
        const { id, source } = JSON.parse(raw);
        this.moveCard(id, source, targetCol);
    }

    handleDragEnd() {
        this.draggedId = null;
        this.overColId = null;
        this.recalcColumnClasses();
    }
}
```

Note `e.preventDefault()` in `dragover` (mandatory for drop to
fire) and `currentTarget.dataset.colId` (lets the same handler
apply to all columns).

---

## Example 2: Card-on-card drop for ordered insertion

For a sortable list, each item is both a draggable and a drop
zone. Use the cursor's vertical position relative to the item
midpoint to decide before/after.

```js
handleCardDragOver(e) {
    e.preventDefault();
    const rect = e.currentTarget.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;
    e.currentTarget.dataset.dropPosition =
        e.clientY < midpoint ? 'before' : 'after';
}

handleCardDrop(e) {
    e.preventDefault();
    const target = e.currentTarget.dataset.cardId;
    const pos    = e.currentTarget.dataset.dropPosition;  // 'before'|'after'
    const raw    = e.dataTransfer.getData(MIME);
    const { id } = JSON.parse(raw);
    this.reorder(id, target, pos);
}
```

A CSS class `.drop-position-before { border-top: 2px solid var(--slds-g-color-accent); }`
gives the user the visual line.

---

## Example 3: Keyboard-accessible alternative

```html
<div class="card"
     tabindex="0"
     draggable="true"
     onkeydown={handleCardKeydown}
     ...>
    {card.title}
    <lightning-button-menu alternative-text="Move to" icon-size="x-small">
        <template for:each={destinations} for:item="d">
            <lightning-menu-item key={d.id}
                                 value={d.id}
                                 label={d.label}
                                 onclick={handleMenuMove}>
            </lightning-menu-item>
        </template>
    </lightning-button-menu>
</div>
```

```js
handleCardKeydown(e) {
    if (e.key === 'ArrowUp')   this.moveByOffset(-1);
    if (e.key === 'ArrowDown') this.moveByOffset(+1);
}
```

The button menu is the dignified path: open, choose target, move.
The arrow keys are the fast path. Together they cover the
accessibility gap left by HTML5 drag.

---

## Example 4: Visual feedback on the dragged element

```css
.card { transition: opacity 120ms; }
.card.dragging { opacity: 0.4; }

.column { transition: background 120ms; }
.column.over-target {
    background: var(--slds-g-color-neutral-95, #f3f3f3);
    outline: 2px dashed var(--slds-g-color-accent, #1589ee);
}
```

```js
get cardCssClass() {
    return this.draggedId === this.cardId ? 'card dragging' : 'card';
}
```

Inline class binding via a getter is cleaner than mutating CSS
classes from JS.

---

## Example 5: Sanitizing the data round-trip

```js
const MIME = 'application/x-acme-card';

handleDragStart(e) {
    const payload = { id: e.currentTarget.dataset.cardId, ts: Date.now() };
    e.dataTransfer.setData(MIME, JSON.stringify(payload));
    // also set 'text/plain' for browser-internal compatibility
    e.dataTransfer.setData('text/plain', payload.id);
}

handleDrop(e) {
    e.preventDefault();
    const raw = e.dataTransfer.getData(MIME);
    if (!raw) {
        // Drop came from outside (e.g. text dragged from another window)
        return;
    }
    let parsed;
    try { parsed = JSON.parse(raw); } catch { return; }
    if (!parsed.id) return;
    this.acceptDrop(parsed.id);
}
```

The custom MIME prefix means foreign drops (from another tab, a
text selection, an image drag) miss your handler cleanly.
