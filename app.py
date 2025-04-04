from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Function to create a database connection
def get_db_connection():
    conn = sqlite3.connect('grocery.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database with improved schema
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'Uncategorized',
                manufacturing_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'manufacturing_date', 'expiry_date', 'quantity']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"status": "error", "message": f"{field.replace('_', ' ').title()} is required"}), 400

        name = data['name']
        category = data.get('category', 'Uncategorized')
        manufacturing_date = data['manufacturing_date']
        expiry_date = data['expiry_date']
        quantity = int(data['quantity'])
        price = float(data.get('price', 0))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products 
                (name, category, manufacturing_date, expiry_date, quantity, price) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, category, manufacturing_date, expiry_date, quantity, price))
            conn.commit()

        return jsonify({"status": "success", "message": "Product added successfully!"})
    except Exception as e:
        print(f"Error adding product: {str(e)}")  # Log the error
        return jsonify({"status": "error", "message": f"Error adding product: {str(e)}"}), 500

@app.route('/edit_product/<int:product_id>', methods=['PUT'])
def edit_product(product_id):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'manufacturing_date', 'expiry_date', 'quantity']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"status": "error", "message": f"{field.replace('_', ' ').title()} is required"}), 400

        name = data['name']
        category = data.get('category', 'Uncategorized')
        manufacturing_date = data['manufacturing_date']
        expiry_date = data['expiry_date']
        quantity = int(data['quantity'])
        price = float(data.get('price', 0))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products 
                SET name=?, category=?, manufacturing_date=?, expiry_date=?, quantity=?, price=?
                WHERE id=?
            """, (name, category, manufacturing_date, expiry_date, quantity, price, product_id))
            conn.commit()

        return jsonify({"status": "success", "message": "Product updated successfully!"})
    except Exception as e:
        print(f"Error editing product: {str(e)}")  # Log the error
        return jsonify({"status": "error", "message": f"Error editing product: {str(e)}"}), 500

@app.route('/get_products', methods=['GET'])
def get_products():
    try:
        category = request.args.get('category', '')
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT * FROM products WHERE category = ?", (category,))
            else:
                cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()

        return jsonify([{
            "id": p["id"], 
            "name": p["name"], 
            "category": p["category"],
            "manufacturing_date": p["manufacturing_date"],
            "expiry_date": p["expiry_date"], 
            "quantity": p["quantity"],
            "price": p["price"]
        } for p in products])
    except Exception as e:
        print(f"Error fetching products: {str(e)}")  # Log the error
        return jsonify({"status": "error", "message": f"Error fetching products: {str(e)}"}), 500

@app.route('/get_categories', methods=['GET'])
def get_categories():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM products")
            categories = [row['category'] for row in cursor.fetchall()]
        return jsonify(categories)
    except Exception as e:
        print(f"Error fetching categories: {str(e)}")  # Log the error
        return jsonify({"status": "error", "message": f"Error fetching categories: {str(e)}"}), 500

@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()

        return jsonify({"status": "success", "message": "Product deleted successfully!"})
    except Exception as e:
        print(f"Error deleting product: {str(e)}")  # Log the error
        return jsonify({"status": "error", "message": f"Error deleting product: {str(e)}"}), 500

@app.route('/check_expiry', methods=['GET'])
def check_expiry():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, expiry_date, quantity FROM products")
            products = cursor.fetchall()

        today = datetime.today()
        expiring_soon = []
        low_stock = []

        for p in products:
            expiry_date = datetime.strptime(p["expiry_date"], '%Y-%m-%d')
            days_left = (expiry_date - today).days

            if days_left <= 7:
                expiring_soon.append({
                    "name": p["name"], 
                    "days_left": days_left
                })
            
            if p["quantity"] <= 10:
                low_stock.append({
                    "name": p["name"], 
                    "quantity": p["quantity"]
                })

        return jsonify({
            "expiring_soon": expiring_soon,
            "low_stock": low_stock
        })
    except Exception as e:
        print(f"Error checking expiry: {str(e)}")  # Log the error
        return jsonify({"status": "error", "message": f"Error checking expiry: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)