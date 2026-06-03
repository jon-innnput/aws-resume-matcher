# AWS Resume Matcher

Python 3.13 AWS Lambda function that accepts a job description, reads a plain-text
resume from S3, and returns a simple keyword-overlap match score.

## Lambda configuration

Handler:

```text
lambda/app.lambda_handler
```

Environment variables:

```text
RESUME_BUCKET=<bucket containing the resume text file>
RESUME_KEY=<path/to/resume.txt>
```

The Lambda execution role needs `s3:GetObject` permission for the configured
resume object.

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
