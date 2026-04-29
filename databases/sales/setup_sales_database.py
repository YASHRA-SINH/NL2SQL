"""
Create and populate a realistic PostgreSQL sales database.

Run from the project root:
    python databases/sales/setup_sales_database.py

Environment:
    SALES_PG_DATABASE defaults to sales.
    SALES_PG_HOST/PORT/USER/PASSWORD override PG_HOST/PORT/USER/PASSWORD.
"""

import os
import random
from datetime import date, datetime, timedelta

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import execute_values

load_dotenv()


def env(key: str, default: str | None = None) -> str | None:
    if key == "DATABASE":
        return os.getenv("SALES_PG_DATABASE", default)
    return os.getenv(f"SALES_PG_{key}", os.getenv(f"PG_{key}", default))


PG_HOST = env("HOST", "localhost")
PG_PORT = env("PORT", "5432")
PG_USER = env("USER", "postgres")
PG_PASSWORD = env("PASSWORD")
PG_DATABASE = env("DATABASE", "sales")

NUM_CUSTOMERS = 650
NUM_REPS = 14
NUM_PRODUCTS = 130
NUM_ORDERS = 2400

random.seed(91)

FIRST_NAMES = [
    "Aarav", "Isha", "Kabir", "Meera", "Rohan", "Ananya", "Vikram", "Priya",
    "Neha", "Arjun", "Kavya", "Rahul", "Diya", "Sahil", "Nisha", "Aditi",
]
LAST_NAMES = [
    "Sharma", "Patel", "Gupta", "Rao", "Nair", "Mehta", "Singh", "Iyer",
    "Das", "Kapoor", "Joshi", "Reddy", "Shah", "Verma", "Bose", "Khan",
]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad"]
REGIONS = ["West", "North", "South", "South", "South", "West", "East", "West"]
CHANNELS = ["website", "marketplace", "retail", "partner", "inside_sales"]
ORDER_STATUSES = ["completed", "completed", "completed", "completed", "returned", "cancelled", "processing"]
PAYMENT_STATUSES = ["paid", "paid", "paid", "paid", "paid", "failed", "refunded", "pending"]
CATEGORIES = {
    "Electronics": ["Wireless Earbuds", "Bluetooth Speaker", "Smart Watch", "USB-C Hub", "Power Bank"],
    "Home": ["Air Purifier", "Desk Lamp", "Memory Foam Pillow", "Cookware Set", "Storage Rack"],
    "Office": ["Ergonomic Chair", "Standing Desk", "Notebook Pack", "Monitor Arm", "Keyboard"],
    "Fashion": ["Denim Jacket", "Running Shoes", "Cotton Shirt", "Backpack", "Sunglasses"],
    "Fitness": ["Yoga Mat", "Resistance Bands", "Dumbbell Set", "Water Bottle", "Fitness Tracker"],
    "Beauty": ["Face Serum", "Sunscreen", "Hair Dryer", "Moisturizer", "Grooming Kit"],
}


def connect(dbname: str):
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=dbname,
    )


def create_database_if_needed():
    conn = connect("postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (PG_DATABASE,))
            if cur.fetchone():
                print(f"Database {PG_DATABASE} already exists.")
            else:
                print(f"Creating database {PG_DATABASE}...")
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(PG_DATABASE)))
    finally:
        conn.close()


