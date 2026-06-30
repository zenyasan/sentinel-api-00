"""Markdownレポートを生成するモジュール。"""

from datetime import datetime
from pathlib import Path


_ADVISORY_SECTION = """## 💡 追加で検討推奨（このツール対象外）
- HTTPS強制：VercelやRailwayを使えば自動で対応できます
- ログ・監視：構造化ログの導入を検討してください
- 依存パッケージの定期スキャン：CIでpip-auditの実行を推奨します
- リバースプロキシ運用：uvicornを直接公開しないことを推奨します
"""


def generate_report(results: list[dict], output_path: str = "SECURITY_STATUS.md") -> None:
    """全項目の処理結果を受け取りMarkdownファイルを生成する。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        f"生成日時：{now}",
        "",
    ]

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

    lines.append(_ADVISORY_SECTION)

    content = "\n".join(lines)
    Path(output_path).write_text(content, encoding="utf-8")
