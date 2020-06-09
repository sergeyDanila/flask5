import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from app import db

items_cat = db.Table("items_cat",
                     db.Column("item_id", db.Integer, db.ForeignKey("items.id")),
                     db.Column("cat_id", db.Integer, db.ForeignKey("categories.id")))


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    items = db.relationship("Item", secondary=items_cat, back_populates="categories")


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(250))
    picture = db.Column(db.String(150))
    # category_id = db.Column(db.Integer, db.ForeignKey="categories.id")  Связь должна быть Many-To-Many чтобы
    # избежать проблем когда появится доп.категории: Итальянская кухня, Мексиканская кухня Вегитарианская хавка,
    # Постное меню, Халяль и т.д. тогда одно и тоже блюдо сможет входить в разные категории.
    categories = db.relationship("Category", secondary=items_cat, back_populates="items")


class Session(db.Model):
    __tablename__ = "sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    cart_id = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.TIMESTAMP, default=datetime.now)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, default=datetime.now)
    remote_addr = db.Column(db.String(100))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(100))
    email = db.Column(db.String(100))
    address = db.Column(db.String(250))
    comment = db.Column(db.String(250))
    password = db.Column(db.String(100))


class Cart(db.Model):
    __tablename__ = "carts"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)

    def total_cost(self):
        return db.session.execute('SELECT sum(qty*price) r FROM cart_items where cart_id=:u', {'u': self.id}).fetchone()

    def total_qty(self):
        return db.session.execute('SELECT sum(qty) r FROM cart_items where cart_id=:u', {'u': self.id}).fetchone()

    def cart_summary(self):
        return db.session.execute('''SELECT "(Блюд: " || sum(qty) || " на: " || sum(qty*price) || " руб.)"  r 
                                     FROM cart_items where cart_id=:u''', {'u': self.id}).fetchone()


class CartItem(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"))
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    qty = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    status_id = db.Column(db.String(20), default='Размещён')
    created = db.Column(db.TIMESTAMP, default=datetime.now)
    phone = db.Column(db.String(100))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    address = db.Column(db.String(250))
    comment = db.Column(db.String(250))

    def total_cost(self):
        return db.session.execute('SELECT sum(qty*price) r FROM order_items where order_id=:u',
                                  {'u': self.id}).fetchone()

    def total_qty(self):
        return db.session.execute('SELECT sum(qty) r FROM order_items where order_id=:u', {'u': self.id}).fetchone()


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.String(50), primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("carts.id"))
    item_id = db.Column(db.Integer,  db.ForeignKey("items.id"))
    qty = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)


db.create_all()

# db.session.commit()
