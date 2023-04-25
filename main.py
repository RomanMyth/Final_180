from flask import Flask, render_template, request
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text

app = Flask(__name__)
conn_str = "mysql://root:Axwell99!@localhost/BoatDB"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()

@app.route('/')
def index():
    return render_template('login.html')