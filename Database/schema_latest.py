import sqlite3

# Connect to the database (creates if not exists)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Drop existing tables if they exist (to avoid schema mismatch)
cursor.execute("DROP TABLE IF EXISTS InvoiceItems")
cursor.execute("DROP TABLE IF EXISTS Invoices")
cursor.execute("DROP TABLE IF EXISTS Customers")
cursor.execute("DROP TABLE IF EXISTS Items")
cursor.execute("DROP TABLE IF EXISTS Compatibility")

# 1? Create Customers table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Customers (
    customer_id TEXT PRIMARY KEY,
    customer_contact_info TEXT NOT NULL,
    billing_address TEXT NOT NULL
)
""")

#  Create Invoices table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Invoices (
    invoice_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    salesperson TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
)
""")

# Create Items table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Items (
    part_number TEXT PRIMARY KEY,
    description TEXT
)
""")

#  Create InvoiceItems table
cursor.execute("""
CREATE TABLE IF NOT EXISTS InvoiceItems (
    invoice_id TEXT NOT NULL,
    part_number TEXT NOT NULL,
    item_description TEXT NOT NULL,
    variant_group TEXT,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    total_amount REAL NOT NULL,
    PRIMARY KEY (invoice_id, part_number),
    FOREIGN KEY (invoice_id) REFERENCES Invoices(invoice_id),
    FOREIGN KEY (part_number) REFERENCES Items(part_number)
)
""")

#  Create Compatibility table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Compatibility (
    core_item TEXT NOT NULL,
    related_item TEXT NOT NULL,
    description TEXT,
    PRIMARY KEY (core_item, related_item),
    FOREIGN KEY (core_item) REFERENCES Items(part_number),
    FOREIGN KEY (related_item) REFERENCES Items(part_number)
)
""")

conn.commit()
print(" Database schema created successfully!")
