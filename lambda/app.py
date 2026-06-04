import base64
import hashlib
import json
import logging
import os
import re
from collections.abc import Sequence
from typing import Any

import boto3


logger = logging.getLogger(__name__)
s3_client = boto3.client("s3")

RESUME_BUCKET_ENV = "RESUME_BUCKET"
RESUME_KEY_ENV = "RESUME_KEY"
SEMANTIC_MATCHING_ENABLED_ENV = "SEMANTIC_MATCHING_ENABLED"
SEMANTIC_EMBEDDING_PROVIDER_ENV = "SEMANTIC_EMBEDDING_PROVIDER"
SEMANTIC_MODEL_NAME_ENV = "SEMANTIC_MODEL_NAME"
BEDROCK_EMBEDDING_MODEL_ID_ENV = "BEDROCK_EMBEDDING_MODEL_ID"
BEDROCK_EMBEDDING_DIMENSIONS_ENV = "BEDROCK_EMBEDDING_DIMENSIONS"
EMBEDDING_CACHE_BUCKET_ENV = "EMBEDDING_CACHE_BUCKET"
EMBEDDING_CACHE_PREFIX_ENV = "EMBEDDING_CACHE_PREFIX"

DEFAULT_SEMANTIC_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_SEMANTIC_EMBEDDING_PROVIDER = "bedrock"
LOCAL_EMBEDDING_PROVIDER = "local"
BEDROCK_EMBEDDING_PROVIDER = "bedrock"
DEFAULT_BEDROCK_EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
DEFAULT_BEDROCK_EMBEDDING_DIMENSIONS = 512
DEFAULT_EMBEDDING_CACHE_PREFIX = "embeddings/resume"
EMBEDDING_CACHE_SCHEMA_VERSION = "1.0"
DEFAULT_KEYWORD_SCORE_WEIGHT = 0.45
DEFAULT_SEMANTIC_SCORE_WEIGHT = 0.55

_embedding_provider = None
_local_embedding_model = None
bedrock_runtime_client = None

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
        resume_object = _read_resume_object_from_s3()
    except ValueError as exc:
        return _response(500, {"message": str(exc)})
    except Exception:
        logger.exception("Failed to read resume from S3")
        return _response(502, {"message": "Unable to read resume from S3"})

    result = compare_resume_to_job(
        resume_object["text"],
        job_description,
        resume_source=resume_object["source"],
    )
    return _response(200, result)


class EmbeddingProvider:
    model_id: str
    dimensions: int | None
    normalize: bool

    def encode(self, text: str) -> list[float]:
        raise NotImplementedError


class LocalSentenceTransformerEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: Any, model_id: str):
        self.model = model
        self.model_id = model_id
        self.dimensions = None
        self.normalize = False

    def encode(self, text: str) -> list[float]:
        return list(self.model.encode(text))


class BedrockEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        client: Any,
        model_id: str,
        dimensions: int,
        normalize: bool = True,
    ):
        self.client = client
        self.model_id = model_id
        self.dimensions = dimensions
        self.normalize = normalize

    def encode(self, text: str) -> list[float]:
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(
                {
                    "inputText": text,
                    "dimensions": self.dimensions,
                    "normalize": self.normalize,
                }
            ),
            accept="application/json",
            contentType="application/json",
        )
        payload = json.loads(response["body"].read().decode("utf-8"))
        return payload["embedding"]


