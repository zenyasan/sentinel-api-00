"""Markdownレポートを生成するモジュール。"""

from datetime import datetime
from pathlib import Path


_ADVISORY_SECTION = """## 💡 追加で検討推奨（このツール対象外）
- HTTPS強制：VercelやRailwayを使えば自動で対応できます
- ログ・監視：構造化ログの導入を検討してください
- 依存パッケージの定期スキャン：CIでpip-auditの実行を推奨します
- リバースプロキシ運用：uvicornを直接公開しないことを推奨します
"""

_REPORTS_DIR = Path(__file__).parent.parent / "reports"


def generate_report(
    results: list[dict],
    project_path: str,
    install_results: list[dict] | None = None,
    python_version_warning: str | None = None,
) -> str:
    """全項目の処理結果を受け取りMarkdownファイルを生成する。戻り値：生成したレポートファイルの絶対パス。"""
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now.strftime("%Y%m%d")
    folder_name = Path(project_path).name

    _REPORTS_DIR.mkdir(exist_ok=True)
    output_path = _REPORTS_DIR / f"{date_str}_{folder_name}_SECURITY_STATUS.md"

    fixed: list[str] = []
    ok: list[str] = []
    warning: list[str] = []
    missing: list[str] = []

    for r in results:
        item = r.get("item", "")
        status = r.get("status", "")
        file_ = r.get("file")
        detail = r.get("detail", "")

        if status == "fixed":
            location = f"（{file_} に追加）" if file_ else ""
            fixed.append(f"- {item}{location}")
        elif status == "ok":
            location = f"（{file_}）" if file_ else ""
            ok.append(f"- {item}{location}（実装済みのため変更なし）")
        elif status == "incomplete":
            file_hint = f"\n  → {file_} を確認してください" if file_ else ""
            warning.append(f"- {item}：{detail}{file_hint}")
        elif status == "missing":
            missing.append(f"- {item}")
        elif status == "error":
            file_hint = f"\n  → {file_} を確認してください" if file_ else ""
            warning.append(f"- {item}：{detail}{file_hint}")

    lines: list[str] = [
        "# セキュリティ実装レポート",
        f"生成日時：{now_str}",
        "",
    ]

    if python_version_warning:
        lines.append(python_version_warning)
        lines.append("")

    lines.append("## ✅ 自動実装済み")
    if fixed or ok:
        lines.extend(fixed)
        lines.extend(ok)
    else:
        lines.append("（なし）")
    lines.append("")

    lines.append("## ⚠️ 要手動対応")
    if warning:
        lines.extend(warning)
    else:
        lines.append("（なし）")
    lines.append("")

    lines.append("## ❌ 未実装（対象ファイルが見つかりませんでした）")
    if missing:
        lines.extend(missing)
    else:
        lines.append("（なし）")
    lines.append("")

    if install_results:
        installed_pkgs = [r for r in install_results if r.get("action") == "installed"]
        if installed_pkgs:
            lines.append("## 🔧 自動インストール済み")
            for r in installed_pkgs:
                pkg = r.get("package", "")
                reason = r.get("reason", "")
                lines.append(f"- {pkg}（{reason}）" if reason else f"- {pkg}")
            lines.append("")

    lines.append(_ADVISORY_SECTION)

    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    return str(output_path.resolve())
