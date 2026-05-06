# Examples — LWC Custom Lookup

## Example 1: Apex search method (single-object SOQL with FLS)

```apex
public with sharing class LookupController {
    @AuraEnabled(cacheable=true)
    public static List<LookupResult> searchAccounts(String term) {
        if (String.isBlank(term) || term.length() < 2) {
            return new List<LookupResult>();
        }
        String like = '%' + String.escapeSingleQuotes(term) + '%';
        List<Account> rows = [
            SELECT Id, Name, Industry
            FROM Account
            WHERE Name LIKE :like WITH SECURITY_ENFORCED
            ORDER BY LastViewedDate DESC NULLS LAST
            LIMIT 10
        ];
        List<LookupResult> out = new List<LookupResult>();
        for (Account a : rows) {
            out.add(new LookupResult(a.Id, a.Name, a.Industry));
        }
        return out;
    }

    public class LookupResult {
        @AuraEnabled public String id;
        @AuraEnabled public String title;
        @AuraEnabled public String subtitle;
        public LookupResult(String i, String t, String s) {
            id = i; title = t; subtitle = s;
        }
    }
}
```

`@AuraEnabled(cacheable=true)` lets `@wire` cache identical
queries. `WITH SECURITY_ENFORCED` enforces FLS without writing
manual `Schema.DescribeFieldResult` checks.

---

## Example 2: Debounced search in LWC controller

```js
import { LightningElement, track } from 'lwc';
import searchAccounts from '@salesforce/apex/LookupController.searchAccounts';

const DEBOUNCE_MS = 280;

export default class CustomLookup extends LightningElement {
    @track results = [];
    @track selected = null;
    @track activeIndex = -1;
    @track isOpen = false;
    isLoading = false;
    _searchTimer;

    handleInput(event) {
        const term = event.target.value;
        clearTimeout(this._searchTimer);
        if (!term || term.length < 2) {
            this.results = [];
            this.isOpen = false;
            return;
        }
        this.isLoading = true;
        this._searchTimer = setTimeout(async () => {
            try {
                this.results = await searchAccounts({ term });
                this.activeIndex = this.results.length ? 0 : -1;
                this.isOpen = true;
            } finally {
                this.isLoading = false;
            }
        }, DEBOUNCE_MS);
    }

    handleSelect(event) {
        const id = event.currentTarget.dataset.id;
        this.selected = this.results.find(r => r.id === id);
        this.isOpen = false;
        this.dispatchEvent(new CustomEvent('select', {
            detail: { recordId: this.selected.id }
        }));
    }
}
```

`clearTimeout` is the key call — without it, three quick
keystrokes fire three callouts. `event.target.value` is captured
synchronously before the timer fires.

---

## Example 3: Keyboard navigation

```js
handleKeydown(event) {
    if (!this.isOpen || !this.results.length) return;
    switch (event.key) {
        case 'ArrowDown':
            event.preventDefault();
            this.activeIndex =
                Math.min(this.activeIndex + 1, this.results.length - 1);
            break;
        case 'ArrowUp':
            event.preventDefault();
            this.activeIndex = Math.max(this.activeIndex - 1, 0);
            break;
        case 'Enter':
            event.preventDefault();
            const r = this.results[this.activeIndex];
            if (r) this.selectRecord(r);
            break;
        case 'Escape':
            this.isOpen = false;
            break;
    }
}

get resultsWithActive() {
    return this.results.map((r, i) => ({
        ...r,
        cssClass: i === this.activeIndex
            ? 'slds-listbox__option slds-has-focus'
            : 'slds-listbox__option'
    }));
}
```

`aria-activedescendant` on the input (set to the active
result's id) lets a screen reader follow the highlighted row
without focus actually jumping into the listbox.

---

## Example 4: Pill rendering for selected state

```html
<template>
    <template lwc:if={selected}>
        <lightning-pill
            label={selected.title}
            href="javascript:void(0)"
            onremove={handleRemove}>
            <lightning-icon
                icon-name="standard:account"
                size="x-small"
                slot="media">
            </lightning-icon>
        </lightning-pill>
    </template>

    <template lwc:else>
        <div class="slds-combobox_container">
            <input type="text"
                   class="slds-input"
                   onkeydown={handleKeydown}
                   oninput={handleInput}
                   role="combobox"
                   aria-expanded={isOpen}
                   aria-autocomplete="list" />

            <template lwc:if={isOpen}>
                <ul role="listbox" class="slds-listbox">
                    <template for:each={resultsWithActive} for:item="r">
                        <li key={r.id}
                            data-id={r.id}
                            class={r.cssClass}
                            onmousedown={handleSelect}
                            role="option">
                            {r.title}
                            <span class="slds-text-color_weak">
                                — {r.subtitle}
                            </span>
                        </li>
                    </template>
                </ul>
            </template>
        </div>
    </template>
</template>
```

`onmousedown` (not `onclick`) on the result lets the click fire
*before* the input's `blur`, which is what would close the list
otherwise.

---

## Example 5: Multi-object SOSL search

```apex
@AuraEnabled(cacheable=true)
public static List<LookupResult> searchMixed(String term) {
    if (String.isBlank(term) || term.length() < 2) {
        return new List<LookupResult>();
    }
    String escaped = String.escapeSingleQuotes(term);
    List<List<SObject>> rs = [
        FIND :escaped IN NAME FIELDS
        RETURNING
            Account(Id, Name, Industry),
            Contact(Id, Name, Email),
            Opportunity(Id, Name, StageName)
        LIMIT 15
    ];
    List<LookupResult> out = new List<LookupResult>();
    for (Account a : (List<Account>) rs[0])
        out.add(new LookupResult(a.Id, a.Name, 'Account: ' + a.Industry));
    for (Contact c : (List<Contact>) rs[1])
        out.add(new LookupResult(c.Id, c.Name, 'Contact: ' + c.Email));
    for (Opportunity o : (List<Opportunity>) rs[2])
        out.add(new LookupResult(o.Id, o.Name, 'Opp: ' + o.StageName));
    return out;
}
```

SOSL is searchable-index-aware (the search index updates
asynchronously after DML), so brand-new records may not appear
for ~30 seconds. Document this in the UI when relevant.
