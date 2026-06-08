# AWS Resume Matcher

[![CI](https://github.com/jon-innnput/aws-resume-matcher/actions/workflows/ci.yml/badge.svg)](https://github.com/jon-innnput/aws-resume-matcher/actions/workflows/ci.yml)
[![Deploy](https://github.com/jon-innnput/aws-resume-matcher/actions/workflows/deploy.yml/badge.svg)](https://github.com/jon-innnput/aws-resume-matcher/actions/workflows/deploy.yml)
![Release](https://img.shields.io/badge/release-v2.7.0-blue)
![Python](https://img.shields.io/badge/python-3.13-blue)
![AWS SAM](https://img.shields.io/badge/IaC-AWS%20SAM-orange)

AWS Resume Matcher is a serverless AI portfolio project that scores how well a resume matches a job description. It supports a static frontend demo, direct-text resume input for demos, `.txt`, `.pdf`, and `.docx` resumes from Amazon S3, direct text, `.txt`, Markdown, and URL-based job descriptions, deterministic keyword scoring, and optional hybrid semantic matching with explainable fit analysis powered by Amazon Bedrock Titan Text Embeddings V2.

The project exists to demonstrate a practical AWS application lifecycle: serverless API design, S3-backed data access, infrastructure as code, CI/CD, least-privilege AWS permissions, automated tests, and an incremental path from deterministic keyword matching to guarded semantic AI matching.

**Current status:** v2.7.0 is complete. The project includes a framework-free static frontend demo, direct-text resume intake for demos, improved keyword extraction quality, a v2.4.0 chunked semantic scoring experiment, semantic-mode explainable fit analysis, calibrated requirement matching for real Bedrock/Titan score ranges, scoped phrase aliasing, narrative resume evidence candidates, top-k evidence reranking, and low-value job-description boilerplate filtering. Keyword matching remains the default production behavior. Semantic matching is implemented behind `SEMANTIC_MATCHING_ENABLED=false` and can be enabled after Bedrock access and embedding-cache permissions are configured in the target AWS account.

The latest release summary is in [`RELEASE_NOTES.md`](RELEASE_NOTES.md). Historical release notes are archived in [`release_notes/`](release_notes/).

## At A Glance

| Area | Capability |
| --- | --- |
| Frontend | Framework-free static demo in `frontend/index.html` |
| Resume intake | Optional direct text for demos, or `.txt`, `.pdf`, and `.docx` resumes from a private S3 object |
| Job description intake | Direct text, inline `.txt`, inline Markdown, or HTTP/HTTPS URL |
| Matching | Deterministic keyword overlap with optional hybrid semantic scoring and explainable fit analysis |
| AI provider | Amazon Bedrock Titan Text Embeddings V2 |
| Architecture | API Gateway, Lambda, S3, Bedrock, and SAM |
| Delivery | GitHub Actions CI/CD with OIDC-based AWS deployment |
| Testing | pytest, SAM validation, SAM build, and Python compilation |

## What This Demonstrates

- Framework-free browser demo that calls the deployed serverless API.
- Serverless API design with Amazon API Gateway and AWS Lambda.
- Private S3-backed document intake without committing resume data to source control.
- Lightweight `.txt`, `.pdf`, and `.docx` resume extraction in Python.
- Multiple job-description intake paths, including URL and Markdown/TXT payloads.
- Deterministic keyword scoring with an optional Bedrock semantic layer.
- Semantic-mode explainable fit analysis with matched job requirements, likely gaps, and supporting resume evidence.
- Requirement-to-evidence ranking with scoped phrase alias handling, narrative evidence windows, boilerplate-aware requirement filtering, and internal top-evidence diagnostics.
- S3 embedding-cache design for avoiding repeated resume embedding work.
- Least-privilege IAM and repeatable infrastructure through AWS SAM.
- CI/CD with GitHub Actions, OIDC role assumption, and automated pytest coverage.

## Architecture

```mermaid
flowchart TD
    User["Client or reviewer"] --> Frontend["Static frontend<br/>HTML / CSS / JS"]
    Frontend -->|"POST /match"| Api["Amazon API Gateway<br/>HTTP API"]
    User -->|"POST /match"| Api
    Api --> Lambda["AWS Lambda<br/>Python 3.13"]

    Lambda --> ResumeInput["Resume intake<br/>S3 .txt / .pdf / .docx"]
    Lambda --> JobInput["Job description intake<br/>text / .txt / .md / URL"]
    ResumeInput --> Keyword["Keyword matching<br/>overlap + missing terms"]
    JobInput --> Keyword
    Keyword --> Semantic{"Semantic matching<br/>enabled?"}

    Semantic -->|"No"| Result["JSON match result"]
    Semantic -->|"Yes"| Bedrock["Amazon Bedrock<br/>Titan Text Embeddings V2"]
    Bedrock --> Cache["Amazon S3<br/>resume embedding cache"]
    Cache --> Hybrid["Hybrid score<br/>keyword + semantic"]
    Keyword -. "keyword component" .-> Hybrid
    Hybrid --> Result
    Result --> User
```

## Supported Inputs

| Input | Supported formats | Source |
| --- | --- | --- |
| Resume | Direct text | Optional `resume_text` JSON field for demos |
| Resume | `.txt`, `.pdf`, `.docx` | Configured private S3 object through `RESUME_BUCKET` and `RESUME_KEY` |
| Job description | Direct text | `job_description` JSON field |
| Job description | `.txt`, `.md` | Inline `job_description_file` JSON object |
| Job description | URL | `job_description_url` HTTP/HTTPS job posting |

The API accepts exactly one job-description input per request. Resume files remain private S3 objects and are not stored in the repository.

### URL Ingestion Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Lambda
    participant Remote as Job Posting URL
    participant Parser as Text Extractor
    participant Matcher as Matching Engine

    Client->>API: POST /match with job_description_url
    API->>Lambda: Invoke Lambda
    Lambda->>Lambda: Validate URL scheme, host, and credentials
    Lambda->>Remote: Fetch job posting
    Remote-->>Lambda: HTML or text response
    Lambda->>Lambda: Enforce response size cap
    Lambda->>Parser: Extract readable text
    Parser-->>Lambda: Job description text
    Lambda->>Matcher: Compare resume and job description
    Matcher-->>Lambda: Score, matching keywords, missing keywords
    Lambda-->>Client: JSON response
```

## Key Capabilities

- Serverless `POST /match` API backed by API Gateway and AWS Lambda.
- Static frontend demo for configuring an API endpoint, submitting resume/job text, loading sample inputs, viewing scores, and copying result JSON.
- Optional direct-text `resume_text` input for demo requests while preserving the configured S3 resume fallback.
- Resume loaded from a configured private S3 object instead of source control, with `.txt`, `.pdf`, and `.docx` intake support.
- Job description intake through direct JSON text, inline `.txt` or `.md` file content, or an HTTP/HTTPS URL.
- Deterministic keyword extraction with stop-word filtering, punctuation cleanup, token-artifact filtering, overlap scoring, matching keywords, and missing keywords.
- Guarded hybrid keyword + semantic scoring using Amazon Bedrock Titan Text Embeddings V2.
- S3 embedding cache keyed by resume bucket, resume key, S3 ETag, embedding model, dimensions, normalization setting, and cache schema version.
- AWS SAM infrastructure as code for API Gateway, Lambda, environment variables, IAM policies, and stack outputs.
- GitHub Actions CI for tests, SAM validation, SAM build, and Python compilation.
- GitHub Actions deployment through OIDC-based AWS role assumption, with no long-lived AWS keys in the repository.
- Pytest coverage for keyword scoring, request validation, semantic helpers, Bedrock provider behavior, S3 cache behavior, and SAM semantic configuration.
- Semantic matching disabled by default to preserve the original keyword-only response shape unless intentionally enabled.
- Lightweight document parsing with `pypdf` and `python-docx`; URL intake uses Python standard-library networking and HTML text extraction.

## Technology Stack

- Python 3.13
- AWS Lambda
- Amazon API Gateway HTTP API
- Amazon S3
- Amazon Bedrock Titan Text Embeddings V2
- AWS SAM / AWS CloudFormation
- AWS IAM
- GitHub Actions
- GitHub OIDC
- Pytest
- Optional local semantic validation with `sentence-transformers/all-MiniLM-L6-v2`

## Example Requests And Responses

### Direct Text Job Description

```bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/match \
  -H "Content-Type: application/json" \
  -d '{"job_description":"Python developer with AWS Lambda, S3, API Gateway, CI/CD, and semantic search experience."}'
```

### Direct Text Resume And Job Description

```bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/match \
  -H "Content-Type: application/json" \
  -d '{"resume_text":"Python developer with AWS Lambda and S3 experience.","job_description":"Python developer with AWS Lambda, S3, API Gateway, CI/CD, and semantic search experience."}'
```

### Inline File Job Description

```bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/match \
  -H "Content-Type: application/json" \
  -d '{"job_description_file":{"filename":"job.md","content":"# Role\nPython developer with AWS Lambda and S3 experience."}}'
```

### URL Job Description

```bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/match \
  -H "Content-Type: application/json" \
  -d '{"job_description_url":"https://example.com/jobs/serverless-python-developer"}'
```

### Keyword-Only Response

```json
{
  "score": 75,
  "matching_keywords": ["api", "aws", "gateway", "lambda", "python", "s3"],
  "missing_keywords": ["semantic"]
}
```

### Semantic-Mode Response

```json
{
  "score": 89,
  "keyword_score": 75,
  "semantic_score": 100,
  "chunked_semantic_score": 82,
  "matching_keywords": ["api", "aws", "gateway", "lambda", "python", "s3"],
  "missing_keywords": ["terraform"],
  "matched_requirements": [
    {
      "requirement": "Build serverless APIs with AWS Lambda and API Gateway",
      "score": 84,
      "evidence": "Built Python APIs on AWS Lambda behind API Gateway."
    }
  ],
  "gaps": [
    {
      "requirement": "Manage infrastructure with Terraform",
      "score": 18
    }
  ],
  "semantic_model": "amazon.titan-embed-text-v2:0",
  "semantic_provider": "bedrock",
  "weights": {
    "keyword": 0.45,
    "semantic": 0.55
  }
}
```

### Score Fields

- `score`: The final match score returned to the client. In keyword-only mode, this is the keyword score. In semantic mode, this is the weighted hybrid score.
- `keyword_score`: The percentage of extracted job-description keywords found in the resume. Present when semantic mode is enabled.
- `semantic_score`: The embedding-similarity score between the resume and job description. Present when semantic mode is enabled.
- `chunked_semantic_score`: The v2.4.0 experimental chunked semantic score. It is retained for comparison and does not change the final score.
- `matched_requirements`: Semantic-mode requirement/evidence pairs with high supporting evidence.
- `gaps`: Semantic-mode requirements with low supporting evidence.

Exact scores depend on the configured resume object and the submitted job description.

### Fit Analysis Calibration

v2.5.1 calibrates requirement-to-evidence matching against real Bedrock/Titan embedding behavior. A real AWS job description and TPM/AI resume produced top requirement scores in the low-to-high 40s, including agentic AI tools at `48`, program/project management at `41`, AI/ML tools at `41`, and content/data systems at `31`. The initial v2.5.0 threshold of `60` was too strict for these observed ranges and classified every requirement as a gap.

The MVP match threshold is now `40`. This keeps clearly weak evidence in `gaps` while allowing plausible requirement/evidence matches in the observed `40-49` range to appear in `matched_requirements`. The implementation also logs a privacy-safe score summary for calibration without exposing detailed internal scoring metadata in normal API responses.

## Project Evolution

- **v1.0 Keyword Matching**: Introduced the serverless resume matching MVP with deterministic keyword overlap scoring.
- **v1.1 AWS SAM IaC**: Migrated infrastructure into AWS SAM for repeatable API Gateway, Lambda, IAM, and output provisioning.
- **v1.2 CI/CD**: Added GitHub Actions validation, SAM build checks, and OIDC-based deployment from `main`.
- **v1.3 Automated Testing**: Added pytest coverage for matching behavior, request handling, and Lambda responses.
- **v2.0 Semantic AI Matching**: Added guarded Amazon Bedrock semantic matching, hybrid scoring, S3 embedding caching, SAM configuration, and least-privilege IAM while keeping keyword-only mode as the default.
- **v2.1 Intake Expansion**: Added resume intake for `.txt`, `.pdf`, and `.docx`, plus job-description intake from direct text, inline `.txt`/`.md` content, and URL text extraction.
- **v2.2 Frontend Demo**: Added a framework-free static frontend and optional direct-text resume intake for reviewer-friendly demos.
- **v2.3 Keyword Quality Improvements**: Reduced keyword noise from numeric-list artifacts, contraction fragments, trailing punctuation, and generic job-description filler while preserving technical terms such as AWS, S3, CI/CD, C++, and C#.
- **v2.4 Semantic Chunking Experiment**: Added whole-document and simple chunked semantic score comparison, confirming generic chunked semantic matching should remain experimental rather than become the product direction.
- **v2.5 Explainable Fit Analysis MVP**: Added semantic-mode matched requirements, likely gaps, and supporting resume evidence while preserving the existing scoring model and keyword-only response shape.
- **v2.5.1 Fit Analysis Calibration**: Lowered the matched requirement threshold based on real Bedrock/Titan score distributions and added privacy-safe score summary diagnostics.
- **v2.6 Evidence Retrieval & Chunk Ranking**: Improved requirement-to-evidence chunk selection with scoped alias handling, alias-aware ranking, and internal top-3 evidence diagnostics while preserving the public response contract.
- **v2.7 Narrative Evidence Chunking & Top-K Ranking Refinement**: Added internal narrative evidence candidates, adjacent evidence windows, top-k reranking diagnostics, and deterministic JD boilerplate filtering while preserving the public response contract.

## Local Development

Install:

- Python 3.13
- AWS CLI
- AWS SAM CLI
- Git

Clone the repository and validate the project:

```bash
git clone <repository-url>
cd aws-resume-matcher
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest
sam validate --template-file template.yaml
sam build --template-file template.yaml --cached --parallel
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

This repository intentionally excludes resume files. For local experiments, create a private resume file outside version control, for example:

```text
sample-data/resume.txt
```

The `sample-data/` directory is ignored by Git to reduce the risk of publishing personal information. Resume intake supports `.txt`, `.pdf`, and `.docx` objects in S3. Text and Markdown job-description file inputs support `.txt` and `.md`.

## Running Locally

The Lambda function expects two environment variables:

```text
RESUME_BUCKET=<bucket containing the resume file>
RESUME_KEY=<path/to/resume.txt|resume.pdf|resume.docx>
```

For a local API run with SAM, use the template parameters that populate those variables:

```bash
sam build --template-file template.yaml --cached --parallel
sam local start-api \
  --parameter-overrides \
    ResumeBucket=<your-bucket> \
    ResumeKey=<your-resume-key>
```

Then call the local endpoint:

```bash
curl -X POST http://127.0.0.1:3000/match \
  -H "Content-Type: application/json" \
  -d "{\"job_description\":\"Python AWS Lambda S3 API Gateway\"}"
```

Expected response shape:

```json
{
  "score": 0,
  "matching_keywords": [],
  "missing_keywords": []
}
```

The exact values depend on the resume object and job description.

## Frontend Demo

Open `frontend/index.html` in a browser and enter the deployed or local `/match` API endpoint.

The demo provides:

- API endpoint configuration saved in browser local storage.
- Resume and job-description text areas.
- Sample resume and sample job-description buttons using fictional content.
- A match button that calls `POST /match`.
- Score, keyword, semantic-detail, and raw JSON result displays.
- Copy Result JSON for sharing or debugging.

When the resume textarea is filled, the frontend sends `resume_text` with the request. When it is blank, the backend falls back to the configured S3 resume object from `RESUME_BUCKET` and `RESUME_KEY`.

## Intake Formats

Resume intake can be provided directly as `resume_text` for demo requests. If `resume_text` is omitted, resume intake falls back to `RESUME_BUCKET` and `RESUME_KEY`; the object key may point to:

- `.txt`: decoded as UTF-8 text.
- `.pdf`: extracted with `pypdf`.
- `.docx`: extracted with `python-docx`, including paragraph and table cell text.

Job descriptions can be submitted in exactly one of these fields:

- `job_description`: Existing direct text input.
- `job_description_file`: An object with `filename`, `content`, and optional `is_base64_encoded`; supported filenames end in `.txt` or `.md`.
- `job_description_url`: An HTTP or HTTPS URL. The Lambda fetches up to 1 MB with a short timeout and extracts readable text from HTML responses with Python standard-library parsing.

URL intake rejects localhost, literal private IP addresses, non-HTTP schemes, and embedded credentials. It does not add any persistent AWS resources, but each URL request performs outbound network I/O from Lambda, so direct text or inline file intake remains the lowest-latency and lowest-variability option.

Direct-text resume intake was added for the v2.2 frontend demo. It does not persist resume content and is intended for reviewer-friendly interaction. Future resume management capabilities may replace or augment this direct-text path with upload, multi-resume, or candidate-ranking workflows.

## Semantic Matching Configuration

Semantic matching is implemented behind `SEMANTIC_MATCHING_ENABLED`, which defaults to `false`. When the flag is disabled, the API keeps the original keyword-only production response shape.

The production-focused semantic provider is Amazon Bedrock Titan Text Embeddings V2:

```text
SEMANTIC_MATCHING_ENABLED=true
SEMANTIC_EMBEDDING_PROVIDER=bedrock
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_EMBEDDING_DIMENSIONS=512
EMBEDDING_CACHE_BUCKET=<bucket for cached resume embeddings>
EMBEDDING_CACHE_PREFIX=embeddings/resume
```

`SEMANTIC_EMBEDDING_PROVIDER` defaults to `bedrock` when semantic matching is enabled. `BEDROCK_EMBEDDING_MODEL_ID`, `BEDROCK_EMBEDDING_DIMENSIONS`, and `EMBEDDING_CACHE_PREFIX` also have code defaults. `EMBEDDING_CACHE_BUCKET` falls back to `RESUME_BUCKET` if it is not set.

Resume embeddings are cached in S3 as JSON. The cache key accounts for the resume bucket, resume key, resume S3 ETag, embedding model ID, embedding dimensions, normalization setting, and cache schema version. This allows a changed resume or changed embedding configuration to produce a new cache object automatically.

For production, a separate embedding cache bucket is recommended when you want clearer lifecycle, access, and cleanup boundaries. For this portfolio app, using the existing resume bucket with the default `embeddings/resume` prefix is acceptable and cost-efficient because it avoids another bucket and keeps the IAM scope prefix-limited.

The local validation provider remains available for experiments:

```text
SEMANTIC_MATCHING_ENABLED=true
SEMANTIC_EMBEDDING_PROVIDER=local
SEMANTIC_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

This repository does not add `sentence-transformers` to the default CI dependency set, does not download model weights in CI, does not change SAM packaging, and does not use Lambda container images. To experiment locally with the local provider, install the optional dependency in your local environment:

```bash
python -m pip install sentence-transformers
```

## AWS SAM Deployment

Infrastructure is defined in `template.yaml`. The SAM stack provisions:

- `ResumeMatcherApi`
- `ResumeMatcherFunction`
- Lambda environment variables for `RESUME_BUCKET` and `RESUME_KEY`, which may reference `.txt`, `.pdf`, or `.docx` resume objects
- HTTP API CORS settings for browser-based frontend demo calls
- IAM policy allowing the function to read only the configured S3 object
- Lambda environment variables for guarded Bedrock semantic matching, defaulted off
- IAM policy allowing scoped `bedrock:InvokeModel` access to the configured embedding model
- IAM policy allowing S3 list/read/write access to the configured embedding cache prefix
- Stack outputs for the API endpoint and Lambda function ARN

Manual deployment can be performed with SAM:

```bash
sam validate --template-file template.yaml
sam build --template-file template.yaml --cached --parallel
sam deploy
```

The repository includes `samconfig.toml` with default build and deploy settings. Review the deploy parameter values before using them in another AWS account. Semantic matching remains disabled by default in `samconfig.toml`.

### Finding The Deployed API Endpoint

After deployment, list the stack outputs:

```bash
sam list stack-outputs --stack-name <stack-name>
```

Look for the `ApiEndpoint` output. It should look similar to:

```text
https://abc123.execute-api.us-east-1.amazonaws.com/match
```

Use that endpoint in `curl` requests or in the frontend demo's API endpoint field.

The SAM template exposes these semantic parameters:

- `SemanticMatchingEnabled`
- `SemanticEmbeddingProvider`
- `BedrockEmbeddingModelId`
- `BedrockEmbeddingDimensions`
- `EmbeddingCacheBucket`
- `EmbeddingCachePrefix`

The deployment workflow still uses the existing required repository variables. To enable semantic matching through GitHub Actions later, add repository variables or workflow parameter overrides for the semantic parameters and validate Bedrock model access in the target account and region.

## CI/CD

The repository has two workflows:

- `.github/workflows/ci.yml`
  - Runs on pull requests and pushes to `main`.
  - Installs Python 3.13 and AWS SAM CLI.
  - Installs pytest test dependencies.
  - Runs `python -m pytest`.
  - Runs `sam validate`.
  - Runs `sam build --cached --parallel`.
  - Compiles Python sources under `lambda/`.
- `.github/workflows/deploy.yml`
  - Runs only on pushes to `main`.
  - Uses GitHub OIDC to assume an AWS deployment role.
  - Installs Python 3.13 and AWS SAM CLI.
  - Runs SAM validation, build, and deployment.

The deployment workflow uses these GitHub repository variables:

- `AWS_REGION`
- `AWS_DEPLOY_ROLE_ARN`
- `SAM_STACK_NAME`
- `RESUME_BUCKET`
- `RESUME_KEY`

Semantic parameters have defaults in `template.yaml` and `samconfig.toml`; no additional repository variables are required while semantic matching remains disabled.

## GitHub OIDC Authentication

The deploy workflow uses `aws-actions/configure-aws-credentials` with GitHub OIDC. Instead of storing long-lived AWS access keys in GitHub, GitHub requests a short-lived OIDC token during the workflow run. AWS IAM validates that token against the trust policy on the configured deployment role, then issues temporary credentials for the job.

At a high level, the AWS deployment role should:

- Trust GitHub's OIDC identity provider.
- Restrict assumptions to the intended repository, branch, and workflow context.
- Grant only the permissions required for SAM and CloudFormation deployment.

No AWS secrets are stored in the repository.

## Repository Structure

```text
.
|-- .github/
|   `-- workflows/
|       |-- ci.yml
|       `-- deploy.yml
|-- frontend/
|   `-- index.html
|-- lambda/
|   |-- app.py
|   `-- requirements.txt
|-- tests/
|   |-- conftest.py
|   |-- test_app.py
|   `-- test_template.py
|-- sample-data/
|   `-- resume.txt
|-- release_notes/
|   |-- RELEASE_NOTES_v2.0.0.md
|   |-- RELEASE_NOTES_v2.1.0.md
|   |-- RELEASE_NOTES_v2.2.0.md
|   |-- RELEASE_NOTES_v2.3.0.md
|   |-- RELEASE_NOTES_v2.5.0.md
|   |-- RELEASE_NOTES_v2.5.1.md
|   |-- RELEASE_NOTES_v2.6.0.md
|   `-- RELEASE_NOTES_v2.7.0.md
|-- .gitignore
|-- CONTEXT.md
|-- README.md
|-- RELEASE_NOTES.md
|-- requirements-dev.txt
|-- samconfig.toml
`-- template.yaml
```

Notes:

- `frontend/index.html` is a self-contained static demo with embedded CSS and JavaScript.
- `sample-data/` is ignored by Git and should not be used for public resume data.
- `RELEASE_NOTES.md` summarizes the latest release; version-specific notes live under `release_notes/`.
- `.aws-sam/`, caches, virtual environments, and Python bytecode are ignored.

## Version History

- **v1.0.0 / `v1.0-serverless-api`**: Introduced the serverless resume matching API and removed local resume data from tracked files.
- **v1.0.1**: Improved deployment documentation for the initial Lambda-based MVP.
- **v1.1.0**: Migrated infrastructure into AWS SAM with an HTTP API, Lambda function, IAM policy, and stack outputs.
- **v1.2.0**: Added GitHub Actions CI/CD support, including SAM validation/build in CI and OIDC-based deployment from pushes to `main`.
- **v1.3.0**: Added pytest-based automated testing and updated CI to run tests before SAM validation and build.
- **v2.0.0**: Added guarded semantic matching with Amazon Bedrock Titan Text Embeddings V2, hybrid keyword + semantic scoring, S3 resume embedding caching and reuse, SAM configuration, and least-privilege IAM while preserving keyword-only behavior by default.
- **v2.1.0**: Added resume and job-description intake expansion for `.txt`, `.pdf`, `.docx`, `.md`, and URL-based job descriptions while preserving the existing direct-text API behavior.
- **v2.2.0**: Added a framework-free static frontend demo, direct-text resume input for demos, browser CORS support, sample input loading, result visualization, and Copy Result JSON.
- **v2.2.1**: Improved README deployment instructions for locating the deployed API endpoint from SAM stack outputs.
- **v2.3.0**: Improved keyword extraction quality by filtering numeric-list artifacts, contraction fragments, trailing punctuation, and selected low-value noise tokens while preserving important technical terms.
- **v2.4.0**: Added whole-document and simple paragraph/bullet chunked semantic score comparison, with real-world validation showing generic chunked semantic matching did not materially improve scoring.
- **v2.5.0**: Added an explainable fit analysis MVP in semantic mode with deterministic requirement parsing, resume evidence chunking, requirement-to-evidence scoring, matched requirements, and gaps while preserving existing score fields and keyword-only behavior.
- **v2.5.1**: Calibrated fit-analysis matching for real Bedrock/Titan score ranges by lowering the matched requirement threshold from `60` to `40` and adding internal score summary diagnostics.
- **v2.6.0**: Improved evidence retrieval and chunk ranking with requirement-scoped phrase aliases for terms such as `program/project management`, `AI/ML`, `agentic AI`, and content/data systems, plus internal top-3 evidence diagnostics.
- **v2.7.0**: Refined semantic-mode evidence selection for narrative-heavy resumes with internal sentence/window candidates, top-k reranking, and deterministic filters for low-value JD chunks such as job IDs, compensation/location text, company narrative, and legal/benefits boilerplate.

## Future Roadmap

- Expand requirement-to-evidence calibration after more real Bedrock/Titan examples, especially around narrative evidence windows and verbose enterprise job descriptions.
- Add richer requirement understanding, such as requirement classification, importance weighting, confidence models, and richer explanations after evidence retrieval quality improves.
- Add richer resume management, such as upload, multi-resume support, or candidate ranking with explicit privacy controls.
- Add weighted scoring for skills, certifications, seniority, and domain experience.
- Support multiple resumes and candidate ranking.
- Add authentication or rate limiting before any public deployment.
- Add structured logging, tracing, and operational metrics.
- Add a separate deployment environment strategy, such as dev and prod stacks.
