from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from collections import defaultdict
import json

app = Flask(_name_)
app.secret_key = 'your-secret-key-here'

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Your-password-here',
    'database': 'expense_tracker'
}

def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.close()
        conn.close()
        
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    description VARCHAR(255) NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully!")
    except Error as e:
        print(f"Error initializing database: {e}")

# HTML Template
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Expense Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
            line-height: 1.6;
        }
        
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 260px;
            height: 100vh;
            background: #1a202c;
            color: white;
            padding: 30px 0;
            z-index: 1000;
        }
        
        .logo {
            padding: 0 30px 30px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .logo h1 {
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .logo p {
            font-size: 13px;
            color: #a0aec0;
            margin-top: 5px;
        }
        
        .nav {
            padding: 30px 0;
        }
        
        .nav-item {
            padding: 12px 30px;
            color: #a0aec0;
            text-decoration: none;
            display: flex;
            align-items: center;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .nav-item:hover, .nav-item.active {
            background: rgba(255,255,255,0.05);
            color: white;
        }
        
        .nav-icon {
            margin-right: 12px;
            font-size: 18px;
        }
        
        .main-content {
            margin-left: 260px;
            padding: 30px 40px;
            min-height: 100vh;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
        }
        
        .header h2 {
            font-size: 28px;
            font-weight: 600;
            color: #1a202c;
        }
        
        .header-right {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .date-display {
            color: #718096;
            font-size: 14px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: #4299e1;
            color: white;
        }
        
        .btn-primary:hover {
            background: #3182ce;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }
        
        .stat-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .stat-label {
            font-size: 13px;
            color: #718096;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 8px;
        }
        
        .stat-change {
            font-size: 13px;
            color: #48bb78;
        }
        
        .stat-change.negative {
            color: #f56565;
        }
        
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 24px;
            margin-bottom: 24px;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: #1a202c;
        }
        
        .table-wrapper {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            text-align: left;
            padding: 12px;
            font-size: 12px;
            font-weight: 600;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        td {
            padding: 16px 12px;
            border-bottom: 1px solid #f7fafc;
            font-size: 14px;
        }
        
        tr:hover {
            background: #f7fafc;
        }
        
        .category-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .category-food { background: #fef5e7; color: #d68910; }
        .category-transportation { background: #ebf8ff; color: #2c5282; }
        .category-shopping { background: #faf5ff; color: #6b46c1; }
        .category-entertainment { background: #fff5f5; color: #c53030; }
        .category-bills { background: #f0fff4; color: #22543d; }
        .category-healthcare { background: #e6fffa; color: #234e52; }
        .category-education { background: #edf2f7; color: #2d3748; }
        .category-other { background: #f7fafc; color: #4a5568; }
        
        .amount {
            font-weight: 600;
            color: #1a202c;
        }
        
        .delete-btn {
            background: transparent;
            color: #e53e3e;
            border: 1px solid #feb2b2;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .delete-btn:hover {
            background: #fff5f5;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-size: 13px;
            font-weight: 500;
            color: #4a5568;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            transition: all 0.2s;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #4299e1;
            box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        }
        
        .no-data {
            text-align: center;
            padding: 60px 20px;
            color: #a0aec0;
        }
        
        .no-data-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }
        
        .alert {
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .alert-success {
            background: #f0fff4;
            color: #22543d;
            border: 1px solid #c6f6d5;
        }
        
        .alert-error {
            background: #fff5f5;
            color: #742a2a;
            border: 1px solid #feb2b2;
        }
        
        .category-breakdown {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .category-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .category-info {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
        }
        
        .category-color {
            width: 8px;
            height: 40px;
            border-radius: 4px;
        }
        
        .category-details h4 {
            font-size: 14px;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 4px;
        }
        
        .category-details p {
            font-size: 12px;
            color: #718096;
        }
        
        .category-amount {
            font-size: 16px;
            font-weight: 600;
            color: #1a202c;
        }
        
        .progress-bar {
            width: 100%;
            height: 6px;
            background: #f7fafc;
            border-radius: 3px;
            margin-top: 8px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4299e1, #3182ce);
            border-radius: 3px;
            transition: width 0.3s;
        }

        @media (max-width: 1200px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
            }
            .main-content {
                margin-left: 0;
                padding: 20px;
            }
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo">
            <h1>💰 FinTrack</h1>
            <p>Expense Dashboard</p>
        </div>
        <nav class="nav">
            <div class="nav-item active">
                <span class="nav-icon">📊</span>
                <span>Dashboard</span>
            </div>
            <div class="nav-item">
                <span class="nav-icon">💳</span>
                <span>Expenses</span>
            </div>
            <div class="nav-item">
                <span class="nav-icon">📈</span>
                <span>Analytics</span>
            </div>
            <div class="nav-item">
                <span class="nav-icon">⚙</span>
                <span>Settings</span>
            </div>
        </nav>
    </div>

    <div class="main-content">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">
                        <span>{% if category == 'success' %}✓{% else %}⚠{% endif %}</span>
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="header">
            <h2>Dashboard Overview</h2>
            <div class="header-right">
                <span class="date-display">{{ current_date }}</span>
                <button class="btn btn-primary" onclick="document.getElementById('add-form').scrollIntoView({behavior: 'smooth'})">
                    + Add Expense
                </button>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-header">
                    <div>
                        <div class="stat-label">Total Balance</div>
                        <div class="stat-value">₹{{ "%.2f"|format(total) }}</div>
                        <div class="stat-change">All time expenses</div>
                    </div>
                    <div class="stat-icon" style="background: #ebf8ff; color: #2c5282;">💰</div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-header">
                    <div>
                        <div class="stat-label">This Month</div>
                        <div class="stat-value">₹{{ "%.2f"|format(month_total) }}</div>
                        <div class="stat-change {% if month_change < 0 %}negative{% endif %}">
                            {% if month_change >= 0 %}+{% endif %}{{ "%.1f"|format(month_change) }}% from last month
                        </div>
                    </div>
                    <div class="stat-icon" style="background: #fef5e7; color: #d68910;">📅</div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-header">
                    <div>
                        <div class="stat-label">This Week</div>
                        <div class="stat-value">₹{{ "%.2f"|format(week_total) }}</div>
                        <div class="stat-change">Last 7 days</div>
                    </div>
                    <div class="stat-icon" style="background: #f0fff4; color: #22543d;">📊</div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-header">
                    <div>
                        <div class="stat-label">Total Entries</div>
                        <div class="stat-value">{{ count }}</div>
                        <div class="stat-change">{{ avg_per_day }} avg/day</div>
                    </div>
                    <div class="stat-icon" style="background: #faf5ff; color: #6b46c1;">📝</div>
                </div>
            </div>
        </div>

        <div class="content-grid">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Recent Transactions</h3>
                </div>
                {% if expenses %}
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Category</th>
                                <th>Description</th>
                                <th>Amount</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for expense in expenses[:10] %}
                            <tr>
                                <td>{{ expense[1] }}</td>
                                <td>
                                    <span class="category-badge category-{{ expense[2]|lower }}">
                                        {{ expense[2] }}
                                    </span>
                                </td>
                                <td>{{ expense[3] }}</td>
                                <td class="amount">₹{{ "%.2f"|format(expense[4]) }}</td>
                                <td>
                                    <form method="POST" action="{{ url_for('delete_expense', id=expense[0]) }}" style="display:inline;">
                                        <button type="submit" class="delete-btn" onclick="return confirm('Delete this expense?')">Delete</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="no-data">
                    <div class="no-data-icon">📭</div>
                    <p>No expenses yet. Add your first expense!</p>
                </div>
                {% endif %}
            </div>

            <div>
                <div class="card" style="margin-bottom: 24px;">
                    <div class="card-header">
                        <h3 class="card-title">Category Breakdown</h3>
                    </div>
                    <div class="category-breakdown">
                        {% for cat_name, cat_amount, cat_percent in category_data %}
                        <div class="category-item">
                            <div class="category-info">
                                <div class="category-color" style="background: {% if cat_name == 'Food' %}#d68910{% elif cat_name == 'Transportation' %}#2c5282{% elif cat_name == 'Shopping' %}#6b46c1{% elif cat_name == 'Entertainment' %}#c53030{% elif cat_name == 'Bills' %}#22543d{% elif cat_name == 'Healthcare' %}#234e52{% elif cat_name == 'Education' %}#2d3748{% else %}#4a5568{% endif %};"></div>
                                <div class="category-details">
                                    <h4>{{ cat_name }}</h4>
                                    <p>{{ "%.1f"|format(cat_percent) }}% of total</p>
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: {{ cat_percent }}%;"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="category-amount">₹{{ "%.2f"|format(cat_amount) }}</div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="card" id="add-form">
                    <div class="card-header">
                        <h3 class="card-title">Add New Expense</h3>
                    </div>
                    <form method="POST" action="{{ url_for('add_expense') }}">
                        <div class="form-group">
                            <label for="date">Date</label>
                            <input type="date" id="date" name="date" required value="{{ today }}">
                        </div>
                        <div class="form-group">
                            <label for="category">Category</label>
                            <select id="category" name="category" required>
                                <option value="">Select Category</option>
                                <option value="Food">🍔 Food</option>
                                <option value="Transportation">🚗 Transportation</option>
                                <option value="Shopping">🛍 Shopping</option>
                                <option value="Entertainment">🎮 Entertainment</option>
                                <option value="Bills">💡 Bills</option>
                                <option value="Healthcare">⚕ Healthcare</option>
                                <option value="Education">📚 Education</option>
                                <option value="Other">📦 Other</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="description">Description</label>
                            <input type="text" id="description" name="description" required placeholder="e.g., Lunch at restaurant">
                        </div>
                        <div class="form-group">
                            <label for="amount">Amount (₹)</label>
                            <input type="number" id="amount" name="amount" step="0.01" required placeholder="0.00">
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">Add Expense</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    conn = get_db()
    if not conn:
        return render_template_string(DASHBOARD_TEMPLATE, 
            expenses=[], total=0, month_total=0, week_total=0, count=0,
            category_data=[], today=datetime.now().strftime('%Y-%m-%d'),
            current_date=datetime.now().strftime('%B %d, %Y'),
            month_change=0, avg_per_day=0
        )
    
    try:
        cursor = conn.cursor()
        
        # Get all expenses
        cursor.execute('SELECT id, date, category, description, amount FROM expenses ORDER BY date DESC, id DESC')
        expenses = cursor.fetchall()
        
        # Total expenses
        cursor.execute('SELECT SUM(amount) as total FROM expenses')
        total = float(cursor.fetchone()[0] or 0)
        
        # This month
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('SELECT SUM(amount) FROM expenses WHERE DATE_FORMAT(date, %s) = %s', ('%Y-%m', current_month))
        month_total = float(cursor.fetchone()[0] or 0)
        
        # Last month for comparison
        last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        cursor.execute('SELECT SUM(amount) FROM expenses WHERE DATE_FORMAT(date, %s) = %s', ('%Y-%m', last_month))
        last_month_total = float(cursor.fetchone()[0] or 0)
        month_change = ((month_total - last_month_total) / last_month_total * 100) if last_month_total > 0 else 0
        
        # This week
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('SELECT SUM(amount) FROM expenses WHERE date >= %s', (week_ago,))
        week_total = float(cursor.fetchone()[0] or 0)
        
        # Count and average
        cursor.execute('SELECT COUNT(*) FROM expenses')
        count = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(date) FROM expenses')
        first_date = cursor.fetchone()[0]
        if first_date:
            days = (datetime.now().date() - first_date).days + 1
            avg_per_day = round(count / days, 1) if days > 0 else 0
        else:
            avg_per_day = 0
        
        # Category breakdown
        cursor.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            GROUP BY category 
            ORDER BY total DESC
        ''')
        categories = cursor.fetchall()
        category_data = []
        for cat, amount in categories:
            percent = (float(amount) / total * 100) if total > 0 else 0
            category_data.append((cat, float(amount), percent))
        
        cursor.close()
        conn.close()
        
    except Error as e:
        flash(f'Database error: {e}', 'error')
        return redirect(url_for('index'))
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        expenses=expenses,
        total=total,
        month_total=month_total,
        week_total=week_total,
        count=count,
        category_data=category_data,
        today=datetime.now().strftime('%Y-%m-%d'),
        current_date=datetime.now().strftime('%B %d, %Y'),
        month_change=month_change,
        avg_per_day=avg_per_day
    )

@app.route('/add', methods=['POST'])
def add_expense():
    date = request.form['date']
    category = request.form['category']
    description = request.form['description']
    amount = float(request.form['amount'])
    
    conn = get_db()
    if not conn:
        flash('Database connection error!', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO expenses (date, category, description, amount) VALUES (%s, %s, %s, %s)',
            (date, category, description, amount)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Expense added successfully!', 'success')
    except Error as e:
        flash(f'Error adding expense: {e}', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    conn = get_db()
    if not conn:
        flash('Database connection error!', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = %s', (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Expense deleted successfully!', 'success')
    except Error as e:
        flash(f'Error deleting expense: {e}', 'error')
    
    return redirect(url_for('index'))

if _name_ == '_main_':
    init_db()
    app.run(debug=True)
