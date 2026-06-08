# Release Notes

Latest release: **v2.6.0 Evidence Retrieval & Chunk Ranking**

v2.6.0 improves semantic-mode requirement-to-evidence matching with scoped phrase alias handling, alias-aware evidence ranking, and internal top-3 evidence diagnostics while preserving the public API response contract.

## Latest Highlights

- Improved evidence ranking for high-signal variants such as `AI/ML`, `artificial intelligence`, `machine learning`, `agentic AI`, and `program/project management`.
- Kept global keyword extraction, keyword-only behavior, and top-level score semantics unchanged.
- Preserved one public `evidence` chunk per matched requirement while retaining richer top-k diagnostics internally.
- Compared real v2.5.1 and v2.6.0 Bedrock/Titan outputs to confirm top-level scores stayed stable while requirement-level evidence scoring improved.

Detailed release notes are archived in [`release_notes/`](release_notes/).

- [v2.6.0](release_notes/RELEASE_NOTES_v2.6.0.md)
- [v2.5.1](release_notes/RELEASE_NOTES_v2.5.1.md)
- [v2.5.0](release_notes/RELEASE_NOTES_v2.5.0.md)
- [v2.3.0](release_notes/RELEASE_NOTES_v2.3.0.md)
- [v2.2.0](release_notes/RELEASE_NOTES_v2.2.0.md)
- [v2.1.0](release_notes/RELEASE_NOTES_v2.1.0.md)
- [v2.0.0](release_notes/RELEASE_NOTES_v2.0.0.md)
