# Examples — LWC Drag and Drop

## Example 1: Priority list reorder

**Context:** Case priority list

**Problem:** Users wanted drag-to-reorder

**Solution:**

`<li draggable=true @dragstart={onDragStart} @drop={onDrop}>` + keyboard arrow handler

**Why it works:** Native API + keyboard fallback


---

## Example 2: File drop zone

**Context:** Attachments upload

**Problem:** Click-to-upload felt clunky

**Solution:**

Dropzone div with `@dragover.prevent` and `@drop` that reads `dataTransfer.files`

**Why it works:** HTML5 file drop natively supports this

