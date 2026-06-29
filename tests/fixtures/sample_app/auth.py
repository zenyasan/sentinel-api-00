"""テスト用認証スタブ（意図的にパスワード平文保存・バリデーションなし）。"""

from fastapi import APIRouter

router = APIRouter()

# シークレット直書き（意図的な脆弱実装）
SECRET_KEY = "unsafe_hardcoded_key_for_demo"

USERS = {}


@router.post("/register")
def register(username: str, password: str):
    """パスワードを平文で保存する（脆弱な実装）。"""
    USERS[username] = password
    return {"message": "registered"}


@router.post("/login")
def login(username: str, password: str):
    """レート制限なし・試行回数制限なしのログイン（脆弱な実装）。"""
    if USERS.get(username) == password:
        return {"message": "ok"}
    return {"message": "error", "detail": f"User {username} not found or wrong password"}
