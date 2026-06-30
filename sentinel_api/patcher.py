"""コードへの自動書き込みを行うモジュール。"""

import json
import os
import shutil


def save_plan(results: list[dict], output_path: str = ".sentinel_plan.json") -> None:
    """judge_and_plan()の結果リストをJSONファイルに保存する。"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def load_plan(output_path: str = ".sentinel_plan.json") -> list[dict]:
    """save_plan()で保存したJSONを読み込んで返す。"""
    with open(output_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_file(file_path: str, content: str) -> None:
    """修正済みコードをファイルに上書き保存する。書き込み前に元ファイルを.bakとしてバックアップする。"""
    if os.path.exists(file_path):
        shutil.copy2(file_path, file_path + ".bak")

    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def cleanup(output_path: str = ".sentinel_plan.json") -> None:
    """作業完了後に.sentinel_plan.jsonを削除する。"""
    if os.path.exists(output_path):
        os.remove(output_path)
