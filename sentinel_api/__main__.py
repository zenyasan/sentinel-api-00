"""CLIエントリポイント。typer を使用してコマンドを定義する。"""

import typer

app = typer.Typer()


@app.command()
def run(
    target: str = typer.Argument(..., help="対象のプロジェクトパスまたはGitHub URL"),
    dry_run: bool = typer.Option(False, "--dry-run", help="書き込みを行わず確認のみ実行する"),
) -> None:
    """FastAPIプロジェクトにセキュリティ実装を自動追加する。"""
    pass


if __name__ == "__main__":
    app()
