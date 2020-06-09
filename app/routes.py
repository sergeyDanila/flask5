from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text

from app import app, db

from app.models import Item, Session, Cart, CartItem, User, Order, OrderItem
from app.form import LoginForm, RegisterForm, CartForm


def current_ses():
    if session.get('id', -10) == -10:
        ses = Session()
        db.session.add(ses)
        db.session.commit()
        session['id'] = ses.id
    else:
        ses = db.session.query(Session).filter(Session.id == session['id']).first()
    return ses


def current_cart():
    ses = current_ses()
    cart_summary = None
    if ses.cart_id is None:
        cart = Cart(session_id=ses.id)
        db.session.add(cart)
        db.session.commit()
        ses.cart_id = cart.id
        db.session.commit()

    cart = db.session.query(Cart).filter(Cart.id == ses.cart_id).first()
    cart_summary = cart.cart_summary()[0]

    return {"id": ses.cart_id, "summary": (cart_summary if cart_summary is not None else '(пусто)')}


# app = Flask(__name__)
# app.secret_key = "YOHOHO & Rum bottle!"


@app.route('/')  # / – здесь будет главная
def render_index():
    nyms = []

    items = db.session.execute('''SELECT rn, cat_id, cat,  id, title, price, description, picture 
                    FROM (
                            SELECT c.cat_id, cat.title cat,  i.id, i.title, i.price, i.description, i.picture,   
                                    row_number() over( partition by c.cat_id order by random() )  rn
                            FROM Items i
                                join  items_cat c on i.id= c.item_id  
                                join categories cat on cat.id =c.cat_id ) t
                            WHERE rn<=3
                            ORDER BY cat_id,rn;''').fetchall()

    for it in items:
        nyms.append(it)

    return render_template('main.html', title='Главная', goods=nyms, cart=current_cart(),
                           auth=session.get('is_auth', False))


@app.route('/cart_add/<int:item_id>/')
def cart_add(item_id):
    ses = current_ses()
    if ses is None or ses.cart_id is None:
        cart = Cart(session_id=ses.id)
        db.session.add(cart)
        db.session.commit()
        ses.cart_id = cart.id
    else:
        cart = db.session.query(Cart).filter(Cart.id == ses.cart_id).first()
    it = db.session.query(Item).filter(Item.id == item_id).first()
    item = CartItem(cart_id=cart.id, item_id=item_id, price=it.price)
    db.session.add(item)
    db.session.commit()
    return redirect("/")
    # return render_template('main.html', title='Главная')


@app.route('/cart/')
def render_cart():
    ses = current_ses()
    cart = current_cart()
    cart_id = cart.get('id', 0)
    nyms = []
    if cart_id is None:
        cart = {"id": cart_id, "summary": '(пусто)'}
    else:

        cart_items = db.session.execute('''SELECT ca.cart_id, i.id, i.title, sum(ca.qty) qty , ca.price , sum(ca.qty*ca.price) tot 
                              FROM carts c join cart_items ca on c.id =ca.cart_id   join items i on i.id = ca.item_id
                              WHERE c.id = ''' + str(cart_id) + '''
                              GROUP BY ca.cart_id, i.id, i.title, ca.price''').fetchall()
        if len(cart_items) == 0:
            cart = {"id": cart_id, "summary": '(пусто)'}
        else:
            for it in cart_items:
                nyms.append(it)

    c_cart = db.session.query(Cart).filter(Cart.id == cart.get('id')).first()
    total = c_cart.total_cost()
    dels = session.get('del', 0)
    session.pop('del', 0)
    auth = session.get('is_auth', False)
    if auth is True:
        user = db.session.query(User).filter(User.id == ses.user_id).first()
        form = CartForm(name=user.name, email=user.email, address=user.address, phone=user.phone)
    else:
        form = CartForm()

    return render_template('cart.html', goods=nyms, cart=cart, total=total[0], dels=dels, auth=auth, form=form)


