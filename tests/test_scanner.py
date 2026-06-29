"""scanner.pyのテスト。"""

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
        "JWT認証検証・有効期限",
        "ログイン試行回数制限",
        "依存パッケージの脆弱性",
    }


def test_each_item_has_files_key(result):
    for item in result["auto_fix"] + result["manual_check"]:
        assert "files" in item, f"{item['item']} に 'files' キーがない"


def test_files_entries_have_path_and_content(result):
    for item in result["auto_fix"] + result["manual_check"]:
        for f in item["files"]:
            assert "path" in f, f"{item['item']} の files エントリに 'path' キーがない"
            assert "content" in f, f"{item['item']} の files エントリに 'content' キーがない"


# sample_appにauth.pyが存在する項目
def test_password_hashing_files_not_empty(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "パスワードハッシュ化")
    assert len(item["files"]) > 0


def test_error_exposure_files_not_empty(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "エラー情報の外部露出防止")
    assert len(item["files"]) > 0


def test_cors_files_not_empty(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "CORS設定")
    assert len(item["files"]) > 0


def test_rate_limiting_files_not_empty(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "レート制限")
    assert len(item["files"]) > 0


def test_security_headers_files_not_empty(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "HTTPセキュリティヘッダ")
    assert len(item["files"]) > 0


def test_hardcoded_secret_files_not_empty(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "シークレット直書き検出")
    assert len(item["files"]) > 0


def test_jwt_files_not_empty(result):
    item = next(i for i in result["manual_check"] if i["item"] == "JWT認証検証・有効期限")
    assert len(item["files"]) > 0


def test_login_attempts_files_not_empty(result):
    item = next(i for i in result["manual_check"] if i["item"] == "ログイン試行回数制限")
    assert len(item["files"]) > 0


def test_password_hashing_file_is_auth(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "パスワードハッシュ化")
    assert any("auth.py" in f["path"] for f in item["files"])


def test_hardcoded_secret_found_in_auth(result):
    item = next(i for i in result["auto_fix"] if i["item"] == "シークレット直書き検出")
    assert any("auth.py" in f["path"] for f in item["files"])
