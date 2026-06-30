"""reporter.pyのテスト。"""

from datetime import datetime
from pathlib import Path

import pytest

from sentinel_api.reporter import generate_report


@pytest.fixture
def sample_results():
    return [
        {"item": "パスワードハッシュ化", "status": "fixed", "file": "auth.py", "detail": "bcryptでハッシュ化を追加しました。"},
        {"item": "CORS設定", "status": "fixed", "file": "main.py", "detail": "CORSミドルウェアを設定しました。"},
        {"item": "JWT認証検証", "status": "incomplete", "file": "auth.py", "detail": "実装はあるが有効期限が未設定"},
        {"item": "ログイン試行回数制限", "status": "missing", "file": None, "detail": "対象ファイルが見つかりませんでした。"},
        {"item": "SQLインジェクション対策", "status": "ok", "file": "db.py", "detail": "ORMを使ったパラメータ化クエリが実装されています。"},
        {"item": "レート制限", "status": "error", "file": "main.py", "detail": "ライブラリが見つかりません"},
    ]


@pytest.fixture
def report_file(tmp_path, sample_results):
    project_path = str(tmp_path / "sample_app")
    Path(project_path).mkdir()
    path = generate_report(sample_results, project_path=project_path)
    yield path
    Path(path).unlink(missing_ok=True)


def test_file_is_created(report_file):
    assert Path(report_file).exists()


def test_output_in_reports_dir(report_file):
    assert Path(report_file).parent.name == "reports"


def test_output_extension_is_txt(report_file):
    assert Path(report_file).suffix == ".txt"


def test_filename_format(report_file):
    date_str = datetime.now().strftime("%Y%m%d")
    assert Path(report_file).name == f"{date_str}_sample_app_SECURITY_STATUS.txt"


def test_all_four_sections_present(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    assert "自動実装済み" in content
    assert "要手動対応（実装はあるが確認が必要）" in content
    assert "未実装（対象ファイルが見つかりませんでした）" in content
    assert "追加で検討推奨（このツールの対象外）" in content


def test_section_separator_equals(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    assert "=" * 50 in content


def test_item_separator_hyphens(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    assert "-" * 50 in content


def test_no_markdown_symbols(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    assert "**" not in content


def test_item_names_in_report(report_file, sample_results):
    content = Path(report_file).read_text(encoding="utf-8")
    for r in sample_results:
        assert r["item"] in content, f"{r['item']} がレポートに含まれていない"


def test_fixed_items_in_implemented_section(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    implemented_section = content.split("自動実装済み")[1].split("要手動対応")[0]
    assert "パスワードハッシュ化" in implemented_section
    assert "CORS設定" in implemented_section


def test_ok_items_show_no_change_message(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    assert "実装済みのため変更なし" in content


def test_incomplete_in_warning_section(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    warning_section = content.split("要手動対応（実装はあるが確認が必要）")[1].split("未実装（対象ファイルが見つかりませんでした）")[0]
    assert "JWT認証検証" in warning_section


def test_error_in_warning_section(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    warning_section = content.split("要手動対応（実装はあるが確認が必要）")[1].split("未実装（対象ファイルが見つかりませんでした）")[0]
    assert "レート制限" in warning_section


def test_missing_in_not_implemented_section(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    not_impl_section = content.split("未実装（対象ファイルが見つかりませんでした）")[1].split("追加で検討推奨")[0]
    assert "ログイン試行回数制限" in not_impl_section


def test_advisory_section_is_fixed_text(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    assert "HTTPS強制" in content
    assert "pip-audit" in content
    assert "uvicorn" in content


def test_timestamp_in_report(report_file):
    content = Path(report_file).read_text(encoding="utf-8")
    assert "生成日時: " in content


def test_returns_absolute_path(tmp_path, sample_results):
    project_path = str(tmp_path / "my_project")
    Path(project_path).mkdir()
    path = generate_report(sample_results, project_path=project_path)
    assert Path(path).is_absolute()
    Path(path).unlink(missing_ok=True)
