# Release Notes: v2.5.1

v2.5.1 calibrates the Explainable Fit Analysis MVP after real semantic-mode testing with Amazon Bedrock Titan embeddings.

## Highlights

- Lowered `MATCHED_REQUIREMENT_MIN_SCORE` from `60` to `40`.
- Added privacy-safe fit-analysis score summary diagnostics for future calibration.
- Preserved selected evidence, keyword score, semantic score, and matching keywords in internal fit-analysis debug structures.
- Added test coverage showing a plausible mid-range semantic requirement match is classified as `matched_requirements` instead of `gaps`.

## Calibration Findings

Real testing with an AWS job description and AI/TPM resume produced:

- `score`: `29`
- `semantic_score`: `32`
- `chunked_semantic_score`: `30`
- `matched_requirements`: `0`
- `gaps`: `21`

Observed requirement-level scores included:

- Agentic AI tools: `48`
- Program/project management: `41`
- AI/ML tools: `41`
- Content/data systems: `31`

The original v2.5.0 threshold of `60` was too strict for real Bedrock/Titan requirement-to-evidence scores. v2.5.1 uses `40` so plausible matches in the observed low-to-high 40s are surfaced as matched requirements while weaker evidence remains in gaps.

## Planning Impact

Real-world testing also showed that future match quality is constrained more by evidence retrieval and chunk selection than by requirement classification or weighting. The next quality-focused milestone should improve evidence retrieval and chunk ranking before adding requirement classification, requirement weighting, confidence models, or richer generated explanations.

## Preserved Behavior

- Keyword-only mode response shape is unchanged.
- Existing top-level `score`, `keyword_score`, `semantic_score`, and `chunked_semantic_score` meanings are unchanged.
- No LLM-generated explanations were introduced.
- No requirement taxonomy, required/preferred classification, agent workflow, or major API redesign was introduced.
- No SAM resource, IAM policy, or API request contract changes were introduced.

## Validation

- `.venv\Scripts\python.exe -m pytest tests/test_app.py` passed with 44 tests.
