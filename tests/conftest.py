import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["JGB_ESTIMATOR"] = "chars4"  # deterministic counts in tests
os.environ.pop("TYPESAFE_API_KEY", None)  # tests never call the network

from jevgb.config import load_config  # noqa: E402


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("JGB_HOME", str(tmp_path))
    c = load_config(ROOT / "config.example.yaml", {"classifier": "local"})
    return c
