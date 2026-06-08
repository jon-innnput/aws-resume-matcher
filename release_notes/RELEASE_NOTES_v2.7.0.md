# Release Notes: v2.7.0

v2.7.0 refines semantic-mode requirement-to-evidence matching for narrative-heavy resumes and verbose job descriptions.

This release keeps the public API contract stable. It does not change the request shape, keyword-only response shape, semantic top-level score fields, or the normal semantic-mode `matched_requirements` / `gaps` response structure.

## Highlights

- Added internal resume evidence candidates for dense narrative paragraphs, including sentence-level candidates and bounded adjacent windows.
- Added conservative adjacent-chunk windowing for related nearby resume chunks.
- Used top-k evidence diagnostics to rerank and select the final single public evidence string per matched requirement.
- Added internal evidence diagnostics for candidate type, source chunks, and word count.
- Filtered obvious low-value job-description chunks before requirement scoring, including job IDs, compensation/location metadata, generic company narrative, benefits text, and legal boilerplate.
- Preserved global keyword extraction, top-level score semantics, keyword-only behavior, and semantic response shape.

## Why This Release

v2.6.0 improved retrieval for compact phrase variants such as `AI/ML`, `agentic AI`, and `program/project management`, but some strong matches still scored moderately when resume evidence was narrative-heavy or spread across nearby text. Verbose job descriptions could also produce low-value requirement candidates from metadata and boilerplate.

v2.7.0 addresses those narrow fit-analysis issues without adding LLM-generated explanations, agent workflows, requirement taxonomies, required/preferred classification, confidence models, or an API redesign.

## Implementation Notes

The new `_extract_resume_evidence_candidates()` helper is used only by fit analysis. Existing resume chunking remains available for the v2.4.0 `chunked_semantic_score` experiment, so top-level semantic score behavior is unchanged.

Evidence candidates include original chunks, sentence candidates from long narrative chunks, and bounded adjacent windows. Adjacent paragraph windows are conservative: they require shared keywords, shared alias concepts, or a short heading-style lead-in. This avoids combining unrelated resume sections while still helping nearby evidence work as one support signal.

Internal top-evidence diagnostics now include:

- `evidence_type`
- `source_chunks`
- `word_count`
- `alias_score`
- `matching_aliases`
- `top_evidence`

These diagnostics are used for tests and calibration. They are not exposed in the normal API response.

## Preserved Behavior

- Keyword-only mode response shape is unchanged.
- Existing top-level `score`, `keyword_score`, `semantic_score`, and `chunked_semantic_score` meanings are unchanged.
- Semantic-mode public response shape is stable.
- Normal API consumers still receive one selected evidence string per matched requirement.
- No LLM-generated explanations were introduced.
- No agent workflow, requirement taxonomy, required/preferred classification, multi-level confidence model, or API redesign was introduced.
- No S3 embedding cache redesign was introduced.
- No SAM resource, IAM policy, or deployment workflow changes were introduced.

## Validation

- Added focused unit tests for narrative-heavy resume evidence windows.
- Added focused unit tests for verbose JD boilerplate filtering.
- Confirmed strong narrative evidence can be selected as the public evidence string through internal top-k reranking.
- Confirmed keyword-only response shape remains unchanged.
- Confirmed semantic-mode public response shape remains stable.
