# Release Notes: v2.9.0

v2.9.0 adds a reviewer-friendly frontend experience for semantic-mode fit analysis.

This release keeps keyword-only behavior unchanged. It does not change backend scoring, the API response contract, infrastructure, GitHub workflows, SAM runtime configuration, AWS resources, dependencies, or deployment behavior.

## Highlights

- Added frontend rendering for semantic-mode `fit_summary` counts.
- Added reviewer-friendly matched requirement cards with requirement score, type, priority, confidence, evidence, and rationale.
- Added reviewer-friendly gap cards with requirement score, type, priority, evidence-support wording, and rationale.
- Sorted gaps so high-priority gaps appear before lower-priority gaps.
- Added readable badges for `requirement_type`, `priority`, matched confidence, and gap evidence support.
- Added browser-only Copy Fit Review using the existing API response data.
- Kept raw JSON available for technical inspection.
- Kept keyword-only responses graceful: semantic sections and Copy Fit Review stay hidden when fit-analysis fields are absent.

## Why This Release

v2.8.0 added deterministic requirement intelligence and confidence scoring to the semantic-mode API response. That made the backend more useful, but the static browser demo still mostly showed score, keyword lists, semantic scores, and raw JSON.

v2.9.0 makes the v2.8.0 intelligence visible to recruiters, hiring managers, and technical reviewers. When semantic-mode fields are returned, the frontend now presents a compact fit summary, matched requirements with supporting evidence, and prioritized gaps with rationale. This makes the project read more like an explainable candidate fit analyzer while preserving the simple static demo architecture.

## Frontend Behavior

Semantic-mode responses can now display:

- `fit_summary`
- `matched_requirements`
- `gaps`
- `requirement_type`
- `priority`
- matched requirement `confidence`
- gap evidence-support wording derived from `confidence`
- `rationale`
- matched requirement `evidence`

The frontend sorts matched requirements by confidence, priority, and score. Gaps are sorted by priority and score so high-priority gaps appear first.

Keyword-only responses still show only the existing score, matching keywords, missing keywords, and raw JSON result. The frontend does not create placeholder semantic analysis when semantic fields are absent.

## Copy Fit Review

Copy Fit Review creates a plain-text browser-only summary from the current semantic-mode response. It includes:

- overall score
- keyword and semantic scores when returned
- fit summary counts
- top matched requirements with priority, confidence, score, and evidence
- top gaps with priority, evidence-support wording, and score

No backend persistence, storage, or new dependency was added.

## Preserved Behavior

- Lambda runtime remains Python 3.12.
- GitHub Actions runners remain Python 3.13.
- Semantic matching remains guarded behind `SEMANTIC_MATCHING_ENABLED`.
- Keyword-only mode remains the default production behavior.
- Backend scoring and response fields are unchanged.
- SAM resources, IAM policies, deployment workflows, and AWS resources are unchanged.
- No new dependencies were added.
- v2.8.0 release notes remain historical and separate.

## Validation

- Ran the pytest suite with the repository virtual environment.
- Ran SAM template validation.
- Ran SAM build with cached parallel build.
- Manually validated the frontend in a browser with semantic-mode response data.
- Manually confirmed keyword-only behavior does not render semantic sections.
