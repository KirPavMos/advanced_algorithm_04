# Реализовать базовые классы для работы с БД с использованием
# SQLAlchemy. Реализовать подключение и абстрактные классы

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from abc import ABC, abstractmethod
import os


# 01. Класс подключения к базе данных
class DatabaseConnection:
    def __init__(self, db_url: str = None):
        """
        Инициализация подключения к БД
        :param db_url: строка подключения (например: 'postgresql://user:password@localhost:5432/dbname')
        """
        self.db_url = db_url or os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("Не указана строка подключения к БД")

        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()

    def get_session(self):
        """Возвращает сессию для работы с БД"""
        return self.SessionLocal()

    def create_tables(self):
        """Создает все таблицы в БД"""
        self.Base.metadata.create_all(bind=self.engine)


# 02. Абстрактный класс таблицы
class BaseTable(ABC):
    @declared_attr
    def __tablename__(cls):
        """Автоматическое определение имени таблицы на основе имени класса"""
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)

    def __init__(self, **kwargs):
        """Конструктор, который заполняет все поля класса"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @abstractmethod
    def to_dict(self):
        """Абстрактный метод для преобразования объекта в словарь"""
        pass


# 03. Реализация конкретных таблиц

# Таблица поставщиков
class Supplier(BaseTable, DatabaseConnection().Base):
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


# Таблица товаров
class Product(BaseTable, DatabaseConnection().Base):
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


# Таблица заказов
class Order(BaseTable, DatabaseConnection().Base):
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


# Таблица элементов заказа (связь многие-ко-многим между заказами и товарами)
class OrderItem(BaseTable, DatabaseConnection().Base):
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
    # Инициализация подключения (можно передать строку подключения или использовать переменную окружения DATABASE_URL)
    db = DatabaseConnection("sqlite:///example.db")

    # Создание таблиц
    db.create_tables()

    # Пример работы с таблицами
    session = db.get_session()

    # Создание поставщика
    supplier = Supplier(
        name="ООО Поставщик",
        contact_person="Иванов Иван",
        phone="+79991234567",
        email="supplier@example.com",
        address="г. Москва, ул. Примерная, 123"
    )
    session.add(supplier)
    session.commit()

    # Создание товара
    product = Product(
        name="Ноутбук",
        description="Мощный ноутбук для работы",
        price=50000.0,
        quantity=10,
        supplier_id=supplier.id
    )
    session.add(product)
    session.commit()

    # Создание заказа
    order = Order(
        customer_name="Петров Петр",
        customer_phone="+79998765432",
        customer_email="customer@example.com",
        status="processing",
        total_amount=50000.0
    )
    session.add(order)
    session.commit()

    # Добавление товара в заказ
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        price=product.price
    )
    session.add(order_item)
    session.commit()

    # Вывод информации
    print("Поставщик:", supplier.to_dict())
    print("Товар:", product.to_dict())
    print("Заказ:", order.to_dict())
    print("Элемент заказа:", order_item.to_dict())

    session.close()