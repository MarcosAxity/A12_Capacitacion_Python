from pydantic import BaseModel, Field, field_validator


class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Teclado"])
    description: str | None = Field(None, max_length=300)
    price: float = Field(..., gt=0, examples=[999.99])
    tax: float | None = Field(0, ge=0)

    @field_validator("price")
    @classmethod
    def redondear_precio(cls, v: float) -> float:
        # Validación/normalización propia: 2 decimales
        return round(v, 2)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    price: float | None = Field(None, gt=0)
    tax: float | None = Field(None, ge=0)


class ItemOut(ItemBase):
    id: int
    owner: str
