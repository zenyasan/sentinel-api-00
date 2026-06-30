"""__main__.py (runコマンド) のテスト。"""

import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from sentinel_api.__main__ import app

runner = CliRunner()
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_app"

requires_api_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


def test_run_missing_path():
    """存在しないパスを指定するとexit code 1で終了する。"""
    result = runner.invoke(app, ["run", "/nonexistent/path/xyz_sentinel_99999"])
    assert result.exit_code == 1
    assert "存在しません" in result.output


def test_run_missing_api_key(tmp_path):
    """ANTHROPIC_API_KEY未設定時はエラーメッセージを出してexit code 1で終了する。"""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        result = runner.invoke(app, ["run", str(tmp_path)])
    assert result.exit_code == 1
    assert "ANTHROPIC_API_KEY" in result.output


def test_dry_run_no_report_generated(tmp_path):
    """dry_run=True の場合にSECURITY_STATUS.mdが生成されない。"""
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    mock_scan = {
        "auto_fix": [{"item": "CORS設定", "files": [{"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()\n"}]}],
        "manual_check": [],
    }
    mock_judge = {
        "item": "CORS設定",
        "status": "missing",
        "plan": [{"file": "main.py", "line": 3, "code": "# cors"}],
        "detail": "未実装",
    }

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch("sentinel_api.ai_client.judge_and_plan", return_value=mock_judge), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        result = runner.invoke(app, ["run", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0
    assert not (tmp_path / "SECURITY_STATUS.md").exists()


def test_dry_run_shows_planned_items(tmp_path):
    """dry_runで未実装項目が出力に含まれることを確認する。"""
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    mock_scan = {
        "auto_fix": [{"item": "CORS設定", "files": []}],
        "manual_check": [],
    }
    mock_judge = {
        "item": "CORS設定",
        "status": "missing",
        "plan": [{"file": "main.py", "line": 3, "code": "# cors"}],
        "detail": "",
    }

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch("sentinel_api.ai_client.judge_and_plan", return_value=mock_judge), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        result = runner.invoke(app, ["run", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0
    assert "CORS設定" in result.output
    assert "実装します" in result.output


def test_dry_run_no_file_write(tmp_path):
    """dry_run=True の場合にソースファイルへの書き込みが発生しない。"""
    original = "from fastapi import FastAPI\napp = FastAPI()\n"
    main_py = tmp_path / "main.py"
    main_py.write_text(original)

    mock_scan = {
        "auto_fix": [{"item": "CORS設定", "files": [{"path": "main.py", "content": original}]}],
        "manual_check": [],
    }
    mock_judge = {
        "item": "CORS設定",
        "status": "missing",
        "plan": [{"file": "main.py", "line": 3, "code": "# cors"}],
        "detail": "",
    }

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch("sentinel_api.ai_client.judge_and_plan", return_value=mock_judge), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        runner.invoke(app, ["run", str(tmp_path), "--dry-run"])

    assert main_py.read_text() == original
    assert not (tmp_path / "main.py.bak").exists()


def test_normal_run_generates_report(tmp_path):
    """通常実行でSECURITY_STATUS.mdが生成されることを確認する。"""
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    mock_scan = {
        "auto_fix": [{"item": "CORS設定", "files": [{"path": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()\n"}]}],
        "manual_check": [{"item": "JWT認証検証", "files": []}],
    }

    def judge_side_effect(item, files):
        if item == "CORS設定":
            return {"item": item, "status": "missing", "plan": [{"file": "main.py", "line": 3, "code": "# cors added"}], "detail": "未実装"}
        return {"item": item, "status": "ok", "plan": None, "detail": "実装済み"}

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch("sentinel_api.ai_client.judge_and_plan", side_effect=judge_side_effect), \
         patch("sentinel_api.ai_client.apply_fix", return_value="from fastapi import FastAPI\napp = FastAPI()\n# cors\n"), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        result = runner.invoke(app, ["run", str(tmp_path)])

    assert result.exit_code == 0, f"Output:\n{result.output}"
    assert (tmp_path / "SECURITY_STATUS.md").exists()


def test_normal_run_report_message(tmp_path):
    """通常実行後にレポート生成メッセージが出力されることを確認する。"""
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    mock_scan = {"auto_fix": [], "manual_check": []}

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        result = runner.invoke(app, ["run", str(tmp_path)])

    assert "レポートを生成しました" in result.output


def test_ok_items_show_skip_message(tmp_path):
    """status=okの項目はスキップと表示されることを確認する。"""
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    mock_scan = {
        "auto_fix": [{"item": "CORS設定", "files": []}],
        "manual_check": [],
    }
    mock_judge = {"item": "CORS設定", "status": "ok", "plan": None, "detail": "実装済み"}

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch("sentinel_api.ai_client.judge_and_plan", return_value=mock_judge), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        result = runner.invoke(app, ["run", str(tmp_path)])

    assert result.exit_code == 0
    assert "スキップ" in result.output


def test_incomplete_item_shows_warning(tmp_path):
    """status=incompleteの項目に警告メッセージが表示されることを確認する。"""
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    mock_scan = {
        "auto_fix": [{"item": "CORS設定", "files": []}],
        "manual_check": [],
    }
    mock_judge = {"item": "CORS設定", "status": "incomplete", "plan": None, "detail": "不完全"}

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch("sentinel_api.ai_client.judge_and_plan", return_value=mock_judge), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        result = runner.invoke(app, ["run", str(tmp_path)])

    assert result.exit_code == 0
    assert "不完全な実装を検出" in result.output


def test_api_error_per_item_continues(tmp_path):
    """個別のAPIエラーはスキップされ処理が継続してレポートが生成されることを確認する。"""
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    mock_scan = {
        "auto_fix": [
            {"item": "CORS設定", "files": []},
            {"item": "レート制限", "files": []},
        ],
        "manual_check": [],
    }

    def judge_side_effect(item, files):
        if item == "CORS設定":
            return {"item": item, "status": "error", "plan": None, "detail": "APIタイムアウト"}
        return {"item": item, "status": "ok", "plan": None, "detail": ""}

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch("sentinel_api.ai_client.judge_and_plan", side_effect=judge_side_effect), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        result = runner.invoke(app, ["run", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / "SECURITY_STATUS.md").exists()


def test_scan_start_message_contains_path(tmp_path):
    """スキャン開始メッセージにプロジェクトパスが含まれることを確認する。"""
    mock_scan = {"auto_fix": [], "manual_check": []}

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        result = runner.invoke(app, ["run", str(tmp_path)])

    assert "スキャン中" in result.output
    # rich が長いパスを改行・エスケープするため、改行を除いた文字列で確認する
    flat = result.output.replace("\n", "").replace("\\\\", "\\")
    assert tmp_path.name in flat


def test_plan_file_cleaned_up_after_run(tmp_path):
    """通常実行後に.sentinel_plan.jsonが削除されることを確認する。"""
    (tmp_path / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")

    mock_scan = {
        "auto_fix": [{"item": "CORS設定", "files": []}],
        "manual_check": [],
    }
    mock_judge = {"item": "CORS設定", "status": "ok", "plan": None, "detail": ""}

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch("sentinel_api.ai_client.judge_and_plan", return_value=mock_judge), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        runner.invoke(app, ["run", str(tmp_path)])

    assert not (tmp_path / ".sentinel_plan.json").exists()


def test_plan_file_cleaned_up_after_dry_run(tmp_path):
    """dry_run後に.sentinel_plan.jsonが削除されることを確認する。"""
    mock_scan = {"auto_fix": [], "manual_check": []}

    with patch("sentinel_api.scanner.scan", return_value=mock_scan), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "dummy-key"}):
        runner.invoke(app, ["run", str(tmp_path), "--dry-run"])

    assert not (tmp_path / ".sentinel_plan.json").exists()


# ---- Integration tests (require real ANTHROPIC_API_KEY) ----

@requires_api_key
def test_integration_dry_run():
    """実際のAPIキーでsample_appに対してdry-runが正常に動作する。"""
    result = runner.invoke(app, ["run", str(FIXTURE_DIR), "--dry-run"])
    assert result.exit_code == 0, f"Exit code: {result.exit_code}\nOutput:\n{result.output}"
    assert "スキャン中" in result.output


@requires_api_key
def test_integration_full_run(tmp_path):
    """実際のAPIキーで通常実行しSECURITY_STATUS.mdが生成される。"""
    sample = tmp_path / "sample_app"
    shutil.copytree(str(FIXTURE_DIR), str(sample))

    result = runner.invoke(app, ["run", str(sample)])
    assert result.exit_code == 0, f"Exit code: {result.exit_code}\nOutput:\n{result.output}"
    assert (sample / "SECURITY_STATUS.md").exists(), "SECURITY_STATUS.md was not generated"
