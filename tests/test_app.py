import base64
import json
from io import BytesIO

import pytest


class FakeS3Client:
    def __init__(
        self,
        body_text="Python AWS Lambda S3 APIs",
        body_bytes=None,
        error=None,
        etag=None,
    ):
        self.body_text = body_text
        self.body_bytes = body_bytes
        self.error = error
        self.etag = etag
        self.calls = []

    def get_object(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        body = self.body_bytes
        if body is None:
            body = self.body_text.encode("utf-8")
        response = {"Body": BytesIO(body)}
        if self.etag:
            response["ETag"] = self.etag
        return response


class FakeEmbeddingModel:
    def __init__(
        self,
        embeddings,
        model_id="fake-model",
        dimensions=2,
        normalize=True,
    ):
        self.embeddings = embeddings
        self.model_id = model_id
        self.dimensions = dimensions
        self.normalize = normalize
        self.calls = []

    def encode(self, text):
        self.calls.append(text)
        return self.embeddings[text]


class FakeBedrockClient:
    def __init__(self, embedding):
        self.embedding = embedding
        self.calls = []

    def invoke_model(self, **kwargs):
        self.calls.append(kwargs)
        return {"body": BytesIO(json.dumps({"embedding": self.embedding}).encode())}


class FakeCacheMiss(Exception):
    response = {"Error": {"Code": "NoSuchKey"}}


class FakeEmbeddingCacheS3Client:
    def __init__(self, objects=None):
        self.objects = objects or {}
        self.get_calls = []
        self.put_calls = []

    def get_object(self, **kwargs):
        self.get_calls.append(kwargs)
        key = kwargs["Key"]
        if key not in self.objects:
            raise FakeCacheMiss()
        return {"Body": BytesIO(json.dumps(self.objects[key]).encode("utf-8"))}

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)


def response_body(response):
    return json.loads(response["body"])


def expected_json_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
    }


def valid_event(job_description="Python Lambda Terraform"):
    return {
        "httpMethod": "POST",
        "body": json.dumps({"job_description": job_description}),
    }


def test_extract_keywords_normalizes_and_filters_stop_words(app_module):
    keywords = app_module._extract_keywords(
        "The Python, AWS-Lambda and C++ APIs are in production."
    )

    assert keywords == {"python", "aws-lambda", "c++", "api", "production"}


def test_extract_keywords_removes_resume_match_noise(app_module):
    keywords = app_module._extract_keywords(
        """
        1. You'll build responses. 2. We've owned systems. 3+ years. 3px spacing.
        Role. AWS Bedrock Lambda S3 API CI/CD C++ C# serverless integrations.
        """
    )

    assert keywords == {
        "api",
        "aws",
        "bedrock",
        "build",
        "c#",
        "c++",
        "ci/cd",
        "integrations",
        "lambda",
        "owned",
        "s3",
        "serverless",
        "spacing",
        "years",
    }
    assert {"1", "2", "3+", "3px", "ll", "ve", "role", "responses", "systems"}.isdisjoint(
        keywords
    )


def test_compare_resume_to_job_uses_cleaned_realistic_keywords(app_module):
    result = app_module.compare_resume_to_job(
        """
        Senior software engineer building AWS Lambda APIs with S3, Bedrock,
        CI/CD pipelines, C++ services, and C# integration tooling.
        """,
        """
        1. Role. You'll build AWS Lambda, S3, API Gateway, Bedrock, and CI/CD
        systems. 2. We need C++ or C# experience. 3+ years. 3px design tokens.
        Responses.
        """,
    )

    assert result == {
        "score": 53,
        "matching_keywords": [
            "api",
            "aws",
            "bedrock",
            "c#",
            "c++",
            "ci/cd",
            "lambda",
            "s3",
        ],
        "missing_keywords": [
            "build",
            "design",
            "experience",
            "gateway",
            "need",
            "tokens",
            "years",
        ],
    }


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


def test_bedrock_embedding_provider_invokes_titan_v2_with_dimensions(app_module):
    client = FakeBedrockClient([0.1, 0.2])
    provider = app_module.BedrockEmbeddingProvider(
        client,
        "amazon.titan-embed-text-v2:0",
        512,
    )

    embedding = provider.encode("serverless python")

    assert embedding == [0.1, 0.2]
    assert client.calls == [
        {
            "modelId": "amazon.titan-embed-text-v2:0",
            "body": json.dumps(
                {
                    "inputText": "serverless python",
                    "dimensions": 512,
                    "normalize": True,
                }
            ),
            "accept": "application/json",
            "contentType": "application/json",
        }
    ]


