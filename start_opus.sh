#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET_PATH=""
while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^# ]] && continue
    [[ -z "$line" ]] && continue
    TARGET_PATH="$line"
    break
done < "$SCRIPT_DIR/target_path.txt"

if [ -z "$TARGET_PATH" ]; then
    echo "target_path.txt に対象フォルダのパスを記載してください"
    read -p "Enterキーで終了..."
    exit 1
fi

if [ ! -d "$TARGET_PATH" ]; then
    echo "指定されたパスが見つかりません: $TARGET_PATH"
    read -p "Enterキーで終了..."
    exit 1
fi

export SENTINEL_MODEL=claude-opus-4-6
echo "Opus版で実行します"
echo ""
python3 -m sentinel_api run "$TARGET_PATH"

echo ""
echo "完了しました。SECURITY_STATUS.md を確認してください"
read -p "Enterキーで終了..."
