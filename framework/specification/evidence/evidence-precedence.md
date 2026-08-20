# Evidence precedence and scope

| Rank | Evidence class | Can prove | Cannot prove alone |
|---:|---|---|---|
| 1 | Direct read-only target observation | State of selected org/job/record at capture time | Uncommitted local source or future state |
| 2 | Deterministic selected-project observation | Local files, references, configuration in that project | What is deployed in an org |
| 3 | Captured official result | State represented by that versioned job/test/analyzer result | Current state after later changes |
| 4 | Official current documentation | Platform semantics and supported behavior | Customer-specific state |
| 5 | Governed SfSkills knowledge | Procedures, patterns, anti-patterns | Target existence or exact runtime branch |
| 6 | Model inference | A hypothesis linking evidence | Fact without support |

Evidence precedence is not a simple total order. The claim's scope must match the evidence's scope. Contradictions remain visible until resolved.
