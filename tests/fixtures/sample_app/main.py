"""テスト用FastAPIサンプルアプリ（意図的にセキュリティ未実装の脆弱な状態）。"""

from fastapi import FastAPI

from .auth import router as auth_router

# debug=True のまま・例外ハンドラなし・セキュリティヘッダなし（意図的な脆弱実装）
app = FastAPI(debug=True)

app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "Hello World"}
