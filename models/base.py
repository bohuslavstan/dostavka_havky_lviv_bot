from datetime import datetime, timedelta
from typing import List

import yaml
from sqlalchemy import create_engine, CheckConstraint, select, ForeignKey, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session


class Base(DeclarativeBase):
    pass

with open("config.yml", "r") as file:
    config = yaml.safe_load(file)
engine = create_engine(config["database"])


class User(Base):
    __tablename__ = "users"
    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(unique=True)
    full_name: Mapped[str] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(CheckConstraint("role IN ('client', 'restaurant_owner', 'delivery_guy', 'admin')"),
                                      default="client", nullable=False)
    saved_locations: Mapped[List["ClientSavedLocation"]] = relationship(back_populates='user')
    restaurant: Mapped["Restaurant"] = relationship(back_populates="owner")
    orders: Mapped[List["OrderHeader"]] = relationship(back_populates="client", foreign_keys="[OrderHeader.client_id]")
    deliveries: Mapped[List["OrderHeader"]] = relationship(back_populates="delivery_guy", foreign_keys="[OrderHeader.delivery_guy_id]")
    promotion_application: Mapped["PromotionApplication"] = relationship(back_populates="user")
    delivery_guy_statuses: Mapped[List["DeliveryGuyStatus"]] = relationship(back_populates="delivery_guy")

    def __repr__(self):
        return f"<User {self.role} - {self.full_name}>"

    def __str__(self):
        with Session(engine) as session:
            session.add(self)
            match self.role:
                case "admin":
                    role_ua = "Адміністратор"
                    details = ""
                case "delivery_guy":
                    role_ua = "Кур`єр"
                    details = f"{len(self.deliveries)} доставок\n"
                case "restaurant_owner":
                    role_ua = "Менеджер ресторану"
                    details = f"Ресторан: {self.restaurant.name if self.restaurant else 'немає'}\n"
                case _:
                    role_ua = "Клієнт"
                    details = ""
            return f"{self.full_name} (@{self.username})\n" \
                   f"{role_ua}\n" \
                   f"{details}" \
                   f"{len(self.orders)} замовлень"

    @classmethod
    def register(cls, telegram_id: int, username: str, phone_number: str, full_name: str = None):
        with Session(engine) as session:
            if not session.get(cls, telegram_id):
                session.add(cls(telegram_id=telegram_id,
                                username=username,
                                phone_number=phone_number,
                                full_name=full_name))
                session.commit()
            else:
                raise IntegrityError

    @classmethod
    def find(cls, role=None):
        with Session(engine) as session:
            return session.scalars(select(cls).where(cls.role == role)).all()

    @classmethod
    def get(cls, telegram_id: int):
        with Session(engine) as session:
            return session.scalar(select(cls).where(cls.telegram_id == telegram_id)).first()

    def promote(self, role: str):
        with Session(engine) as session:
            print(f"{self.role} == {role}")
            if self.role != role:
                self.role = role
                session.commit()
            else:
                raise IntegrityError

    def get_restaurant(self):
        with Session(engine) as session:
            session.add(self)
            return self.restaurant


class DeliveryGuyStatus(Base):
    __tablename__ = "delivery_guy_statuses"
    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_guy_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    active: Mapped[bool] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    delivery_guy: Mapped["User"] = relationship(back_populates="delivery_guy_statuses")


    @classmethod
    def last_status(cls, delivery_guy_id):
        with Session(engine) as session:
            return session.scalars(select(cls).where(cls.delivery_guy_id == delivery_guy_id).order_by(desc(cls.id))).first()

    @classmethod
    def check_in(cls, delivery_guy_id: int, status: bool):
        with Session(engine) as session:
            last_status = session.scalars(select(cls).where(cls.delivery_guy_id == delivery_guy_id).order_by(desc(cls.id))).first()
            if last_status and last_status.active == status:
                raise IntegrityError
            else:
                new_status = cls(delivery_guy_id=delivery_guy_id,
                                 active=status,
                                 timestamp=datetime.now())
                session.add(new_status)
                session.commit()
            if last_status:
                return new_status.timestamp - last_status.timestamp



