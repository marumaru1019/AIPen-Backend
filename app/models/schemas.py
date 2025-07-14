# app/models/schemas.py
from pydantic import BaseModel

class EhonRequest(BaseModel):
    panel_num: int
    commit_outline: str
    genre: str
    style: str

class MangaRequest(BaseModel):
    panel_num: int
    commit_outline: str
    genre: str
    style: str
