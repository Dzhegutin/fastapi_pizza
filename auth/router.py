from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from models import UserPizzaCart
from schemas import AddToCartSchema


async def create_user_pizza_cart_item(user_id, cart_items: List[AddToCartSchema], db: AsyncSession):
    for item in cart_items:
        new_cart_item = UserPizzaCart(
            user_id=user_id,
            pizza_id=item['pizza_id'],
            dough_type_id=item['dough_type_id'],
            dough_thickness_id=item['dough_thickness_id'],
            quantity=item['quantity']
        )
        db.add(new_cart_item)
    await db.commit()
