from pydantic import BaseModel

class UnitCreate(BaseModel):
    code: str
    name: str | None = None

class UnitJoin(BaseModel):
    code: str

class UnitResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    code: str
    name: str | None = None
