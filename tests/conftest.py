"""テスト共通設定。test_main.pyではinstaller関数をモック化する。"""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _mock_installer_for_main_tests(request):
    """test_main.pyのテストではinstaller関数をモック化してCI環境でも動作させる。"""
    if request.fspath.basename == "test_main.py":
        with patch("sentinel_api.installer.check_python_version", return_value=True), \
             patch("sentinel_api.installer.check_and_install", return_value=[]):
            yield
    else:
        yield
