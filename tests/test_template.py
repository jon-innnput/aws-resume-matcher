from pathlib import Path


def template_text():
    return (Path(__file__).resolve().parents[1] / "template.yaml").read_text()


def test_semantic_matching_is_disabled_by_default_in_sam_template():
    template = template_text()

    assert "SemanticMatchingEnabled:" in template
    assert 'Default: "false"' in template
    assert "SEMANTIC_MATCHING_ENABLED: !Ref SemanticMatchingEnabled" in template


def test_sam_template_wires_bedrock_embedding_configuration():
    template = template_text()

    assert "SemanticEmbeddingProvider:" in template
    assert "Default: bedrock" in template
    assert "BedrockEmbeddingModelId:" in template
    assert "Default: amazon.titan-embed-text-v2:0" in template
    assert "BedrockEmbeddingDimensions:" in template
    assert "Default: 512" in template
    assert "SEMANTIC_EMBEDDING_PROVIDER: !Ref SemanticEmbeddingProvider" in template
    assert "BEDROCK_EMBEDDING_MODEL_ID: !Ref BedrockEmbeddingModelId" in template
    assert 'BEDROCK_EMBEDDING_DIMENSIONS: !Sub "${BedrockEmbeddingDimensions}"' in template


def test_sam_template_scopes_bedrock_and_embedding_cache_permissions():
    template = template_text()

    assert "Sid: InvokeConfiguredBedrockEmbeddingModel" in template
    assert "bedrock:InvokeModel" in template
    assert (
        "arn:${AWS::Partition}:bedrock:${AWS::Region}::foundation-model/"
        "${BedrockEmbeddingModelId}"
    ) in template
    assert "Sid: ListEmbeddingCachePrefix" in template
    assert "s3:ListBucket" in template
    assert "arn:${AWS::Partition}:s3:::${CacheBucket}" in template
    assert "StringLike:" in template
    assert "s3:prefix:" in template
    assert "- !Sub ${EmbeddingCachePrefix}/*" in template
    assert "Sid: ReadWriteEmbeddingCache" in template
    assert "s3:GetObject" in template
    assert "s3:PutObject" in template
    assert "arn:${AWS::Partition}:s3:::${CacheBucket}/${EmbeddingCachePrefix}/*" in template


def test_sam_template_enables_cors_for_frontend_demo():
    template = template_text()

    assert "CorsConfiguration:" in template
    assert "AllowOrigins:" in template
    assert '- "*"' in template
    assert "AllowMethods:" in template
    assert "- OPTIONS" in template
    assert "- POST" in template
    assert "AllowHeaders:" in template
    assert "- Content-Type" in template
