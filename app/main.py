# app/main.py
from fastapi import FastAPI
from app.api.endpoints import ehon, manga

app = FastAPI(title="絵本・漫画生成API")

# 各エンドポイントをルーティングに登録
app.include_router(ehon.router, prefix="/ehon", tags=["ehon"])
app.include_router(manga.router, prefix="/manga", tags=["manga"])

# 例: uvicorn で実行する場合
# uvicorn app.main:app --reload
