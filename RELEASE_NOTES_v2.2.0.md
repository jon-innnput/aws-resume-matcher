# Release Notes: v2.2.0

## Summary

v2.2.0 adds a minimal framework-free frontend demo for AWS Resume Matcher while preserving the existing API Gateway, Lambda, S3, SAM, and optional Bedrock semantic matching architecture.

## Added

- Static frontend demo in `frontend/index.html` with embedded HTML, CSS, and JavaScript.
- API endpoint configuration saved in browser local storage.
- Resume and job-description text areas for demo input.
- Sample resume and sample job-description buttons using fictional content.
- Match result visualization for score, matching keywords, missing keywords, semantic details when enabled, and raw JSON.
- Copy Result JSON button.
- Optional `resume_text` API request field for direct-text resume demo intake.
- HTTP API CORS configuration for browser-based demo calls.
- Tests for direct-text resume matching, S3 fallback behavior, invalid `resume_text`, CORS-friendly Lambda headers, and SAM CORS configuration.

## Preserved

- Existing S3-backed resume behavior when `resume_text` is omitted.
- Existing job-description inputs: `job_description`, `job_description_file`, and `job_description_url`.
- Existing keyword-only default response shape.
- Guarded semantic matching behind `SEMANTIC_MATCHING_ENABLED=false`.
- Existing AWS SAM deployment model and GitHub Actions workflows.

## Notes

Direct-text resume intake is intended for the v2.2 demo experience and does not persist resume content. Future resume upload, multi-resume, or candidate-ranking capabilities may replace or augment this mechanism with explicit privacy controls.
