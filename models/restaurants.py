from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base import Base
from models.orders import OrderHeader, OrderItem
from models.users import User


class Restaurant(Base):
    __tablename__ = "restaurants"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), nullable=False)
    tags: Mapped[List["RestaurantTag"]] = relationship(back_populates="restaurant")
    locations: Mapped[List["RestaurantLocation"]] = relationship(back_populates="restaurant")
    owner: Mapped[User] = relationship(back_populates="restaurant")
    menu_categories: Mapped[List["MenuCategory"]] = relationship(back_populates="restaurant")


class RestaurantTag(Base):
    __tablename__ = "restaurant_tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(nullable=False)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    restaurant: Mapped["Restaurant"] = relationship(back_populates="tags")


class RestaurantLocation(Base):
    __tablename__ = "restaurant_locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurant.id"))
    location_description: Mapped[str] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    restaurant: Mapped["Restaurant"] = relationship(back_populates="locations")
    orders: Mapped[List["OrderHeader"]] = relationship(back_populates="restaurant_location")


class MenuCategory(Base):
    __tablename__ = "menu_categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    restaurant_id: Mapped[int] = mapped_column(nullable=False)
    restaurant: Mapped["Restaurant"] = relationship(back_populates="menu_categories")
    items: Mapped[List["MenuItem"]] = relationship(back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("menu_categories.id"))
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[float] = mapped_column(nullable=False)
    category: Mapped[MenuCategory] = relationship(back_populates="items")
    tags: Mapped[List["MenuItemTag"]] = relationship(back_populates="items")
    orders: Mapped[List["OrderItem"]] = relationship(back_populates="menu_item")


class MenuItemTag(Base):
    __tablename__ = "menu_item_tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    items: Mapped[List["MenuItem"]] = relationship(back_populates="tags")