class PromotionApplication(Base):
    __tablename__ = "user_promotion_applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    role_to_promote: Mapped[str] = mapped_column(CheckConstraint("role_to_promote IN ('restaurant_owner', 'delivery_guy')"),
                                      nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    closed: Mapped[bool] = mapped_column(default=False)
    user: Mapped["User"] = relationship(back_populates="promotion_application")

    @classmethod
    def create(cls, user_id: int, role_to_promote: str):
        with Session(engine) as session:
            user = User.get(user_id)
            print(f"{user.telegram_id}\n{role_to_promote}\n{datetime.now()}")
            print(session.scalars(select(cls).where(cls.user == user)))
            if not session.scalars(select(cls).where(cls.user == user)).first():
                session.add(cls(user_id=user.telegram_id,
                                role_to_promote=role_to_promote,
                                timestamp=datetime.now()))
                if role_to_promote == "delivery_guy":
                    DeliveryGuyStatus(delivery_guy_id=user.telegram_id,
                                      active=False,
                                      timestamp=datetime.now())
                session.commit()
            else:
                raise IntegrityError

    @classmethod
    def find(cls, user_id: int):
        with Session(engine) as session:
            return session.scalars(select(cls).where(cls.user_id == user_id and not cls.closed)).first()

    @classmethod
    def all_open(cls, role):
        with Session(engine) as session:
            return session.scalars(select(cls).where(cls.role_to_promote == role and not cls.closed)).all()

    @classmethod
    def close(cls, appl_id: int):
        with Session(engine) as session:
            appl = session.get(cls, appl_id)
            appl.closed = True
            session.commit()

    @classmethod
    def promote(cls, user_id: int):
        with Session(engine) as session:
            appl = session.scalars(select(cls).where(cls.user_id == user_id and not cls.closed)).first()
            appl.user.promote(appl.role_to_promote)
            appl.closed = True
            role_to_promote = appl.role_to_promote
            session.commit()
        if role_to_promote == "delivery_guy":
            DeliveryGuyStatus.check_in(delivery_guy_id=user_id, status=False)
        return role_to_promote

    def __str__(self):
        with Session(engine) as session:
            session.add(self)
            _str = f"{self.user.full_name} (@{self.user.username})\n" \
                   f"{'Кур`єр' if self.role_to_promote == 'delivery_guy' else 'Власник ресторану'}\n" \
                   f"{self.timestamp}"
        return _str


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

    @classmethod
    def create(cls, user: User, location_name, longitude, latitude):
        with Session(engine) as session:
            if not location_name in session.execute(select(cls).where(cls.user == user)):
                session.add(cls(user=user,
                                location_name=location_name,
                                longitude=longitude,
                                latitude=latitude))
                session.commit()
            else:
                raise IntegrityError

    def delete(self):
        with Session(engine) as session:
            session.delete(self)
            session.commit()

class Restaurant(Base):
    __tablename__ = "restaurants"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str] = mapped_column(nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), nullable=False, unique=True)
    tags: Mapped[List["RestaurantTag"]] = relationship(back_populates="restaurant")
    locations: Mapped[List["RestaurantLocation"]] = relationship(back_populates="restaurant")
    owner: Mapped[User] = relationship(back_populates="restaurant")
    menu_categories: Mapped[List["MenuCategory"]] = relationship(back_populates="restaurant")
    item_tags: Mapped[List["MenuItemTag"]] = relationship(back_populates="restaurant")

    def __repr__(self):
        return f"<Restaurant '{self.name}'>"

    def __str__(self):
        with Session(engine) as session:
            session.add(self)
            _str = f"Заклад '{self.name}\n" \
                   f"{', '.join(str(x) for x in self.tags) if self.tags else ''}\n'" \
                   f"{self.description}\n"
        return _str

    @classmethod
    def create(cls, name: str, description: str, owner_id: int):
        with Session(engine) as session:
            owner = User.get(owner_id)
            session.add(owner)
            if owner.restaurant:
                raise IntegrityError
            elif owner.role != "restaurant_owner":
                raise IntegrityError
            elif session.execute(select(cls).where(cls.name == name)).all:
                raise IntegrityError
            else:
                session.add(cls(name=name,
                                description=description,
                                owner=owner))

    @classmethod
    def find(cls, owner_id: int):
        with Session(engine) as session:
            return session.scalars(select(cls).where(cls.owner_id == owner_id)).first()

    def list_categories(self):
        with Session(engine) as session:
            session.add(self)
            return [*self.menu_categories]

    def create_category(self, category_name):
        with Session(engine) as session:
            session.add(self)
            session.add(MenuCategory(name=category_name, restaurant=self))
            session.commit()


class RestaurantTag(Base):
    __tablename__ = "restaurant_tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(nullable=False)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    restaurant: Mapped["Restaurant"] = relationship(back_populates="tags")

    def __repr__(self):
        return f"<Tag '{self.tag} of restaurant '{self.restaurant.__repr__()}'>"


