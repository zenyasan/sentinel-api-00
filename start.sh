#!/bin/bash
echo "==================================="
echo " sentinel-api を起動します"
echo "==================================="
echo ""

if [ -z "$1" ]; then
    echo "使い方：対象のFastAPIプロジェクトフォルダを"
    echo "このファイルにドラッグ＆ドロップするか、引数として渡してください。"
    read -p "Enterキーで終了..."
    exit 1
fi

echo "使用するモデルを選んでください"
echo "  1: Sonnet（標準・低コスト）"
echo "  2: Opus（高精度・高コスト）"
echo ""
read -p "番号を入力してEnter (1 or 2): " MODEL_CHOICE

if [ "$MODEL_CHOICE" = "2" ]; then
    export SENTINEL_MODEL=claude-opus-4-6
    echo "Opus版で実行します"
else
    export SENTINEL_MODEL=claude-sonnet-4-6
    echo "Sonnet版で実行します"
fi

echo ""
python3 -m sentinel_api run "$1"

echo ""
echo "==================================="
echo " 完了しました。SECURITY_STATUS.md を確認してください。"
echo "==================================="
read -p "Enterキーで終了..."
