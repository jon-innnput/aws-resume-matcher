# Release Notes: v2.5.0

v2.5.0 introduces the Explainable Fit Analysis MVP for AWS Resume Matcher. This release begins the shift from a simple resume matcher toward a Candidate Fit Analyzer backed by a Requirement-to-Evidence Matching Engine.

## Highlights

- Added semantic-mode `matched_requirements` with requirement text, confidence score, and supporting resume evidence.
- Added semantic-mode `gaps` for parsed requirements with little supporting resume evidence.
- Added deterministic job-description requirement parsing from paragraphs, bullets, and numbered lists.
- Added resume evidence chunking using paragraph and bullet-style parsing.
- Combined existing keyword overlap with semantic similarity to select the best resume evidence chunk for each requirement.
- Retained richer internal requirement/evidence scoring metadata for future ranking, debugging, and product expansion without exposing it in the API response yet.

## Preserved Behavior

- Keyword-only mode response shape is unchanged.
- The existing top-level `score`, `keyword_score`, `semantic_score`, and `chunked_semantic_score` meanings are unchanged.
- Generic chunked semantic scoring remains experimental and is not productionized as the product direction.
- No LLM-based requirement extraction was introduced.
- No API request contract, S3 embedding cache design, SAM resource, or IAM policy changes were introduced.

## Validation

- `python -m pytest tests/test_app.py` was attempted with the system Python, but pytest was not installed there.
- `.venv\Scripts\python.exe -m pytest tests/test_app.py` passed with 43 tests.

