# Release Notes: v2.3.0

v2.3.0 improves keyword extraction quality for AWS Resume Matcher while preserving the existing API Gateway, Lambda, S3, SAM, frontend, and optional Bedrock semantic matching architecture.

## Highlights

- Removed numeric-list and numeric-unit artifacts such as `1.`, `2.`, `3+`, and `3px` from extracted keywords.
- Removed contraction fragments such as `ll`, `ve`, and `re`.
- Stripped trailing punctuation so words such as `production.` normalize to `production`.
- Normalized obvious tokenization artifacts such as `APIs` to `api`.
- Filtered selected low-value job-description filler such as `role`, `systems`, and `responses`.
- Preserved important technical terms including `aws`, `bedrock`, `lambda`, `s3`, `api`, `ci/cd`, `c++`, and `c#`.

## Preserved Behavior

- API response schema is unchanged.
- Keyword-only mode remains the default behavior.
- Optional Bedrock semantic matching remains guarded by `SEMANTIC_MATCHING_ENABLED=false`.
- No weighted scoring, phrase extraction, stemming, lemmatization, PDF support, or DOCX support changes were introduced.

## Validation

- `python -m pytest` was attempted with the system Python but pytest was not installed there.
- `.venv\Scripts\python.exe -m pytest` passed with 41 tests.