class S3EmbeddingCache:
    def __init__(self, client: Any, bucket: str, prefix: str):
        self.client = client
        self.bucket = bucket
        self.prefix = prefix.strip("/")

    def cache_key(
        self,
        resume_source: dict[str, str],
        provider: EmbeddingProvider,
    ) -> str:
        cache_identity = {
            "schema_version": EMBEDDING_CACHE_SCHEMA_VERSION,
            "resume_bucket": resume_source["bucket"],
            "resume_key": resume_source["key"],
            "resume_etag": resume_source["etag"],
            "model_id": provider.model_id,
            "dimensions": provider.dimensions,
            "normalize": provider.normalize,
        }
        digest = hashlib.sha256(
            json.dumps(cache_identity, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return f"{self.prefix}/{digest}.json"

    def get(self, key: str) -> list[float] | None:
        try:
            s3_object = self.client.get_object(Bucket=self.bucket, Key=key)
        except Exception as exc:
            if _is_s3_cache_miss(exc):
                return None
            raise

        payload = json.loads(s3_object["Body"].read().decode("utf-8"))
        return payload["embedding"]["vector"]

    def put(
        self,
        key: str,
        resume_source: dict[str, str],
        provider: EmbeddingProvider,
        embedding: Sequence[float],
    ) -> None:
        payload = {
            "schema_version": EMBEDDING_CACHE_SCHEMA_VERSION,
            "source": resume_source,
            "embedding": {
                "provider": _semantic_embedding_provider_name(),
                "model_id": provider.model_id,
                "dimensions": provider.dimensions,
                "normalize": provider.normalize,
                "vector": list(embedding),
            },
        }
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json",
        )


def compare_resume_to_job(
    resume_text: str,
    job_description: str,
    resume_source: dict[str, str] | None = None,
) -> dict[str, Any]:
    resume_keywords = _extract_keywords(resume_text)
    job_keywords = _extract_keywords(job_description)

    if not job_keywords:
        return {"score": 0, "matching_keywords": [], "missing_keywords": []}

    matching_keywords = sorted(job_keywords & resume_keywords)
    missing_keywords = sorted(job_keywords - resume_keywords)
    keyword_score = calculate_keyword_score(resume_keywords, job_keywords)

    if not _semantic_matching_enabled():
        return {
            "score": keyword_score,
            "matching_keywords": matching_keywords,
            "missing_keywords": missing_keywords,
        }

    embedding_provider = _load_embedding_provider()
    embedding_cache = _load_embedding_cache() if resume_source else None
    semantic_score = calculate_semantic_score(
        resume_text,
        job_description,
        embedding_model=embedding_provider,
        resume_source=resume_source,
        embedding_cache=embedding_cache,
    )
    score = combine_scores(keyword_score, semantic_score)

    return {
        "score": score,
        "keyword_score": keyword_score,
        "semantic_score": semantic_score,
        "matching_keywords": matching_keywords,
        "missing_keywords": missing_keywords,
        "semantic_model": embedding_provider.model_id,
        "semantic_provider": _semantic_embedding_provider_name(),
        "weights": {
            "keyword": DEFAULT_KEYWORD_SCORE_WEIGHT,
            "semantic": DEFAULT_SEMANTIC_SCORE_WEIGHT,
        },
    }


def calculate_keyword_score(resume_keywords: set[str], job_keywords: set[str]) -> int:
    if not job_keywords:
        return 0

    matching_keywords = job_keywords & resume_keywords
    return round((len(matching_keywords) / len(job_keywords)) * 100)


def calculate_semantic_score(
    resume_text: str,
    job_description: str,
    embedding_model: Any | None = None,
    resume_source: dict[str, str] | None = None,
    embedding_cache: S3EmbeddingCache | None = None,
) -> int:
    model = embedding_model or _load_embedding_provider()
    resume_embedding = _get_resume_embedding(
        resume_text,
        resume_source,
        model,
        embedding_cache,
    )
    job_embedding = model.encode(job_description)
    similarity = max(0.0, cosine_similarity(resume_embedding, job_embedding))
    return round(similarity * 100)


def _get_resume_embedding(
    resume_text: str,
    resume_source: dict[str, str] | None,
    provider: EmbeddingProvider,
    embedding_cache: S3EmbeddingCache | None,
) -> list[float]:
    if resume_source is None or embedding_cache is None:
        return provider.encode(resume_text)

    cache_key = embedding_cache.cache_key(resume_source, provider)
    cached_embedding = embedding_cache.get(cache_key)
    if cached_embedding is not None:
        return cached_embedding

    resume_embedding = provider.encode(resume_text)
    embedding_cache.put(cache_key, resume_source, provider, resume_embedding)
    return resume_embedding


def combine_scores(
    keyword_score: int | float,
    semantic_score: int | float,
    keyword_weight: float = DEFAULT_KEYWORD_SCORE_WEIGHT,
    semantic_weight: float = DEFAULT_SEMANTIC_SCORE_WEIGHT,
) -> int:
    total_weight = keyword_weight + semantic_weight
    if total_weight <= 0:
        raise ValueError("score weights must sum to a positive value")

    weighted_score = (
        (keyword_score * keyword_weight) + (semantic_score * semantic_weight)
    ) / total_weight
    return round(weighted_score)


def cosine_similarity(
    left_embedding: Sequence[float],
    right_embedding: Sequence[float],
) -> float:
    if len(left_embedding) != len(right_embedding):
        raise ValueError("embeddings must have the same dimension")

    dot_product = sum(left * right for left, right in zip(left_embedding, right_embedding))
    left_magnitude = sum(value * value for value in left_embedding) ** 0.5
    right_magnitude = sum(value * value for value in right_embedding) ** 0.5

    if left_magnitude == 0 or right_magnitude == 0:
        return 0.0

    return dot_product / (left_magnitude * right_magnitude)


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
    return _read_resume_object_from_s3()["text"]


def _read_resume_object_from_s3() -> dict[str, Any]:
    bucket = os.environ.get(RESUME_BUCKET_ENV)
    key = os.environ.get(RESUME_KEY_ENV)

    if not bucket or not key:
        raise ValueError(f"{RESUME_BUCKET_ENV} and {RESUME_KEY_ENV} must be configured")

    s3_object = s3_client.get_object(Bucket=bucket, Key=key)
    etag = s3_object.get("ETag", "").strip('"') or "unknown"
    return {
        "text": s3_object["Body"].read().decode("utf-8"),
        "source": {
            "bucket": bucket,
            "key": key,
            "etag": etag,
        },
    }


def _semantic_matching_enabled() -> bool:
    return os.environ.get(SEMANTIC_MATCHING_ENABLED_ENV, "false").casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _semantic_model_name() -> str:
    return os.environ.get(SEMANTIC_MODEL_NAME_ENV, DEFAULT_SEMANTIC_MODEL_NAME)


def _semantic_embedding_provider_name() -> str:
    return os.environ.get(
        SEMANTIC_EMBEDDING_PROVIDER_ENV,
        DEFAULT_SEMANTIC_EMBEDDING_PROVIDER,
    ).casefold()


def _bedrock_embedding_model_id() -> str:
    return os.environ.get(
        BEDROCK_EMBEDDING_MODEL_ID_ENV,
        DEFAULT_BEDROCK_EMBEDDING_MODEL_ID,
    )


def _bedrock_embedding_dimensions() -> int:
    value = os.environ.get(
        BEDROCK_EMBEDDING_DIMENSIONS_ENV,
        str(DEFAULT_BEDROCK_EMBEDDING_DIMENSIONS),
    )
    try:
        dimensions = int(value)
    except ValueError as exc:
        raise ValueError(f"{BEDROCK_EMBEDDING_DIMENSIONS_ENV} must be an integer") from exc

    if dimensions <= 0:
        raise ValueError(f"{BEDROCK_EMBEDDING_DIMENSIONS_ENV} must be positive")

    return dimensions


def _embedding_cache_bucket() -> str | None:
    return os.environ.get(EMBEDDING_CACHE_BUCKET_ENV) or os.environ.get(
        RESUME_BUCKET_ENV
    )


def _embedding_cache_prefix() -> str:
    return os.environ.get(EMBEDDING_CACHE_PREFIX_ENV, DEFAULT_EMBEDDING_CACHE_PREFIX)


def _load_embedding_provider() -> EmbeddingProvider:
    global _embedding_provider

    if _embedding_provider is None:
        provider_name = _semantic_embedding_provider_name()
        if provider_name == BEDROCK_EMBEDDING_PROVIDER:
            _embedding_provider = BedrockEmbeddingProvider(
                _bedrock_runtime_client(),
                _bedrock_embedding_model_id(),
                _bedrock_embedding_dimensions(),
            )
        elif provider_name == LOCAL_EMBEDDING_PROVIDER:
            _embedding_provider = _load_local_embedding_provider()
        else:
            raise ValueError(
                f"{SEMANTIC_EMBEDDING_PROVIDER_ENV} must be "
                f"{BEDROCK_EMBEDDING_PROVIDER!r} or {LOCAL_EMBEDDING_PROVIDER!r}"
            )

    return _embedding_provider


def _load_local_embedding_provider() -> LocalSentenceTransformerEmbeddingProvider:
    model_id = _semantic_model_name()
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Local semantic matching requires the optional sentence-transformers "
            "package for validation."
        ) from exc

    return LocalSentenceTransformerEmbeddingProvider(SentenceTransformer(model_id), model_id)


def _bedrock_runtime_client() -> Any:
    global bedrock_runtime_client

    if bedrock_runtime_client is None:
        bedrock_runtime_client = boto3.client("bedrock-runtime")

    return bedrock_runtime_client


def _load_embedding_cache() -> S3EmbeddingCache:
    bucket = _embedding_cache_bucket()
    if not bucket:
        raise ValueError(
            f"{EMBEDDING_CACHE_BUCKET_ENV} or {RESUME_BUCKET_ENV} must be configured"
        )

    return S3EmbeddingCache(s3_client, bucket, _embedding_cache_prefix())


def _is_s3_cache_miss(exc: Exception) -> bool:
    error_code = (
        getattr(exc, "response", {})
        .get("Error", {})
        .get("Code")
    )
    return error_code in {"NoSuchKey", "NotFound", "404"} or isinstance(
        exc, FileNotFoundError
    )


def _load_embedding_model() -> Any:
    global _local_embedding_model

    if _local_embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Semantic matching requires the optional sentence-transformers "
                "package for local validation."
            ) from exc

        _local_embedding_model = SentenceTransformer(_semantic_model_name())

    return _local_embedding_model


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
