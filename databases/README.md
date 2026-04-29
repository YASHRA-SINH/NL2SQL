# Database Setup Scripts

This folder keeps database-specific bootstrap and seed scripts organized.

- `clinic/setup_clinic_database.py` creates clinic schema and realistic seed data.
- `clinic/seed_clinic_memory.py` seeds clinic-specific NL2SQL memory examples.
- `clinic/create_clinic_database.py` creates the clinic PostgreSQL database if it does not exist.
- `sales/setup_sales_database.py` creates a realistic sales database with seven related tables.
- `sales/seed_sales_memory.py` seeds sales-specific NL2SQL examples into `memory_store/sales.json`.
