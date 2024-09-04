from typing import List, Dict, Any, Optional

from fastapi import Depends, HTTPException, APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from auth.app import current_user
from crud import create_pizza_type, create_dough_thickness, create_pizza_dough_type, create_pizza, \
    read_pizza_types, get_pizza_price, get_pizzas, get_count_pizza_pages, \
    read_cart_amount_and_count, get_pizza_count_in_cart, create_or_update_item_in_cart, delete_all_user_cart_items, \
    delete_user_cart_item, get_user_cart
from db import get_async_session
from models import User
from schemas import DoughTypeGetOrCreate, DoughThicknessGetOrCreate, PizzaTypeGetOrCreate, \
    PizzaCreate, PizzaListWithPages, AddToCartSchema, PizzaPriceResponse, PizzaTypeBase, DoughTypeBase, \
    DoughThicknessBase, PizzaBase, ReadUserCartSumAndCount, ReadItemQuantity, AddToCartSchemaAction, \
    DeleteCartItemsResponse, DeleteCartItemResponse, UserCartResponse

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "Welcome to PizzaRestaurant"}


@router.get("/read_pizza_types/", response_model=List[PizzaTypeGetOrCreate])
async def pizza_types_read_router(db: AsyncSession = Depends(get_async_session)):
    pizza_types = await read_pizza_types(db)
    return pizza_types


@router.post("/create_pizza_type/", response_model=PizzaTypeGetOrCreate)
async def pizza_type_create_router(pizza_type: PizzaTypeBase, db: AsyncSession = Depends(get_async_session)):
    return await create_pizza_type(pizza_type.type, db)


@router.post("/create_dough_type/", response_model=DoughTypeGetOrCreate)
async def dough_type_create_router(dough_type: DoughTypeBase, db: AsyncSession = Depends(get_async_session)):
    return await create_pizza_dough_type(dough_type.dough, db)


@router.post("/create_dough_thickness/", response_model=DoughThicknessGetOrCreate)
async def dough_thickness_create_router(dough_thickness: DoughThicknessBase,
                                        db: AsyncSession = Depends(get_async_session)):
    return await create_dough_thickness(dough_thickness.thickness, db)


@router.post("/create_pizza/", response_model=PizzaBase)
async def pizza_create_router(pizza: PizzaCreate, db: AsyncSession = Depends(get_async_session)):
    return await create_pizza(db, pizza)


@router.post("/read_pizza_price/", response_model=PizzaPriceResponse)
async def pizza_price_read_router(
        pizza_id: int,
        dough_type_id: int,
        dough_thickness_id: int,
        db: AsyncSession = Depends(get_async_session)
):
    price_response = await get_pizza_price(pizza_id, dough_type_id, dough_thickness_id, db)

    return price_response


@router.get("/pizzas/")
async def read_pizzas(pizza_type_ids: Optional[List[int]] = Query(None),
                      search_query: Optional[str] = None,
                      page: int = Query(1, ge=1),
                      limit: int = Query(4, ge=1),
                      sort_by: Optional[str] = Query(None, description="Sort by field: 'orders' or 'name'"),
                      sort_order: str = Query("asc", description="Sort order: 'asc' or 'desc'"),
                      db: AsyncSession = Depends(get_async_session)):
    offset = (page - 1) * limit

    pizzas = await get_pizzas(db, offset, limit, pizza_type_ids, search_query, sort_by, sort_order)
    total_pages = await get_count_pizza_pages(db, limit, pizza_type_ids, search_query)

    return {"pizzas": pizzas, "total_pages": total_pages}


@router.post("/cart/create_or_update", status_code=201)
async def item_create_or_update_in_cart_router(item: AddToCartSchemaAction, db: AsyncSession = Depends(get_async_session), user: User = Depends(current_user)):
    return await create_or_update_item_in_cart(item, db, user)




@router.get("/read_cart_amount_and_count/", response_model=ReadUserCartSumAndCount)
async def cart_amount_and_count_read_router(db: AsyncSession = Depends(get_async_session), user: User = Depends(current_user)):
    return await read_cart_amount_and_count(db, user)


@router.post("/read_items_quantity/", response_model=List[ReadItemQuantity])
async def item_quantity_read_router(items: List[AddToCartSchema], db: AsyncSession = Depends(get_async_session), user: User = Depends(current_user)):
    return await get_pizza_count_in_cart(items, db, user)


@router.delete("/delete_all_user_cart_items", response_model=DeleteCartItemsResponse)
async def all_user_cart_items_delete_router(db: AsyncSession = Depends(get_async_session), user: User = Depends(current_user)):
    return await delete_all_user_cart_items(db, user)

@router.delete("/delete_user_cart_item", response_model=DeleteCartItemResponse)
async def all_user_cart_item_delete_router(item: AddToCartSchema, db: AsyncSession = Depends(get_async_session), user: User = Depends(current_user)):
    return await delete_user_cart_item(item, db, user)

@router.get("/user/cart", response_model=UserCartResponse)
async def get_user_cart_router(db: AsyncSession = Depends(get_async_session), user: User = Depends(current_user)):
    return await get_user_cart(db, user.id)