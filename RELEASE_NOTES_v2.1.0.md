# Release Notes: v2.1.0

## Summary

v2.1.0 expands resume and job-description intake while preserving the v2.0.0 scoring behavior, semantic matching guardrails, serverless architecture, and existing direct-text API contract.

## Added

- Resume intake for configured S3 objects ending in `.txt`, `.pdf`, or `.docx`.
- Job-description intake from exactly one of:
  - `job_description` direct text.
  - `job_description_file` with `.txt` or `.md` content.
  - `job_description_url` for HTTP/HTTPS job posting text extraction.
- Lightweight Lambda dependencies for PDF and DOCX extraction through `pypdf` and `python-docx`.
- URL intake guardrails for scheme, credentials, localhost/private literal IPs, timeout, and response size.
- Pytest coverage for the new intake paths.

## Preserved

- Existing `job_description` requests and keyword-only response shape.
- Guarded semantic matching behind `SEMANTIC_MATCHING_ENABLED=false`.
- S3 resume embedding cache behavior keyed by resume source metadata.
- Existing SAM resource shape with no additional AWS resources.

## Validation

- `python -m compileall lambda`
- `.venv\Scripts\python.exe -m pytest` (`34 passed`)
- `sam validate --template-file template.yaml`

Local `sam build --template-file template.yaml --cached --parallel` was not completed because this workstation exposes Python 3.12 on `PATH`, while the SAM template correctly targets Python 3.13.
