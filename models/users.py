from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.orders import OrderHeader
from models.restaurants import Restaurant


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(unique=True)
    users: Mapped[List["User"]] = relationship(back_populates='role')

    def __repr__(self):
        return f"<Role {self.description}>"


class User(Base):
    __tablename__ = "users"
    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(unique=True)
    full_name: Mapped[str] = mapped_column(nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), nullable=False)
    role: Mapped["Role"] = relationship(back_populates='users')
    saved_locations: Mapped[List["ClientSavedLocation"]] = relationship(back_populates='user')
    restaurant: Mapped["Restaurant"] = relationship(back_populates="owner")
    orders: Mapped[List["OrderHeader"]] = relationship(back_populates="client")

    def __repr__(self):
        return f"<User {self.role} - {self.full_name}>"


class ClientSavedLocation(Base):
    __tablename__ = "client_saved_locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.telegram_id'), nullable=False)
    location_name: Mapped[str] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    user: Mapped["User"] = relationship(back_populates='saved_locations')
    orders: Mapped[List["OrderHeader"]] = relationship(back_populates="client_location")

    def __repr__(self):
        return f"<{self.user}'s location - {self.location_name}>"
