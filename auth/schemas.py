from datetime import date
from typing import Optional, List

from fastapi_users import schemas
from pydantic import BaseModel
from pydantic.v1.utils import GetterDict


class AddToCartSchema(BaseModel):
    pizza_id: int
    dough_type_id: int
    dough_thickness_id: int
    quantity: int


class UserRead(schemas.BaseUser[int]):
    # id, email, is_active, is_superuser, is_verified GET from BaseUserCreate

    name: str
    surname: str
    last_name: Optional[str] = None
    birthday: date
    phone_number: str
    user_city: str
    address: str

    # cart: List[AddToCartSchema] = []

    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    # email, password, is_active, is_superuser, is_verified GET from BaseUserCreate
    name: str
    surname: str
    last_name: Optional[str] = None
    birthday: date
    phone_number: str
    user_city: str
    address: str

    cart: List[AddToCartSchema]

    class Config:
        from_attributes = True
