# Release Notes: v2.6.0

v2.6.0 improves evidence retrieval and chunk ranking for semantic-mode requirement-to-evidence matching.

## Highlights

- Added requirement-scoped phrase alias handling for high-signal variants such as `program/project management`, `program management`, `project management`, `AI/ML`, `artificial intelligence`, `machine learning`, `agentic AI`, and content/data systems.
- Added alias-aware evidence ranking on top of the existing keyword and semantic requirement scoring.
- Retained the top three evidence chunks internally for diagnostics and focused tests.
- Preserved the public response contract: normal API responses still return one `evidence` chunk per matched requirement.

## Implementation Notes

Alias normalization is intentionally scoped to requirement-to-evidence scoring. It does not change global keyword extraction, keyword-only response shape, top-level `keyword_score`, or the API request contract.

The internal fit-analysis debug structure now includes:

- `alias_score`
- `matching_aliases`
- `top_evidence`

These fields are used for diagnostics and tests. They are not exposed in the normal semantic-mode API response.

## Preserved Behavior

- Keyword-only mode response shape is unchanged.
- Existing top-level `score`, `keyword_score`, `semantic_score`, and `chunked_semantic_score` meanings are unchanged.
- Semantic-mode public response shape is stable.
- No LLM-generated explanations were introduced.
- No agent workflow, requirement taxonomy, required/preferred classification, multi-level confidence model, or API redesign was introduced.
- No S3 embedding cache redesign was introduced.
- No SAM resource, IAM policy, or deployment workflow changes were introduced.

## Validation

- Added focused tests for `program/project management` and `AI/ML` phrase variants.
- Added test coverage confirming the top three evidence chunks are retained internally.
- Confirmed keyword-only response shape remains unchanged.
- Confirmed semantic-mode public response shape remains stable.
