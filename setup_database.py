"""One-time database initializer: python setup_database.py."""
from payroll.database import Database, DatabaseError


def main():
    print("Initializing Payroll Management System database...")
    try:
        db = Database()
        db.initialize()
        print("Database schema is ready.")
        print("MySQL version:", db.ping())
    except DatabaseError as exc:
        print("Setup failed:", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
