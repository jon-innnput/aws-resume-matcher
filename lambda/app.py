import base64
import json
import logging
import os
import re
from typing import Any

import boto3


logger = logging.getLogger(__name__)
s3_client = boto3.client("s3")

RESUME_BUCKET_ENV = "RESUME_BUCKET"
RESUME_KEY_ENV = "RESUME_KEY"

STOP_WORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "now",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    request_method = _request_method(event)
    if request_method and request_method != "POST":
        return _response(405, {"message": "Method not allowed"})

    try:
        payload = _parse_body(event)
        job_description = payload["job_description"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return _response(400, {"message": f"Invalid request body: {exc}"})

    if not isinstance(job_description, str) or not job_description.strip():
        return _response(400, {"message": "job_description must be a non-empty string"})

    try:
        resume_text = _read_resume_from_s3()
    except ValueError as exc:
        return _response(500, {"message": str(exc)})
    except Exception:
        logger.exception("Failed to read resume from S3")
        return _response(502, {"message": "Unable to read resume from S3"})

    result = compare_resume_to_job(resume_text, job_description)
    return _response(200, result)


def compare_resume_to_job(resume_text: str, job_description: str) -> dict[str, Any]:
    resume_keywords = _extract_keywords(resume_text)
    job_keywords = _extract_keywords(job_description)

    if not job_keywords:
        return {"score": 0, "matching_keywords": [], "missing_keywords": []}

    matching_keywords = sorted(job_keywords & resume_keywords)
    missing_keywords = sorted(job_keywords - resume_keywords)
    score = round((len(matching_keywords) / len(job_keywords)) * 100)

    return {
        "score": score,
        "matching_keywords": matching_keywords,
        "missing_keywords": missing_keywords,
    }


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if body is None:
        raise ValueError("body is required")

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    if isinstance(body, str):
        return json.loads(body)

    if isinstance(body, dict):
        return body

    raise ValueError("body must be JSON")


def _request_method(event: dict[str, Any]) -> str | None:
    if event.get("httpMethod"):
        return event["httpMethod"].upper()

    return (
        event.get("requestContext", {})
        .get("http", {})
        .get("method", "")
        .upper()
        or None
    )


def _read_resume_from_s3() -> str:
    bucket = os.environ.get(RESUME_BUCKET_ENV)
    key = os.environ.get(RESUME_KEY_ENV)

    if not bucket or not key:
        raise ValueError(f"{RESUME_BUCKET_ENV} and {RESUME_KEY_ENV} must be configured")

    s3_object = s3_client.get_object(Bucket=bucket, Key=key)
    return s3_object["Body"].read().decode("utf-8")


def _extract_keywords(text: str) -> set[str]:
    normalized_text = _normalize_text(text)
    words = re.findall(r"[a-z0-9][a-z0-9+#.-]*", normalized_text)
    return {word for word in words if word not in STOP_WORDS and len(word) > 1}


def _normalize_text(text: str) -> str:
    return text.casefold()


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
