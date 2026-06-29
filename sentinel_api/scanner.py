"""セキュリティ実装の有無をチェックするモジュール。"""

import re
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


def _keyword_check(root: Path, item: str, priority_names: list, keywords: list) -> dict:
    priority = _collect_priority_files(root, priority_names)

    if priority:
        hits = _files_with_keywords(priority, keywords)
        if hits:
            return {"item": item, "status": "ok", "files": [_rel(root, f) for f in hits]}
        return {"item": item, "status": "missing", "files": [_rel(root, f) for f in priority]}

    hits = _files_with_keywords(_all_py_files(root), keywords)
    if hits:
        return {"item": item, "status": "ok", "files": [_rel(root, f) for f in hits]}
    return {"item": item, "status": "missing", "files": []}


# --- auto_fix checks ---

def _check_password_hashing(root: Path) -> dict:
    return _keyword_check(
        root, "パスワードハッシュ化",
        ["auth.py", "users.py", "models.py"],
        ["bcrypt", "argon2", "passlib", "hash"],
    )


def _check_sql_injection(root: Path) -> dict:
    return _keyword_check(
        root, "SQLインジェクション対策",
        ["database.py", "db.py", "models.py", "crud.py"],
        ["SQLAlchemy", "bindparam", ":param"],
    )


def _check_error_exposure(root: Path) -> dict:
    return _keyword_check(
        root, "エラー情報の外部露出防止",
        ["main.py"],
        ["exception_handler", "debug=False"],
    )


def _check_cors(root: Path) -> dict:
    return _keyword_check(
        root, "CORS設定",
        ["main.py"],
        ["CORSMiddleware", "allow_origins"],
    )


def _check_rate_limiting(root: Path) -> dict:
    return _keyword_check(
        root, "レート制限",
        ["main.py", "routers/*.py"],
        ["slowapi", "RateLimiter", "limiter"],
    )


def _check_security_headers(root: Path) -> dict:
    return _keyword_check(
        root, "HTTPセキュリティヘッダ",
        ["main.py"],
        ["X-Frame-Options", "X-Content-Type-Options", "SecurityHeadersMiddleware"],
    )


def _check_hardcoded_secrets(root: Path) -> dict:
    # 直書きパターン: 変数名 = "文字列" の形式を検出
    pattern = re.compile(
        r'(ANTHROPIC_API_KEY|SECRET_KEY|API_KEY|[Pp]assword)\s*=\s*["\']'
    )
    hits = []
    for f in _all_py_files(root):
        if pattern.search(_read_file(f)):
            hits.append(f)

    if hits:
        return {"item": "シークレット直書き検出", "status": "missing", "files": [_rel(root, f) for f in hits]}
    return {"item": "シークレット直書き検出", "status": "ok", "files": []}


# --- manual_check checks ---

def _check_jwt(root: Path) -> dict:
    priority = _collect_priority_files(root, ["auth.py", "dependencies.py", "security.py"])
    keywords = ["jwt", "decode", "exp", "JWTError"]

    if priority:
        hits = _files_with_keywords(priority, keywords)
        if hits:
            all_content = "".join(_read_file(f) for f in hits)
            missing_kw = [kw for kw in ["decode", "exp"] if kw not in all_content]
            if missing_kw:
                return {
                    "item": "JWT検証・有効期限",
                    "status": "incomplete",
                    "files": [_rel(root, f) for f in hits],
                    "detail": f"JWT使用あり、不足: {', '.join(missing_kw)}",
                }
            return {
                "item": "JWT検証・有効期限",
                "status": "ok",
                "files": [_rel(root, f) for f in hits],
                "detail": "",
            }
        return {
            "item": "JWT検証・有効期限",
            "status": "missing",
            "files": [_rel(root, f) for f in priority],
            "detail": "JWT実装なし",
        }

    hits = _files_with_keywords(_all_py_files(root), keywords)
    if hits:
        return {
            "item": "JWT検証・有効期限",
            "status": "incomplete",
            "files": [_rel(root, f) for f in hits],
            "detail": "JWT実装あり、要確認",
        }
    return {"item": "JWT検証・有効期限", "status": "missing", "files": [], "detail": "JWT実装なし"}


def _check_login_attempts(root: Path) -> dict:
    priority = _collect_priority_files(root, ["auth.py", "routers/auth.py"])
    keywords = ["attempt", "lockout", "count"]

    if priority:
        hits = _files_with_keywords(priority, keywords)
        if hits:
            return {
                "item": "ログイン試行回数制限",
                "status": "ok",
                "files": [_rel(root, f) for f in hits],
                "detail": "",
            }
        return {
            "item": "ログイン試行回数制限",
            "status": "missing",
            "files": [_rel(root, f) for f in priority],
            "detail": "試行回数制限なし",
        }

    hits = _files_with_keywords(_all_py_files(root), keywords)
    if hits:
        return {
            "item": "ログイン試行回数制限",
            "status": "ok",
            "files": [_rel(root, f) for f in hits],
            "detail": "",
        }
    return {"item": "ログイン試行回数制限", "status": "missing", "files": [], "detail": "試行回数制限なし"}


def _check_dependency_versions(root: Path) -> dict:
    req_path = root / "requirements.txt"
    if not req_path.exists():
        return {
            "item": "依存パッケージの脆弱性",
            "status": "missing",
            "files": [],
            "detail": "requirements.txt が存在しない",
        }

    content = _read_file(req_path)
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    unpinned = [l for l in lines if not re.search(r"[=<>!~]", l)]

    if unpinned:
        return {
            "item": "依存パッケージの脆弱性",
            "status": "missing",
            "files": ["requirements.txt"],
            "detail": f"バージョン未固定: {', '.join(unpinned)}",
        }
    return {
        "item": "依存パッケージの脆弱性",
        "status": "ok",
        "files": ["requirements.txt"],
        "detail": "全パッケージバージョン固定済み",
    }


def scan(project_path: str) -> dict:
    """
    プロジェクトをスキャンして判定結果を返す。

    戻り値の形式:
    {
        "auto_fix": [
            {"item": "パスワードハッシュ化", "status": "missing" | "ok", "files": ["auth.py"]},
            ...
        ],
        "manual_check": [
            {"item": "JWT検証", "status": "missing" | "ok" | "incomplete", "files": [...], "detail": "..."},
            ...
        ]
    }
    """
    root = Path(project_path).resolve()
    return {
        "auto_fix": [
            _check_password_hashing(root),
            _check_sql_injection(root),
            _check_error_exposure(root),
            _check_cors(root),
            _check_rate_limiting(root),
            _check_security_headers(root),
            _check_hardcoded_secrets(root),
        ],
        "manual_check": [
            _check_jwt(root),
            _check_login_attempts(root),
            _check_dependency_versions(root),
        ],
    }
