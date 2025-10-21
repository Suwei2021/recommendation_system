from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

#get DB connection
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/invoices', methods=['POST'])
def add_invoice():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    customer = data.get('customer')
    invoice = data.get('invoice')
    items = data.get('items')

    #validate all parts exist
    if not all([customer, invoice, items]):
        return jsonify({"error": "Missing customer, invoice, or items"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert or ignore customer
        cursor.execute("""
            INSERT OR IGNORE INTO Customers (customer_id, customer_contact_info, billing_address)
            VALUES (?, ?, ?)
        """, (customer['customer_id'], customer['customer_contact_info'], customer['billing_address']))

        # Insert invoice
        cursor.execute("""
            INSERT INTO Invoices (invoice_id, date, customer_id, salesperson)
            VALUES (?, ?, ?, ?)
        """, (invoice['invoice_id'], invoice['date'], customer['customer_id'], invoice['salesperson']))

        # Insert each item
        for item in items:
            # Ensure item exists in Items table
            cursor.execute("""
                INSERT OR IGNORE INTO Items (part_number, description)
                VALUES (?, ?)
            """, (item['part_number'], item['item_description']))

            # Insert into InvoiceItems
            cursor.execute("""
                INSERT INTO InvoiceItems (invoice_id, part_number, item_description, variant_group, quantity, unit_price, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice['invoice_id'],
                item['part_number'],
                item['item_description'],
                item['variant_group'],
                item['quantity'],
                item['unit_price'],
                item['total_amount']
            ))

        conn.commit()
        return jsonify({"message": "Invoice inserted successfully"}), 201

    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)