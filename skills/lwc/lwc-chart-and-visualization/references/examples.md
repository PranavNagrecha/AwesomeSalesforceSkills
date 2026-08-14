# Examples — LWC Chart and Visualization

Worked artifacts for the patterns in `SKILL.md`.

---

## Example 1: Chart.js from a static resource, created once and torn down

**Context:** A pipeline-by-stage bar chart on the Account record page.

**Problem:** `renderedCallback` fires on every render, so the naive version
constructs a new Chart on each one. Instances stack on the same canvas, tooltips
fire multiple times, and nothing is released when the user navigates away.

**Solution:** Load the library once, build the chart once behind a guard, update
data in place, destroy on disconnect.

```html
<!-- pipelineChart.html -->
<template>
    <lightning-card title="Pipeline by Stage">
        <div class="slds-p-around_medium">
            <canvas class="chart" role="img"
                    aria-describedby="chart-data"></canvas>

            <!-- The accessible representation of the same numbers. -->
            <table id="chart-data" class="slds-assistive-text">
                <caption>Pipeline amount by opportunity stage</caption>
                <thead><tr><th scope="col">Stage</th><th scope="col">Amount</th></tr></thead>
                <tbody>
                    <template for:each={buckets} for:item="b">
                        <tr key={b.stage}>
                            <th scope="row">{b.stage}</th><td>{b.amount}</td>
                        </tr>
                    </template>
                </tbody>
            </table>
        </div>
    </lightning-card>
</template>
```

```js
// pipelineChart.js
import { LightningElement, api, wire } from 'lwc';
import { loadScript } from 'lightning/platformResourceLoader';
import CHARTJS from '@salesforce/resourceUrl/chartjs_v4_4_0';
import getPipelineByStage from '@salesforce/apex/PipelineChartController.getPipelineByStage';

export default class PipelineChart extends LightningElement {
    @api recordId;

    buckets = [];
    chart;                 // the live Chart.js instance
    libLoaded = false;     // boolean guard — renderedCallback runs many times

    @wire(getPipelineByStage, { accountId: '$recordId' })
    wiredBuckets({ data, error }) {
        if (data) {
            this.buckets = data;
            this.refreshChart();
        } else if (error) {
            this.buckets = [];
        }
    }

    async renderedCallback() {
        if (this.libLoaded) {
            return;                       // without this, a new Chart per render
        }
        this.libLoaded = true;
        await loadScript(this, CHARTJS + '/chart.umd.js');
        this.refreshChart();
    }

    refreshChart() {
        if (!this.libLoaded || !this.buckets.length) {
            return;
        }
        // Shadow DOM: document.getElementById would return null here.
        const canvas = this.template.querySelector('canvas.chart');
        if (!canvas) {
            return;                       // not rendered yet; the wire will re-call us
        }

        if (this.chart) {                 // update in place, do not reconstruct
            this.chart.data.labels = this.buckets.map((b) => b.stage);
            this.chart.data.datasets[0].data = this.buckets.map((b) => b.amount);
            this.chart.update();
            return;
        }

        // eslint-disable-next-line no-undef
        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: this.buckets.map((b) => b.stage),
                datasets: [{ label: 'Amount', data: this.buckets.map((b) => b.amount) }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    disconnectedCallback() {
        this.chart?.destroy();            // otherwise the instance outlives the page
        this.chart = undefined;
    }
}
```

**Why it works:** `libLoaded` is the boolean guard the LWC docs prescribe for
one-time work in `renderedCallback`. `this.template.querySelector` is the only
way to reach a node inside the shadow root. The hidden `<table>` is generated
from the same `buckets` array the chart uses, so it cannot drift, and
`aria-describedby` ties it to the canvas. `disconnectedCallback` releases the
instance.

---

## Example 2: Aggregate in Apex so the browser never sees the rows

**Context:** A 12-month revenue trend across an org with 300,000 closed-won
Opportunities.

**Problem:** Returning row-level data serialises hundreds of thousands of records
into the wire response for a chart that draws twelve points — and a single SOQL
transaction can retrieve at most 50,000 records, so the query is fragile as well
as wasteful.

**Solution:** `GROUP BY` on the server; return exactly the points the chart draws.

