from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy import desc, asc, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, aliased, selectinload
from models import User, Pizza, DoughType, DoughThickness, PizzaType, Order, PizzaPrice, pizza_dough_thickness, \
    pizza_dough_type, OrderItem, UserPizzaCart
from schemas import PizzaCreate, DoughTypeGetOrCreate, DoughThicknessGetOrCreate, PizzaTypeGetOrCreate, AddToCartSchema, \
    PizzaPriceResponse, PizzaPriceBase, PizzaInCartResponse, UserCartResponse


async def create_pizza_type(type: str, db: AsyncSession):
    try:
        new_pizza_type = PizzaType(type=type)
        db.add(new_pizza_type)
        await db.commit()
        await db.refresh(new_pizza_type)
        return new_pizza_type
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error adding pizza_type: {str(e)}")


async def create_pizza_dough_type(dough: str, db: AsyncSession):
    try:
        new_dough_type = DoughType(dough=dough)
        db.add(new_dough_type)
        await db.commit()
        await db.refresh(new_dough_type)
        return new_dough_type
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error adding dough_type: {str(e)}")


async def create_dough_thickness(dough_thickness: float, db: AsyncSession):
    try:
        new_dough_thickness = DoughThickness(thickness=dough_thickness)
        db.add(new_dough_thickness)
        await db.commit()
        await db.refresh(new_dough_thickness)
        return new_dough_thickness
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error adding dough_thickness: {str(e)}")


async def read_pizza_types(db: AsyncSession):
    pizza_types = await db.execute(select(PizzaType))
    return pizza_types.scalars().all()


# вспомогательная фича для create_pizza
async def get_dough_types_and_thicknesses(new_pizza_id: int, db: AsyncSession):
    # Запрос на получение dough_types
    result = await db.execute(
        select(pizza_dough_type.c.dough_type_id).where(pizza_dough_type.c.pizza_id == new_pizza_id))
    dough_types_lst = [row[0] for row in result.fetchall()]

    # Запрос на получение dough_thicknesses
    result = await db.execute(
        select(pizza_dough_thickness.c.dough_thickness_id).where(pizza_dough_thickness.c.pizza_id == new_pizza_id))
    dough_thickness_lst = [row[0] for row in result.fetchall()]
    return dough_types_lst, dough_thickness_lst


async def create_pizza(db: AsyncSession, pizza: PizzaCreate):
    try:
        new_pizza = Pizza(
            pizza_name=pizza.pizza_name,
            pizza_img=pizza.pizza_img,
        )

        if pizza.dough_types:
            stmt = select(DoughType).where(DoughType.id.in_(pizza.dough_types))
            result = await db.execute(stmt)
            new_pizza.dough_types = result.scalars().all()

        if pizza.dough_thicknesses:
            stmt = select(DoughThickness).where(DoughThickness.id.in_(pizza.dough_thicknesses))
            result = await db.execute(stmt)
            new_pizza.dough_thicknesses = result.scalars().all()

        if pizza.pizza_types:
            stmt = select(PizzaType).where(PizzaType.id.in_(pizza.pizza_types))
            result = await db.execute(stmt)
            new_pizza.pizza_types = result.scalars().all()

        db.add(new_pizza)
        await db.commit()

        await db.refresh(new_pizza)

        dough_types_lst, dough_thickness_lst = await get_dough_types_and_thicknesses(new_pizza.id, db)

        for price_set in pizza.price_sets:
            if price_set.dough_type_id in dough_types_lst and price_set.dough_thickness_id in dough_thickness_lst:
                new_price = PizzaPrice(
                    pizza_id=new_pizza.id,
                    dough_type_id=price_set.dough_type_id,
                    dough_thickness_id=price_set.dough_thickness_id,
                    price=price_set.price
                )
                db.add(new_price)

        await db.commit()

        stmt = select(Pizza).options(
            selectinload(Pizza.pizza_types),
            selectinload(Pizza.dough_types),
            selectinload(Pizza.dough_thicknesses),
            selectinload(Pizza.prices)
        ).where(Pizza.id == new_pizza.id)

        result = await db.execute(stmt)
        full_pizza = result.scalar_one()

        await db.commit()

        return full_pizza

    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise


async def get_pizza_price(pizza_id: int, dough_type_id: int, dough_thickness_id: int, db: AsyncSession):
    result = await db.execute(
        select(PizzaPrice).filter(
            PizzaPrice.pizza_id == pizza_id,
            PizzaPrice.dough_type_id == dough_type_id,
            PizzaPrice.dough_thickness_id == dough_thickness_id
        )
    )

    pizza_price = result.scalars().first()

    await db.commit()

    if pizza_price:
        return pizza_price
    else:
        raise HTTPException(status_code=404, detail="Price not found for the given pizza configuration")


