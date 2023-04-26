from flask import Flask, render_template, request
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text


import Conn
app = Flask(__name__)
conn_str = f"mysql://root:{Conn.password()}@localhost/DbProject"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


@app.route('/', method=['POST'])
def signup():
    try:
        conn.execute(
            text("INSERT INTO UserInfo (`Username`, `Name`, `Email`, `Password`, `Account_Type`) values (:Username, :Password, 'Customer')"),
            request.form
        )
        conn.commit()
        return render_template('Base.html', error=None, success="Data inserted successfully!")

    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('Base.html', error=error, success=None)


@app.route('/login', method=['POST'])
def login():
    try:
        conn.execute(
            text("SELECT if(Password = :Password, 'Yes', 'No') FROM UserInfo WHERE Username = :Info OR Email = :Info;"),
            request.form
        )
        if conn == 'Yes':
            return render_template('Products.html', error=None, success="Data inserted successfully!")
        else:
            return render_template('login.html', error=None, success="Incorrect Username/Email or Password")
    except Exception as e:
        error = e.orig.args[1]
        print(error)
        return render_template('login.html', error=error, success=None)


if __name__ == '__main__':
    app.run(debug=True)
