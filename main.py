from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import func
from database import (
    register as db_register, 
    login as db_login,
    add_product, 
    all_products, 
    add_sale, 
    all_sales, 
    add_stock, 
    all_stocks, 
    delete_product,
    Product, 
    Sale,
    session as db_session 
)

app = Flask(__name__)
app.secret_key = "Sup@duka123!!"

# ── Index ──
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# ── Register ──
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username         = request.form['username']
        email            = request.form['email']
        password         = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match!', hide_footer=True)

        result = db_register(username, email, password, confirm_password)
        if result:
            return redirect(url_for('login_page'))
        else:
            return render_template('register.html', error='User already exists!', hide_footer=True)

    return render_template('register.html', hide_footer=True)

# ── Login ──
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db_login(username, password)
        if user:
            session['user_id']  = user.id 
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password!", hide_footer=True)

    return render_template('login.html', hide_footer=True)

# ── Dashboard ──
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    username = session.get('username', 'User')

    try:
        # 1. Fetch all actual products from the database for this user
        products = db_session.query(Product).filter(Product.user_id == user_id).all()

        labels = []
        values = []

        for p in products:
            labels.append(p.name)
            # 2. Use your existing logic to get the current stock level
            # This ensures the chart shows exactly what's in your store
            current_stock = available_stock(user_id, p.id)
            values.append(current_stock)
            
    except Exception as e:
        print(f"Error: {e}")
        labels, values = [], []

    return render_template(
        'chart.html', 
        username=username, 
        labels=labels, 
        values=values
    )
# ── Products ──
@app.route('/products', methods=['GET', 'POST'])
def products_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        name = request.form['name']
        buying_price = float(request.form['buying_price'])
        selling_price = float(request.form['selling_price'])
        
        # Add product to database
        add_product(user_id, name, buying_price, selling_price)
        
        return redirect(url_for('products_page'))

    products = all_products(user_id)
    return render_template('products.html', products=products)

@app.route('/delete_product/<int:product_id>')
def delete_product_route(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    delete_product(user_id, product_id)
    
    return redirect(url_for('products_page'))

# ── Sales ──
@app.route('/sales', methods=['GET', 'POST'])
def sales_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user_id = session['user_id']
    if request.method == 'POST':
        pid = int(request.form['pid'])
        quantity = int(request.form['quantity'])
        add_sale(user_id, pid, quantity)
        return redirect(url_for('sales_page'))

    sales = all_sales(user_id)
    products = all_products(user_id)
    return render_template('sales.html', sales=sales, products=products)

# ── Stock ──
@app.route('/stock', methods=['GET', 'POST'])
def stock_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    if request.method == 'POST':
        pid = int(request.form['pid'])
        quantity = int(request.form['stock'])
        add_stock(user_id, pid, quantity)
        return redirect(url_for('stock_page'))

    products = all_products(user_id)
    stocks = all_stocks(user_id)

    stock_data = []
    for product in products:
        total_stock = sum(s.stock_quantity for s in stocks if s.pid == product.id)
        stock_data.append({
            'product': product,
            'available_stock': total_stock
        })

    return render_template('stock.html', stock_data=stock_data, products=products)

# ── Logout ──
@app.route('/logout')
def logout():
    session.clear() 
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)