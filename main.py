import sys

import sqlalchemy
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text
from datetime import datetime
import Conn
app = Flask(__name__)
conn_str = f"mysql://root:{Conn.password()}@localhost/DbProject"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()

@app.route('/signup', methods=['GET'])
def get_signup():
    return render_template('Base.html')


@app.route('/signup', methods=['POST'])
def signup():
    try:
        conn.execute(
            text("INSERT INTO UserInfo (`Username`, `Name`, `Email`, `Password`, `Account_Type`) values (:Username, :Name, :Email, :Password, :Account_type);"),
            request.form
        )
        user = conn.execute(
            text("SELECT User_id FROM UserInfo WHERE Username = :Username"),
            request.form
        ).one_or_none()
        conn.execute(
            text(f"INSERT INTO CART (`User_id`) SELECT User_id FROM UserInfo WHERE Username = :Username"),
            request.form
        )
        conn.commit()
        cookie = redirect('/products')
        cookie.set_cookie('User_id', str(user[0]))
        return cookie

    except Exception as e:
        error = e.orig.args[1]
        return render_template('Base.html', error=error, success=None)


@app.route('/login', methods=['GET'])
def get_login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    auth = conn.execute(
        text("SELECT if(Password = :Password, 'Yes', 'No'), Account_Type, User_id FROM UserInfo WHERE Username = :Info OR Email = :Info;"),
        request.form
    ).one_or_none()
    if auth is not None and auth[0] == 'Yes':
        if auth[1] == 'Customer':
            cookie = redirect('/products')
            cookie.set_cookie('User_id', str(auth[2]))
            conn.execute(text(f"INSERT IGNORE INTO CART (`User_id`) VALUES ({auth[2]})"))
            conn.commit()
            return cookie
        else:
            cookie = redirect('/product_edit')
            cookie.set_cookie('User_id', str(auth[2]))
            return cookie
    else:
        return render_template('login.html', error=None, success="Incorrect Username/Email or Password")


@app.route('/', methods=['GET'])
def default():
    products = conn.execute(text(f"SELECT * FROM Products Natural JOIN Images Left JOIN (SELECT * FROM Discount WHERE Expiration IS NULL or now() < Expiration) as vdiscount ON Products.Product_id = vdiscount.Product_id;")).all()

    return render_template('Products_start.html', products=products, success=None)


@app.route('/search', methods=['GET', 'POST'])
def get_searched_products():
    param = request.form['Search']
    products = conn.execute(text(f"SELECT * FROM Products Natural JOIN Images Left JOIN (SELECT * FROM Discount WHERE Expiration IS NULL or now() < Expiration) as vdiscount ON Products.Product_id = vdiscount.Product_id WHERE Products.Product_name LIKE '%{param}%' OR Products.Description LIKE '%{param}%';"), request.form).all()

    return render_template('Products.html', products=products, success=None)

@app.route('/products', methods=['GET'])
def get_products():
    products = conn.execute(text(f"SELECT * FROM Products Natural JOIN Images Left JOIN (SELECT * FROM Discount WHERE Expiration IS NULL or now() < Expiration) as vdiscount ON Products.Product_id = vdiscount.Product_id;")).all()

    return render_template('Products.html', products=products, success=None)


@app.route('/products', methods=['POST'])
def add_to_cart():
    id = request.cookies.get('User_id')
    cid = conn.execute(text(f"SELECT Cart_id FROM cart Where User_id = {id};")).one_or_none()
    conn.execute(
        text(f"INSERT INTO Cart_Items(`Cart_id`, `Product_id`, `Price`) VALUES ({cid[0]}, :Product_id, :Price);"),
        request.form
    )
    conn.commit()

    return redirect('/products')


@app.route('/product_edit', methods=['GET'])
def get_vendor_products():
    id = request.cookies.get('User_id')
    account = conn.execute(text(f'SELECT Account_type FROM UserInfo WHERE User_id = {id}')).one_or_none()
    if account[0] == 'Vendor':
        products = conn.execute(text(f"SELECT * FROM Products Where User_id = {id};")).all()
    else:
        products = conn.execute(text(f"SELECT * FROM Products")).all()

    return render_template('ProductEdit.html', products=products, success=None)


