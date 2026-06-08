# Release Notes: v2.6.0

v2.6.0 improves evidence retrieval and chunk ranking for semantic-mode requirement-to-evidence matching.

This release keeps the public API contract stable. It does not change the request shape, keyword-only response shape, semantic top-level score fields, or the normal semantic-mode `matched_requirements` / `gaps` response structure.

## Highlights

- Added requirement-scoped phrase alias handling for high-signal variants such as `program/project management`, `program management`, `project management`, `AI/ML`, `artificial intelligence`, `machine learning`, `agentic AI`, and content/data systems.
- Added alias-aware evidence ranking on top of the existing keyword and semantic requirement scoring.
- Retained the top three evidence chunks internally for diagnostics and focused tests.
- Continued to return one public `evidence` chunk per matched requirement.
- Preserved global keyword extraction and top-level `keyword_score` behavior.

## Why This Release

v2.5.1 calibrated the match threshold after real Bedrock/Titan testing, but the remaining quality constraint was evidence retrieval. Strong resume evidence could still score lower than expected when a requirement used compact phrase variants such as `AI/ML` or `program/project management` and the resume used expanded phrasing such as `artificial intelligence`, `machine learning`, `program management`, or `project management`.

v2.6.0 addresses that narrow retrieval problem without adding LLM explanations, agent workflows, requirement taxonomies, required/preferred classification, confidence models, or an API redesign.

## Test Insights

The same real AWS job description and TPM/AI resume outputs were compared between v2.5.1 and v2.6.0:

| Metric | v2.5.1 | v2.6.0 | Change |
| --- | ---: | ---: | ---: |
| `score` | 29 | 29 | 0 |
| `keyword_score` | 25 | 25 | 0 |
| `semantic_score` | 32 | 32 | 0 |
| `chunked_semantic_score` | 30 | 30 | 0 |
| `matched_requirements` | 3 | 4 | +1 |
| `gaps` | 18 | 17 | -1 |

The unchanged top-level scores confirm that v2.6.0 did not alter document-level scoring semantics. The improvement appears only in fit-analysis evidence selection and requirement-level classification, which was the intended scope.

Notable requirement-level movements:

| Requirement theme | v2.5.1 | v2.6.0 | Change |
| --- | ---: | ---: | ---: |
| AI/ML tools, agentic AI, generative AI | 41 | 61 | +20 |
| AI-assisted or agentic AI tools | 48 | 68 | +20 |
| Broad program management, data fluency, business analysis, content strategy | 25 | 44 | +19 |
| Program/project management, content strategy, business operations | 41 | 41 | 0 |

These results support the v2.6.0 implementation direction: scoped alias handling improves requirements that contain explicit AI/ML and agentic-AI variants while preserving unrelated requirement scores. They also show that `program/project management` still needs more real-world calibration, because the tested requirement remained at `41` even though it selected plausible resume evidence.

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
- Normal API consumers still receive one selected evidence chunk per matched requirement.
- No LLM-generated explanations were introduced.
- No agent workflow, requirement taxonomy, required/preferred classification, multi-level confidence model, or API redesign was introduced.
- No S3 embedding cache redesign was introduced.
- No SAM resource, IAM policy, or deployment workflow changes were introduced.

## Validation

- Added focused unit tests for `program/project management` and `AI/ML` phrase variants.
- Added test coverage confirming the top three evidence chunks are retained internally.
- Confirmed keyword-only response shape remains unchanged.
- Confirmed semantic-mode public response shape remains stable.
- Compared real v2.5.1 and v2.6.0 Bedrock/Titan outputs in `sample-data/` to verify that top-level scores stayed stable while requirement-level evidence scoring improved.
