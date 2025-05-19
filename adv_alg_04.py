# Реализовать базовые классы для работы с БД с использованием
# SQLAlchemy. Реализовать подключение и абстрактные классы

from abc import ABC, abstractmethod
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from contextlib import contextmanager
import psycopg2

def create_database():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="yourpassword",
            host="localhost"
        )
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM pg_database WHERE datname='synregy'")
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("CREATE DATABASE synregy")
            print("База данных 'synregy' успешно создана")
        else:
            print("База данных 'synregy' уже существует")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")

create_database()

Base = declarative_base()

class DatabaseConnection:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL') or "postgresql://postgres:yourpassword@localhost:5432/synregy"
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

class BaseTable(Base):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @abstractmethod
    def to_dict(self):
        pass

class Supplier(BaseTable):
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(String(200))

    products = relationship("Product", back_populates="supplier")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "address": self.address
        }

class Product(BaseTable):
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    supplier_id = Column(Integer, ForeignKey('supplier.id'))

    supplier = relationship("Supplier", back_populates="products")
    orders = relationship("OrderItem", back_populates="product")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "quantity": self.quantity,
            "supplier_id": self.supplier_id
        }

class Order(BaseTable):
    order_date = Column(DateTime, default=datetime.utcnow)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(20))
    customer_email = Column(String(100))
    status = Column(String(50), default="created")
    total_amount = Column(Float, default=0.0)

    items = relationship("OrderItem", back_populates="order")

    def to_dict(self):
        return {
            "id": self.id,
            "order_date": self.order_date.isoformat(),
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_email": self.customer_email,
            "status": self.status,
            "total_amount": self.total_amount
        }

class OrderItem(BaseTable):
    order_id = Column(Integer, ForeignKey('order.id'))
    product_id = Column(Integer, ForeignKey('product.id'))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="orders")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": self.price
        }

# Пример использования
if __name__ == "__main__":
    db = DatabaseConnection()
    db.create_tables()

    with db.get_session() as session:
        supplier = Supplier(
            name="Trade",
            contact_person="Иванов Иван",
            phone="+79991234567",
            email="supplier@example.com",
            address="г. Москва"
        )
        session.add(supplier)
        session.commit()

        product = Product(
            name="Ноутбук",
            description="Игровой ноутбук",
            price=50000.0,
            quantity=10,
            supplier_id=supplier.id
        )
        session.add(product)
        session.commit()

        order = Order(
            customer_name="Петров Петр",
            customer_phone="+79998765432",
            customer_email="customer@example.com",
            status="processing",
            total_amount=50000.0
        )
        session.add(order)
        session.commit()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            price=product.price
        )
        session.add(order_item)
        session.commit()

        print("Поставщик:", supplier.to_dict())
        print("Товар:", product.to_dict())
        print("Заказ:", order.to_dict())
        print("Элемент заказа:", order_item.to_dict())