import csv

from app import db
from app.models import Category, Item

# Заливаем исходные данные из CSV

db.session.execute("delete from categories;")
categories = []
x = 0
csv_path = "../delivery_categories.csv"
with open(csv_path, "r") as f_cat:
    cat = csv.reader(f_cat)
    next(cat)  # Пропуск хедера
    for i in cat:
        categories.append(Category(id=i[0], title=i[1]))
        db.session.add(categories[x])
        x += 1

db.session.execute("delete from items;")
db.session.execute("delete from items_cat;")
items = []
x = 0
csv_path = "../delivery_items.csv"
with open(csv_path, "r") as f_item:
    item = csv.reader(f_item)
    next(item)  # Пропуск хедера
    for i in item:
        items.append(Item(id=i[0], title=i[1], price=i[2], description=i[3], picture=i[4]))  # categories=list(i[5])))
        db.session.add(items[x])
        items[x].categories.append(db.session.query(Category).filter(Category.id == i[5]).first())
        x += 1

db.session.commit()
