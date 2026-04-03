import os
from flask import Flask, request, jsonify
from psycopg2 import pool

app = Flask(__name__)

# ------------------- DATABASE SETUP -------------------
# Create a connection pool using the DATABASE_URL provided by Railway
# If running locally, set DATABASE_URL environment variable or use a fallback
DATABASE_URL = os.environ.get('postgresql://user:password@localhost:5432/items')
if not DATABASE_URL:
    # Fallback for local testing (create a local PostgreSQL database first)
    DATABASE_URL = "postgresql://user:password@localhost:5432/items"

db_pool = pool.SimpleConnectionPool(1, 20, DATABASE_URL)

# Ensure the 'items' table exists
def init_db():
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT
                )
            """)
        conn.commit()
    finally:
        db_pool.putconn(conn)

init_db()

# ------------------- ROUTES -------------------
# 1. Root route – simple success message
@app.route('/')
def hello():
    return 'My cloud deployment is successful!'

# 2. CREATE: Add a new item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id",
                (name, description)
            )
            item_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"id": item_id, "name": name, "description": description}), 201
    finally:
        db_pool.putconn(conn)

# 3. READ: Get all items
@app.route('/items', methods=['GET'])
def get_items():
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM items")
            items = [{"id": row[0], "name": row[1], "description": row[2]} for row in cur.fetchall()]
        return jsonify(items)
    finally:
        db_pool.putconn(conn)

# 4. UPDATE: Update an existing item by ID
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE items SET name = %s, description = %s WHERE id = %s",
                (name, description, item_id)
            )
        conn.commit()
        return jsonify({"id": item_id, "name": name, "description": description})
    finally:
        db_pool.putconn(conn)

# 5. DELETE: Remove an item by ID
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM items WHERE id = %s", (item_id,))
        conn.commit()
        return jsonify({"message": "Item deleted"}), 200
    finally:
        db_pool.putconn(conn)

# ------------------- PRODUCTION SERVER -------------------
# This section is used only when running locally with `python app.py`.
# On Railway, Gunicorn (defined in Procfile) will run the app.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False for production
    