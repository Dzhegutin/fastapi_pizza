from pydantic import BaseModel, field_validator
from typing import List, Optional, Set, Tuple, Literal
from datetime import datetime


class PizzaTypeBase(BaseModel):
    type: str


class PizzaTypeGetOrCreate(PizzaTypeBase):
    id: int

    class Config:
        from_attributes = True


class DoughTypeBase(BaseModel):
    dough: str


class DoughTypeGetOrCreate(DoughTypeBase):
    id: int

    class Config:
        from_attributes = True


class DoughThicknessBase(BaseModel):
    thickness: float


class DoughThicknessGetOrCreate(DoughThicknessBase):
    id: int

    class Config:
        from_attributes = True


class PizzaPriceBase(BaseModel):
    dough_type_id: int
    dough_thickness_id: int
    price: float


class PizzaPriceResponse(PizzaPriceBase):
    pizza_id: int


###############################################
class PizzaMinimum(BaseModel):
    pizza_name: str
    pizza_img: Optional[str]


class PizzaBase(PizzaMinimum):
    id: int

    pizza_types: List[PizzaTypeGetOrCreate]
    dough_types: List[DoughTypeGetOrCreate]
    dough_thicknesses: List[DoughThicknessGetOrCreate]
    prices: List[PizzaPriceResponse]

    class Config:
        from_attributes = True


class PizzaListWithPages(BaseModel):
    pizzas: List[PizzaBase]
    total_pages: int

    class Config:
        from_attributes = True


class PizzaCreate(PizzaMinimum):
    pizza_types: List[int]
    dough_types: List[int]
    dough_thicknesses: List[int]
    price_sets: List[PizzaPriceBase]

    @field_validator('price_sets', mode='after')
    def validate_price_sets(cls, v, info):
        data = info.data

        dough_types = data.get('dough_types', [])
        dough_thicknesses = data.get('dough_thicknesses', [])

        expected_combinations: Set[Tuple[int, int]] = {
            (dough_type, dough_thickness)
            for dough_type in dough_types
            for dough_thickness in dough_thicknesses
        }

        provided_combinations: Set[Tuple[int, int]] = {
            (price_set.dough_type_id, price_set.dough_thickness_id)
            for price_set in v
        }

        if expected_combinations != provided_combinations:
            missing_combinations = expected_combinations - provided_combinations
            raise ValueError(f"Missing combinations: {missing_combinations}. "
                             f"Expected all combinations of dough_types {dough_types} "
                             f"and dough_thicknesses {dough_thicknesses}.")
        return v

########################################################################################


class AddToCartSchema(BaseModel):
    pizza_id: int
    dough_type_id: int
    dough_thickness_id: int

class AddToCartSchemaAction(AddToCartSchema):
    action: Literal["increase", "decrease"]

class ReadUserCartSumAndCount(BaseModel):
    user_cart_sum: int
    user_cart_count: int


class ReadItemQuantity(BaseModel):
    pizza_id: int
    dough_type_id: int
    dough_thickness_id: int
    quantity: int

class DeleteCartItemsResponse(BaseModel):
    message: str
    deleted_count: int

class DeleteCartItemResponse(ReadItemQuantity):
    message: str


class PizzaInCartResponse(BaseModel):
    pizza_id: int
    pizza_name: str
    pizza_img: str
    dough_type_id: int
    dough_type: str
    dough_thickness_id: int
    dough_thickness: float
    quantity: int
    total_price: float

class UserCartResponse(BaseModel):
    pizzas: List[PizzaInCartResponse]