async def get_pizzas(db: AsyncSession,
                     offset: int,
                     limit: int,
                     pizza_type_ids: Optional[List[int]] = None,
                     search_query: Optional[str] = None,
                     sort_by: Optional[str] = None,
                     sort_order: Optional[str] = "asc"):
    # Подзапрос для подсчета количества заказов
    order_count_subquery = (
        select(OrderItem.pizza_id, func.count(OrderItem.id).label('order_count'))
        .group_by(OrderItem.pizza_id)
        .subquery()
    )

    # Основной запрос
    stmt = (
        select(Pizza, func.coalesce(order_count_subquery.c.order_count, 0).label('order_count'))
        .outerjoin(order_count_subquery, Pizza.id == order_count_subquery.c.pizza_id)
        .options(
            joinedload(Pizza.dough_types),
            joinedload(Pizza.dough_thicknesses),
            joinedload(Pizza.pizza_types),
            joinedload(Pizza.prices),
            joinedload(Pizza.orders)
        )
    )

    if pizza_type_ids:
        stmt = stmt.join(Pizza.pizza_types).filter(PizzaType.id.in_(pizza_type_ids))

    if search_query:
        stmt = stmt.filter(Pizza.pizza_name.ilike(f'%{search_query}%'))

    if sort_by:
        if sort_by == "orders":
            sort_column = 'order_count'
        elif sort_by == "name":
            sort_column = Pizza.pizza_name
        else:
            raise ValueError("Invalid sort_by value")

        if sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))

    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)

    pizzas = result.scalars().unique().all()
    return pizzas


async def get_count_pizza_pages(db: AsyncSession,
                                limit: int,
                                pizza_type_ids: Optional[List[int]] = None,
                                search_query: Optional[str] = None):
    stmt = select(func.count(Pizza.id))

    if pizza_type_ids:
        stmt = stmt.join(Pizza.pizza_types).filter(PizzaType.id.in_(pizza_type_ids))

    if search_query:
        stmt = stmt.filter(Pizza.pizza_name.ilike(f'%{search_query}%'))

    result = await db.execute(stmt)
    total_count = result.scalar_one()

    total_pages = (total_count + limit - 1) // limit

    return total_pages


async def create_or_update_item_in_cart(item: AddToCartSchema, db: AsyncSession, user: User):
    pizza_result = await db.execute(select(Pizza).filter(Pizza.id == item.pizza_id))
    pizza = pizza_result.scalar_one_or_none()

    if not pizza:
        raise HTTPException(status_code=404, detail="Pizza not found")

    cart_item_result = await db.execute(select(UserPizzaCart).filter_by(
        user_id=user.id,
        pizza_id=item.pizza_id,
        dough_type_id=item.dough_type_id,
        dough_thickness_id=item.dough_thickness_id
    ))
    cart_item = cart_item_result.scalar_one_or_none()

    if cart_item:
        if item.action == "increase":
            cart_item.quantity += 1
        elif item.action == "decrease":
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                await db.delete(cart_item)
                await db.commit()
                return {"message": "Pizza removed from cart", "quantity": 0}

        await db.commit()
        return {"message": f"Pizza quantity {'increased' if item.action == 'increase' else 'decreased'} successfully",
                "quantity": cart_item.quantity}

    else:
        if item.action == "increase":
            try:
                cart_item = UserPizzaCart(
                    user_id=user.id,
                    pizza_id=item.pizza_id,
                    dough_type_id=item.dough_type_id,
                    dough_thickness_id=item.dough_thickness_id,
                    quantity=1
                )
                db.add(cart_item)
                await db.commit()
                return {"message": "Pizza added to cart successfully", "quantity": cart_item.quantity}
            except Exception as e:
                raise HTTPException(status_code=404, detail=f"Error: {e}")

        else:
            raise HTTPException(status_code=404, detail="Pizza not found in cart to decrease")


async def read_cart_amount_and_count(db: AsyncSession, user: User):
    result = await db.execute(
        select(
            func.sum(UserPizzaCart.quantity).label('total_quantity'),
            func.sum(UserPizzaCart.quantity * PizzaPrice.price).label('total_price')
        )
        .join(PizzaPrice,
              (UserPizzaCart.pizza_id == PizzaPrice.pizza_id) &
              (UserPizzaCart.dough_type_id == PizzaPrice.dough_type_id) &
              (UserPizzaCart.dough_thickness_id == PizzaPrice.dough_thickness_id))
        .filter(UserPizzaCart.user_id == user.id)
    )

    total_quantity, total_price = result.one_or_none()

    total_quantity = total_quantity or 0
    total_price = total_price or 0.0

    return {"user_cart_sum": total_price, "user_cart_count": total_quantity}


