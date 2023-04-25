from flask import Flask, render_template, request
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text
import Conn
app = Flask(__name__)
conn_str = f"mysql://root:{Conn.password()}@localhost/DbProject"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()

@app.route('/')
def index():
    return render_template('')

if __name__ == '__main__':
    app.run(debug=True)