class RestaurantLocation(Base):
    __tablename__ = "restaurant_locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    location_description: Mapped[str] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    restaurant: Mapped["Restaurant"] = relationship(back_populates="locations")
    orders: Mapped[List["OrderHeader"]] = relationship(back_populates="restaurant_location")

    def __repr__(self):
        return f"<Restaurant '{self.restaurant.__repr__()}' at {self.location_description}>"


class MenuCategory(Base):
    __tablename__ = "menu_categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    restaurant: Mapped["Restaurant"] = relationship(back_populates="menu_categories")
    items: Mapped[List["MenuItem"]] = relationship(back_populates="category")

    def __repr__(self):
        return f"<Restaurant category '{self.name}' of '{self.restaurant.__repr__()}'>"

    def __str__(self):
        return self.name

    @classmethod
    def get(cls, category_id):
        with Session(engine) as session:
            return session.scalars(select(cls).where(cls.id == category_id)).first()

    def change_name(self, name):
        with Session(engine) as session:
            session.add(self)
            self.name = name
            session.commit()

    @classmethod
    def list_items(cls, category_id):
        with Session(engine) as session:
            category = session.scalars(select(cls).where(cls.id == category_id)).first()
            return category.items


class MenuItemTagToMenuItem(Base):
    __tablename__ = "menu_item_tag_to_menu_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('menu_items.id'))
    tag_id: Mapped[int] = mapped_column(ForeignKey('menu_item_tags.id'))


class MenuItem(Base):
    __tablename__ = "menu_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("menu_categories.id"))
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[float] = mapped_column(nullable=False)
    category: Mapped[MenuCategory] = relationship(back_populates="items")
    tags: Mapped[List["MenuItemTag"]] = relationship(back_populates="items", secondary="menu_item_tag_to_menu_items")
    orders: Mapped[List["OrderItem"]] = relationship(back_populates="menu_item")

    def __repr__(self):
        return f"<Item '{self.name}' from '{self.category.restaurant.__repr__()}'>"

    @classmethod
    def create(cls, name, category_id, description, price):
        with Session(engine) as session:
            menu_item = cls(name=name,
                            category_id=category_id,
                            description=description,
                            price=price)
            session.add(menu_item)
            session.commit()
        return menu_item


class MenuItemTag(Base):
    __tablename__ = "menu_item_tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    items: Mapped[List["MenuItem"]] = relationship(back_populates="tags", secondary="menu_item_tag_to_menu_items")
    restaurant: Mapped["Restaurant"] = relationship(back_populates="item_tags")

    def __repr__(self):
        return f"<Item tag '{self.name}' of '{self.restaurant.__repr__()}'>"


class OrderHeader(Base):
    __tablename__ = "order_headers"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    restaurant_location_id: Mapped[int] = mapped_column(ForeignKey("restaurant_locations.id"))
    client_location_id: Mapped[int] = mapped_column(ForeignKey("client_saved_locations.id"))
    delivery_guy_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"))
    comment: Mapped[str] = mapped_column(nullable=True)
    paid: Mapped[bool] = mapped_column(default=False)
    client: Mapped["User"] = relationship(back_populates="orders", foreign_keys=[client_id])
    restaurant_location: Mapped["RestaurantLocation"] = relationship(back_populates="orders")
    client_location: Mapped["ClientSavedLocation"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="header")
    statuses: Mapped[List["OrderStatusUpdate"]] = relationship(back_populates="header")
    delivery_guy: Mapped["User"] = relationship(back_populates="deliveries", foreign_keys=[delivery_guy_id])


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_header_id: Mapped[int] = mapped_column(ForeignKey("order_headers.id"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    quantity: Mapped[int] = mapped_column(nullable=False)
    header: Mapped["OrderHeader"] = relationship(back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship(back_populates="orders")


class OrderStatusUpdate(Base):
    __tablename__ = "order_status_updates"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_header_id: Mapped[int] = mapped_column(ForeignKey("order_headers.id"))
    status: Mapped[str] = mapped_column(CheckConstraint("status IN ('CREATED', 'CHOSEN BY DELIVERY GUY', 'PREPARED', "
                                                        "'PICKED BY DELIVERY GUY', 'DELIVERED')"))
    status_ts: Mapped[datetime] = mapped_column(nullable=False)
    header: Mapped["OrderHeader"] = relationship(back_populates="statuses")