async def get_pizza_count_in_cart(items: List[AddToCartSchema], db: AsyncSession, user: User):
    dataset = []
    for item in items:
        result = await db.execute(
            select(UserPizzaCart).filter(
                UserPizzaCart.pizza_id == item.pizza_id,
                UserPizzaCart.dough_type_id == item.dough_type_id,
                UserPizzaCart.dough_thickness_id == item.dough_thickness_id,
                UserPizzaCart.user_id == user.id
            )
        )

        pizza_obj = result.scalars().first()

        if pizza_obj:
            dataset.append({"pizza_id": pizza_obj.pizza_id,
                            "dough_type_id": pizza_obj.dough_type_id,
                            "dough_thickness_id": pizza_obj.dough_thickness_id,
                            "quantity": pizza_obj.quantity})
        else:
            dataset.append({"pizza_id": item.pizza_id,
                            "dough_type_id": item.dough_type_id,
                            "dough_thickness_id": item.dough_thickness_id,
                            "quantity": 0})
    return dataset


async def delete_all_user_cart_items(db: AsyncSession, user: User):
    result = await db.execute(select(UserPizzaCart).filter_by(user_id=user.id))
    cart_items = result.scalars().all()

    if not cart_items:
        raise HTTPException(status_code=404, detail="No items in the cart to delete")

    for item in cart_items:
        await db.delete(item)

    await db.commit()

    return {"message": "All items deleted from cart", "deleted_count": len(cart_items)}


async def delete_user_cart_item(item: AddToCartSchema, db: AsyncSession, user: User):
    result = await db.execute(select(UserPizzaCart).filter_by(user_id=user.id,
                                                              pizza_id=item.pizza_id,
                                                              dough_type_id=item.dough_type_id,
                                                              dough_thickness_id=item.dough_thickness_id))
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="No item in the cart to delete")

    await db.delete(cart_item)
    await db.commit()

    return {"message": "Item deleted from cart",
            "pizza_id": cart_item.pizza_id,
            "dough_type_id": cart_item.dough_type_id,
            "dough_thickness_id": cart_item.dough_thickness_id,
            "quantity": cart_item.quantity}


# async def get_user_cart_items(db: AsyncSession, user: User):
#     await db.execute(select(UserPizzaCart))
#
#     pass

async def get_user_cart(db: AsyncSession, user_id: int):
    # Запрос для получения всех элементов корзины пользователя с загрузкой связанной пиццы
    stmt = (
        select(UserPizzaCart)
        .filter(UserPizzaCart.user_id == user_id)
        .options(
            joinedload(UserPizzaCart.pizza).joinedload(Pizza.dough_types),
            joinedload(UserPizzaCart.pizza).joinedload(Pizza.dough_thicknesses),
            joinedload(UserPizzaCart.pizza).joinedload(Pizza.prices)
        )
    )
    result = await db.execute(stmt)
    cart_items = result.unique().scalars().all()  # Добавлен вызов .unique()

    if not cart_items:
        raise HTTPException(status_code=404, detail="Cart is empty or user not found")

    response = []
    for item in cart_items:
        pizza = item.pizza
        # Поиск цены пиццы
        price_result = await db.execute(
            select(PizzaPrice).filter_by(
                pizza_id=item.pizza_id,
                dough_type_id=item.dough_type_id,
                dough_thickness_id=item.dough_thickness_id
            )
        )
        price = price_result.scalar_one_or_none()
        if price is None:
            raise HTTPException(status_code=500, detail="Price not found for pizza configuration")

        # Находим соответствующий dough_type и dough_thickness
        dough_type = next((dt.dough for dt in pizza.dough_types if dt.id == item.dough_type_id), None)
        dough_thickness = next((dt.thickness for dt in pizza.dough_thicknesses if dt.id == item.dough_thickness_id), None)

        response.append(PizzaInCartResponse(
            pizza_id=pizza.id,
            pizza_name=pizza.pizza_name,
            pizza_img=pizza.pizza_img,
            dough_type_id=item.dough_type_id,
            dough_type=dough_type,
            dough_thickness_id=item.dough_thickness_id,
            dough_thickness=dough_thickness,
            quantity=item.quantity,
            total_price=price.price * item.quantity
        ))

    return UserCartResponse(pizzas=response)