"""ai_client.pyのテスト。"""

import os
from pathlib import Path

import pytest

from sentinel_api.ai_client import apply_fix, judge_and_plan

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_app"
SAMPLE_AUTH_CONTENT = (FIXTURE_DIR / "auth.py").read_text(encoding="utf-8")
SAMPLE_FILES = [{"path": "auth.py", "content": SAMPLE_AUTH_CONTENT}]

requires_api_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


@requires_api_key
def test_judge_and_plan_password_hashing_missing():
    result = judge_and_plan("パスワードハッシュ化", SAMPLE_FILES)
    assert result["status"] == "missing", f"Expected 'missing', got: {result}"


@requires_api_key
def test_judge_and_plan_returns_plan():
    result = judge_and_plan("パスワードハッシュ化", SAMPLE_FILES)
    assert result.get("plan") is not None, f"Expected plan to be present, got: {result}"
    assert len(result["plan"]) > 0, "plan should contain at least one item"


@requires_api_key
def test_apply_fix_returns_string():
    judge_result = judge_and_plan("パスワードハッシュ化", SAMPLE_FILES)
    assert judge_result.get("plan"), f"No plan returned: {judge_result}"

    plan_item = judge_result["plan"][0]
    result = apply_fix("auth.py", SAMPLE_AUTH_CONTENT, plan_item)

    assert isinstance(result, str), "apply_fix should return a string"
    assert len(result) > 0, "apply_fix returned empty string"