def create_schema(cur):
    cur.execute(
        """
        DROP TABLE IF EXISTS invoices;
        DROP TABLE IF EXISTS treatments;
        DROP TABLE IF EXISTS appointments;
        DROP TABLE IF EXISTS doctors;
        DROP TABLE IF EXISTS patients;

        DROP TABLE IF EXISTS support_tickets;
        DROP TABLE IF EXISTS payments;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS sales_reps;

        CREATE TABLE customers (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(120) NOT NULL,
            last_name VARCHAR(120) NOT NULL,
            email VARCHAR(255) UNIQUE,
            city VARCHAR(120),
            region VARCHAR(80),
            segment VARCHAR(80),
            signup_date DATE,
            lifetime_value DOUBLE PRECISION DEFAULT 0
        );

        CREATE TABLE sales_reps (
            id SERIAL PRIMARY KEY,
            name VARCHAR(180) NOT NULL,
            region VARCHAR(80),
            quota DOUBLE PRECISION,
            hire_date DATE
        );

        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            sku VARCHAR(40) UNIQUE NOT NULL,
            name VARCHAR(180) NOT NULL,
            category VARCHAR(100),
            unit_price DOUBLE PRECISION,
            unit_cost DOUBLE PRECISION,
            active BOOLEAN DEFAULT TRUE
        );

        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            sales_rep_id INTEGER REFERENCES sales_reps(id),
            order_date TIMESTAMP,
            status VARCHAR(40),
            channel VARCHAR(60),
            discount_pct DOUBLE PRECISION DEFAULT 0,
            shipping_city VARCHAR(120),
            shipping_region VARCHAR(80)
        );

        CREATE TABLE order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price DOUBLE PRECISION NOT NULL,
            discount_pct DOUBLE PRECISION DEFAULT 0
        );

        CREATE TABLE payments (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            payment_date TIMESTAMP,
            amount DOUBLE PRECISION,
            method VARCHAR(60),
            status VARCHAR(40)
        );

        CREATE TABLE support_tickets (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            order_id INTEGER REFERENCES orders(id),
            created_at TIMESTAMP,
            category VARCHAR(100),
            priority VARCHAR(30),
            status VARCHAR(40),
            satisfaction_score INTEGER
        );
        """
    )


def weighted_choice(items: list[str], weights: list[int]) -> str:
    return random.choices(items, weights=weights, k=1)[0]


def random_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def insert_sales_reps(cur) -> list[int]:
    reps = []
    for i in range(NUM_REPS):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        region = random.choice(["West", "North", "South", "East"])
        quota = round(random.uniform(900_000, 2_400_000), 2)
        hire_date = random_date(date(2017, 1, 1), date(2025, 12, 31))
        reps.append((name, region, quota, hire_date))
    execute_values(cur, "INSERT INTO sales_reps (name, region, quota, hire_date) VALUES %s", reps)
    cur.execute("SELECT id FROM sales_reps")
    return [row[0] for row in cur.fetchall()]


def insert_customers(cur) -> list[int]:
    rows = []
    for i in range(NUM_CUSTOMERS):
        city_index = random.randrange(len(CITIES))
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        segment = weighted_choice(["consumer", "small_business", "enterprise"], [70, 24, 6])
        signup = random_date(date(2021, 1, 1), date.today())
        rows.append(
            (
                first,
                last,
                f"{first.lower()}.{last.lower()}{i + 1}@example.com",
                CITIES[city_index],
                REGIONS[city_index],
                segment,
                signup,
            )
        )
    execute_values(
        cur,
        """
        INSERT INTO customers (first_name, last_name, email, city, region, segment, signup_date)
        VALUES %s
        """,
        rows,
    )
    cur.execute("SELECT id FROM customers")
    return [row[0] for row in cur.fetchall()]


def insert_products(cur) -> list[dict]:
    rows = []
    for i in range(NUM_PRODUCTS):
        category = random.choice(list(CATEGORIES.keys()))
        base_name = random.choice(CATEGORIES[category])
        price = round(random.lognormvariate(4.6, 0.55), 2)
        cost = round(price * random.uniform(0.42, 0.72), 2)
        rows.append((f"SKU-{i + 1:04d}", f"{base_name} {random.choice(['Lite', 'Pro', 'Plus', 'Max'])}", category, price, cost, random.random() > 0.04))
    execute_values(
        cur,
        "INSERT INTO products (sku, name, category, unit_price, unit_cost, active) VALUES %s",
        rows,
    )
    cur.execute("SELECT id, unit_price FROM products")
    return [{"id": row[0], "unit_price": float(row[1])} for row in cur.fetchall()]


