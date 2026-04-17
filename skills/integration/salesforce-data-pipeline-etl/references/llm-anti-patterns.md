# LLM Anti-Patterns — Salesforce Data Pipeline / ETL

1. LastModifiedDate polling as primary path
2. Ignoring GAP_FILL events
3. No replay-id checkpointing
4. Snapshot-only (no delta)
5. Storing replay id in memory only
