"""パッケージの自動インストールとPythonバージョン確認を行うモジュール。"""

import importlib.util
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()

PACKAGE_REASONS = {
    "slowapi": "レート制限の実装に必要なため",
    "passlib": "パスワードハッシュ化の実装に必要なため",
    "anthropic": "Claude APIの呼び出しに必要なため",
    "typer": "CLIの動作に必要なため",
    "httpx": "GitHub API通信に必要なため",
    "rich": "出力整形に必要なため",
    "python-dotenv": "環境変数の読み込みに必要なため",
    "pytest": "テストの実行に必要なため",
}

# パッケージ名とimport名が異なるもののマッピング
_IMPORT_NAMES: dict[str, str] = {
    "python-dotenv": "dotenv",
    "pytest-asyncio": "pytest_asyncio",
}


def _pkg_name(raw: str) -> str:
    """requirements.txtの1行からパッケージ名を取得する（extras・バージョン指定除去）。"""
    name = raw.strip().split("[")[0]
    for sep in ("==", ">=", "<=", "!=", "~=", ">", "<"):
        name = name.split(sep)[0]
    return name.strip()


def _import_name(pkg: str) -> str:
    """パッケージ名から実際のimport名を返す。"""
    return _IMPORT_NAMES.get(pkg, pkg.replace("-", "_"))


def _is_installed(pkg: str) -> bool:
    """importlibでパッケージがインポート可能か確認する。"""
    module = _import_name(pkg)
    try:
        return importlib.util.find_spec(module) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def check_python_version() -> bool:
    """Python 3.11以上かチェックする。未満の場合はrichで警告を表示してFalseを返す。"""
    if sys.version_info < (3, 11):
        console.print(
            f"[yellow]⚠️  Python 3.11以上が必要です（現在: {sys.version.split()[0]}）[/yellow]"
        )
        return False
    return True


def check_and_install(requirements_path: str | None = None) -> list[dict]:
    """requirements.txtを読み込みパッケージの状態を確認・インストールする。

    戻り値の各要素:
      {"package": str, "action": "installed"|"skipped"|"failed"|"already_installed", "reason": str}
    """
    if requirements_path is None:
        req_file = Path(__file__).parent.parent / "requirements.txt"
    else:
        req_file = Path(requirements_path)

    if not req_file.exists():
        console.print("[yellow]⚠️  requirements.txt が見つかりません[/yellow]")
        return []

    raw_lines = req_file.read_text(encoding="utf-8").splitlines()
    packages = [
        _pkg_name(line)
        for line in raw_lines
        if line.strip() and not line.startswith("#")
    ]

    missing = [pkg for pkg in packages if not _is_installed(pkg)]
    results: list[dict] = []

    if missing:
        table = Table(title="未インストールのパッケージ")
        table.add_column("パッケージ")
        table.add_column("理由")
        for pkg in missing:
            table.add_row(pkg, PACKAGE_REASONS.get(pkg, ""))
        console.print(table)

        answer = Prompt.ask("インストールしますか？(y/n)", default="n")
        if answer.lower() == "y":
            for pkg in missing:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", pkg],
                        check=True,
                        capture_output=True,
                    )
                    results.append({
                        "package": pkg,
                        "action": "installed",
                        "reason": PACKAGE_REASONS.get(pkg, ""),
                    })
                except subprocess.CalledProcessError:
                    results.append({
                        "package": pkg,
                        "action": "failed",
                        "reason": PACKAGE_REASONS.get(pkg, ""),
                    })
        else:
            console.print("[yellow]⚠️  未インストールのパッケージがあります。処理を続行します。[/yellow]")
            for pkg in missing:
                results.append({
                    "package": pkg,
                    "action": "skipped",
                    "reason": PACKAGE_REASONS.get(pkg, ""),
                })

    for pkg in packages:
        if pkg not in missing:
            results.append({
                "package": pkg,
                "action": "already_installed",
                "reason": PACKAGE_REASONS.get(pkg, ""),
            })

    return results
