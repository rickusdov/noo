from flask import Flask, session
from markupsafe import escape
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import abort
from flask import g
from flask import flash
from werkzeug.utils import secure_filename
from flask import send_from_directory
from array import *
import sqlite3
from flask_session import Session
from hashlib import md5

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
sid = 'rWAMsmRhdmlkLXNob3A='
pid = 'kQO8FU93i'
secret = 'tOAbRwKosVg8AKQkZykO4WPVhrkA'

'''read database
   input: name of table
   return: all database data that can be set to new variable
'''


def read_database(table_name):
    try:
        con = sqlite3.connect('book_shop.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM " + table_name + ';')
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print(e)
    finally:
        cur.close()
        con.close()


@app.route('/sign_out')
def sign_out():
    session.pop('name')  # deletes username from session so that user cannot use website without logging in again
    return redirect('/', code=302)


@app.route('/', methods=['post', 'get'])
def login():
    session['logged_in'] = False  # set default state of session till user logs in
    if session['logged_in'] == False:
        if request.method == 'POST':
            return do_the_login(request.form['username'], request.form['password'])
        else:
            return show_the_login_form()
    else:
        return redirect('/home', code=302)


def show_the_login_form():
    return render_template('login.html')


def do_the_login(u, p):
    database = read_database('members')
    # set everything in session to default values

    for i in range(0, len(database)):
        if u == database[i][0] and p == database[i][1]:
            session["name"] = u
            session["role"] = str(database[i][2])
            session['cart'] = []
            session['total_price'] = 0
            session['total_quantity'] = 0
            session['logged_in'] = True
            return redirect('/home', code=302)
        
    # if users details is incorrect show error message
    return abort(403)


@app.route('/home', methods=['post', 'get'])
def home():
    database = []
    database = list(read_database("book_info"))    
    if session['logged_in'] == True: # checks if user has logged in
        if request.method == 'POST':
            shopping_cart = []
            max_quantity = []
            for i in range(0,len(database)):
                max_quantity.append(database[i][8])
            condition = False # set boolean condition variable use to check if new item is already in cart or no
            book_cart = (request.form.get('ISBM13'))
            cart_quantity = str(request.form.get('quantity_cart'))
            # if item was added to shopping cart every detail of item assigned to temporary variable 'shopping_cart'
            for i in range(0, len(database)):
                if book_cart == database[i][0]:
                    shopping_cart.clear()
                    shopping_cart.append(str(database[i][5]))
                    shopping_cart.append(str(database[i][1]))
                    shopping_cart.append(str(database[i][0]))
                    shopping_cart.append(int(cart_quantity))
                    shopping_cart.append(format(int(database[i][6]), ".2f"))
                    shopping_cart.append(int(database[i][8]))
            for row in session['cart']:
                if shopping_cart[2] in row: #Checks if item is already in shopping cart or not
                    condition = True #if it is in cart set variable to True
            if condition == False: 
                if shopping_cart[3] > 0:
                    session['cart'].append(shopping_cart)
            if condition == True: #if it is not  in the cart
                for i in range(0, len(session['cart'])):
                    if shopping_cart[2] == session['cart'][i][2]: #find item with the same isbm-13 (which is primary key)
                        session['cart'][i][3] += shopping_cart[3] #add only the quantity to sessions variable
            #checks how many same items is available in database
            for i in range(0,len(session['cart'])):
                for j in range(0,len(database)):
                    if session['cart'][i][2] == database[j][0]:
                        max_quantity[j] = int(database[j][8]) - int(session['cart'][i][3]) # sets max quantity available to add to shopping cart, so user would not be able to add more items than there is on database
            total_price = float(session['total_price']) + (float(shopping_cart[4]) * float(cart_quantity))
           
            session['total_price'] =  format((total_price), ".2f") #set two digits after comma
            total_quantity = session['total_quantity'] + int(cart_quantity)
            session['total_quantity'] = total_quantity

            cart_condition = False #if items already been added to cart change max available quantity to new one
            return render_template('home.html', db_length=int(len(database)), db=database, max_quantity=max_quantity,
                                   cart_condition=cart_condition)
        #if nothing has changed in 'home.html' forms leave max_quantity as set in database
        else:
            cart_condition = True
            return render_template('home.html', db_length=int(len(database)), db=database, max_quantity=database,
                                   cart_condition=cart_condition)

    else:
        return redirect('/', code=302) # if user tries to access home page before logging in, redirects back to login page


# deletes everything in current shopping cart
@app.route('/empty_cart', methods=['post', 'get'])
def empty_cart():
    session['cart'] = []
    session['total_price'] = 0
    session['total_quantity'] = 0
    session['shipping_price'] = 0
    session['all_total_price'] = 0
    return redirect('/home', code=302)


# code used from simple-payment documentation
@app.route('/checkout', methods=['post', 'get'])
def checkout():
    total_price = session['total_price']
    shipping_price = 3 + ((session['total_quantity'] - 1) * 1)
    session['shipping_price'] = format((shipping_price), ".2f")
    all_total_price = float(session['shipping_price']) + float(session['total_price'])
    session['all_total_price'] = format((all_total_price), ".2f")
    checksumstr = f"pid={pid:s}&sid={sid:s}&amount={all_total_price:.2f}&token={secret:s}"
    print('checksumstr is', checksumstr)
    checksum = md5(checksumstr.encode('utf-8')).hexdigest()
    session['checksum'] = checksum
    print('checksum is', checksum)
    session['sid'] = sid
    session['pid'] = pid
    return render_template('checkout.html')


###########
@app.route('/stock_level', methods=['post', 'get'])
def stock_level():
    if session['logged_in'] == True and session['role'] == 'admin':  # checks if user has access to this page
        database = list(read_database("book_info"))
        stock_level = []
        # gets data from 'stock-level.html' form and stores in database
        if request.method == 'POST':
            stock_level.clear()
            stock_level.append(request.form.get('isbm-13'))
            stock_level.append(request.form.get('book-name'))
            stock_level.append(request.form.get('book-author'))
            stock_level.append(request.form.get('release-date'))
            stock_level.append(request.form.get('description'))
            stock_level.append(request.form.get('cover-image'))
            stock_level.append(request.form.get('retail-price'))
            stock_level.append(request.form.get('trade-price'))
            stock_level.append(int((request.form.get('quantity'))))
            add_to_database(stock_level)
        return render_template('stock-level.html', db=database)
    # if user doesn't have access to this page redirects to home page
    else:
        return redirect('/', code=302)


'''add to database
   input: list of product details
   adds new data to directly to database
'''
def add_to_database(stock_level):
    con = sqlite3.connect('book_shop.db', isolation_level=None)
    cur = con.cursor()
    cur.execute(('insert into book_info values (?, ?, ?, ?, ?, ?, ?, ?, ?);'), (*stock_level,))
    con.commit()
    cur.close()
    con.close()


@app.route('/stock_display', methods=['post', 'get'])
def change_stock():
    if session['logged_in'] == True and session['role'] == 'admin':  # checks if user has access to this page
        database = list(read_database("book_info"))
        if request.method == 'POST':
            new_quantity = int(request.form.get('quantity_changed'))
            isbm = "'" + str(request.form.get('ISBM-13')) + "'" # added extra quotes because without them python could not read sql statment
            con = sqlite3.connect('book_shop.db')
            cur = con.cursor()
            if new_quantity > 0:
                new_quantity = "'" + str(request.form.get('quantity_changed')) + "'" # added extra quotes because without them python could not read sql statment
                cur.execute("UPDATE book_info SET quantity = " + new_quantity + " WHERE ISBM13 = " + isbm + ";")
                con.commit()
            if new_quantity == 0:
                cur.execute(('DELETE FROM book_info WHERE ISBM13=' + isbm + ';'))
                con.commit()
            cur.close()
            con.close()
        else:
            return render_template('stock_display.html', db=database)
        return render_template('stock_display.html', db=database)
    else:
        return redirect('/', code=302)


@app.route('/success')
def success():
    con = sqlite3.connect('book_shop.db')
    cur = con.cursor()
    database = read_database('book_info')
    for i in range(0, len(session['cart'])):
        for j in range(0, len(database)):
            if session['cart'][i][2] == database[j][0]:
                isbm = "'" + session['cart'][i][2] + "'" # added extra quotes because without them python could not read sql statment
                new_quantity = int(database[j][8]) - int(session['cart'][i][3])
                new_quantity = str(new_quantity)
                new_quantity = "'" + new_quantity + "'" # added extra quotes because without them python could not read sql statment
                cur.execute("UPDATE book_info SET quantity = " + new_quantity + " WHERE ISBM13 = " + isbm + ";")
                con.commit()

    return render_template('success.html')


@app.route('/success-to-home')
def success_to_home():
    empty_cart()
    return redirect('/home', code=302)


@app.route('/pay')
def pay():
    return render_template('pay.html')