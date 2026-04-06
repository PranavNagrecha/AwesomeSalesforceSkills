# Apex Performance Profiling -- Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `apex-performance-profiling`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Debug log available: (yes/no; if yes, log level and whether it is truncated)
- Transaction type: (sync user action / trigger / batch / queueable / scheduled / API)
- Governor limit under pressure: (CPU / SOQL count / SOQL rows / DML / heap / callouts / unknown)
- Approximate data volume: (record count for primary object)

## Profiling Results

### Tool Used

(Apex Log Analyzer flame graph / Developer Console Timeline / Limits checkpoints / Query Plan tool)

### Top Hotspots

| Rank | Method or Operation | Time (ms) | SOQL | DML | Category |
|------|---------------------|-----------|------|-----|----------|
| 1    |                     |           |      |     |          |
| 2    |                     |           |      |     |          |
| 3    |                     |           |      |     |          |

### Query Plan Results (if applicable)

| Query | Leading Operation | Cost | Cardinality | Index Recommendation |
|-------|-------------------|------|-------------|----------------------|
|       |                   |      |             |                      |

## Approach

Which optimization skill applies to the identified hotspot?

- [ ] apex-cpu-and-heap-optimization (CPU or heap fix patterns)
- [ ] soql-query-optimization (SOQL rewrite or index request)
- [ ] async-apex (move work to async context)
- [ ] Other: ___

## Checklist

- [ ] Debug log captured at FINEST Apex Code level and is not truncated
- [ ] Flame graph or timeline reviewed; top hotspot identified with specific method and line
- [ ] SOQL Query Plan checked for queries on objects with more than 10,000 records
- [ ] Limits checkpoint instrumentation in place with before/after measurements
- [ ] Optimization verified by comparing checkpoint values before and after fix
- [ ] Permanent instrumentation decision made

## Notes

Record any deviations from the standard profiling pattern and why.
