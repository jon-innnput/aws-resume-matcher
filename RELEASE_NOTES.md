# Release Notes

Latest release: **v2.7.0 Narrative Evidence Chunking & Top-K Ranking Refinement**

v2.7.0 improves semantic-mode fit-analysis evidence selection for narrative-heavy resumes and verbose job descriptions while preserving the public API response contract.

## Latest Highlights

- Added internal resume evidence candidates for dense narrative paragraphs, including sentence-level candidates and bounded adjacent windows.
- Added top-k evidence reranking diagnostics that preserve one public `evidence` string per matched requirement.
- Filtered obvious low-value JD chunks such as job IDs, compensation/location metadata, generic company narrative, benefits text, and legal boilerplate before requirement-to-evidence scoring.
- Kept global keyword extraction, keyword-only behavior, semantic response shape, and top-level score semantics unchanged.

Detailed release notes are archived in [`release_notes/`](release_notes/).

- [v2.7.0](release_notes/RELEASE_NOTES_v2.7.0.md)
- [v2.6.0](release_notes/RELEASE_NOTES_v2.6.0.md)
- [v2.5.1](release_notes/RELEASE_NOTES_v2.5.1.md)
- [v2.5.0](release_notes/RELEASE_NOTES_v2.5.0.md)
- [v2.3.0](release_notes/RELEASE_NOTES_v2.3.0.md)
- [v2.2.0](release_notes/RELEASE_NOTES_v2.2.0.md)
- [v2.1.0](release_notes/RELEASE_NOTES_v2.1.0.md)
- [v2.0.0](release_notes/RELEASE_NOTES_v2.0.0.md)
