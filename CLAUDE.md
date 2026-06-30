# sentinel-api-v2

## Project Overview
FastAPIプロジェクトに対してセキュリティ実装を自動で追加するCLIツール。
「検出して教える」ではなく「コードに書き込む」が目的。
- Python 3.11+ / anthropic SDK（claude-sonnet-4-6固定） / typer / httpx / rich / python-dotenv
- 実行形式：CLIローカル実行 + GitHub Action（PR時自動実行）の両対応

## Commands
```bash
# 開発環境セットアップ
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 実行（通常）
python -m sentinel_api run <project_path_or_github_url>

# ドライラン（書き込みなし・確認のみ）
python -m sentinel_api run <path> --dry-run

# テスト
pytest tests/ -v
```

## Rules

### 実装ルール
- Anthropic SDKはclaude-sonnet-4-6固定。モデル名を変えない
- `Skill(claude-api)は使用しないこと` を各セッション冒頭に明記する
- ファイル書き込みは必ずバックアップ（`.bak`）を取ってから実行する
- 自動実装とドライランは同じロジックを通す（dry_runフラグで分岐するだけ）

### やってはいけないこと
- requirements.txtを指示文に含めない（Skill発動でコンテキスト爆発の原因）
- 複数セキュリティ項目を1セッションで一括実装しない（必ずStep分割）
- 実装済みチェックをスキップしない（上書き事故防止）

### ディレクトリ構成（予定）
```
sentinel_api/
  __main__.py       # CLIエントリポイント（typer）
  scanner.py        # セキュリティ実装の有無チェック
  patcher.py        # コードへの自動書き込み
  reporter.py       # Markdownレポート生成
  ai_client.py      # Claude API呼び出し
tests/
  fixtures/         # テスト用FastAPIプロジェクトサンプル
SECURITY_STATUS.md  # セキュリティ実装状況管理
```

##対象セキュリティ項目（10項目）
JWT認証検証 / パスワードハッシュ化 / SQLインジェクション対策 / コマンドインジェクション対策 /
レート制限 / ログイン試行回数制限 / HTTPS強制 / CORS設定 / CSRFトークン / エラー情報の外部露出防止

## Workflow
1. Plan Modeで設計確認 → 合意してから実装
2. 実装完了後：`pytest tests/ -v` で検証
3. セキュリティ関連の実装完了時は必ずSECURITY_STATUS.mdを更新する
4. コミット：`git add . && git commit -m "feat|fix|docs: 内容" && git push`
