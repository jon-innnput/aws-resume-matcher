import importlib.util
import sys
import types
from pathlib import Path

import pytest


class StubS3Client:
    def get_object(self, **kwargs):
        raise AssertionError("Unexpected AWS S3 call during tests")


@pytest.fixture
def app_module(monkeypatch):
    monkeypatch.delenv("SEMANTIC_MATCHING_ENABLED", raising=False)
    monkeypatch.delenv("SEMANTIC_MODEL_NAME", raising=False)
    boto3_stub = types.SimpleNamespace(client=lambda service_name: StubS3Client())
    monkeypatch.setitem(sys.modules, "boto3", boto3_stub)

    module_path = Path(__file__).resolve().parents[1] / "lambda" / "app.py"
    spec = importlib.util.spec_from_file_location("resume_matcher_app", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["resume_matcher_app"] = module
    spec.loader.exec_module(module)
    return module
