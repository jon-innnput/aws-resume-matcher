import base64
import json
from io import BytesIO

import pytest


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


class FakeEmbeddingModel:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.calls = []

    def encode(self, text):
        self.calls.append(text)
        return self.embeddings[text]


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


def test_calculate_keyword_score_uses_existing_overlap_formula(app_module):
    score = app_module.calculate_keyword_score(
        {"python", "aws", "lambda"},
        {"python", "lambda", "terraform"},
    )

    assert score == 67


def test_cosine_similarity_returns_expected_similarity(app_module):
    assert app_module.cosine_similarity([1, 0], [0, 1]) == 0
    assert app_module.cosine_similarity([1, 1], [1, 1]) == pytest.approx(1)


def test_cosine_similarity_rejects_mismatched_dimensions(app_module):
    try:
        app_module.cosine_similarity([1, 0], [1])
    except ValueError as exc:
        assert str(exc) == "embeddings must have the same dimension"
    else:
        raise AssertionError("Expected mismatched embeddings to raise ValueError")


def test_calculate_semantic_score_uses_mocked_embeddings(app_module):
    model = FakeEmbeddingModel(
        {
            "resume": [1, 1],
            "job": [1, 0],
        }
    )

    score = app_module.calculate_semantic_score("resume", "job", model)

    assert score == 71
    assert model.calls == ["resume", "job"]


def test_calculate_semantic_score_clamps_negative_similarity(app_module):
    model = FakeEmbeddingModel(
        {
            "resume": [1, 0],
            "job": [-1, 0],
        }
    )

    assert app_module.calculate_semantic_score("resume", "job", model) == 0


def test_combine_scores_uses_default_hybrid_weights(app_module):
    assert app_module.combine_scores(keyword_score=75, semantic_score=90) == 83


def test_compare_resume_to_job_keeps_keyword_only_shape_by_default(app_module):
    result = app_module.compare_resume_to_job(
        "Python AWS Lambda S3 DynamoDB",
        "Python Lambda Terraform S3",
    )

    assert set(result) == {"score", "matching_keywords", "missing_keywords"}
    assert result["score"] == 75


def test_compare_resume_to_job_adds_semantic_fields_when_enabled(
    app_module, monkeypatch
):
    monkeypatch.setenv(app_module.SEMANTIC_MATCHING_ENABLED_ENV, "true")
    monkeypatch.setattr(
        app_module,
        "_embedding_model",
        FakeEmbeddingModel(
            {
                "Python AWS Lambda S3 DynamoDB": [1, 0],
                "Python Lambda Terraform S3": [1, 0],
            }
        ),
    )

    result = app_module.compare_resume_to_job(
        "Python AWS Lambda S3 DynamoDB",
        "Python Lambda Terraform S3",
    )

    assert result == {
        "score": 89,
        "keyword_score": 75,
        "semantic_score": 100,
        "matching_keywords": ["lambda", "python", "s3"],
        "missing_keywords": ["terraform"],
        "semantic_model": "sentence-transformers/all-MiniLM-L6-v2",
        "weights": {
            "keyword": 0.45,
            "semantic": 0.55,
        },
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
