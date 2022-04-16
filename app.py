from flask import Flask, render_template, request, redirect, session, url_for
import pyrebase
import re

app = Flask(__name__)

app.config['SECRET_KEY'] = "c6e803cd18a8c528c161eb9fcf013245248506ffb540ff70"

firebaseConfig = {
  "apiKey": "AIzaSyAyyDCMp8e8ZGXLUmpH4rLfCUnuodHj4so",
  "authDomain": "mercator-9ff70.firebaseapp.com",
  "databaseURL": "https://mercator-9ff70-default-rtdb.firebaseio.com",
  "projectId": "mercator-9ff70",
  "storageBucket": "mercator-9ff70.appspot.com",
  "messagingSenderId": "529306745786",
  "appId": "1:529306745786:web:a21ca88ed37d76aa7d3b83",
  "measurementId": "G-HGHHKPBERF"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

def check_credentials(email,password):
    try:
        if db.child("Email Ids").child(email.replace(".","_").replace("@","_")).get().val() is None:
            return False
    except:
        return False
    return True


def get_sold_product_details():
    res = []
    data_check = db.child("All Products").get()
    try:
        for i in data_check.each():
            temp = i.val()
            if temp['price'] != "Free":
                temp['price'] = "Rs. "+temp['price']
            else:
                continue
            res.append(temp)
    except:
        pass
    return res

def get_donated_product_details():
    res = []
    try:
        data_check = db.child("All Products").get()
        for i in data_check.each():
            temp = i.val()
            if temp['price'] == "Free":
                res.append(temp)
    except:
        pass
    return res

def get_personal_sold_products(email):
    res = []
    data_check = db.child("All Products").get()
    try:
        for i in data_check.each():
            temp = i.val()
            if temp['seller_email'] == email and temp['price'] != 'Free':
                temp['delete_url'] = "/account/sell/delete/"+i.key()
                res.append(temp)
    except:
        return []
    return res

def get_personal_donated_products(email):
    res = []
    data_check = db.child("All Products").get()
    try:
        for i in data_check.each():
            temp = i.val()
            if temp['seller_email'] == email and temp['price'] == 'Free':
                temp['delete_url'] = "/account/donate/delete/"+i.key()
                res.append(temp)
    except:
        return []
    return res

@app.route('/')
@app.route('/login',methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email'].lower()
        password = request.form['password']
        try:
            auth.sign_in_with_email_and_password(email, password)
            session['loggedin'] = True
            session['email'] = email
            msg = 'Logged in successfully !'
            return redirect("/account/buy")
        except:
            msg = 'Incorrect username / password !'
    if request.method == "GET":
        try:
            if session['loggedin'] is True:
                return redirect("/account/buy")
        except:
            pass
    return render_template('login.html', ermsg=msg)


@app.route('/account/logout')
def logout():
    try:
        session['loggedin'] = False
        session.pop('email', None)
    except:
        pass
    return redirect(url_for('login'))


#edit start
@app.route('/account')
@app.route('/account/buy')
def account():
    try:
        if session['loggedin'] is False:
            return render_template('login.html',ermsg = 'Please login before continuing')
    except:
        pass
    sold_product_details = get_sold_product_details()
    donated_product_details = get_donated_product_details()
    return render_template('buy.html',sold_res=sold_product_details,donated_res = donated_product_details)

@app.route('/account/sell',methods=['GET', 'POST'] )
def sell():
    try:
        if session['loggedin'] is False:
            return render_template('login.html',ermsg = 'Please login before continuing')
    except:
        pass
    if request.method == "POST":
        product_name = request.form['product_name']
        price = request.form['price']
        public_email = request.form['public_email']
        public_phone = request.form['public_phone']
        description = request.form['description']
        seller_email = session['email']
        product_details = {"product_name" : product_name,"price":price,"public_mail":public_email,"public_phone":public_phone,"description":description,"seller_email":seller_email}
        db.child("All Products").push(product_details)
    personal_sold_list = get_personal_sold_products(session['email'])
    return render_template('seller page.html',soldres=personal_sold_list)

@app.route('/account/donate',methods=['GET', 'POST'])
def donate():
    try:
        if session['loggedin'] is False:
            return render_template('login.html', ermsg='Please login before continuing')
    except:
        pass
    if request.method == "POST":
        product_name = request.form['product_name']
        price = "Free"
        public_email = request.form['public_email']
        public_phone = request.form['public_phone']
        description = request.form['description']
        seller_email = session['email']
        product_details = {"product_name": product_name, "price": price, "public_mail": public_email,"public_phone": public_phone, "description": description, "seller_email": seller_email}
        db.child("All Products").push(product_details)
    donated_items = get_personal_donated_products(session['email'])
    return render_template('Donations.html',donatedres = donated_items)

@app.route('/account/sell/delete/<string:inp>', methods = ["POST","GET"])
def remove_sold_item(inp):
    try:
        if session['loggedin'] is False:
            return render_template('login.html',ermsg = 'Please login before continuing')
    except:
        pass
    db.child("All Products").child(inp).remove()
    return redirect("/account/sell")

@app.route('/account/donate/delete/<string:inp>',methods = ["POST","GET"])
def remove_donate_item(inp):
    try:
        if session['loggedin'] is False:
            return render_template('login.html',ermsg = 'Please login before continuing')
    except:
        pass
    db.child("All Products").child(inp).remove()
    return redirect("/account/donate")


@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['name']
        password = request.form['password']
        email = request.form['email']
        mobile_no = request.form['phone_num']
        if check_credentials(email,password):
            msg = 'Account already exists !'
        elif (mobile_no.isnumeric() is False) or len(mobile_no) != 10:
            msg = 'Mobile number is invalid'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            if db.child("User Data").child(username).get().val() is None:
                auth.create_user_with_email_and_password(email,password)
                db.child("User Data").child(username).update({"Name":username,"Email":email,"Mobile Number":mobile_no})
                db.child("Email Ids").child(email.replace(".","_").replace("@","_")).update({"check":"1"})
                return redirect("/account/buy")
            else:
                msg = 'Account with same name already exists !!'
        return render_template('register.html', ermsg = msg)
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', ermsg = msg)


if __name__ == '__main__':
    app.run()
