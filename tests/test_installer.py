"""installer.pyのテスト。"""

import sys
from pathlib import Path
from unittest.mock import patch

from sentinel_api import installer
from sentinel_api.reporter import generate_report


def test_check_python_version_returns_true_for_311():
    """Python 3.11〜3.13の場合にTrueを返すこと。"""
    with patch.object(sys, "version_info", (3, 12, 0)):
        assert installer.check_python_version() is True


def test_check_python_version_returns_false_and_warns_for_314(capsys):
    """Python 3.14以上の場合にFalseを返し、警告が出ること。"""
    with patch.object(sys, "version_info", (3, 14, 0)):
        result = installer.check_python_version()
    assert result is False


def test_check_python_version_returns_false_for_310():
    """Python 3.11未満の場合にFalseを返すこと。"""
    with patch.object(sys, "version_info", (3, 10, 0)):
        assert installer.check_python_version() is False


def test_check_and_install_already_installed(tmp_path):
    """インストール済みのパッケージにaction='already_installed'を返すこと。"""
    req = tmp_path / "requirements.txt"
    req.write_text("rich\ntyper\n", encoding="utf-8")

    results = installer.check_and_install(requirements_path=str(req))

    actions = {r["package"]: r["action"] for r in results}
    assert actions["rich"] == "already_installed"
    assert actions["typer"] == "already_installed"


def test_check_and_install_returns_reason(tmp_path):
    """PACKAGE_REASONSに定義されたパッケージにreasonが付くこと。"""
    req = tmp_path / "requirements.txt"
    req.write_text("rich\n", encoding="utf-8")

    results = installer.check_and_install(requirements_path=str(req))

    assert results[0]["reason"] == installer.PACKAGE_REASONS["rich"]


def test_check_and_install_missing_requirements_file():
    """requirements.txtが見つからない場合は空リストを返すこと。"""
    results = installer.check_and_install(requirements_path="/nonexistent/requirements.txt")
    assert results == []


def test_generate_report_with_install_results(tmp_path):
    """install_resultsを渡すと🔧セクションが生成されること。"""
    output = tmp_path / "SECURITY_STATUS.md"
    install_results = [
        {"package": "slowapi", "action": "installed", "reason": "レート制限の実装に必要なため"},
        {"package": "passlib", "action": "installed", "reason": "パスワードハッシュ化の実装に必要なため"},
    ]

    generate_report([], output_path=str(output), install_results=install_results)

    content = output.read_text(encoding="utf-8")
    assert "🔧 自動インストール済み" in content
    assert "slowapi" in content
    assert "passlib" in content
    assert "レート制限の実装に必要なため" in content


def test_generate_report_no_install_section_when_none(tmp_path):
    """install_results=Noneの場合は🔧セクションが生成されないこと。"""
    output = tmp_path / "SECURITY_STATUS.md"
    generate_report([], output_path=str(output), install_results=None)

    content = output.read_text(encoding="utf-8")
    assert "🔧 自動インストール済み" not in content


def test_generate_report_no_install_section_when_all_already_installed(tmp_path):
    """action='already_installed'のみの場合は🔧セクションが生成されないこと。"""
    output = tmp_path / "SECURITY_STATUS.md"
    install_results = [
        {"package": "rich", "action": "already_installed", "reason": "出力整形に必要なため"},
    ]

    generate_report([], output_path=str(output), install_results=install_results)

    content = output.read_text(encoding="utf-8")
    assert "🔧 自動インストール済み" not in content
