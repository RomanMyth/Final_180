import sys

from flask import Flask, render_template, request
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text


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
            text("INSERT INTO UserInfo (`Username`, `Name`, `Email`, `Password`, `Account_Type`) values (:Username, :Password, :Username, :Password, 'Customer')"),
            request.form
        )
        conn.commit()
        return render_template('Base.html', error=None, success="Data inserted successfully!")

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
            text("SELECT if(Password = :Password, 'Yes', 'No') FROM UserInfo WHERE Username = :Info OR Email = :Info;"),
            request.form
        ).one_or_none()
        print(auth)
        print(auth)
        if auth[0] == 'Yes':
            return render_template('Products.html', error=None, success="Data inserted successfully!")
        else:
            print(auth)
            return render_template('login.html', error=None, success="Incorrect Username/Email or Password")
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('login.html', error=error, success=f'hello')


if __name__ == '__main__':
    app.run(debug=True)
