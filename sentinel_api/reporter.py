"""プレーンテキストレポートを生成するモジュール。"""

from datetime import datetime
from pathlib import Path

_SEP_SECTION = "=" * 50
_SEP_ITEM = "-" * 50

_REPORTS_DIR = Path(__file__).parent.parent / "reports"

_ADVISORY_ITEMS = [
    (
        "HTTPS強制",
        "通信を暗号化するHTTPSへの切り替えを強制する設定です。\n"
        "VercelやRailwayなどのホスティングサービスを使えば、\n"
        "多くの場合自動で対応してくれます。",
    ),
    (
        "ログ・監視",
        "アプリの動作状況やエラーを記録する「ログ」と、\n"
        "異常があった時に気づける「監視」の仕組みです。\n"
        "構造化ログ（後から検索・分析しやすい形式のログ）の\n"
        "導入を検討してください。",
    ),
    (
        "依存パッケージの定期スキャン",
        "使用しているライブラリに新しい脆弱性が\n"
        "見つかっていないかを定期的にチェックする仕組みです。\n"
        "CI（継続的インテグレーション）の中でpip-auditを\n"
        "実行することを推奨します。",
    ),
    (
        "リバースプロキシ運用",
        "アプリを直接インターネットに公開するのではなく、\n"
        "Nginxなどのリバースプロキシを間に挟む構成です。\n"
        "uvicornを直接公開しないことを推奨します。",
    ),
]


def _item_implemented(num: int, r: dict) -> str:
    name = r.get("item", "")
    file_ = r.get("file")
    detail = r.get("detail", "")
    status = r.get("status", "")

    lines = [f"[{num}] {name}", ""]
    if status == "ok":
        lines.append("状態: 実装済みのため変更なし")
    else:
        lines.append(f"対象ファイル: {file_}" if file_ else "対象ファイル: (不明)")
    lines.append("")
    lines.append("内容:")
    lines.append(detail)
    return "\n".join(lines)


def _item_manual(num: int, r: dict) -> str:
    name = r.get("item", "")
    file_ = r.get("file")
    detail = r.get("detail", "")
    recommendation = r.get("recommendation", "")

    lines = [f"[{num}] {name}", ""]
    if file_:
        lines.append(f"対象ファイル: {file_}")
        lines.append("")
    lines.append("現状の問題:")
    lines.append(detail)
    if recommendation:
        lines.append("")
        lines.append("推奨する対応:")
        lines.append(recommendation)
    if file_:
        lines.append("")
        lines.append(f"→ {file_} を確認してください")
    return "\n".join(lines)


def _item_missing(num: int, r: dict) -> str:
    name = r.get("item", "")
    detail = r.get("detail", "")

    lines = [f"[{num}] {name}", ""]
    lines.append("内容:")
    lines.append(detail)
    return "\n".join(lines)


def _item_advisory(num: int, name: str, content: str) -> str:
    lines = [f"[{num}] {name}", ""]
    lines.append("内容:")
    lines.append(content)
    return "\n".join(lines)


def _section_block(title: str, item_blocks: list[str]) -> str:
    header = f"{_SEP_SECTION}\n{title}\n{_SEP_SECTION}"
    if item_blocks:
        body = f"\n\n\n{_SEP_ITEM}\n\n\n".join(item_blocks)
    else:
        body = "該当項目はありません"
    return f"{header}\n\n\n{body}"


def generate_report(
    results: list[dict],
    project_path: str,
    install_results: list[dict] | None = None,
    python_version_warning: str | None = None,
) -> str:
    """全項目の処理結果を受け取りtxtファイルを生成する。戻り値：生成したレポートファイルの絶対パス。"""
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str = now.strftime("%Y%m%d")
    folder_name = Path(project_path).name

    _REPORTS_DIR.mkdir(exist_ok=True)
    output_path = _REPORTS_DIR / f"{date_str}_{folder_name}_SECURITY_STATUS.txt"

    implemented = [r for r in results if r.get("status") in ("fixed", "ok")]
    manual = [r for r in results if r.get("status") in ("incomplete", "error")]
    missing = [r for r in results if r.get("status") == "missing"]

    file_header = (
        f"セキュリティ実装レポート\n"
        f"生成日時: {now_str}\n"
        f"対象プロジェクト: {folder_name}"
    )

    sections = [
        _section_block(
            "自動実装済み",
            [_item_implemented(i + 1, r) for i, r in enumerate(implemented)],
        ),
        _section_block(
            "要手動対応（実装はあるが確認が必要）",
            [_item_manual(i + 1, r) for i, r in enumerate(manual)],
        ),
        _section_block(
            "未実装（対象ファイルが見つかりませんでした）",
            [_item_missing(i + 1, r) for i, r in enumerate(missing)],
        ),
        _section_block(
            "追加で検討推奨（このツールの対象外）",
            [_item_advisory(i + 1, name, cnt) for i, (name, cnt) in enumerate(_ADVISORY_ITEMS)],
        ),
    ]

    content = file_header + "\n\n\n" + "\n\n\n".join(sections) + "\n\n\n"
    output_path.write_text(content, encoding="utf-8")
    return str(output_path.resolve())
