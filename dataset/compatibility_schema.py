import sqlite3
import csv
import os
import re
from pathlib import Path

# Prefix-to-description mapping
prefix_description = {
    'DO': 'Door', 'KN': 'Knob', 'HI': 'Hinge', 'HA': 'Handle', 'PA': 'Panel', 'NA': 'Nail', 'LO': 'Lock',
    'WI': 'Window', 'FR': 'Frame', 'SE': 'Seal', 'SC': 'Screen', 'TR': 'Track',
    'SI': 'Sink', 'FA': 'Faucet', 'DR': 'Drain', 'PI': 'Pipe', 'MO': 'Mount', 'CA': 'Cabinet',
    'SH': 'Shower', 'HE': 'Head', 'HO': 'Holder', 'CU': 'Cupboard', 'VA': 'Vane', 'LI': 'Lid',
    'AD': 'Adhesive', 'MI': 'Mirror'
}

def create_database(db_path):
    """Create and initialize the SQLite database with required tables and indexes."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS items (
                code TEXT PRIMARY KEY,
                category TEXT,
                description TEXT
            );
            CREATE TABLE IF NOT EXISTS compatibilities (
                main_item TEXT NOT NULL,
                compatible_item TEXT NOT NULL,
                compat_description TEXT,
                PRIMARY KEY (main_item, compatible_item),
                FOREIGN KEY (main_item) REFERENCES items(code) ON DELETE CASCADE,
                FOREIGN KEY (compatible_item) REFERENCES items(code) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_compat_main ON compatibilities(main_item);
            CREATE INDEX IF NOT EXISTS idx_compat_compatible ON compatibilities(compatible_item);
        """)
        conn.commit()
        print("Database schema created successfully.")
        return conn, cursor
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise

def validate_code(code):
    """Validate item code format (2 letters followed by 3 digits)."""
    return bool(re.match(r'^[A-Z]{2}\d{3}$', code))

def process_csv(csv_path):
    """Read and validate compatibility data from CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    unique_codes = set()
    compatibility_data = []

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            expected_headers = ['Core Item', 'Related Item', 'Description']
            if not all(header in reader.fieldnames for header in expected_headers):
                raise ValueError("CSV file missing required headers: Core Item, Related Item, Description")

            for row in reader:
                main_item = row['Core Item'].strip()
                compatible_item = row['Related Item'].strip()
                description = row['Description'].strip()

                # Validate item codes
                if not (validate_code(main_item) and validate_code(compatible_item)):
                    print(f"Skipping invalid row: {main_item}, {compatible_item}")
                    continue

                unique_codes.add(main_item)
                unique_codes.add(compatible_item)
                compatibility_data.append((main_item, compatible_item, description))

        print(f"Processed {len(compatibility_data)} compatibility entries and {len(unique_codes)} unique item codes.")
        return unique_codes, compatibility_data
    except csv.Error as e:
        print(f"CSV processing error: {e}")
        raise

def populate_database(cursor, unique_codes, compatibility_data):
    """Populate the database with items and compatibilities."""
    # Insert items
    cursor.executemany("INSERT OR IGNORE INTO items (code) VALUES (?)", [(code,) for code in unique_codes])
    print(f"Inserted {cursor.rowcount} items into the items table.")

    # Insert compatibilities
    cursor.executemany(
        "INSERT OR IGNORE INTO compatibilities (main_item, compatible_item, compat_description) VALUES (?, ?, ?)",
        compatibility_data
    )
    print(f"Inserted {cursor.rowcount} compatibility entries.")

    # Insert symmetric compatibilities
    cursor.execute("""
        INSERT OR IGNORE INTO compatibilities (main_item, compatible_item, compat_description)
        SELECT compatible_item, main_item, compat_description
        FROM compatibilities
        WHERE (compatible_item, main_item) NOT IN (SELECT main_item, compatible_item FROM compatibilities)
    """)
    print(f"Inserted {cursor.rowcount} symmetric compatibility entries.")

    # Update item categories
    cursor.execute("UPDATE items SET category = SUBSTR(code, 1, 2)")
    print("Updated item categories based on code prefixes.")

    # Update item descriptions
    for prefix, desc in prefix_description.items():
        cursor.execute("UPDATE items SET description = ? WHERE category = ?", (desc, prefix))
    print("Updated item descriptions based on prefix mappings.")

def main():
    """Main function to process CSV and populate database."""
    db_path = "compatability.db"
    csv_path = Path("data/compatibility.csv")

    try:
        # Create database and tables
        conn, cursor = create_database(db_path)

        # Process CSV file
        unique_codes, compatibility_data = process_csv(csv_path)

        # Populate database
        populate_database(cursor, unique_codes, compatibility_data)

        # Commit changes and close connection
        conn.commit()
        print("Database update completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()