```apex
public with sharing class RevenueTrendController {

    public class Bucket {
        @AuraEnabled public String  period { get; set; }
        @AuraEnabled public Decimal amount { get; set; }
    }

    @AuraEnabled(cacheable=true)
    public static List<Bucket> getMonthlyRevenue(Integer months) {
        Integer window = (months == null || months <= 0) ? 12 : Math.min(months, 36);
        Date cutoff = Date.today().addMonths(-window).toStartOfMonth();

        List<Bucket> buckets = new List<Bucket>();
        for (AggregateResult ar : [
                SELECT CALENDAR_YEAR(CloseDate)  yr,
                       CALENDAR_MONTH(CloseDate) mo,
                       SUM(Amount)               total
                FROM   Opportunity
                WHERE  IsWon = true
                  AND  CloseDate >= :cutoff
                WITH   USER_MODE
                GROUP BY CALENDAR_YEAR(CloseDate), CALENDAR_MONTH(CloseDate)
                ORDER BY CALENDAR_YEAR(CloseDate), CALENDAR_MONTH(CloseDate)
        ]) {
            Bucket b = new Bucket();
            b.period = String.valueOf(ar.get('yr')) + '-' +
                       String.valueOf(ar.get('mo')).leftPad(2, '0');
            b.amount = (Decimal) ar.get('total');
            buckets.add(b);
        }
        return buckets;
    }
}
```

**Why it works:** The aggregate runs in the database and returns at most 36 rows
regardless of how many Opportunities exist, so the 50,000-row retrieval limit is
never in play. `WITH USER_MODE` enforces the running user's object and field
permissions and record sharing — it is the current idiom; `WITH SECURITY_ENFORCED`
was removed in API 67.0 (Summer '26), which also made user mode and `with sharing`
the defaults for classes on that API version. `cacheable=true` lets the wire
service serve repeat views from the client cache without another round trip.

---

## Example 3: D3 needs `lwc:dom="manual"`, and scoped CSS will not reach its output

**Context:** A bespoke force-directed view of account relationships that no chart
library covers.

**Problem:** D3 appends `<g>`, `<circle>` and `<path>` elements into the SVG. LWC
owns the template's DOM and will not tolerate foreign insertions unless told, and
scoped styles do not apply to what gets appended.

**Solution:**

```html
<template>
    <!-- Empty native element; D3 appends into it. Directive is required. -->
    <svg class="graph" lwc:dom="manual"
         role="img" aria-label="Account relationship graph"></svg>
</template>
```

```js
renderedCallback() {
    if (this.drawn) {
        return;
    }
    this.drawn = true;
    loadScript(this, D3 + '/d3.min.js').then(() => this.draw());
}

draw() {
    const host = this.template.querySelector('svg.graph');
    // eslint-disable-next-line no-undef
    d3.select(host)
      .selectAll('circle')
      .data(this.nodes)
      .enter()
      .append('circle')
      .attr('r', 6)
      .attr('fill', (d) => d.isPartner ? '#0176D3' : '#747474')   // style here,
      .attr('stroke', '#FFFFFF')                                  // not in .css
      .attr('stroke-width', 1);
}
```

**Why it works:** The directive marks the `<svg>` as manually managed, which is
exactly the contract the docs describe — an empty native element whose children
the owner inserts with `appendChild()`. The colours are set as attributes because
the docs warn that "If a call to `appendChild()` manipulates the DOM, styling
isn't applied to the appended element": a `.graph circle { fill: ... }` rule in
the component's stylesheet would be ignored.

---

## Anti-Pattern: Loading the library from a CDN

**What practitioners do:** Copy a `<script src="https://cdn.jsdelivr.net/...">`
tag out of the library's quick-start, or call `loadScript(this, 'https://...')`
with a CDN URL.

**What goes wrong:** It does not load. LWC requires third-party libraries to be
uploaded as static resources, which the documentation describes as "a Lightning
Web Components content security policy requirement." The failure appears as an
undefined global at the point of first use, which reads like a load-order bug and
sends people to add timeouts and retries rather than to the actual cause.

**Correct approach:** Upload a purpose-built bundle as a static resource and
import it via `@salesforce/resourceUrl/<name>`. Build only the modules you use —
the single-resource ceiling is 5 MB and the org total is 250 MB, both of which a
full vendor build with source maps can strain. Version the resource name so a
library upgrade changes the URL and defeats browser caching.