def test_s3_embedding_cache_key_includes_resume_and_model_identity(app_module):
    cache = app_module.S3EmbeddingCache(
        FakeEmbeddingCacheS3Client(),
        "resume-bucket",
        "cache-prefix",
    )
    provider = FakeEmbeddingModel({}, model_id="model-a", dimensions=512)
    resume_source = {
        "bucket": "resume-bucket",
        "key": "resume.txt",
        "etag": "etag-1",
    }

    key = cache.cache_key(resume_source, provider)
    changed_etag_key = cache.cache_key(
        {**resume_source, "etag": "etag-2"},
        provider,
    )
    changed_model_key = cache.cache_key(
        resume_source,
        FakeEmbeddingModel({}, model_id="model-b", dimensions=512),
    )
    changed_dimensions_key = cache.cache_key(
        resume_source,
        FakeEmbeddingModel({}, model_id="model-a", dimensions=1024),
    )

    assert key.startswith("cache-prefix/")
    assert key.endswith(".json")
    assert key != changed_etag_key
    assert key != changed_model_key
    assert key != changed_dimensions_key


def test_calculate_semantic_score_reuses_cached_resume_embedding(app_module):
    provider = FakeEmbeddingModel(
        {
            "job": [1, 0],
        },
        model_id="model-a",
        dimensions=2,
    )
    resume_source = {
        "bucket": "resume-bucket",
        "key": "resume.txt",
        "etag": "etag-1",
    }
    cache_client = FakeEmbeddingCacheS3Client()
    cache = app_module.S3EmbeddingCache(cache_client, "cache-bucket", "cache")
    cache_key = cache.cache_key(resume_source, provider)
    cache_client.objects[cache_key] = {
        "embedding": {
            "vector": [1, 0],
        }
    }

    score = app_module.calculate_semantic_score(
        "resume",
        "job",
        provider,
        resume_source,
        cache,
    )

    assert score == 100
    assert provider.calls == ["job"]
    assert cache_client.put_calls == []


