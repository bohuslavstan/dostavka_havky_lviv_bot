from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base import Base
from models.restaurants import RestaurantLocation, MenuItem
from models.users import User, ClientSavedLocation


class OrderHeader(Base):
    __tablename__ = "order_headers"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    restaurant_location_id: Mapped[int] = mapped_column(ForeignKey("restaurant_locations.id"))
    client_location_id: Mapped[int] = mapped_column(ForeignKey("client_saved_locations.id"))
    comment: Mapped[str] = mapped_column(nullable=True)
    client: Mapped["User"] = relationship(back_populates="orders")
    restaurant_location: Mapped["RestaurantLocation"] = relationship(back_populates="orders")
    client_location: Mapped["ClientSavedLocation"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="header")


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_header_id: Mapped[int] = mapped_column(ForeignKey("order_headers.id"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    quantity: Mapped[int] = mapped_column(nullable=False)
    header: Mapped["OrderHeader"] = relationship(back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship(back_populates="orders")
