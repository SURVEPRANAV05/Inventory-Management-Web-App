from flask import Flask, render_template, request, jsonify, send_from_directory
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

        # Convert to list of dictionaries
        result = []
        for p in products:
            result.append({
                "id": p["id"], 
                "name": p["name"], 
                "category": p["category"],
                "manufacturing_date": p["manufacturing_date"],
                "expiry_date": p["expiry_date"], 
                "quantity": p["quantity"],
                "price": p["price"]
            })

        return jsonify(result)
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

# Serve static files from the templates directory
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Make sure the templates directory exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Write the HTML file to the templates directory with UTF-8 encoding
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grocery Inventory Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
</head>
<body>
<div class="container mt-5">
    <h1 class="mb-4">Grocery Inventory Management</h1>

    <div class="card mb-4">
        <div class="card-header" id="productFormHeader">Add Product</div>
        <div class="card-body">
            <form id="productForm">
                <input type="hidden" id="productId">
                <div class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label">Product Name</label>
                        <input type="text" id="productName" class="form-control" placeholder="Enter product name" required>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Category</label>
                        <select id="productCategory" class="form-select">
                            <option value="Uncategorized">Uncategorized</option>
                            <option value="Dairy">Dairy</option>
                            <option value="Produce">Produce</option>
                            <option value="Bakery">Bakery</option>
                            <option value="Meat">Meat</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Manufacturing Date</label>
                        <input type="date" id="manufacturingDate" class="form-control" required>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Expiry Date</label>
                        <input type="date" id="expiryDate" class="form-control" required>
                    </div>
                    <div class="col-md-1">
                        <label class="form-label">Quantity</label>
                        <input type="number" id="quantity" class="form-control" placeholder="Qty" required>
                    </div>
                    <div class="col-md-1">
                        <label class="form-label">Price (₹)</label>
                        <input type="number" id="price" class="form-control" placeholder="Price" step="0.01">
                    </div>
                    <div class="col-md-1 d-flex align-items-end">
                        <button type="submit" class="btn btn-primary w-100" id="submitButton">Add</button>
                        <button type="button" class="btn btn-secondary w-100 d-none" id="cancelEditButton">Cancel</button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
            Product List
            <div>
                <button class="btn btn-warning me-2" onclick="checkExpiry()">Check Expiry</button>
                <select id="categoryFilter" class="form-select w-auto d-inline-block">
                    <option value="">All Categories</option>
                    <option value="Uncategorized">Uncategorized</option>
                    <option value="Dairy">Dairy</option>
                    <option value="Produce">Produce</option>
                    <option value="Bakery">Bakery</option>
                    <option value="Meat">Meat</option>
                </select>
            </div>
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-striped table-hover mb-0">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Category</th>
                            <th>Manufacturing Date</th>
                            <th>Expiry Date</th>
                            <th>Quantity</th>
                            <th>Price (₹)</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="productTable"></tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
    // Set default dates
    document.addEventListener('DOMContentLoaded', () => {
        const today = new Date();
        const manufacturingDateInput = document.getElementById('manufacturingDate');
        const expiryDateInput = document.getElementById('expiryDate');

        // Set manufacturing date to today
        manufacturingDateInput.valueAsDate = today;

        // Set expiry date to 30 days from today
        const expiryDate = new Date(today);
        expiryDate.setDate(today.getDate() + 30);
        expiryDateInput.valueAsDate = expiryDate;
        
        // Load products
        fetchProducts();
    });

    // Product Form Submission Handler
    document.getElementById('productForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const productId = document.getElementById('productId').value;
        
        if (productId) {
            // Edit existing product
            editProduct(productId);
        } else {
            // Add new product
            addProduct();
        }
    });

    function addProduct() {
        // Collect form data
        const name = document.getElementById("productName").value;
        const category = document.getElementById("productCategory").value;
        const manufacturingDate = document.getElementById("manufacturingDate").value;
        const expiryDate = document.getElementById("expiryDate").value;
        const quantity = document.getElementById("quantity").value;
        const price = document.getElementById("price").value || 0;

        // Basic validation
        if (!name || !manufacturingDate || !expiryDate || !quantity) {
            alert("Please fill in all required fields.");
            return;
        }

        // Prepare data for submission
        const productData = {
            name, 
            category, 
            manufacturing_date: manufacturingDate, 
            expiry_date: expiryDate, 
            quantity, 
            price
        };

        // Send product data to server
        fetch('/add_product', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(productData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Reset form
                resetProductForm();
                
                // Refresh product list
                fetchProducts();
                
                // Show success message
                alert(data.message);
            } else {
                // Show error message
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while adding the product.');
        });
    }

    function editProduct(productId) {
        // Collect form data
        const name = document.getElementById("productName").value;
        const category = document.getElementById("productCategory").value;
        const manufacturingDate = document.getElementById("manufacturingDate").value;
        const expiryDate = document.getElementById("expiryDate").value;
        const quantity = document.getElementById("quantity").value;
        const price = document.getElementById("price").value || 0;

        // Basic validation
        if (!name || !manufacturingDate || !expiryDate || !quantity) {
            alert("Please fill in all required fields.");
            return;
        }

        // Prepare data for submission
        const productData = {
            name, 
            category, 
            manufacturing_date: manufacturingDate, 
            expiry_date: expiryDate, 
            quantity, 
            price
        };

        // Send product data to server
        fetch(`/edit_product/${productId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(productData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Reset form
                resetProductForm();
                
                // Refresh product list
                fetchProducts();
                
                // Show success message
                alert(data.message);
            } else {
                // Show error message
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while editing the product.');
        });
    }

    function prepareEditForm(product) {
        // Populate form with product details
        document.getElementById('productId').value = product.id;
        document.getElementById('productName').value = product.name;
        document.getElementById('productCategory').value = product.category;
        document.getElementById('manufacturingDate').value = product.manufacturing_date;
        document.getElementById('expiryDate').value = product.expiry_date;
        document.getElementById('quantity').value = product.quantity;
        document.getElementById('price').value = product.price;

        // Change form header and button
        document.getElementById('productFormHeader').textContent = 'Edit Product';
        document.getElementById('submitButton').textContent = 'Update';
        document.getElementById('cancelEditButton').classList.remove('d-none');
    }

    function resetProductForm() {
        // Reset form fields
        document.getElementById('productId').value = '';
        document.getElementById('productName').value = '';
        document.getElementById('quantity').value = '';
        document.getElementById('price').value = '';

        // Reset form header and button
        document.getElementById('productFormHeader').textContent = 'Add Product';
        document.getElementById('submitButton').textContent = 'Add';
        document.getElementById('cancelEditButton').classList.add('d-none');

        // Reset date inputs to defaults
        const today = new Date();
        const manufacturingDateInput = document.getElementById('manufacturingDate');
        const expiryDateInput = document.getElementById('expiryDate');

        manufacturingDateInput.valueAsDate = today;
        const expiryDate = new Date(today);
        expiryDate.setDate(today.getDate() + 30);
        expiryDateInput.valueAsDate = expiryDate;
    }

    // Cancel Edit Button
    document.getElementById('cancelEditButton').addEventListener('click', resetProductForm);

    function fetchProducts() {
        // Get selected category filter
        const categoryFilter = document.getElementById('categoryFilter').value;
        const url = categoryFilter ? `/get_products?category=${encodeURIComponent(categoryFilter)}` : '/get_products';

        // Fetch products from server with error handling
        fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(products => {
            // Debug
            console.log('Fetched products:', products);
            
            const tableBody = document.getElementById('productTable');
            
            // Clear existing table rows
            tableBody.innerHTML = '';

            // Display message if no products
            if (products.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="7" class="text-center">No products found</td></tr>';
                return;
            }

            // Populate table with products
            products.forEach(product => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${product.name}</td>
                    <td>${product.category}</td>
                    <td>${product.manufacturing_date}</td>
                    <td>${product.expiry_date}</td>
                    <td>${product.quantity}</td>
                    <td>₹${parseFloat(product.price).toFixed(2)}</td>
                    <td>
                        <button class="btn btn-sm btn-primary me-1 edit-btn">Edit</button>
                        <button class="btn btn-sm btn-danger delete-btn">Delete</button>
                    </td>
                `;
                
                // Add event listeners directly to the buttons
                row.querySelector('.edit-btn').addEventListener('click', () => {
                    prepareEditForm(product);
                });
                
                row.querySelector('.delete-btn').addEventListener('click', () => {
                    deleteProduct(product.id);
                });
                
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error fetching products:', error);
            alert('An error occurred while fetching products: ' + error.message);
        });
    }

    function deleteProduct(productId) {
        // Confirm before deleting
        if (!confirm('Are you sure you want to delete this product?')) {
            return;
        }
        
        fetch(`/delete_product/${productId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Refresh product list
                fetchProducts();
                alert(data.message);
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error deleting product:', error);
            alert('An error occurred while deleting the product.');
        });
    }

    function checkExpiry() {
        fetch('/check_expiry')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            let alertMessage = '';

            if (data.expiring_soon && data.expiring_soon.length > 0) {
                alertMessage += 'Expiring Soon:\\n';
                data.expiring_soon.forEach(product => {
                    alertMessage += `${product.name} - ${product.days_left} days left\\n`;
                });
            }

            if (data.low_stock && data.low_stock.length > 0) {
                alertMessage += '\\nLow Stock:\\n';
                data.low_stock.forEach(product => {
                    alertMessage += `${product.name} - ${product.quantity} remaining\\n`;
                });
            }

            if (alertMessage) {
                alert(alertMessage);
                
                // Voice alert (only if browser supports it)
                if ('speechSynthesis' in window) {
                    const utterance = new SpeechSynthesisUtterance(alertMessage.replace(/\\n/g, ' '));
                    window.speechSynthesis.speak(utterance);
                }
            } else {
                alert('No products expiring soon or low on stock.');
            }
        })
        .catch(error => {
            console.error('Error checking expiry:', error);
            alert('An error occurred while checking product expiry.');
        });
    }

    // Event listener for category filter
    document.getElementById('categoryFilter').addEventListener('change', fetchProducts);
</script>
</body>
</html>''')

    app.run(debug=True)
