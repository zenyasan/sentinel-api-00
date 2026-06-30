"""Claude API呼び出しを担当するモジュール。"""

import json
import os

import anthropic

MODEL = "claude-sonnet-4-6"


def judge_and_plan(item: str, files: list[dict]) -> dict:
    """
    項目名と対象ファイル群を受け取り、
    実装が必要かを判定して実装コードを生成する。
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    files_text = ""
    for f in files:
        files_text += f"### {f['path']}\n```python\n{f['content']}\n```\n\n"

    user_prompt = f"""以下のFastAPIプロジェクトのファイルを解析し、「{item}」が実装されているか判定してください。

## 対象ファイル
{files_text}

## 判定基準
- "ok": 適切に実装済み
- "missing": 未実装
- "incomplete": 部分的に実装されているが不完全

## 出力形式
以下のJSON形式のみで返してください。コードブロックや前置き・後置き不要です。

{{
    "item": "{item}",
    "status": "missing" | "ok" | "incomplete",
    "plan": [
        {{
            "file": "ファイル名",
            "line": 行番号（整数）,
            "code": "実装するコードの全文"
        }}
    ],
    "detail": "判定の根拠・補足説明（下記の文章表現ルールに従って記述すること）"
}}

statusが"ok"の場合はplanをnullにしてください。
statusが"missing"または"incomplete"の場合は、planに実装すべきコードを含めてください。

## detailフィールドの文章表現ルール

ターゲットユーザーはセキュリティやコードに詳しくない個人開発者です。
以下のルールに従って、誰でも理解できる文章でdetailを記述してください。

### 避けるべき表現
- CryptContext、ORM、バインドパラメータなど専門用語を説明なしで使わない
- 「14〜19行目に重複挿入されており」のような行番号・関数名を多用した説明は避け、
  「コードの一部が重複して書かれているため」のように平易に言い換える
- 1文を80文字以上にしない。長くなる場合は文を分割する

### 推奨する書き方
- 「何が問題か」→「なぜ問題か」→「どう直したか・直すべきか」の順で短い文を重ねる
- 専門用語を使う場合は必ず一言補足を入れる
  （例：「ORM（データベースを安全に操作する仕組み）」）
- 詳細な技術的根拠は省略し、結論と理由を中心に書く

### 番号付き列挙のルール
(1)(2)(3)のような番号付き列挙を使う場合、各番号は必ず改行して独立した行にする。
1文の中に複数の番号を詰め込まない。

良い例：
以下の3つの問題があります。

(1) レート制限はあるが、ログイン失敗回数のカウントがありません。

(2) 一定回数失敗した際にロックする仕組みがありません。

(3) コードの一部に重複した記述があり、正常に動作しません。

悪い例：
(1)レート制限はあるが...(2)ロックする仕組みがなく...(3)また重複も..."""

    raw = ""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system="あなたはFastAPIのセキュリティ実装の専門家です。コードを解析し、セキュリティ上の問題を特定して修正案を提供します。",
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    except anthropic.APIError as e:
        return {
            "item": item,
            "status": "error",
            "plan": None,
            "detail": f"API error: {e}",
        }
    except json.JSONDecodeError as e:
        return {
            "item": item,
            "status": "error",
            "plan": None,
            "detail": f"JSON parse error: {e}. Raw response: {raw}",
        }


def apply_fix(file_path: str, file_content: str, plan: dict) -> str:
    """
    対象ファイルの全内容と実装計画を受け取り、
    修正済みのファイル全体を返す。
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_prompt = f"""以下のファイルに、指定されたセキュリティ実装を追加してください。

## ファイル: {file_path}
```python
{file_content}
```

## 実装内容
- 挿入位置（行番号）: {plan.get('line', 'N/A')}
- 実装するコード:
```python
{plan.get('code', '')}
```

修正済みのファイル全体をそのまま返してください。
コードブロック（```）や前置き・後置きのテキストは不要です。Pythonコードのみを返してください。"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            messages=[{"role": "user", "content": user_prompt}],
        )

        result = response.content[0].text.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            inner_lines = []
            started = False
            for line in lines:
                if not started:
                    if line.startswith("```"):
                        started = True
                    continue
                if line.strip() == "```":
                    break
                inner_lines.append(line)
            result = "\n".join(inner_lines)

        return result

    except anthropic.APIError as e:
        return f"# ERROR: API call failed: {e}\n{file_content}"
