"""CLIエントリポイント。typer を使用してコマンドを定義する。"""

import os
from pathlib import Path

import typer
from rich.console import Console

from sentinel_api import ai_client, installer, patcher, reporter, scanner

app = typer.Typer()
console = Console()


@app.callback()
def callback() -> None:
    """FastAPIプロジェクトにセキュリティ実装を自動追加するCLIツール。"""


@app.command()
def run(
    project_path: str = typer.Argument(..., help="対象のFastAPIプロジェクトパス"),
    dry_run: bool = typer.Option(False, "--dry-run", help="実際には書き込まず確認のみ"),
) -> None:
    """FastAPIプロジェクトにセキュリティ実装を自動追加する。"""
    if not installer.check_python_version():
        console.print("[yellow]⚠️  Python 3.11以上での実行を推奨します。続行します。[/yellow]")
    install_results = installer.check_and_install()

    root = Path(project_path)
    if not root.exists():
        console.print(f"[red]エラー: パスが存在しません: {project_path}[/red]")
        raise typer.Exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]エラー: ANTHROPIC_API_KEY が設定されていません[/red]")
        raise typer.Exit(1)

    plan_path = str(root / ".sentinel_plan.json")
    report_path = str(root / "SECURITY_STATUS.md")

    # Phase 1: スキャン・計画
    console.print(f"🔍 スキャン中... {project_path}")
    scan_result = scanner.scan(project_path)
    auto_fix_items = scan_result["auto_fix"]
    manual_check_items = scan_result["manual_check"]

    auto_fix_results = []
    for entry in auto_fix_items:
        item = entry["item"]
        files = entry["files"]
        try:
            result = ai_client.judge_and_plan(item, files)
        except Exception as e:
            result = {"item": item, "status": "error", "plan": None, "detail": str(e)}

        status = result.get("status", "error")
        if status == "missing":
            console.print(f"✅ {item}：未実装を検出 → 実装します")
        elif status == "ok":
            console.print(f"✅ {item}：実装済み → スキップ")
        elif status == "incomplete":
            console.print(f"⚠️  {item}：不完全な実装を検出")
        else:
            console.print(f"[yellow]⚠️  {item}：判定エラー - {result.get('detail', '')}[/yellow]")

        auto_fix_results.append(result)

    patcher.save_plan(auto_fix_results, plan_path)

    # Phase 2: 実装
    if dry_run:
        console.print("\n[bold]以下を実装します（ドライラン）：[/bold]")
        for result in auto_fix_results:
            if result.get("status") in ("missing", "incomplete"):
                plans = result.get("plan") or []
                for p in plans:
                    console.print(f"  - {result['item']}: {p.get('file', 'N/A')}")
        patcher.cleanup(plan_path)
        return

    loaded_results = patcher.load_plan(plan_path)
    final_auto_results = []
    for result in loaded_results:
        item = result.get("item", "")
        status = result.get("status", "error")
        plans = result.get("plan") or []
        detail = result.get("detail", "")

        if status in ("missing", "incomplete") and plans:
            fixed_file = None
            apply_error = None
            for plan_item in plans:
                file_rel = plan_item.get("file", "")
                file_abs = str(root / file_rel)
                try:
                    file_content = (
                        Path(file_abs).read_text(encoding="utf-8")
                        if Path(file_abs).exists()
                        else ""
                    )
                    new_content = ai_client.apply_fix(file_rel, file_content, plan_item)
                    patcher.write_file(file_abs, new_content)
                    fixed_file = file_rel
                except Exception as e:
                    apply_error = str(e)
                    console.print(f"[yellow]⚠️  {item} の実装中にエラー: {e}[/yellow]")
                    break

            if apply_error:
                final_auto_results.append(
                    {"item": item, "status": "error", "file": fixed_file, "detail": apply_error}
                )
            else:
                final_auto_results.append(
                    {"item": item, "status": "fixed", "file": fixed_file, "detail": detail}
                )
        else:
            first_file = plans[0].get("file") if plans else None
            final_auto_results.append(
                {"item": item, "status": status, "file": first_file, "detail": detail}
            )

    # Phase 3: レポート生成
    manual_results = []
    for entry in manual_check_items:
        item = entry["item"]
        files = entry["files"]
        try:
            result = ai_client.judge_and_plan(item, files)
            status = result.get("status", "error")
            plans = result.get("plan") or []
            manual_results.append({
                "item": item,
                "status": status,
                "file": plans[0].get("file") if plans else None,
                "detail": result.get("detail", ""),
            })
        except Exception as e:
            manual_results.append(
                {"item": item, "status": "error", "file": None, "detail": str(e)}
            )

    all_results = final_auto_results + manual_results
    reporter.generate_report(all_results, output_path=report_path, install_results=install_results)
    console.print(f"\n📝 レポートを生成しました → {report_path}")

    patcher.cleanup(plan_path)


if __name__ == "__main__":
    app()
