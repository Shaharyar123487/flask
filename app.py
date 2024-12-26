from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import sqlite3
import threading
import os
import shutil
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for authentication
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

# Replace with database-backed users
users = {
    'ayyanztech': {'password': 'admin'},
    'admin': {'password': 'admin'}  # keeping the admin user as backup
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in users else None

# Thread-local storage for database connections
db_local = threading.local()

# Database connection helper
def get_db():
    if not hasattr(db_local, 'db'):
        db_local.db = sqlite3.connect('inventory.db', timeout=30)
        db_local.db.row_factory = sqlite3.Row
    return db_local.db

def close_db():
    if hasattr(db_local, 'db'):
        db_local.db.close()
        del db_local.db

# Initialize database
def init_db():
    db = sqlite3.connect('inventory.db', timeout=30)
    try:
        db.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                supplier_price REAL NOT NULL,
                wholesale_price REAL NOT NULL,
                retail_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (purchase_id) REFERENCES purchases (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                refund_amount REAL NOT NULL,
                reason TEXT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS return_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                original_price REAL NOT NULL,
                return_price REAL NOT NULL,
                FOREIGN KEY (return_id) REFERENCES returns (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS expense_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                reference_no TEXT,
                FOREIGN KEY (category_id) REFERENCES expense_categories (id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                reference_no TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add balance column to existing suppliers table if it doesn't exist
        try:
            db.execute('SELECT balance FROM suppliers LIMIT 1')
        except sqlite3.OperationalError:
            db.execute('ALTER TABLE suppliers ADD COLUMN balance REAL DEFAULT 0')
            db.commit()
        
        # Create settings table
        db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                tax_number TEXT,
                currency_symbol TEXT DEFAULT '$',
                currency_code TEXT DEFAULT 'USD',
                decimal_places INTEGER DEFAULT 2,
                date_format TEXT DEFAULT 'YYYY-MM-DD',
                logo_path TEXT,
                footer_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default settings if not exists
        db.execute('''
            INSERT OR IGNORE INTO settings (id, business_name, currency_symbol)
            VALUES (1, 'My Business', '$')
        ''')
        
        db.commit()
    finally:
        db.close()

@app.teardown_appcontext
def teardown_db(exception=None):
    close_db()

# Routes
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login_post():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            login_user(User(username))
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    
    # Get total counts
    counts = {
        'customers': db.execute('SELECT COUNT(*) as count FROM customers').fetchone()['count'],
        'suppliers': db.execute('SELECT COUNT(*) as count FROM suppliers').fetchone()['count'],
        'products': db.execute('SELECT COUNT(*) as count FROM products').fetchone()['count']
    }
    
    # Get financial summaries
    financials = {
        'total_sales': db.execute('SELECT SUM(total_amount) as total FROM sales').fetchone()['total'] or 0,
        'total_purchases': db.execute('SELECT SUM(total_amount) as total FROM purchases').fetchone()['total'] or 0,
        'receivables': db.execute('SELECT SUM(balance) as total FROM customers').fetchone()['total'] or 0,
        'payables': db.execute('SELECT SUM(balance) as total FROM suppliers').fetchone()['total'] or 0
    }
    
    # Get recent sales
    recent_sales = db.execute('''
        SELECT s.*, c.name as customer_name,
               strftime('%Y-%m-%d %H:%M', s.date) as formatted_date
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        ORDER BY s.date DESC LIMIT 5
    ''').fetchall()
    
    # Get recent purchases
    recent_purchases = db.execute('''
        SELECT p.*, s.name as supplier_name,
               strftime('%Y-%m-%d %H:%M', p.date) as formatted_date
        FROM purchases p
        JOIN suppliers s ON p.supplier_id = s.id
        ORDER BY p.date DESC LIMIT 5
    ''').fetchall()
    
    # Get top selling products
    top_products = db.execute('''
        SELECT p.name, SUM(si.quantity) as total_quantity,
               SUM(si.quantity * si.price) as total_amount
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        GROUP BY si.product_id
        ORDER BY total_quantity DESC
        LIMIT 5
    ''').fetchall()
    
    # Get monthly sales data for chart
    monthly_sales = db.execute('''
        SELECT strftime('%Y-%m', date) as month,
               SUM(total_amount) as total
        FROM sales
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
        LIMIT 12
    ''').fetchall()
    
    # Get monthly purchases data for chart
    monthly_purchases = db.execute('''
        SELECT strftime('%Y-%m', date) as month,
               SUM(total_amount) as total
        FROM purchases
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
        LIMIT 12
    ''').fetchall()
    
    # Get low stock products
    low_stock = db.execute('''
        SELECT name, quantity
        FROM products
        WHERE quantity <= 10
        ORDER BY quantity ASC
        LIMIT 5
    ''').fetchall()
    
    settings = db.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    
    return render_template('dashboard.html',
                         counts=counts,
                         financials=financials,
                         recent_sales=recent_sales,
                         recent_purchases=recent_purchases,
                         top_products=top_products,
                         monthly_sales=monthly_sales,
                         monthly_purchases=monthly_purchases,
                         low_stock=low_stock,
                         settings=settings)

@app.route('/suppliers')
@login_required
def suppliers():
    db = get_db()
    suppliers = db.execute('SELECT * FROM suppliers ORDER BY name').fetchall()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/suppliers/add', methods=['POST'])
@login_required
def add_supplier():
    name = request.form['name']
    contact = request.form['contact']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    balance = float(request.form['balance'])

    db = get_db()
    db.execute('''
        INSERT INTO suppliers (name, contact, phone, email, address, balance)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, contact, phone, email, address, balance))
    db.commit()
    
    flash('Supplier added successfully!', 'success')
    return redirect(url_for('suppliers'))

@app.route('/customers')
@login_required
def customers():
    db = get_db()
    customers = db.execute('SELECT * FROM customers ORDER BY name').fetchall()
    return render_template('customers.html', customers=customers)

@app.route('/customers/add', methods=['POST'])
@login_required
def add_customer():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    balance = float(request.form['balance'])

    db = get_db()
    db.execute('''
        INSERT INTO customers (name, phone, email, address, balance)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, phone, email, address, balance))
    db.commit()
    
    flash('Customer added successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/sales')
@login_required
def sales():
    db = get_db()
    settings = db.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    sales = db.execute('''
        SELECT s.*, c.name as customer_name
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        ORDER BY s.date DESC
    ''').fetchall()
    
    customers = db.execute('SELECT * FROM customers ORDER BY name').fetchall()
    products = db.execute('SELECT * FROM products ORDER BY name').fetchall()
    return render_template('sales.html', sales=sales, customers=customers, products=products, settings=settings)

@app.route('/sales/add', methods=['POST'])
@login_required
def add_sale():
    customer_id = request.form['customer_id']
    products = request.form.getlist('products[]')
    quantities = request.form.getlist('quantities[]')
    prices = request.form.getlist('prices[]')
    paid_amount = float(request.form['paid_amount'])
    
    total_amount = sum(float(p) * float(q) for p, q in zip(prices, quantities))
    
    db = get_db()
    cursor = db.cursor()
    
    # Insert sale record
    cursor.execute('''
        INSERT INTO sales (customer_id, total_amount, paid_amount)
        VALUES (?, ?, ?)
    ''', (customer_id, total_amount, paid_amount))
    sale_id = cursor.lastrowid
    
    # Insert sale items and update products
    for product_id, quantity, price in zip(products, quantities, prices):
        quantity = int(quantity)
        price = float(price)
        
        cursor.execute('''
            INSERT INTO sale_items (sale_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        ''', (sale_id, product_id, quantity, price))
        
        # Update product quantity
        cursor.execute('''
            UPDATE products 
            SET quantity = quantity - ?
            WHERE id = ?
        ''', (quantity, product_id))
    
    # Update customer balance
    cursor.execute('''
        UPDATE customers 
        SET balance = balance + ? 
        WHERE id = ?
    ''', (total_amount - paid_amount, customer_id))
    
    db.commit()
    flash('Sale added successfully!', 'success')
    return redirect(url_for('sales'))

@app.route('/purchases')
@login_required
def purchases():
    db = get_db()
    settings = db.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    purchases = db.execute('''
        SELECT p.*, s.name as supplier_name
        FROM purchases p
        JOIN suppliers s ON p.supplier_id = s.id
        ORDER BY p.date DESC
    ''').fetchall()
    
    suppliers = db.execute('SELECT * FROM suppliers ORDER BY name').fetchall()
    products = db.execute('SELECT * FROM products ORDER BY name').fetchall()
    return render_template('purchases.html', purchases=purchases, suppliers=suppliers, products=products, settings=settings)

@app.route('/add_purchase', methods=['POST'])
@login_required
def add_purchase():
    db = get_db()
    try:
        data = request.json
        supplier_id = data['supplier_id']
        items = data['items']
        total_amount = sum(item['quantity'] * item['price'] for item in items)
        paid_amount = data.get('paid_amount', 0)
        
        cursor = db.cursor()
        
        # Insert purchase record
        cursor.execute('''
            INSERT INTO purchases (supplier_id, total_amount, paid_amount, date)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', [supplier_id, total_amount, paid_amount])
        
        purchase_id = cursor.lastrowid
        
        # Insert purchase items
        for item in items:
            cursor.execute('''
                INSERT INTO purchase_items (purchase_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', [purchase_id, item['product_id'], item['quantity'], item['price']])
            
            # Update product quantity and supplier price
            cursor.execute('''
                UPDATE products
                SET quantity = quantity + ?,
                    supplier_price = ?
                WHERE id = ?
            ''', [item['quantity'], item['price'], item['product_id']])
        
        # Update supplier balance if not fully paid
        if paid_amount < total_amount:
            cursor.execute('''
                UPDATE suppliers
                SET balance = balance + ?
                WHERE id = ?
            ''', [total_amount - paid_amount, supplier_id])
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Purchase added successfully',
            'purchase_id': purchase_id
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/products')
@login_required
def products():
    db = get_db()
    products = db.execute('SELECT * FROM products ORDER BY name').fetchall()
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['POST'])
@login_required
def add_product():
    name = request.form['name']
    supplier_price = float(request.form['supplier_price'])
    wholesale_price = float(request.form['wholesale_price'])
    retail_price = float(request.form['retail_price'])
    quantity = int(request.form['quantity'])
    description = request.form['description']

    with get_db() as db:
        db.execute('''
            INSERT INTO products (name, supplier_price, wholesale_price, retail_price, quantity, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, supplier_price, wholesale_price, retail_price, quantity, description))
        db.commit()
    flash('Product added successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/reports')
@login_required
def reports():
    db = get_db()
    today = datetime.now().strftime('%Y-%m-%d')
    first_day = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    
    # Get all customers and suppliers for filtering
    customers = db.execute('SELECT id, name FROM customers ORDER BY name').fetchall()
    suppliers = db.execute('SELECT id, name FROM suppliers ORDER BY name').fetchall()
    
    # Get initial summary data
    summary = get_summary_data(db, first_day, today)
    
    return render_template('reports.html',
                         customers=customers,
                         suppliers=suppliers,
                         summary=summary)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/returns')
@login_required
def returns():
    db = get_db()
    returns = db.execute('''
        SELECT 
            r.*, 
            CASE 
                WHEN r.return_type = 'customer' THEN c.name
                ELSE s.name
            END as entity_name,
            strftime('%Y-%m-%d %H:%M:%S', r.date) as formatted_date
        FROM returns r
        LEFT JOIN customers c ON r.return_type = 'customer' AND r.entity_id = c.id
        LEFT JOIN suppliers s ON r.return_type = 'supplier' AND r.entity_id = s.id
        ORDER BY r.date DESC
    ''').fetchall()
    
    products = db.execute('SELECT * FROM products ORDER BY name').fetchall()
    return render_template('returns.html', returns=returns, products=products)

@app.route('/api/entities')
@login_required
def get_entities():
    db = get_db()
    customers = db.execute('SELECT id, name FROM customers ORDER BY name').fetchall()
    suppliers = db.execute('SELECT id, name FROM suppliers ORDER BY name').fetchall()
    
    return jsonify({
        'customers': [dict(c) for c in customers],
        'suppliers': [dict(s) for s in suppliers]
    })

@app.route('/returns/add', methods=['POST'])
@login_required
def add_return():
    return_type = request.form['return_type']
    entity_id = request.form['entity_id']
    products = request.form.getlist('products[]')
    quantities = request.form.getlist('quantities[]')
    prices = request.form.getlist('prices[]')
    refund_amount = float(request.form['refund_amount'])
    reason = request.form['reason']
    
    total_amount = sum(float(p) * float(q) for p, q in zip(prices, quantities))
    
    db = get_db()
    cursor = db.cursor()
    
    # Insert return record
    cursor.execute('''
        INSERT INTO returns (return_type, entity_id, total_amount, refund_amount, reason)
        VALUES (?, ?, ?, ?, ?)
    ''', (return_type, entity_id, total_amount, refund_amount, reason))
    return_id = cursor.lastrowid
    
    # Insert return items and update products
    for product_id, quantity, price in zip(products, quantities, prices):
        quantity = int(quantity)
        price = float(price)
        
        # Get original price
        product = cursor.execute(
            'SELECT supplier_price, retail_price FROM products WHERE id = ?', 
            (product_id,)
        ).fetchone()
        
        original_price = product['retail_price'] if return_type == 'customer' else product['supplier_price']
        
        cursor.execute('''
            INSERT INTO return_items (return_id, product_id, quantity, original_price, return_price)
            VALUES (?, ?, ?, ?, ?)
        ''', (return_id, product_id, quantity, original_price, price))
        
        # Update product quantity
        if return_type == 'customer':
            cursor.execute('''
                UPDATE products 
                SET quantity = quantity + ?
                WHERE id = ?
            ''', (quantity, product_id))
        else:  # supplier return
            cursor.execute('''
                UPDATE products 
                SET quantity = quantity - ?
                WHERE id = ?
            ''', (quantity, product_id))
    
    # Update entity balance
    if return_type == 'customer':
        cursor.execute('''
            UPDATE customers 
            SET balance = balance - ? 
            WHERE id = ?
        ''', (refund_amount, entity_id))
    else:
        cursor.execute('''
            UPDATE suppliers 
            SET balance = balance - ? 
            WHERE id = ?
        ''', (refund_amount, entity_id))
    
    db.commit()
    flash('Return added successfully!', 'success')
    return redirect(url_for('returns'))

@app.route('/expenses')
@login_required
def expenses():
    db = get_db()
    expenses = db.execute('''
        SELECT e.*, c.name as category_name,
               strftime('%Y-%m-%d %H:%M', e.date) as date
        FROM expenses e 
        JOIN expense_categories c ON e.category_id = c.id 
        ORDER BY e.date DESC
    ''').fetchall()
    categories = db.execute('SELECT * FROM expense_categories ORDER BY name').fetchall()
    return render_template('expenses.html', expenses=expenses, categories=categories)

@app.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    date = request.form['date']
    category_id = request.form['category_id']
    description = request.form['description']
    amount = float(request.form['amount'])
    payment_method = request.form['payment_method']
    reference_no = request.form['reference_no']
    
    db = get_db()
    db.execute('''
        INSERT INTO expenses (date, category_id, description, amount, payment_method, reference_no)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date, category_id, description, amount, payment_method, reference_no))
    db.commit()
    
    flash('Expense added successfully!', 'success')
    return redirect(url_for('expenses'))

@app.route('/expenses/categories/add', methods=['POST'])
@login_required
def add_expense_category():
    name = request.form['name']
    
    db = get_db()
    try:
        db.execute('INSERT INTO expense_categories (name) VALUES (?)', (name,))
        db.commit()
        flash('Category added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Category already exists!', 'error')
    
    return redirect(url_for('expenses'))

@app.route('/api/reports', methods=['POST'])
@login_required
def get_report_data():
    data = request.json
    report_type = data['report_type']
    date_from = data['date_from']
    date_to = data['date_to']
    entity_id = data['entity_id']
    search_term = data.get('search_term', '')
    transaction_type = data.get('transaction_type', '')
    
    db = get_db()
    
    if report_type == 'all':
        return get_all_transactions(db, date_from, date_to, transaction_type, search_term)
    elif report_type == 'customer':
        return get_customer_transactions(db, date_from, date_to, entity_id, search_term)
    elif report_type == 'supplier':
        return get_supplier_transactions(db, date_from, date_to, entity_id, search_term)
    elif report_type == 'expense':
        return get_expense_transactions(db, date_from, date_to)
    elif report_type == 'summary':
        return get_summary_data(db, date_from, date_to)
    
    return jsonify({'error': 'Invalid report type'})

def get_customer_transactions(db, date_from, date_to, customer_id=None, search_term=''):
    query = '''
        SELECT 
            c.name as customer_name,
            'Sale' as type,
            s.date,
            s.id as transaction_id,
            'Sale #' || s.id as description,
            s.total_amount as debit,
            s.paid_amount as credit,
            0 as balance
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        WHERE s.date BETWEEN ? AND ?
        AND (c.name LIKE ? OR 'Sale #' || s.id LIKE ?)
    '''
    
    search_param = f'%{search_term}%'
    params = [date_from, date_to, search_param, search_param]
    if customer_id:
        query += ' AND c.id = ?'
        params.append(customer_id)
    
    query += ' ORDER BY s.date'
    transactions = db.execute(query, params).fetchall()
    
    # Calculate running balance
    running_balance = 0
    result = []
    for trans in transactions:
        trans = dict(trans)
        running_balance += trans['debit'] - trans['credit']
        trans['balance'] = running_balance
        result.append(trans)
    
    return jsonify({'transactions': result})

def get_supplier_transactions(db, date_from, date_to, supplier_id=None, search_term=''):
    query = '''
        SELECT 
            s.name as supplier_name,
            'Purchase' as type,
            p.date,
            p.id as transaction_id,
            'Purchase #' || p.id as description,
            p.total_amount as debit,
            p.paid_amount as credit,
            0 as balance
        FROM purchases p
        JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.date BETWEEN ? AND ?
        AND (s.name LIKE ? OR 'Purchase #' || p.id LIKE ?)
    '''
    
    search_param = f'%{search_term}%'
    params = [date_from, date_to, search_param, search_param]
    if supplier_id:
        query += ' AND s.id = ?'
        params.append(supplier_id)
    
    query += ' ORDER BY date'
    
    transactions = db.execute(query, params).fetchall()
    
    # Calculate running balance
    running_balance = 0
    result = []
    for trans in transactions:
        trans = dict(trans)
        running_balance += trans['debit'] - trans['credit']
        trans['balance'] = running_balance
        result.append(trans)
    
    return jsonify({'transactions': result})

def get_expense_transactions(db, date_from, date_to):
    transactions = db.execute('''
        SELECT 
            e.*,
            c.name as category_name
        FROM expenses e
        JOIN expense_categories c ON e.category_id = c.id
        WHERE e.date BETWEEN ? AND ?
        ORDER BY e.date
    ''', [date_from, date_to]).fetchall()
    
    total = sum(t['amount'] for t in transactions)
    
    return jsonify({
        'transactions': [dict(t) for t in transactions],
        'total': total
    })

def get_summary_data(db, date_from, date_to):
    # Get sales data
    sales = db.execute('''
        SELECT 
            SUM(total_amount) as total_sales,
            SUM(paid_amount) as received_sales
        FROM sales
        WHERE date BETWEEN ? AND ?
    ''', [date_from, date_to]).fetchone()
    
    # Get purchases data
    purchases = db.execute('''
        SELECT 
            SUM(total_amount) as total_purchases,
            SUM(paid_amount) as paid_purchases
        FROM purchases
        WHERE date BETWEEN ? AND ?
    ''', [date_from, date_to]).fetchone()
    
    # Get expenses total
    expenses = db.execute('''
        SELECT SUM(amount) as total_expenses
        FROM expenses
        WHERE date BETWEEN ? AND ?
    ''', [date_from, date_to]).fetchone()
    
    total_sales = sales['total_sales'] or 0
    received_sales = sales['received_sales'] or 0
    total_purchases = purchases['total_purchases'] or 0
    paid_purchases = purchases['paid_purchases'] or 0
    total_expenses = expenses['total_expenses'] or 0
    
    # Calculate net position
    net_position = (received_sales - paid_purchases - total_expenses)
    
    return {
        'total_sales': total_sales,
        'received_sales': received_sales,
        'outstanding_sales': total_sales - received_sales,
        'total_purchases': total_purchases,
        'paid_purchases': paid_purchases,
        'outstanding_purchases': total_purchases - paid_purchases,
        'total_expenses': total_expenses,
        'net_position': net_position
    }

def get_all_transactions(db, date_from, date_to, transaction_type='', search_term=''):
    queries = []
    params = []
    
    # Sales query
    if not transaction_type or transaction_type == 'sale':
        queries.append('''
            SELECT 
                s.date,
                'Sale' as type,
                c.name as entity_name,
                'Sale #' || s.id as description,
                s.total_amount as amount,
                CASE 
                    WHEN s.paid_amount >= s.total_amount THEN 'Paid'
                    WHEN s.paid_amount > 0 THEN 'Partial'
                    ELSE 'Unpaid'
                END as status,
                s.id as transaction_id
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE s.date BETWEEN ? AND ?
            AND (c.name LIKE ? OR 'Sale #' || s.id LIKE ?)
        ''')
        params.extend([date_from, date_to, f'%{search_term}%', f'%{search_term}%'])
    
    # Purchases query
    if not transaction_type or transaction_type == 'purchase':
        queries.append('''
            SELECT 
                p.date,
                'Purchase' as type,
                s.name as entity_name,
                'Purchase #' || p.id as description,
                p.total_amount as amount,
                CASE 
                    WHEN p.paid_amount >= p.total_amount THEN 'Paid'
                    WHEN p.paid_amount > 0 THEN 'Partial'
                    ELSE 'Unpaid'
                END as status,
                p.id as transaction_id
            FROM purchases p
            JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.date BETWEEN ? AND ?
            AND (s.name LIKE ? OR 'Purchase #' || p.id LIKE ?)
        ''')
        params.extend([date_from, date_to, f'%{search_term}%', f'%{search_term}%'])
    
    # Returns query
    if not transaction_type or transaction_type == 'return':
        queries.append('''
            SELECT 
                r.date,
                r.return_type || ' Return' as type,
                CASE 
                    WHEN r.return_type = 'customer' THEN c.name
                    ELSE s.name
                END as entity_name,
                'Return #' || r.id || ' - ' || r.reason as description,
                r.total_amount as amount,
                'Completed' as status,
                r.id as transaction_id
            FROM returns r
            LEFT JOIN customers c ON r.return_type = 'customer' AND r.entity_id = c.id
            LEFT JOIN suppliers s ON r.return_type = 'supplier' AND r.entity_id = s.id
            WHERE r.date BETWEEN ? AND ?
            AND (c.name LIKE ? OR s.name LIKE ? OR 'Return #' || r.id LIKE ?)
        ''')
        params.extend([date_from, date_to, f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'])
    
    # Combine queries
    full_query = ' UNION ALL '.join(queries) + ' ORDER BY date DESC'
    
    transactions = db.execute(full_query, params).fetchall()
    return jsonify({'transactions': [dict(t) for t in transactions]})

@app.route('/api/sales/<int:sale_id>')
@login_required
def get_sale_details(sale_id):
    db = get_db()
    sale = db.execute('''
        SELECT s.*, c.name as customer_name,
               strftime('%Y-%m-%d %H:%M', s.date) as date
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        WHERE s.id = ?
    ''', [sale_id]).fetchone()
    
    items = db.execute('''
        SELECT si.*, p.name as product_name
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
    ''', [sale_id]).fetchall()
    
    return jsonify({
        'sale': dict(sale),
        'items': [dict(item) for item in items]
    })

@app.route('/api/purchases/<int:purchase_id>')
@login_required
def get_purchase_details(purchase_id):
    db = get_db()
    purchase = db.execute('''
        SELECT p.*, s.name as supplier_name,
               strftime('%Y-%m-%d %H:%M', p.date) as date
        FROM purchases p
        JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.id = ?
    ''', [purchase_id]).fetchone()
    
    items = db.execute('''
        SELECT pi.*, p.name as product_name
        FROM purchase_items pi
        JOIN products p ON pi.product_id = p.id
        WHERE pi.purchase_id = ?
    ''', [purchase_id]).fetchall()
    
    return jsonify({
        'purchase': dict(purchase),
        'items': [dict(item) for item in items]
    })

@app.route('/api/customer_history/<int:customer_id>')
@login_required
def get_customer_history(customer_id):
    db = get_db()
    transactions = db.execute('''
        SELECT 
            date,
            'Sale' as type,
            'Sale #' || id as description,
            total_amount as debit,
            paid_amount as credit
        FROM sales
        WHERE customer_id = ?
        UNION ALL
        SELECT 
            date,
            'Payment' as type,
            'Payment #' || id || CASE 
                WHEN payment_method != 'cash' 
                THEN ' (' || payment_method || 
                    CASE WHEN reference_no IS NOT NULL 
                        THEN ': ' || reference_no 
                        ELSE '' 
                    END || ')'
                ELSE ''
            END as description,
            0 as debit,
            amount as credit
        FROM payments
        WHERE entity_type = 'customer' AND entity_id = ?
        ORDER BY date DESC
    ''', [customer_id, customer_id]).fetchall()
    
    current_balance = db.execute(
        'SELECT balance FROM customers WHERE id = ?', 
        [customer_id]
    ).fetchone()['balance']
    
    return jsonify({
        'transactions': [dict(t) for t in transactions],
        'current_balance': current_balance
    })

@app.route('/api/supplier_history/<int:supplier_id>')
@login_required
def get_supplier_history(supplier_id):
    db = get_db()
    transactions = db.execute('''
        SELECT 
            date,
            'Purchase' as type,
            'Purchase #' || id as description,
            total_amount as debit,
            paid_amount as credit
        FROM purchases
        WHERE supplier_id = ?
        UNION ALL
        SELECT 
            date,
            'Payment' as type,
            'Payment #' || id || CASE 
                WHEN payment_method != 'cash' 
                THEN ' (' || payment_method || 
                    CASE WHEN reference_no IS NOT NULL 
                        THEN ': ' || reference_no 
                        ELSE '' 
                    END || ')'
                ELSE ''
            END as description,
            0 as debit,
            amount as credit
        FROM payments
        WHERE entity_type = 'supplier' AND entity_id = ?
        ORDER BY date DESC
    ''', [supplier_id, supplier_id]).fetchall()
    
    current_balance = db.execute(
        'SELECT balance FROM suppliers WHERE id = ?', 
        [supplier_id]
    ).fetchone()['balance']
    
    return jsonify({
        'transactions': [dict(t) for t in transactions],
        'current_balance': current_balance
    })

@app.route('/api/submit_payment', methods=['POST'])
@login_required
def submit_payment():
    data = request.json
    db = get_db()
    
    try:
        cursor = db.cursor()
        
        # Insert payment record
        cursor.execute('''
            INSERT INTO payments (
                entity_type, entity_id, amount, 
                payment_method, reference_no, date
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', [
            data['entity_type'],
            data['entity_id'],
            data['amount'],
            data['payment_method'],
            data['reference']
        ])
        
        # Update entity balance
        table_name = data['entity_type'] + 's'
        cursor.execute(f'''
            UPDATE {table_name}
            SET balance = balance - ?
            WHERE id = ?
        ''', [data['amount'], data['entity_id']])
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)})

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/settings')
@login_required
def settings():
    db = get_db()
    settings_row = db.execute('SELECT * FROM settings WHERE id = 1').fetchone()
    settings = dict(zip(settings_row.keys(), settings_row))
    return render_template('settings.html', settings=settings)

@app.route('/update_business_settings', methods=['POST'])
@login_required
def update_business_settings():
    db = get_db()
    
    # Handle logo upload
    logo_path = None
    if 'logo' in request.files:
        file = request.files['logo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            logo_path = f'/static/uploads/{filename}'
    
    # Update settings
    db.execute('''
        UPDATE settings SET
            business_name = ?,
            address = ?,
            phone = ?,
            email = ?,
            website = ?,
            tax_number = ?,
            footer_text = ?,
            logo_path = COALESCE(?, logo_path),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    ''', [
        request.form['business_name'],
        request.form['address'],
        request.form['phone'],
        request.form['email'],
        request.form['website'],
        request.form['tax_number'],
        request.form['footer_text'],
        logo_path
    ])
    
    db.commit()
    flash('Business information updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/update_currency_settings', methods=['POST'])
@login_required
def update_currency_settings():
    db = get_db()
    db.execute('''
        UPDATE settings SET
            currency_symbol = ?,
            currency_code = ?,
            decimal_places = ?,
            date_format = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    ''', [
        request.form['currency_symbol'],
        request.form['currency_code'],
        request.form['decimal_places'],
        request.form['date_format']
    ])
    
    db.commit()
    flash('Currency settings updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/create_backup')
@login_required
def create_backup():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'backup_{timestamp}.db'
    
    # Create backup directory if it doesn't exist
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    # Copy the database file
    shutil.copy2('inventory.db', f'backups/{backup_filename}')
    
    # Send the file to the user
    return send_file(
        f'backups/{backup_filename}',
        as_attachment=True,
        download_name=backup_filename
    )

@app.route('/restore_backup', methods=['POST'])
@login_required
def restore_backup():
    if 'backup_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('settings'))
    
    file = request.files['backup_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('settings'))
    
    try:
        # Create backup of current database
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.copy2('inventory.db', f'inventory_{timestamp}.db')
        
        # Save and restore from uploaded file
        file.save('inventory.db')
        
        flash('Database restored successfully', 'success')
    except Exception as e:
        flash(f'Error restoring database: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/invoice/<transaction_type>/<int:transaction_id>')
@login_required
def view_invoice(transaction_type, transaction_id):
    db = get_db()
    
    # Get settings with default values if not set
    settings = db.execute('''
        INSERT OR REPLACE INTO settings (
            id, business_name, currency_symbol, 
            address, phone, email, 
            tax_number, footer_text,
            currency_code, decimal_places
        ) 
        VALUES (
            1, 
            COALESCE((SELECT business_name FROM settings WHERE id = 1), 'My Business'),
            COALESCE((SELECT currency_symbol FROM settings WHERE id = 1), '$'),
            COALESCE((SELECT address FROM settings WHERE id = 1), ''),
            COALESCE((SELECT phone FROM settings WHERE id = 1), ''),
            COALESCE((SELECT email FROM settings WHERE id = 1), ''),
            COALESCE((SELECT tax_number FROM settings WHERE id = 1), ''),
            COALESCE((SELECT footer_text FROM settings WHERE id = 1), ''),
            COALESCE((SELECT currency_code FROM settings WHERE id = 1), 'USD'),
            COALESCE((SELECT decimal_places FROM settings WHERE id = 1), 2)
        )
        RETURNING *
    ''').fetchone()

    if transaction_type == 'sale':
        # Get sale details
        transaction = db.execute('''
            SELECT 
                s.*,
                c.name as entity_name,
                'sale' as type,
                strftime('%Y-%m-%d %H:%M:%S', s.date) as formatted_date,
                CASE 
                    WHEN s.paid_amount >= s.total_amount THEN 'Paid'
                    WHEN s.paid_amount > 0 THEN 'Partial'
                    ELSE 'Unpaid'
                END as status
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE s.id = ?
        ''', [transaction_id]).fetchone()

        # Get sale items
        items = db.execute('''
            SELECT 
                si.*,
                p.name as product_name,
                (si.quantity * si.price) as line_total
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
        ''', [transaction_id]).fetchall()

    elif transaction_type == 'purchase':
        # Get purchase details
        transaction = db.execute('''
            SELECT 
                p.*,
                s.name as entity_name,
                'purchase' as type,
                strftime('%Y-%m-%d %H:%M:%S', p.date) as formatted_date,
                CASE 
                    WHEN p.paid_amount >= p.total_amount THEN 'Paid'
                    WHEN p.paid_amount > 0 THEN 'Partial'
                    ELSE 'Unpaid'
                END as status
            FROM purchases p
            JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id = ?
        ''', [transaction_id]).fetchone()

        # Get purchase items
        items = db.execute('''
            SELECT 
                pi.*,
                p.name as product_name,
                (pi.quantity * pi.price) as line_total
            FROM purchase_items pi
            JOIN products p ON pi.product_id = p.id
            WHERE pi.purchase_id = ?
        ''', [transaction_id]).fetchall()

    else:
        flash('Invalid transaction type', 'error')
        return redirect(url_for('dashboard'))

    if not transaction:
        flash('Transaction not found', 'error')
        return redirect(url_for('dashboard'))

    return render_template('invoice.html',
                         settings=settings,
                         transaction=transaction,
                         items=items)

# Initialize database
with app.app_context():
    init_db()

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)
