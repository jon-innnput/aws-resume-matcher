# Release Notes: v2.0.0

## Summary

v2.0.0 adds guarded semantic AI matching to AWS Resume Matcher while preserving the existing keyword-only behavior by default. The release moves the project from deterministic keyword overlap into a hybrid AI matching architecture using Amazon Bedrock Titan Text Embeddings V2, weighted keyword + semantic scoring, and S3-cached resume embeddings to reduce repeated embedding work.

This release is complete, tagged, and runtime-validated. It is still intentionally conservative for production use: semantic matching must be explicitly enabled with AWS account, Bedrock model access, and embedding-cache configuration in place.

## Highlights

- Added hybrid keyword + semantic scoring.
- Added Amazon Bedrock Titan Text Embeddings V2 as the production semantic embedding provider.
- Added optional local semantic validation with `sentence-transformers/all-MiniLM-L6-v2`.
- Added S3 resume embedding caching keyed by resume bucket, resume key, ETag, embedding model, dimensions, normalization setting, and cache schema version.
- Added SAM parameters for semantic enablement, Bedrock model configuration, embedding dimensions, and S3 cache location.
- Added least-privilege IAM for Bedrock invocation and S3 embedding-cache list/read/write access.
- Preserved standard AWS SAM ZIP deployment.
- Preserved keyword-only API behavior when `SEMANTIC_MATCHING_ENABLED=false`.
- Added mocked tests for semantic scoring, Bedrock provider behavior, S3 cache behavior, and SAM semantic configuration.

## Runtime Validation

End-to-end runtime validation completed successfully:

- Bedrock Titan Embeddings V2 access verified.
- Bedrock embedding generation verified.
- Semantic scoring verified through the deployed API.
- S3 embedding cache creation verified.
- S3 embedding cache reuse verified on subsequent requests.
- IAM permissions verified, including scoped cache-prefix listing.
- API Gateway to Lambda to Bedrock to Lambda flow verified.
- Keyword-only behavior verified with semantic matching disabled.

## API Behavior

Default keyword-only behavior remains:

- Request body: `{"job_description":"..."}`
- Response fields: `score`, `matching_keywords`, `missing_keywords`
- No semantic provider, model, or weight fields are returned while semantic mode is disabled.

Semantic mode adds:

- `keyword_score`
- `semantic_score`
- `semantic_model`
- `semantic_provider`
- `weights`

The top-level `score` remains the primary client-facing score. In semantic mode, it is the weighted hybrid score.

## Configuration

Semantic matching remains disabled by default.

Key environment variables:

```text
SEMANTIC_MATCHING_ENABLED=false
SEMANTIC_EMBEDDING_PROVIDER=bedrock
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_EMBEDDING_DIMENSIONS=512
EMBEDDING_CACHE_BUCKET=<cache-bucket>
EMBEDDING_CACHE_PREFIX=embeddings/resume
```

When semantic matching is disabled, responses keep the original shape:

```json
{
  "score": 75,
  "matching_keywords": ["aws", "python", "s3"],
  "missing_keywords": ["docker"]
}
```

When semantic matching is enabled, responses include hybrid scoring details:

```json
{
  "score": 89,
  "keyword_score": 75,
  "semantic_score": 100,
  "matching_keywords": ["lambda", "python", "s3"],
  "missing_keywords": ["terraform"],
  "semantic_model": "amazon.titan-embed-text-v2:0",
  "semantic_provider": "bedrock",
  "weights": {
    "keyword": 0.45,
    "semantic": 0.55
  }
}
```

## Upgrade Notes

- Existing deployments remain keyword-only unless semantic matching is explicitly enabled.
- Existing clients that rely on `score`, `matching_keywords`, and `missing_keywords` remain compatible when semantic matching is disabled.
- Enabling semantic matching requires Bedrock model access in the deployment region.
- The embedding cache bucket must exist before semantic matching is enabled.
- For production isolation, a separate embedding cache bucket is recommended; using the resume bucket with the default `embeddings/resume` prefix remains acceptable for small portfolio deployments.
- The SAM template includes semantic IAM and configuration, but the GitHub deployment workflow does not yet pass semantic parameter overrides.

## Deferred To v2.1.0

- Richer semantic explanations with top matching resume/job snippets.
- Structured CloudWatch logging for cache hits, cache misses, Bedrock latency, and scoring breakdowns.
- CloudWatch metrics and alarms for semantic-mode failures and latency.
- Deployment workflow parameter overrides for enabling semantic matching through GitHub Actions.
- Dedicated dev/prod environment strategy.
- Optional separate managed embedding cache bucket in SAM.
- PDF/DOCX resume ingestion.
- Frontend for reviewer-friendly semantic matching demos.