@app.route('/cart_remove_item/<int:item_id>/')
def cart_remove_item(item_id):
    cart = current_cart()
    cart_id = cart.get('id', 0)
    # тут sql инжекция не страшна т.к. преобразование к int левого пользовательского ввода даст ошибку
    db.session.execute("delete from cart_items where cart_id = "
                       + str(cart_id) + " and item_id = "
                       + str(item_id) + ";")
    db.session.commit()

    if session.get('del', 0) == 0:
        session['del'] = 1
    return redirect("/cart/")


@app.route('/logout/')
def ses_logout():
    session.pop('id')
    session.pop('is_auth')
    return redirect('/')


@app.route('/auth/', methods=["GET", "POST"])
def render_login():
    error_msg = ""  # Пока ошибок нет
    form = LoginForm()
    ses = current_ses()
    if request.method == "POST":
        login = form.login.data
        password = form.password.data

        user = db.session.query(User).filter(User.email == login).first()
        # user = db.session.execute("select email, password from users where email = '" + login + "';").fetchone()

        if user is None or password != user.password:
            error_msg = "Неверный логин или пароль"
        else:
            ses.user_id = user.id
            db.session.commit()
            session["is_auth"] = True

            return render_template("account.html", title='Главная', cart=current_cart())

    return render_template("login.html", error_msg=error_msg, form=form)


@app.route('/register/', methods=["GET", "POST"])
def render_reg():
    error_msg = ""  # Пока ошибок нет
    form = RegisterForm()
    if request.method == "POST":
        login = form.login.data
        password = form.password.data
        user = db.session.query(User).filter(User.email == login).first()
        if user is not None:
            error_msg = "Пользователь с таким логином уже есть"
            return render_template("register.html", error_msg=error_msg, form=form)

        user = User(email=login, password=password, created=datetime.now(), remote_addr=request.remote_addr)
        db.session.add(user)
        db.session.commit()

        ses = current_ses()

        ses.user_id = user.id
        db.session.commit()
        session["is_auth"] = True
        return redirect("/account/")

    return render_template("register.html", error_msg=error_msg, form=form)


@app.route('/order/', methods=["GET", "POST"])
def render_order():
    ses = current_ses()
    form = CartForm()
    if request.method == "POST":
        email = form.email.data
        name = form.name.data
        phone = form.phone.data
        address = form.address.data
        order = Order(email=email, name=name, phone=phone, address=address, user_id=ses.user_id, created=datetime.now())
        db.session.add(order)
        db.session.commit()
        db.session.execute(''' insert into order_items(id, order_id,item_id,qty,price)
        SELECT ''' + str(order.id) + '''||'-'|| i.id  ids, ''' + str(order.id) + ''' oid, 
                                i.id,  sum(ca.qty) qty , ca.price 
                              FROM carts c join cart_items ca on c.id =ca.cart_id   join items i on i.id = ca.item_id
                              WHERE c.id = ''' + str(ses.cart_id) + '''
                              GROUP BY ca.cart_id, i.id,  ca.price
        ''')
        user = db.session.query(User).filter(User.id == ses.user_id).first()
        user.name = name
        user.address = address
        user.phone = phone
        db.session.commit()
        session.pop('id')
        # session.pop('is_auth')
        ses = current_ses()
        ses.user_id = user.id
        db.session.commit()
        return render_template('ordered.html')
    return redirect('/cart/')


@app.route('/account/')
def render_account():
    ses = current_ses()
    auth = session.get('is_auth', False)
    if auth is False:
        return redirect('/auth/')
    u = []
    orders = db.session.query(Order).filter(Order.user_id == ses.user_id).order_by(Order.created)
    for o in orders.all():
        items = db.session.execute('''select i.title, oi.qty, oi.price
                                      from order_items oi join items i  on i.id = oi.item_id
                                      where oi.order_id =''' + str(o.id)).fetchall()
        a = {'id': o.id, 'created': o.created.strftime("%Y-%m-%d"), 'status': o.status_id, 'total': o.total_cost()[0],
             'pos': items}
        u.append(a)

    return render_template('account.html', title='Профиль', cart=current_cart(), orders=u, auth=auth)
