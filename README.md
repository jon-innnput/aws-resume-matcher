# AWS Resume Matcher

Python 3.13 AWS Lambda function that accepts a job description, reads a plain-text
resume from S3, and returns a simple keyword-overlap match score.

## Deployment

Source code:

```text
lambda/app.py
```

For this MVP, the Lambda code is deployed manually through the AWS Lambda Console.

Environment variables:

```text
RESUME_BUCKET=<bucket containing the resume text file>
RESUME_KEY=<path/to/resume.txt>
```

IAM permissions:

```text
s3:GetObject
```

The Lambda execution role must have permission to read the configured resume object from Amazon S3.

## Request

```json
{
  "job_description": "..."
}
```

## Response

```json
{
  "score": 0,
  "matching_keywords": [],
  "missing_keywords": []
}
```

## Local Testing

This repository intentionally excludes resume files.

Create a local file at:

sample-data/resume.txt

and upload it to your configured S3 bucket.

The sample-data directory is ignored by Git to prevent accidental publication of personal information.

## Future Enhancements

### AI Improvements
- Replace keyword matching with semantic similarity using sentence embeddings.
- Support PDF resumes instead of plain text files.
- Add weighted scoring for skills, certifications, and experience.
- Add support for multiple resumes and candidate ranking.

### AWS Enhancements
- Automate deployments using GitHub Actions and AWS Lambda.
- Manage infrastructure with AWS SAM, CDK, or Terraform.
- Add authentication and authorization to the API.

### Amazon Bedrock Integration (Future)
- Replace local embedding generation with Amazon Titan Embeddings via Amazon Bedrock.
- Compare local embeddings versus Bedrock embeddings for match quality.
- Explore Retrieval-Augmented Generation (RAG) to explain why a resume matches a job description.
- Add cost monitoring and usage controls before enabling Bedrock in production.
