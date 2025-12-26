# schemas/keyword.py
from pydantic import BaseModel


class KeywordCreate(BaseModel):
    keyword: str


class KeywordUpdate(BaseModel):
    old: str
    new: str
