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
    "detail": "判定の根拠・補足説明"
}}

statusが"ok"の場合はplanをnullにしてください。
statusが"missing"または"incomplete"の場合は、planに実装すべきコードを含めてください。"""

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
