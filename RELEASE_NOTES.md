# Release Notes

Latest release: **v2.8.0 Requirement Intelligence & Confidence Scoring**

v2.8.0 improves semantic-mode explainable fit analysis with deterministic requirement classification, calibrated priority bands, calibrated confidence bands, stricter boilerplate filtering, concise rationales, and a compact `fit_summary`.

## Latest Highlights

- Added conservative requirement types: `required`, `preferred`, `responsibility`, `experience`, `credential`, and `other`.
- Added deterministic `priority`, `confidence`, and `rationale` fields to semantic-mode `matched_requirements` and `gaps`.
- Tightened requirement extraction against real sample job descriptions to reduce non-requirement boilerplate and false gaps.
- Added semantic-mode `fit_summary` counts for total requirements, matched requirements, gaps, high-confidence matches, and high-priority gaps.
- Kept keyword-only behavior, infrastructure, workflows, Lambda runtime, and top-level score semantics unchanged.

Detailed release notes are archived in [`release_notes/`](release_notes/).

- [v2.8.0](release_notes/RELEASE_NOTES_v2.8.0.md)
- [v2.7.1](release_notes/RELEASE_NOTES_v2.7.1.md)
- [v2.7.0](release_notes/RELEASE_NOTES_v2.7.0.md)
- [v2.6.0](release_notes/RELEASE_NOTES_v2.6.0.md)
- [v2.5.1](release_notes/RELEASE_NOTES_v2.5.1.md)
- [v2.5.0](release_notes/RELEASE_NOTES_v2.5.0.md)
- [v2.3.0](release_notes/RELEASE_NOTES_v2.3.0.md)
- [v2.2.0](release_notes/RELEASE_NOTES_v2.2.0.md)
- [v2.1.0](release_notes/RELEASE_NOTES_v2.1.0.md)
- [v2.0.0](release_notes/RELEASE_NOTES_v2.0.0.md)