@app.route('/product_edit', methods=['POST'])
def update_products():
    column = request.form['Attribute']
    conn.execute(text(f'UPDATE Products SET {column} = :Change WHERE Product_id = :Product_id'), request.form)
    conn.commit()

    return redirect('/product_edit')


@app.route('/product_delete', methods=['POST'])
def delete_products():
    conn.execute(text(f'DELETE FROM Colors Where Product_id = :Product_id'), request.form)
    conn.execute(text(f'DELETE FROM Images Where Product_id = :Product_id'), request.form)
    conn.execute(text(f'DELETE FROM Sizes Where Product_id = :Product_id'), request.form)
    conn.execute(text(f'DELETE FROM Products Where Product_id = :Product_id'), request.form)
    conn.commit()

    return redirect('/product_edit')


@app.route('/product_add', methods=['GET'])
def add_products():
    id = request.cookies.get('User_id')
    account = conn.execute(text(f'SELECT Account_Type From UserInfo Where User_id = {id}')).all()
    vendors = []
    if account[0][0] == 'Admin':
        vendors = conn.execute(text(f'SELECT Account_Type, User_id, Name From UserInfo Where Account_Type = "Vendor"')).all()

    return render_template('ProductAdd.html', account=account, vendors=vendors, id=id)


@app.route('/product_add', methods=['POST'])
def add_products_post():
    warranty = request.form["warranty"]
    if warranty == "None":
        warranty = sqlalchemy.sql.null()
        conn.execute(
            text(
                f"INSERT INTO Products (Product_name, Description, Quantity, Warranty, Price, User_id) Values (:productname, :description, :quantity, {warranty}, :price, :vendorid)"),
            request.form
        )
    else:
        warranty = datetime.strptime(warranty, '%Y/%m/%d %H:%M:%S')
        conn.execute(
            text(
                f"INSERT INTO Products (Product_name, Description, Quantity, Warranty, Price, User_id) Values (:productname, :description, :quantity, '{warranty}', :price, :vendorid)"),
            request.form
        )
    pid = conn.execute(text("SELECT max(Product_id) FROM Products;")).one_or_none()
    sizes = request.form["Sizes"]
    list_sizes = sizes.split()
    for size in list_sizes:
        conn.execute(
            text(f"INSERT INTO Sizes (Product_id, Sizes) Values ('{pid[0]}', '{size}');"),
            request.form
        )
    colors = request.form["Colors"]
    list_colors = colors.split()
    for color in list_colors:
        conn.execute(
            text(f"INSERT INTO Colors (Product_id, Colors) Values ('{pid[0]}', '{color}');"),
            request.form
        )
    conn.execute(
        text(f"INSERT INTO Images (Product_id, Image) Values ('{pid[0]}', :Images);"),
        request.form
    )
    conn.commit()

    return redirect("/product_add")


@app.route('/cart', methods=['GET'])
def get_cart_items():
    id = request.cookies.get('User_id')
    items = conn.execute(text(f"SELECT c.User_id, c.Cart_id, ci.Product_id, p.Product_name, ci.Price FROM Cart c NATURAL JOIN Cart_items ci JOIN Products p WHERE c.Cart_id = (SELECT Cart_id FROM Cart WHERE User_id = {id} LIMIT 1) AND p.Product_id = ci.Product_id;")).all()
    if len(items) > 0:
        total = conn.execute(text(f"SELECT SUM(Price) FROM Cart_items WHERE Cart_id = {items[0][1]}")).one_or_none()
        total = round(total[0], 2)
    else:
        total = 0

    return render_template('Cart.html', items=items, total=total, success=None)


