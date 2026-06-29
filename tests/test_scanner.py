"""scanner.pyのテスト。sample_appは意図的に全項目未実装の脆弱な状態。"""

from pathlib import Path

import pytest

from sentinel_api.scanner import scan

SAMPLE_APP = Path(__file__).parent / "fixtures" / "sample_app"


@pytest.fixture(scope="module")
def result():
    return scan(str(SAMPLE_APP))


def test_scan_returns_required_keys(result):
    assert "auto_fix" in result
    assert "manual_check" in result


def test_auto_fix_item_count(result):
    assert len(result["auto_fix"]) == 7


def test_manual_check_item_count(result):
    assert len(result["manual_check"]) == 3


def test_auto_fix_item_names(result):
    names = {item["item"] for item in result["auto_fix"]}
    assert names == {
        "パスワードハッシュ化",
        "SQLインジェクション対策",
        "エラー情報の外部露出防止",
        "CORS設定",
        "レート制限",
        "HTTPセキュリティヘッダ",
        "シークレット直書き検出",
    }


def test_manual_check_item_names(result):
    names = {item["item"] for item in result["manual_check"]}
    assert names == {
        "JWT検証・有効期限",
        "ログイン試行回数制限",
        "依存パッケージの脆弱性",
    }


def test_auto_fix_all_missing(result):
    for item in result["auto_fix"]:
        assert item["status"] == "missing", (
            f"[{item['item']}] expected 'missing', got '{item['status']}' (files={item['files']})"
        )


def test_manual_check_all_missing(result):
    for item in result["manual_check"]:
        assert item["status"] == "missing", (
            f"[{item['item']}] expected 'missing', got '{item['status']}'"
        )


def test_each_item_has_files_key(result):
    for item in result["auto_fix"] + result["manual_check"]:
        assert "files" in item, f"{item['item']} に 'files' キーがない"


def test_manual_check_has_detail(result):
    for item in result["manual_check"]:
        assert "detail" in item, f"{item['item']} に 'detail' キーがない"


def test_password_hashing_file_is_auth(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "パスワードハッシュ化")
    assert "auth.py" in item["files"][0]


def test_hardcoded_secret_found_in_auth(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "シークレット直書き検出")
    assert any("auth.py" in f for f in item["files"])
