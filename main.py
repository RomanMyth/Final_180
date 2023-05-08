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


@app.route('/', methods=['GET'])
def get_signup():
    return render_template('Base.html')


@app.route('/', methods=['POST'])
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
        print(user)
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
        print(error)
        return render_template('Base.html', error=error, success=None)


@app.route('/login', methods=['GET'])
def get_login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    try:
        auth = conn.execute(
            text("SELECT if(Password = :Password, 'Yes', 'No'), Account_Type, User_id FROM UserInfo WHERE Username = :Info OR Email = :Info;"),
            request.form
        ).one_or_none()
        print(auth)
        if auth is not None and auth[0] == 'Yes':
            if auth[1] == 'Customer':
                cookie = redirect('/products')
                cookie.set_cookie('User_id', str(auth[2]))
                return cookie
            else:
                cookie = redirect('/product_edit')
                cookie.set_cookie('User_id', str(auth[2]))
                return cookie
        else:
            return render_template('login.html', error=None, success="Incorrect Username/Email or Password")

    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('login.html', error=error, success=f'hello')


@app.route('/products', methods=['GET'])
def get_products():
    products = conn.execute(text(f"SELECT * FROM Products Natural JOIN Images;")).all()
    print(products)
    return render_template('Products.html', products=products, success=None)


@app.route('/products', methods=['POST'])
def add_to_cart():
    id = request.cookies.get('User_id')
    cid = conn.execute(text(f"SELECT Cart_id FROM cart Where User_id = {id};")).one_or_none()
    print(cid[0])
    conn.execute(
        text(f"INSERT INTO Cart_Items(`Cart_id`, `Product_id`) VALUES ({cid[0]}, :Product_id);"),
        request.form
    )
    conn.commit()

    return redirect('/products')


@app.route('/product_edit', methods=['GET'])
def get_vendor_products():
    id = request.cookies.get('User_id')
    account = conn.execute(text(f'SELECT Account_type FROM UserInfo WHERE User_id = {id}')).one_or_none()
    print(account)
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
    print(warranty)
    print(type(warranty))
    if warranty == "None":
        warranty = sqlalchemy.sql.null()
    else:
        warranty = datetime.strptime(warranty, '%Y/%m/%d %H:%M:%S')
    print(warranty)
    print(type(warranty))
    conn.execute(
        text(f"INSERT INTO Products (Product_name, Description, Quantity, Warranty, Price, User_id) Values (:productname, :description, :quantity, '{warranty}', :price, :vendorid)"),
        request.form
    )
    conn.commit()
    return redirect("/product_add")


@app.route('/cart', methods=['GET'])
def get_cart_items():
    id = request.cookies.get('User_id')
    items = conn.execute(text(f"SELECT c.User_id, c.Cart_id, ci.Product_id, p.Product_name, p.Price FROM Cart c NATURAL JOIN Cart_items ci JOIN Products p WHERE c.Cart_id = (SELECT Cart_id FROM Cart WHERE User_id = {id} LIMIT 1) AND p.Product_id = ci.Product_id;")).all()
    return render_template('Cart.html', items=items, success=None)


@app.route('/orders', methods=['GET'])
def get_orders():
    User_id = request.cookies.get('User_id')
    orders = conn.execute(text(f'SELECT Status, date_ordered, Order_id FROM Orders WHERE User_id = {User_id}')).all()
    print(orders)
    order_items = []
    products = []
    for i in orders:
        order_items.append(conn.execute(text(f'SELECT Product_id FROM Order_items WHERE Order_id = {i[2]}')).all())

    for i in order_items:
        items = []
        for j in range(len(i)):
            items.append(conn.execute(text(f"SELECT * FROM Products Natural JOIN Images WHERE Products.Product_id = {i[j][0]};")).all())
        products.append(items)
    print('\n', products)

    print(order_items)
    print(order_items[0])
    return render_template('order.html', orders=orders, products=products, success=None)


if __name__ == '__main__':
    app.run(debug=True)
