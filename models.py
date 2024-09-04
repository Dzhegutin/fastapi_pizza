from sqlalchemy import Table, Column, Integer, ForeignKey, UniqueConstraint, String, Float, DateTime, func
from sqlalchemy.orm import relationship

from db import Base
from auth.database import User

pizza_type_pizza = Table(
    'pizza_type_pizza',
    Base.metadata,
    Column('pizza_id', Integer, ForeignKey('pizzas.id'), primary_key=True),
    Column('pizza_type_id', Integer, ForeignKey('pizza_types.id'), primary_key=True)
)

pizza_dough_type = Table(
    'pizza_dough_type',
    Base.metadata,
    Column('pizza_id', Integer, ForeignKey('pizzas.id'), primary_key=True),
    Column('dough_type_id', Integer, ForeignKey('dough_types.id'), primary_key=True)
)

pizza_dough_thickness = Table(
    'pizza_dough_thickness',
    Base.metadata,
    Column('pizza_id', Integer, ForeignKey('pizzas.id'), primary_key=True),
    Column('dough_thickness_id', Integer, ForeignKey('dough_thicknesses.id'), primary_key=True)
)
class UserPizzaCart(Base):
    __tablename__ = 'user_pizza_cart'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    pizza_id = Column(Integer, ForeignKey('pizzas.id'), primary_key=True)
    dough_type_id = Column(Integer, ForeignKey('dough_types.id'), primary_key=True)
    dough_thickness_id = Column(Integer, ForeignKey('dough_thicknesses.id'), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint('user_id', 'pizza_id', 'dough_type_id', 'dough_thickness_id', name='_user_pizza_uc'),
    )

    user = relationship("User", back_populates="cart")
    pizza = relationship("Pizza", back_populates="users_in_cart")


class Pizza(Base):
    __tablename__ = "pizzas"

    id = Column(Integer, primary_key=True, index=True)
    pizza_name = Column(String)
    pizza_img = Column(String)

    pizza_types = relationship("PizzaType", secondary=pizza_type_pizza, back_populates="pizzas")

    dough_types = relationship("DoughType", secondary=pizza_dough_type, back_populates="pizzas")
    dough_thicknesses = relationship("DoughThickness", secondary=pizza_dough_thickness, back_populates="pizzas")

    prices = relationship("PizzaPrice", back_populates="pizza")

    users_in_cart = relationship("UserPizzaCart", back_populates="pizza")
    orders = relationship("OrderItem", back_populates="pizza")


class PizzaPrice(Base):
    __tablename__ = "pizza_prices"

    pizza_id = Column(Integer, ForeignKey('pizzas.id'), primary_key=True)
    dough_type_id = Column(Integer, ForeignKey('dough_types.id'), primary_key=True)
    dough_thickness_id = Column(Integer, ForeignKey('dough_thicknesses.id'), primary_key=True)
    price = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint('pizza_id', 'dough_type_id', 'dough_thickness_id', name='_pizza_price_uc'),)

    pizza = relationship("Pizza", back_populates="prices")
    dough_type = relationship("DoughType")
    dough_thickness = relationship("DoughThickness")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    pizza_id = Column(Integer, ForeignKey('pizzas.id'))
    dough_type_id = Column(Integer, ForeignKey('dough_types.id'))
    dough_thickness_id = Column(Integer, ForeignKey('dough_thicknesses.id'))

    pizza = relationship("Pizza", back_populates="orders")
    order = relationship("Order", back_populates="order_items")
    dough_type = relationship("DoughType")
    dough_thickness = relationship("DoughThickness")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    total_price = Column(Float)

    order_items = relationship("OrderItem", back_populates="order")


class DoughType(Base):
    __tablename__ = "dough_types"

    id = Column(Integer, primary_key=True, index=True)
    dough = Column(String, unique=True)

    pizzas = relationship("Pizza", secondary=pizza_dough_type, back_populates="dough_types")


class DoughThickness(Base):
    __tablename__ = "dough_thicknesses"

    id = Column(Integer, primary_key=True, index=True)
    thickness = Column(Float, unique=True)

    pizzas = relationship("Pizza", secondary=pizza_dough_thickness, back_populates="dough_thicknesses")


class PizzaType(Base):
    __tablename__ = "pizza_types"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, unique=True)

    pizzas = relationship("Pizza", secondary=pizza_type_pizza, back_populates="pizza_types")