def test_calculate_semantic_score_writes_resume_embedding_on_cache_miss(app_module):
    provider = FakeEmbeddingModel(
        {
            "resume": [1, 0],
            "job": [1, 0],
        },
        model_id="model-a",
        dimensions=2,
    )
    resume_source = {
        "bucket": "resume-bucket",
        "key": "resume.txt",
        "etag": "etag-1",
    }
    cache_client = FakeEmbeddingCacheS3Client()
    cache = app_module.S3EmbeddingCache(cache_client, "cache-bucket", "cache")

    score = app_module.calculate_semantic_score(
        "resume",
        "job",
        provider,
        resume_source,
        cache,
    )

    assert score == 100
    assert provider.calls == ["resume", "job"]
    assert len(cache_client.put_calls) == 1
    put_call = cache_client.put_calls[0]
    assert put_call["Bucket"] == "cache-bucket"
    assert put_call["Key"].startswith("cache/")
    assert put_call["ContentType"] == "application/json"
    payload = json.loads(put_call["Body"].decode("utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["source"] == resume_source
    assert payload["embedding"]["model_id"] == "model-a"
    assert payload["embedding"]["vector"] == [1, 0]


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
        "_embedding_provider",
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
        "semantic_model": "fake-model",
        "semantic_provider": "bedrock",
        "weights": {
            "keyword": 0.45,
            "semantic": 0.55,
        },
    }


def test_lambda_handler_rejects_non_post_requests(app_module):
    response = app_module.lambda_handler({"httpMethod": "GET"}, None)

    assert response["statusCode"] == 405
    assert response["headers"] == expected_json_headers()
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


def test_lambda_handler_rejects_multiple_job_description_inputs(app_module):
    response = app_module.lambda_handler(
        {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "job_description": "Python Lambda",
                    "job_description_url": "https://example.com/job",
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 400
    assert "provide exactly one" in response_body(response)["message"]


def test_lambda_handler_accepts_job_description_text_file(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "s3_client", FakeS3Client("Python AWS Lambda S3"))
    monkeypatch.setenv(app_module.RESUME_BUCKET_ENV, "resume-bucket")
    monkeypatch.setenv(app_module.RESUME_KEY_ENV, "resume.txt")

    response = app_module.lambda_handler(
        {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "job_description_file": {
                        "filename": "job.txt",
                        "content": "Python Lambda API",
                    }
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert response_body(response) == {
        "score": 67,
        "matching_keywords": ["lambda", "python"],
        "missing_keywords": ["api"],
    }


def test_lambda_handler_accepts_base64_markdown_job_description_file(
    app_module, monkeypatch
):
    monkeypatch.setattr(app_module, "s3_client", FakeS3Client("Python AWS Lambda S3"))
    monkeypatch.setenv(app_module.RESUME_BUCKET_ENV, "resume-bucket")
    monkeypatch.setenv(app_module.RESUME_KEY_ENV, "resume.txt")
    encoded_file = base64.b64encode(b"# Role\nPython Lambda API").decode("utf-8")

    response = app_module.lambda_handler(
        {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "job_description_file": {
                        "filename": "job.md",
                        "content": encoded_file,
                        "is_base64_encoded": True,
                    }
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert response_body(response)["matching_keywords"] == ["lambda", "python"]


def test_lambda_handler_rejects_unsupported_job_description_file(app_module):
    response = app_module.lambda_handler(
        {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "job_description_file": {
                        "filename": "job.pdf",
                        "content": "Python Lambda",
                    }
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 400
    assert "Unsupported job description file type" in response_body(response)["message"]


def test_job_description_from_url_extracts_html_text(app_module, monkeypatch):
    class FakeUrlResponse:
        headers = {"Content-Type": "text/html; charset=utf-8"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self, size):
            return (
                b"<html><style>ignore</style><body><h1>Python Lambda</h1>"
                b"<script>ignore</script><p>API Gateway</p></body></html>"
            )

    monkeypatch.setattr(
        app_module.urllib.request,
        "urlopen",
        lambda request, timeout: FakeUrlResponse(),
    )

    text = app_module._job_description_from_url("https://example.com/jobs/1")

    assert text == "Python Lambda API Gateway"


def test_job_description_url_rejects_private_literal_address(app_module):
    with pytest.raises(ValueError, match="private address"):
        app_module._job_description_from_url("http://10.0.0.1/job")


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
    assert response["headers"] == expected_json_headers()
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
    assert response["headers"] == expected_json_headers()
    assert set(body) == {"score", "matching_keywords", "missing_keywords"}
    assert body["score"] == 75
    assert body["matching_keywords"] == ["aws", "python", "s3"]
    assert body["missing_keywords"] == ["docker"]


def test_lambda_handler_accepts_direct_resume_text_without_s3(app_module, monkeypatch):
    s3_client = FakeS3Client(error=AssertionError("S3 should not be called"))
    monkeypatch.setattr(app_module, "s3_client", s3_client)
    monkeypatch.delenv(app_module.RESUME_BUCKET_ENV, raising=False)
    monkeypatch.delenv(app_module.RESUME_KEY_ENV, raising=False)

    response = app_module.lambda_handler(
        {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "resume_text": "Python AWS Lambda S3",
                    "job_description": "Python Lambda API",
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert response_body(response) == {
        "score": 67,
        "matching_keywords": ["lambda", "python"],
        "missing_keywords": ["api"],
    }
    assert s3_client.calls == []


def test_lambda_handler_falls_back_to_s3_when_resume_text_is_not_supplied(
    app_module, monkeypatch
):
    s3_client = FakeS3Client("Python AWS Lambda S3")
    monkeypatch.setattr(app_module, "s3_client", s3_client)
    monkeypatch.setenv(app_module.RESUME_BUCKET_ENV, "resume-bucket")
    monkeypatch.setenv(app_module.RESUME_KEY_ENV, "resume.txt")

    response = app_module.lambda_handler(
        {
            "httpMethod": "POST",
            "body": json.dumps({"job_description": "Python Lambda API"}),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert response_body(response)["score"] == 67
    assert s3_client.calls == [{"Bucket": "resume-bucket", "Key": "resume.txt"}]


def test_lambda_handler_rejects_empty_resume_text(app_module):
    response = app_module.lambda_handler(
        {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "resume_text": "   ",
                    "job_description": "Python Lambda API",
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 400
    assert "resume_text must be a non-empty string" in response_body(response)["message"]


def test_lambda_handler_rejects_non_string_resume_text(app_module):
    response = app_module.lambda_handler(
        {
            "httpMethod": "POST",
            "body": json.dumps(
                {
                    "resume_text": ["Python", "Lambda"],
                    "job_description": "Python Lambda API",
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 400
    assert "resume_text must be a non-empty string" in response_body(response)["message"]


def test_read_resume_object_extracts_pdf_by_extension(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "s3_client", FakeS3Client(body_bytes=b"%PDF"))
    monkeypatch.setattr(app_module, "_extract_text_from_pdf", lambda body: "Python PDF")
    monkeypatch.setenv(app_module.RESUME_BUCKET_ENV, "resume-bucket")
    monkeypatch.setenv(app_module.RESUME_KEY_ENV, "resume.pdf")

    resume_object = app_module._read_resume_object_from_s3()

    assert resume_object["text"] == "Python PDF"
    assert resume_object["source"]["key"] == "resume.pdf"


def test_read_resume_object_extracts_docx_by_extension(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "s3_client", FakeS3Client(body_bytes=b"PK"))
    monkeypatch.setattr(app_module, "_extract_text_from_docx", lambda body: "Python DOCX")
    monkeypatch.setenv(app_module.RESUME_BUCKET_ENV, "resume-bucket")
    monkeypatch.setenv(app_module.RESUME_KEY_ENV, "resume.docx")

    resume_object = app_module._read_resume_object_from_s3()

    assert resume_object["text"] == "Python DOCX"


def test_read_resume_object_rejects_unsupported_extension(app_module, monkeypatch):
    monkeypatch.setattr(app_module, "s3_client", FakeS3Client(body_bytes=b"rtf"))
    monkeypatch.setenv(app_module.RESUME_BUCKET_ENV, "resume-bucket")
    monkeypatch.setenv(app_module.RESUME_KEY_ENV, "resume.rtf")

    with pytest.raises(ValueError, match="Unsupported resume file type"):
        app_module._read_resume_object_from_s3()
