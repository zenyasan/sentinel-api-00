"""セキュリティ実装の有無をチェックするモジュール。"""

from pathlib import Path


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def _collect_priority_files(root: Path, names: list) -> list:
    files = []
    for name in names:
        if "*" in name:
            files.extend(sorted(root.glob(name)))
        else:
            p = root / name
            if p.exists():
                files.append(p)
    return files


def _all_py_files(root: Path) -> list:
    return sorted(
        f for f in root.rglob("*.py")
        if ".venv" not in f.parts and "__pycache__" not in f.parts
    )


def _files_with_keywords(files: list, keywords: list) -> list:
    result = []
    for f in files:
        content = _read_file(f)
        if any(kw in content for kw in keywords):
            result.append(f)
    return result


def _file_entries(root: Path, files: list) -> list:
    return [{"path": _rel(root, f), "content": _read_file(f)} for f in files]


def _collect_files(root: Path, priority_names: list, fallback_keywords: list) -> list:
    priority = _collect_priority_files(root, priority_names)
    if priority:
        return priority
    return _files_with_keywords(_all_py_files(root), fallback_keywords)


def scan(project_path: str) -> dict:
    """
    プロジェクトをスキャンして項目ごとの対象ファイルを返す。

    戻り値の形式:
    {
        "auto_fix": [
            {"item": "パスワードハッシュ化", "files": [{"path": "auth.py", "content": "..."}]},
            ...
        ],
        "manual_check": [
            {"item": "JWT認証検証・有効期限", "files": [{"path": "auth.py", "content": "..."}, ...]},
            ...
        ]
    }
    """
    root = Path(project_path).resolve()

    return {
        "auto_fix": [
            {
                "item": "パスワードハッシュ化",
                "files": _file_entries(root, _collect_files(
                    root,
                    ["auth.py", "users.py", "models.py"],
                    ["bcrypt", "argon2", "passlib", "hash"],
                )),
            },
            {
                "item": "SQLインジェクション対策",
                "files": _file_entries(root, _collect_files(
                    root,
                    ["database.py", "db.py", "models.py", "crud.py"],
                    ["SQLAlchemy", "bindparam", ":param"],
                )),
            },
            {
                "item": "エラー情報の外部露出防止",
                "files": _file_entries(root, _collect_files(
                    root,
                    ["main.py"],
                    ["exception_handler", "debug=False"],
                )),
            },
            {
                "item": "CORS設定",
                "files": _file_entries(root, _collect_files(
                    root,
                    ["main.py"],
                    ["CORSMiddleware", "allow_origins"],
                )),
            },
            {
                "item": "レート制限",
                "files": _file_entries(root, _collect_files(
                    root,
                    ["main.py", "routers/*.py"],
                    ["slowapi", "RateLimiter", "limiter"],
                )),
            },
            {
                "item": "HTTPセキュリティヘッダ",
                "files": _file_entries(root, _collect_files(
                    root,
                    ["main.py"],
                    ["X-Frame-Options", "X-Content-Type-Options", "SecurityHeadersMiddleware"],
                )),
            },
            {
                "item": "シークレット直書き検出",
                "files": _file_entries(root, _all_py_files(root)),
            },
        ],
        "manual_check": [
            {
                "item": "JWT認証検証・有効期限",
                "files": _file_entries(root, _collect_files(
                    root,
                    ["auth.py", "dependencies.py", "security.py"],
                    ["jwt", "decode", "exp", "JWTError"],
                )),
            },
            {
                "item": "ログイン試行回数制限",
                "files": _file_entries(root, _collect_files(
                    root,
                    ["auth.py", "routers/auth.py"],
                    ["attempt", "lockout", "count"],
                )),
            },
            {
                "item": "依存パッケージの脆弱性",
                "files": _file_entries(root, _collect_priority_files(root, ["requirements.txt"])),
            },
        ],
    }