@app.route('/cart', methods=['POST'])
def checkout():
    id = request.cookies.get('User_id')
    now = datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(text(f"INSERT INTO Orders (`Status`, `User_id`, `Cart_id`, `Date_ordered`) VALUES ('Pending', {id}, :Cart_id, '{now}');"), request.form)
    items = conn.execute(text(f"SELECT ci.Product_id FROM Cart_items ci JOIN Cart c WHERE c.Cart_id = ci.Cart_id and c.User_id = {id};")).all()
    for item in items:
        conn.execute(text(f"INSERT INTO Order_items (`Order_id`, `Product_id`) VALUES ((SELECT MAX(Order_id) FROM Orders), {item[0]});"))
    conn.execute(text(f"DELETE FROM Cart_items WHERE Cart_id = :Cart_id"), request.form)
    conn.commit()

    return redirect('/cart')




@app.route('/cart_remove', methods=['GET', 'POST'])
def remove_from_cart():
    id = request.cookies.get('User_id')
    cart = conn.execute(text(f'SELECT Cart_id from Cart WHERE User_id = {id}')).all()
    conn.execute(text(f'DELETE FROM Cart_items Where Cart_id = {cart[0][0]} and Product_id = :Product_id'), request.form)
    conn.commit()

    return redirect('/cart')



@app.route('/orders', methods=['GET'])
def get_orders():
    User_id = request.cookies.get('User_id')
    orders = conn.execute(text(f'SELECT Status, date_ordered, Order_id FROM Orders WHERE User_id = {User_id}')).all()
    order_items = []
    products = []
    for i in orders:
        order_items.append(conn.execute(text(f'SELECT Product_id FROM Order_items WHERE Order_id = {i[2]}')).all())

    for i in order_items:
        items = []
        for j in range(len(i)):
            items.append(conn.execute(text(f"SELECT * FROM Products Natural JOIN Images WHERE Products.Product_id = {i[j][0]};")).all())
        products.append(items)

    return render_template('order.html', orders=orders, products=products, success=None)


@app.route('/admin_order', methods=['GET'])
def get_admin_orders():
    id = request.cookies.get('User_id')
    user = conn.execute(text(f"SELECT Account_Type FROM UserInfo WHERE User_id = {id}")).one_or_none()
    if user[0] == "Admin":
        orders = conn.execute(text(f'SELECT Status, date_ordered, Order_id FROM Orders')).all()
    else:
        orders = conn.execute(text(f'SELECT orders.Status, orders.date_ordered, orders.Order_id FROM Orders natural join order_items join products on products.product_id = order_items.product_id where products.user_id = {id};')).all()
    order_items = []
    products = []
    for i in orders:
        order_items.append(conn.execute(text(f'SELECT Product_id FROM Order_items WHERE Order_id = {i[2]}')).all())

    for i in order_items:
        items = []
        for j in range(len(i)):
            items.append(conn.execute(
                text(f"SELECT * FROM Products Natural JOIN Images WHERE Products.Product_id = {i[j][0]};")).all())
        products.append(items)

    return render_template('Admin_Order.html', orders=orders, products=products, success=None)

@app.route('/admin_order', methods=['POST'])
def update_order_status():
    conn.execute(text(f'UPDATE Orders SET Status = :Status WHERE Order_id = :Order_id'), request.form)
    conn.commit()

    return redirect('/admin_order')


@app.route('/chat', methods=['GET'])
def get_customer_chat():
    id = request.cookies.get('User_id')
    chats = conn.execute(text(f'SELECT Chat_id, User_id2 FROM Chat Where User_id1 = {id}')).all()
    account = conn.execute(text(f'SELECT Account_type from UserInfo WHERE User_id = {id}')).all()
    vendors = conn.execute(text("SELECT Name, User_id FROM UserInfo WHERE Account_type = 'Vendor'")).all()
    print(vendors)
    messages = []
    users = []
    for chat in range(len(chats)):
        messages.append(conn.execute(text(f'SELECT * FROM Chat_message WHERE Chat_id = {chats[chat][0]}')).all())
        users.append(conn.execute(text(f'SELECT Name FROM UserInfo WHERE User_id = {chats[chat][1]}')).all())

    return render_template('Chat.html', chats=chats, messages=messages, id=id, users=users, account=account, vendors=vendors)

