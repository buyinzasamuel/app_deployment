import os
from flask import Flask, request, jsonify
from psycopg2 import pool

app = Flask(__name__)

# ------------------- DATABASE SETUP -------------------
# Railway automatically provides a DATABASE_URL environment variable.
# The fallback below is only for local testing – it will never be used on Railway.
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    # Local fallback (change to match your local PostgreSQL setup)
    DATABASE_URL = "postgresql://user:password@localhost:5432/students"

# Create a connection pool (min 1, max 20 connections)
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

# Run table creation
init_db()

# ------------------- ROUTES -------------------
@app.route('/')
def hello():
    return 'My cloud deployment is successful!'

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
# This block is only used when running `python app.py` locally.
# On Railway, Gunicorn (from the Procfile) will run the app.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)