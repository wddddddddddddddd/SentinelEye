from pydantic import BaseModel
class Keyword(BaseModel):
    keyword: str

    class Config:
        orm_mode = True