def insert_orders(cur, customer_ids: list[int], rep_ids: list[int], products: list[dict]):
    customer_pool = customer_ids + random.sample(customer_ids, k=120) * 5 + random.sample(customer_ids, k=30) * 12
    order_rows = []
    start = datetime.now() - timedelta(days=730)
    for _ in range(NUM_ORDERS):
        customer_id = random.choice(customer_pool)
        order_date = start + timedelta(days=random.randint(0, 730), hours=random.randint(0, 23))
        status = weighted_choice(ORDER_STATUSES, [68, 8, 6, 4, 5, 4, 5])
        channel = weighted_choice(CHANNELS, [46, 24, 16, 8, 6])
        discount = round(random.choice([0, 0, 0, 5, 10, 15, 20]) / 100, 2)
        city_index = random.randrange(len(CITIES))
        rep_id = random.choice(rep_ids) if channel in {"partner", "inside_sales"} or random.random() < 0.35 else None
        order_rows.append((customer_id, rep_id, order_date, status, channel, discount, CITIES[city_index], REGIONS[city_index]))

    execute_values(
        cur,
        """
        INSERT INTO orders
          (customer_id, sales_rep_id, order_date, status, channel, discount_pct, shipping_city, shipping_region)
        VALUES %s RETURNING id, customer_id, status, order_date, discount_pct
        """,
        order_rows,
    )
    orders = cur.fetchall()

    item_rows = []
    payment_rows = []
    for order_id, customer_id, status, order_date, order_discount in orders:
        item_count = weighted_choice([1, 2, 3, 4, 5], [52, 27, 12, 6, 3])
        total = 0
        for product in random.sample(products, k=int(item_count)):
            quantity = weighted_choice([1, 2, 3, 4, 5, 6], [58, 22, 10, 5, 3, 2])
            line_discount = max(float(order_discount), random.choice([0, 0, 0, 0.05, 0.10]))
            item_rows.append((order_id, product["id"], quantity, product["unit_price"], line_discount))
            total += quantity * product["unit_price"] * (1 - line_discount)

        payment_status = "refunded" if status == "returned" else weighted_choice(PAYMENT_STATUSES, [74, 6, 4, 3, 2, 5, 3, 3])
        paid_amount = 0 if status == "cancelled" else round(total, 2)
        payment_rows.append((order_id, order_date + timedelta(hours=random.randint(0, 72)), paid_amount, random.choice(["card", "upi", "bank_transfer", "wallet", "cash"]), payment_status))

    execute_values(
        cur,
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_pct) VALUES %s",
        item_rows,
    )
    execute_values(
        cur,
        "INSERT INTO payments (order_id, payment_date, amount, method, status) VALUES %s",
        payment_rows,
    )


def insert_support_tickets(cur):
    cur.execute("SELECT id, customer_id, order_date FROM orders WHERE status IN ('completed', 'returned') ORDER BY random() LIMIT 420")
    rows = []
    for order_id, customer_id, order_date in cur.fetchall():
        created_at = order_date + timedelta(days=random.randint(1, 30))
        status = weighted_choice(["open", "pending", "resolved", "closed"], [8, 12, 36, 44])
        rows.append(
            (
                customer_id,
                order_id,
                created_at,
                random.choice(["delivery", "returns", "billing", "product_quality", "warranty"]),
                weighted_choice(["low", "medium", "high", "urgent"], [50, 32, 14, 4]),
                status,
                random.choice([None, 1, 2, 3, 4, 5]) if status in {"resolved", "closed"} else None,
            )
        )
    execute_values(
        cur,
        """
        INSERT INTO support_tickets
          (customer_id, order_id, created_at, category, priority, status, satisfaction_score)
        VALUES %s
        """,
        rows,
    )


def refresh_customer_lifetime_value(cur):
    cur.execute(
        """
        UPDATE customers c
        SET lifetime_value = COALESCE(revenue.total_revenue, 0)
        FROM (
            SELECT o.customer_id, SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS total_revenue
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.status IN ('completed', 'processing')
            GROUP BY o.customer_id
        ) revenue
        WHERE revenue.customer_id = c.id
        """
    )


def main():
    create_database_if_needed()
    conn = connect(PG_DATABASE)
    try:
        with conn.cursor() as cur:
            print("Creating sales schema...")
            create_schema(cur)
            print("Inserting sales reps...")
            rep_ids = insert_sales_reps(cur)
            print("Inserting customers...")
            customer_ids = insert_customers(cur)
            print("Inserting products...")
            products = insert_products(cur)
            print("Inserting orders, order items, and payments...")
            insert_orders(cur, customer_ids, rep_ids, products)
            print("Inserting support tickets...")
            insert_support_tickets(cur)
            refresh_customer_lifetime_value(cur)
        conn.commit()

        with conn.cursor() as cur:
            counts = {}
            for table in ["customers", "sales_reps", "products", "orders", "order_items", "payments", "support_tickets"]:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
                counts[table] = cur.fetchone()[0]
        print("\n[OK] Sales database created successfully!")
        print(f"   Database: {PG_DATABASE} on {PG_HOST}:{PG_PORT}")
        for table, count in counts.items():
            print(f"   {table}: {count}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
