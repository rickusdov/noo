from flask import Flask
from flask import render_template
import sqlite3 

app = Flask(__name__)

@app.route('/students')
def students():

    con = sqlite3.connect('products.sql')

    try:
        con.execute('CREATE TABLE students (name TEXT, id INT)')
        print ('Table created successfully');
    except:
        pass

    con.close()

    con = sqlite3.connect("products.sql")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * from students")
    rows = cur.fetchall();

    print(rows)
