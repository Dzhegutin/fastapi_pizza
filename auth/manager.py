from typing import Optional, List

from fastapi_users import IntegerIDMixin, BaseUserManager, schemas, models, exceptions

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from auth.database import User, get_user_db
from auth.router import create_user_pizza_cart_item
from config import SECRETMANAGER
from db import AsyncSessionLocal
from schemas import AddToCartSchema


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRETMANAGER
    verification_token_secret = SECRETMANAGER

    async def on_after_register(self, user: User, request: Optional[Request] = None,
                                cart_items: List[AddToCartSchema] = None,
                                db: AsyncSession = None):
        if cart_items:
            await create_user_pizza_cart_item(user.id, cart_items, db)

        print(f"User {user.id} has registered.")

    async def create(
            self,
            user_create: schemas.UC,
            safe: bool = False,
            request: Optional[Request] = None,
    ) -> models.UP:
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
        )
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)
        user_dict["name"] = "Васильич"
        cart = user_dict.pop("cart")

        # Получение сеанса базы данных и передача в метод on_after_register
        created_user = await self.user_db.create(user_dict)
        async with AsyncSessionLocal() as db:
            await self.on_after_register(created_user, request, cart, db)

        return created_user


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
