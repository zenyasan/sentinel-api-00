"""patcher.pyのテスト。"""

import os
import pytest
from sentinel_api.patcher import save_plan, load_plan, write_file, cleanup


PLAN_PATH = ".test_sentinel_plan.json"


def test_save_and_load_plan(tmp_path):
    plan_file = str(tmp_path / "plan.json")
    results = [
        {"file": "auth.py", "item": "JWT認証検証", "action": "add"},
        {"file": "main.py", "item": "CORS設定", "action": "modify"},
    ]
    save_plan(results, plan_file)
    loaded = load_plan(plan_file)
    assert loaded == results


def test_write_file_creates_file(tmp_path):
    target = str(tmp_path / "new_file.py")
    write_file(target, "print('hello')\n")
    assert os.path.exists(target)
    with open(target, encoding="utf-8") as f:
        assert f.read() == "print('hello')\n"


def test_write_file_creates_backup(tmp_path):
    target = str(tmp_path / "auth.py")
    with open(target, "w", encoding="utf-8") as f:
        f.write("original content\n")

    write_file(target, "modified content\n")

    bak = target + ".bak"
    assert os.path.exists(bak)
    with open(bak, encoding="utf-8") as f:
        assert f.read() == "original content\n"
    with open(target, encoding="utf-8") as f:
        assert f.read() == "modified content\n"


def test_write_file_no_backup_when_not_exists(tmp_path):
    target = str(tmp_path / "brand_new.py")
    write_file(target, "new content\n")
    assert os.path.exists(target)
    assert not os.path.exists(target + ".bak")


def test_cleanup_removes_plan_file(tmp_path):
    plan_file = str(tmp_path / "plan.json")
    save_plan([{"item": "test"}], plan_file)
    assert os.path.exists(plan_file)
    cleanup(plan_file)
    assert not os.path.exists(plan_file)


def test_cleanup_no_error_when_file_missing(tmp_path):
    plan_file = str(tmp_path / "nonexistent.json")
    cleanup(plan_file)  # should not raise
