"""
setup_database.py
Creates the clinic.db SQLite database with schema and realistic dummy data.
Run this once to bootstrap the database for the NL2SQL chatbot.
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinic.db")

NUM_PATIENTS = 200
NUM_DOCTORS = 15
NUM_APPOINTMENTS = 500
NUM_TREATMENTS = 350
NUM_INVOICES = 300

SPECIALIZATIONS = ["Dermatology", "Cardiology", "Orthopedics", "General", "Pediatrics"]
DEPARTMENTS = {
    "Dermatology": "Skin & Aesthetics",
    "Cardiology": "Heart & Vascular",
    "Orthopedics": "Bone & Joint",
    "General": "General Medicine",
    "Pediatrics": "Child Health",
}
APPOINTMENT_STATUSES = ["Scheduled", "Completed", "Cancelled", "No-Show"]
INVOICE_STATUSES = ["Paid", "Pending", "Overdue"]
GENDERS = ["M", "F"]

CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
]

FIRST_NAMES_MALE = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh",
    "Ayaan", "Krishna", "Ishaan", "Rohan", "Rahul", "Amit", "Vikram",
    "Suresh", "Rajesh", "Karan", "Nikhil", "Deepak", "Manoj",
    "Pranav", "Yash", "Siddharth", "Harsh", "Gaurav", "Ankit",
    "Ravi", "Sandeep", "Abhishek", "Varun",
]

FIRST_NAMES_FEMALE = [
    "Ananya", "Diya", "Myra", "Sara", "Aadhya", "Isha", "Kavya",
    "Riya", "Priya", "Neha", "Pooja", "Sneha", "Anjali", "Megha",
    "Swati", "Shruti", "Divya", "Nisha", "Tanvi", "Sakshi",
    "Aditi", "Mansi", "Simran", "Komal", "Pallavi", "Rashmi",
    "Sonal", "Bhavna", "Jyoti", "Meera",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Joshi",
    "Reddy", "Nair", "Mehta", "Shah", "Rao", "Das", "Mukherjee",
    "Iyer", "Chopra", "Malhotra", "Bhat", "Pillai", "Desai",
    "Kapoor", "Agarwal", "Chauhan", "Pandey", "Mishra", "Sinha",
    "Banerjee", "Kulkarni", "Thakur", "Saxena",
]

DOCTOR_FIRST_NAMES = [
    "Anand", "Meena", "Rajiv", "Sunita", "Prakash",
    "Kavita", "Sunil", "Nandini", "Ashok", "Lakshmi",
    "Ramesh", "Geeta", "Vijay", "Aarti", "Mohan",
]

TREATMENT_NAMES = {
    "Dermatology": [
        "Skin Biopsy", "Laser Treatment", "Chemical Peel",
        "Acne Treatment", "Mole Removal", "Botox Injection",
    ],
    "Cardiology": [
        "ECG", "Echocardiogram", "Stress Test",
        "Angiography", "Cardiac Catheterization", "Holter Monitoring",
    ],
    "Orthopedics": [
        "X-Ray", "MRI Scan", "Physiotherapy Session",
        "Joint Injection", "Fracture Cast", "Arthroscopy",
    ],
    "General": [
        "Blood Test", "General Checkup", "Vaccination",
        "Wound Dressing", "IV Drip", "Health Screening",
    ],
    "Pediatrics": [
        "Growth Assessment", "Immunization", "Ear Examination",
        "Nebulization", "Pediatric Consultation", "Developmental Screening",
    ],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
random.seed(42)  # reproducible data

def random_date(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between start and end."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def random_phone() -> str:
    return f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}"


def maybe_null(value, null_probability: float = 0.15):
    """Return None with the given probability, else return value."""
    return None if random.random() < null_probability else value


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------
def create_schema(cur: sqlite3.Cursor):
    cur.executescript("""
        DROP TABLE IF EXISTS invoices;
        DROP TABLE IF EXISTS treatments;
        DROP TABLE IF EXISTS appointments;
        DROP TABLE IF EXISTS doctors;
        DROP TABLE IF EXISTS patients;

        CREATE TABLE patients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name      TEXT NOT NULL,
            last_name       TEXT NOT NULL,
            email           TEXT,
            phone           TEXT,
            date_of_birth   DATE,
            gender          TEXT CHECK(gender IN ('M', 'F')),
            city            TEXT,
            registered_date DATE
        );

        CREATE TABLE doctors (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            specialization  TEXT,
            department      TEXT,
            phone           TEXT
        );

        CREATE TABLE appointments (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id        INTEGER NOT NULL,
            doctor_id         INTEGER NOT NULL,
            appointment_date  DATETIME,
            status            TEXT CHECK(status IN ('Scheduled','Completed','Cancelled','No-Show')),
            notes             TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id)  REFERENCES doctors(id)
        );

        CREATE TABLE treatments (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id    INTEGER NOT NULL,
            treatment_name    TEXT,
            cost              REAL,
            duration_minutes  INTEGER,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        );

        CREATE TABLE invoices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      INTEGER NOT NULL,
            invoice_date    DATE,
            total_amount    REAL,
            paid_amount     REAL,
            status          TEXT CHECK(status IN ('Paid','Pending','Overdue')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
    """)


# ---------------------------------------------------------------------------
# Data insertion
# ---------------------------------------------------------------------------
def insert_doctors(cur: sqlite3.Cursor) -> list[dict]:
    """Insert 15 doctors across 5 specializations (3 each)."""
    doctors = []
    for i, first in enumerate(DOCTOR_FIRST_NAMES[:NUM_DOCTORS]):
        last = random.choice(LAST_NAMES)
        spec = SPECIALIZATIONS[i % len(SPECIALIZATIONS)]
        dept = DEPARTMENTS[spec]
        phone = random_phone()
        cur.execute(
            "INSERT INTO doctors (name, specialization, department, phone) VALUES (?,?,?,?)",
            (f"Dr. {first} {last}", spec, dept, phone),
        )
        doctors.append({"id": cur.lastrowid, "specialization": spec})
    return doctors


def insert_patients(cur: sqlite3.Cursor) -> list[int]:
    """Insert 200 patients with realistic attributes."""
    patient_ids = []
    now = datetime.now()
    for _ in range(NUM_PATIENTS):
        gender = random.choice(GENDERS)
        first = random.choice(FIRST_NAMES_MALE if gender == "M" else FIRST_NAMES_FEMALE)
        last = random.choice(LAST_NAMES)
        email = maybe_null(f"{first.lower()}.{last.lower()}{random.randint(1,999)}@email.com", 0.10)
        phone = maybe_null(random_phone(), 0.08)
        dob = random_date(datetime(1950, 1, 1), datetime(2015, 12, 31)).strftime("%Y-%m-%d")
        city = random.choice(CITIES)
        reg_date = random_date(now - timedelta(days=730), now).strftime("%Y-%m-%d")

        cur.execute(
            """INSERT INTO patients
               (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
               VALUES (?,?,?,?,?,?,?,?)""",
            (first, last, email, phone, dob, gender, city, reg_date),
        )
        patient_ids.append(cur.lastrowid)
    return patient_ids


def insert_appointments(
    cur: sqlite3.Cursor,
    patient_ids: list[int],
    doctors: list[dict],
) -> list[dict]:
    """
    Insert 500 appointments over the past 12 months.
    Some patients are 'repeat visitors' with many appointments.
    Some doctors get more appointments than others.
    """
    now = datetime.now()
    twelve_months_ago = now - timedelta(days=365)

    # Create a weighted patient pool — ~20 % of patients are frequent visitors
    frequent_patients = random.sample(patient_ids, k=int(len(patient_ids) * 0.2))
    patient_pool = patient_ids + frequent_patients * 4  # frequent ones appear 5x total

    # Create a weighted doctor pool — some doctors busier
    busy_doctors = random.sample(doctors, k=5)
    doctor_pool = doctors + busy_doctors * 3

    appointments = []
    for _ in range(NUM_APPOINTMENTS):
        pid = random.choice(patient_pool)
        doc = random.choice(doctor_pool)
        appt_date = random_date(twelve_months_ago, now)
        # Future appointments are always Scheduled
        if appt_date > now:
            status = "Scheduled"
        else:
            status = random.choices(
                APPOINTMENT_STATUSES,
                weights=[5, 70, 15, 10],  # heavily Completed to ensure enough treatments
                k=1,
            )[0]
        notes = maybe_null(
            random.choice([
                "Follow-up required", "First visit", "Routine checkup",
                "Referred by GP", "Patient reported improvement",
                "Needs lab work", "Urgent consultation",
            ]),
            0.30,
        )
        cur.execute(
            """INSERT INTO appointments
               (patient_id, doctor_id, appointment_date, status, notes)
               VALUES (?,?,?,?,?)""",
            (pid, doc["id"], appt_date.strftime("%Y-%m-%d %H:%M:%S"), status, notes),
        )
        appointments.append({
            "id": cur.lastrowid,
            "doctor_spec": doc["specialization"],
            "status": status,
            "patient_id": pid,
            "date": appt_date,
        })
    return appointments


def insert_treatments(cur: sqlite3.Cursor, appointments: list[dict]):
    """Insert 350 treatments linked to Completed appointments."""
    completed = [a for a in appointments if a["status"] == "Completed"]
    if len(completed) < NUM_TREATMENTS:
        chosen = completed  # use all completed if not enough
    else:
        chosen = random.sample(completed, NUM_TREATMENTS)

    for appt in chosen:
        spec = appt["doctor_spec"]
        treatment = random.choice(TREATMENT_NAMES.get(spec, TREATMENT_NAMES["General"]))
        cost = round(random.uniform(50, 5000), 2)
        duration = random.choice([10, 15, 20, 30, 45, 60, 90, 120])
        cur.execute(
            """INSERT INTO treatments
               (appointment_id, treatment_name, cost, duration_minutes)
               VALUES (?,?,?,?)""",
            (appt["id"], treatment, cost, duration),
        )


def insert_invoices(cur: sqlite3.Cursor, appointments: list[dict]):
    """Insert 300 invoices with a mix of statuses."""
    # Pick unique patients who have completed appointments for invoices
    completed = [a for a in appointments if a["status"] == "Completed"]
    random.shuffle(completed)

    created = 0
    for appt in completed:
        if created >= NUM_INVOICES:
            break
        total = round(random.uniform(100, 8000), 2)
        status = random.choices(
            INVOICE_STATUSES,
            weights=[50, 30, 20],
            k=1,
        )[0]
        if status == "Paid":
            paid = total
        elif status == "Pending":
            paid = round(random.uniform(0, total * 0.5), 2)
        else:  # Overdue
            paid = round(random.uniform(0, total * 0.3), 2)

        invoice_date = appt["date"] + timedelta(days=random.randint(0, 7))
        cur.execute(
            """INSERT INTO invoices
               (patient_id, invoice_date, total_amount, paid_amount, status)
               VALUES (?,?,?,?,?)""",
            (appt["patient_id"], invoice_date.strftime("%Y-%m-%d"), total, paid, status),
        )
        created += 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Remove old DB if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    print("Creating schema …")
    create_schema(cur)

    print("Inserting doctors …")
    doctors = insert_doctors(cur)

    print("Inserting patients …")
    patient_ids = insert_patients(cur)

    print("Inserting appointments …")
    appointments = insert_appointments(cur, patient_ids, doctors)

    print("Inserting treatments …")
    insert_treatments(cur, appointments)

    print("Inserting invoices …")
    insert_invoices(cur, appointments)

    conn.commit()

    # ---- Summary ----
    counts = {}
    for table in ["patients", "doctors", "appointments", "treatments", "invoices"]:
        counts[table] = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    conn.close()

    print("\n[OK] Database created successfully!")
    print(f"   File: {DB_PATH}\n")
    print(f"   Created {counts['patients']} patients, "
          f"{counts['doctors']} doctors, "
          f"{counts['appointments']} appointments, "
          f"{counts['treatments']} treatments, "
          f"{counts['invoices']} invoices.")


if __name__ == "__main__":
    main()
