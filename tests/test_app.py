import base64
import json
from io import BytesIO


class FakeS3Client:
    def __init__(self, body_text="Python AWS Lambda S3 APIs", error=None):
        self.body_text = body_text
        self.error = error
        self.calls = []

    def get_object(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {"Body": BytesIO(self.body_text.encode("utf-8"))}


def response_body(response):
    return json.loads(response["body"])


def valid_event(job_description="Python Lambda Terraform"):
    return {
        "httpMethod": "POST",
        "body": json.dumps({"job_description": job_description}),
    }


def test_extract_keywords_normalizes_and_filters_stop_words(app_module):
    keywords = app_module._extract_keywords(
        "The Python, AWS-Lambda and C++ APIs are in production."
    )

    assert keywords == {"python", "aws-lambda", "c++", "apis", "production."}


def test_compare_resume_to_job_returns_score_matches_and_missing(app_module):
    result = app_module.compare_resume_to_job(
        "Python AWS Lambda S3 DynamoDB",
        "Python Lambda Terraform S3",
    )

    assert result == {
        "score": 75,
        "matching_keywords": ["lambda", "python", "s3"],
        "missing_keywords": ["terraform"],
    }


def test_compare_resume_to_job_handles_empty_job_keywords(app_module):
    result = app_module.compare_resume_to_job("Python AWS", "the and to")

    assert result == {
        "score": 0,
        "matching_keywords": [],
        "missing_keywords": [],
    }


def test_lambda_handler_rejects_non_post_requests(app_module):
    response = app_module.lambda_handler({"httpMethod": "GET"}, None)

    assert response["statusCode"] == 405
    assert response["headers"] == {"Content-Type": "application/json"}
    assert response_body(response) == {"message": "Method not allowed"}


def test_lambda_handler_rejects_missing_body(app_module):
    response = app_module.lambda_handler({"httpMethod": "POST"}, None)

    assert response["statusCode"] == 400
    assert response_body(response)["message"].startswith("Invalid request body:")


def test_lambda_handler_rejects_empty_job_description(app_module):
    response = app_module.lambda_handler(
        {"httpMethod": "POST", "body": json.dumps({"job_description": "   "})},
        None,
    )

    assert response["statusCode"] == 400
    assert response_body(response) == {
        "message": "job_description must be a non-empty string"
    }


def test_lambda_handler_accepts_base64_encoded_json(app_module, monkeypatch):
    s3_client = FakeS3Client("Python AWS Lambda S3")
    monkeypatch.setattr(app_module, "s3_client", s3_client)
    monkeypatch.setenv(app_module.RESUME_BUCKET_ENV, "resume-bucket")
    monkeypatch.setenv(app_module.RESUME_KEY_ENV, "resume.txt")

    encoded_body = base64.b64encode(
        json.dumps({"job_description": "Python Lambda API"}).encode("utf-8")
    ).decode("utf-8")
    response = app_module.lambda_handler(
        {
            "requestContext": {"http": {"method": "POST"}},
            "isBase64Encoded": True,
            "body": encoded_body,
        },
        None,
    )

    assert response["statusCode"] == 200
    assert response["headers"] == {"Content-Type": "application/json"}
    assert response_body(response) == {
        "score": 67,
        "matching_keywords": ["lambda", "python"],
        "missing_keywords": ["api"],
    }
    assert s3_client.calls == [{"Bucket": "resume-bucket", "Key": "resume.txt"}]


def test_lambda_handler_returns_500_when_s3_configuration_missing(
    app_module, monkeypatch
):
    monkeypatch.delenv(app_module.RESUME_BUCKET_ENV, raising=False)
    monkeypatch.delenv(app_module.RESUME_KEY_ENV, raising=False)

    response = app_module.lambda_handler(valid_event(), None)

    assert response["statusCode"] == 500
    assert response_body(response) == {
        "message": "RESUME_BUCKET and RESUME_KEY must be configured"
    }


def test_lambda_handler_returns_502_when_s3_read_fails(app_module, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "s3_client",
        FakeS3Client(error=RuntimeError("network unavailable")),
    )
    monkeypatch.setenv(app_module.RESUME_BUCKET_ENV, "resume-bucket")
    monkeypatch.setenv(app_module.RESUME_KEY_ENV, "resume.txt")

    response = app_module.lambda_handler(valid_event(), None)

    assert response["statusCode"] == 502
    assert response_body(response) == {"message": "Unable to read resume from S3"}


def test_lambda_handler_success_response_structure(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "s3_client", FakeS3Client("Python AWS Lambda S3"))
    monkeypatch.setenv(app_module.RESUME_BUCKET_ENV, "resume-bucket")
    monkeypatch.setenv(app_module.RESUME_KEY_ENV, "resume.txt")

    response = app_module.lambda_handler(valid_event("Python AWS S3 Docker"), None)
    body = response_body(response)

    assert set(response) == {"statusCode", "headers", "body"}
    assert response["statusCode"] == 200
    assert response["headers"] == {"Content-Type": "application/json"}
    assert set(body) == {"score", "matching_keywords", "missing_keywords"}
    assert body["score"] == 75
    assert body["matching_keywords"] == ["aws", "python", "s3"]
    assert body["missing_keywords"] == ["docker"]