@app.route('/chat', methods=['POST'])
def send_message():
    conn.execute(text('INSERT INTO Chat_message (`Message`, `Chat_id`, `User_id`) VALUES (:message, :Chat, :Id)'), request.form)
    conn.commit()

    return redirect('/chat')

@app.route('/new_message', methods=['POST'])
def new_message():
    id = request.cookies.get('User_id')
    conn.execute(text(f'INSERT INTO Chat (`User_id1`, `User_id2`) VALUES ({id}, :New)'), request.form)
    chat_id = conn.execute(text(f'SELECT Chat_id FROM Chat WHERE User_id1 = {id} and User_id2 = :New'), request.form).all()
    conn.execute(text(f'INSERT INTO Chat_message (`Message`, `Chat_id`, `User_id`) VALUES (:message, {chat_id[0][0]}, {id})'), request.form)
    conn.commit()

    return redirect('/chat')

@app.route('/admin_chat', methods=['GET'])
def get_admin_chat():
    id = request.cookies.get('User_id')
    chats = conn.execute(text(f'SELECT Chat_id, User_id1 FROM Chat Where User_id2 = {id}')).all()
    account = conn.execute(text(f'SELECT Account_type from UserInfo WHERE User_id = {id}')).all()
    messages = []
    users = []
    for chat in range(len(chats)):
        messages.append(conn.execute(text(f'SELECT * FROM Chat_message WHERE Chat_id = {chats[chat][0]}')).all())
        users.append(conn.execute(text(f'SELECT Name FROM UserInfo WHERE User_id = {chats[chat][1]}')).all())

    return render_template('Chat.html', chats=chats, messages=messages, id=id, users=users, account=account)


@app.route('/reviews', methods=['GET', 'POST'])
def get_reviews():
    list_reviews = conn.execute(text(f"SELECT * FROM Review Natural JOIN UserInfo WHERE Product_id = :id;"), request.form).all()
    name = conn.execute(text(f"SELECT Product_name FROM Products where Product_id = :id;"), request.form).one_or_none()
    Success = True
    if len(list_reviews) <= 0:
        list_reviews = ["There are no reviews for this product yet."]
        Success = False

    return render_template('reviews.html', reviews=list_reviews, Success=Success, name=name)


@app.route('/admin_chat', methods=['POST'])
def send_admin_message():
    conn.execute(text('INSERT INTO Chat_message (`Message`, `Chat_id`, `User_id`) VALUES (:message, :Chat, :Id)'), request.form)
    conn.commit()

    return redirect('/admin_chat')


@app.route('/profile', methods=['GET'])
def get_profile():
    id = request.cookies.get('User_id')
    profile = conn.execute(text(f"SELECT * FROM UserInfo where User_id = {id}")).one_or_none()

    return render_template('profile.html', profile=profile)




@app.route('/returns', methods=['GET'])
def get_returns_list():
    id = request.cookies.get('User_id')
    returns = conn.execute(text(f'SELECT Returns.*, Products.Product_name FROM Returns JOIN Products ON Products.Product_id = Returns.Product_id WHERE Returns.User_id = {id}')).all()
    print(returns)
    return_item_list = conn.execute(text(f'Select Product_name, orders.Order_id from products join order_items natural join orders on products.product_id = order_items.product_id where orders.user_id = {id}')).all()
    return render_template('Returns.html', returns=returns, return_item_list=return_item_list)

@app.route('/returns', methods=['POST'])
def return_submit():
    time = datetime.now()
    time = time.strftime('%Y-%m-%d %H:%M:%S')
    order_item = request.form['Return_Items']
    print(order_item)
    order = order_item.split(',')
    product_id = conn.execute(text(f'SELECT Product_id FROM Products WHERE Product_name = "{order[0]}";'), request.form).all()
    id = request.cookies.get('User_id')
    conn.execute(text(f'INSERT INTO Returns (Date_requested, Description, Demand, Image, Product_id, User_id, Order_id) VALUES ("{time}", :comp_name, :customer_demand, :comp_img, {product_id[0][0]}, {id}, {order[1]});'), request.form)
    conn.commit()

    return redirect('/returns')


if __name__ == '__main__':
    app.run(debug=True)
