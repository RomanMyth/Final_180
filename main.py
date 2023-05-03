import sys
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text
#import mysql.connector
import base64
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
        cookie=redirect('/products')
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
            elif auth[1] == 'Vendor':
                return redirect(url_for('get_vendor_products', user=auth[2]))
            elif auth[1] == 'Admin':
                return redirect('/product_edit')
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

# @app.route('/products', methods=['POST'])
# def add_to_cart():

@app.route('/product_edit/<user>', methods=['GET'])
def get_vendor_products(user):
    products = conn.execute(text(f"SELECT * FROM Products Where User_id = {user};")).all()
    return render_template('ProductEdit.html', products=products, success=None)

@app.route('/product_edit', methods=['GET'])
def get_admin_products():
    products = conn.execute(text(f"SELECT * FROM Products")).all()
    return render_template('ProductEdit.html', products=products, success=None)


@app.route('/product_add', methods=['GET'])
def add_products():
    account = conn.execute(text(f'SELECT Account_Type From UserInfo Where User_id = {8}')).all()
    vendors = []
    if account[0][0] == 'Admin':
        vendors = conn.execute(text(f'SELECT Account_Type, User_id, Name From UserInfo Where Account_Type = "Vendor"')).all()

    print(account, '\n', vendors)

    return render_template('ProductAdd.html', account=account, vendors=vendors)

@app.route('/cart', methods=['GET'])
def get_cart_items():
    id = request.cookies.get('User_id')
    items = conn.execute(text(f"SELECT c.User_id, c.Cart_id, ci.Product_id, p.Product_name, p.Price FROM Cart c NATURAL JOIN Cart_items ci JOIN Products p WHERE c.Cart_id = (SELECT Cart_id FROM Cart WHERE User_id = {id} LIMIT 1) AND p.Product_id = ci.Product_id;")).all()
    return render_template('Cart.html', items=items, success=None)


if __name__ == '__main__':
    app.run(debug=True)
