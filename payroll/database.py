"""MySQL access layer: all user values use parameterized queries."""
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
import mysql.connector
from mysql.connector import Error, errorcode
from .config import settings


class DatabaseError(RuntimeError):
    """Raised when a database operation cannot be completed."""


class Database:
    def __init__(self, configuration=settings):
        self.config = configuration

    def connect(self, include_database=True):
        options = {
            "host": self.config.host,
            "port": self.config.port,
            "user": self.config.user,
            "password": self.config.password,
            "connection_timeout": 8,
            "autocommit": False,
        }
        if include_database:
            options["database"] = self.config.database
        try:
            return mysql.connector.connect(**options)
        except Error as exc:
            raise DatabaseError(f"Cannot connect to MySQL: {exc}") from exc

    @contextmanager
    def session(self, dictionary=True):
        conn = self.connect()
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield conn, cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def initialize(self, schema_path=None):
        """Initialize the database from the bundled SQL file.

        This intentionally runs trusted local schema SQL only; no arbitrary
        SQL is accepted from the user interface.
        """
        schema_path = Path(schema_path or
                           Path(__file__).resolve().parent.parent / "sql" / "schema.sql")
        schema = schema_path.read_text(encoding="utf-8")
        connection = self.connect(include_database=False)
        cursor = connection.cursor()
        try:
            for statement in schema.split(";"):
                if statement.strip():
                    cursor.execute(statement)
            connection.commit()
        except Error as exc:
            connection.rollback()
            raise DatabaseError(f"Database initialization failed: {exc}") from exc
        finally:
            cursor.close()
            connection.close()


    def admin_count(self):
        with self.session() as (_, cursor):
            cursor.execute("SELECT COUNT(*) AS count FROM app_users WHERE active=1")
            return cursor.fetchone()["count"]

    def create_admin(self, username, password_hash):
        username = username.strip()
        if not 3 <= len(username) <= 60:
            raise ValueError("Username must be 3-60 characters.")
        with self.session() as (_, cursor):
            cursor.execute(
                "INSERT INTO app_users(username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )

    def authenticate_admin(self, username):
        with self.session() as (_, cursor):
            cursor.execute(
                "SELECT id, username, password_hash FROM app_users "
                "WHERE username=%s AND active=1",
                (username.strip(),),
            )
            return cursor.fetchone()

    def ping(self):
        with self.session() as (_, cursor):
            cursor.execute("SELECT VERSION() AS version")
            return cursor.fetchone()["version"]

    def list_departments(self):
        with self.session() as (_, cursor):
            cursor.execute("SELECT id, name FROM departments ORDER BY name")
            return cursor.fetchall()

    def add_department(self, name):
        name = name.strip()
        if not 2 <= len(name) <= 100:
            raise ValueError("Department name must be 2-100 characters")
        with self.session() as (_, cursor):
            cursor.execute("INSERT INTO departments(name) VALUES (%s)", (name,))
            return cursor.lastrowid

    def list_employees(self, search="", include_inactive=True):
        sql = """SELECT e.*, d.name AS department_name
                 FROM employees e LEFT JOIN departments d ON e.department_id=d.id
                 WHERE 1=1"""
        params = []
        if not include_inactive:
            sql += " AND e.active=1"
        if search.strip():
            sql += " AND (e.employee_code LIKE %s OR e.full_name LIKE %s OR e.designation LIKE %s)"
            term = f"%{search.strip()}%"
            params.extend([term, term, term])
        sql += " ORDER BY e.full_name, e.id"
        with self.session() as (_, cursor):
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()

    def get_employee(self, employee_id):
        with self.session() as (_, cursor):
            cursor.execute("""SELECT e.*, d.name AS department_name FROM employees e
                              LEFT JOIN departments d ON e.department_id=d.id
                              WHERE e.id=%s""", (int(employee_id),))
            return cursor.fetchone()

    def create_employee(self, data):
        from .calculations import validate_employee
        clean = validate_employee(data)
        columns = list(clean)
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"INSERT INTO employees ({', '.join(columns)}) VALUES ({placeholders})"
        with self.session() as (_, cursor):
            cursor.execute(sql, tuple(clean.values()))
            return cursor.lastrowid

    def update_employee(self, employee_id, data):
        from .calculations import validate_employee
        clean = validate_employee(data)
        columns = list(clean)
        assignments = ", ".join(f"{key}=%s" for key in columns)
        with self.session() as (_, cursor):
            cursor.execute(f"UPDATE employees SET {assignments} WHERE id=%s",
                           (*clean.values(), int(employee_id)))
            if cursor.rowcount == 0:
                raise ValueError("Employee not found or no fields changed")

    def set_employee_active(self, employee_id, active):
        with self.session() as (_, cursor):
            cursor.execute("UPDATE employees SET active=%s WHERE id=%s",
                           (bool(active), int(employee_id)))
            if cursor.rowcount == 0:
                raise ValueError("Employee not found or already in selected state")

    def employee_count(self):
        with self.session() as (_, cursor):
            cursor.execute("SELECT COUNT(*) AS count FROM employees WHERE active=1")
            return cursor.fetchone()["count"]

    def list_payroll_runs(self):
        with self.session() as (_, cursor):
            cursor.execute("""SELECT r.id, r.payroll_month, r.generated_at,
                              COUNT(i.id) AS employee_count,
                              COALESCE(SUM(i.gross_salary),0) AS gross_total,
                              COALESCE(SUM(i.net_salary),0) AS net_total
                              FROM payroll_runs r
                              LEFT JOIN payroll_items i ON i.run_id=r.id
                              GROUP BY r.id, r.payroll_month, r.generated_at
                              ORDER BY r.payroll_month DESC""")
            return cursor.fetchall()

    def get_payroll_run(self, run_id):
        with self.session() as (_, cursor):
            cursor.execute("SELECT * FROM payroll_runs WHERE id=%s", (int(run_id),))
            return cursor.fetchone()

    def payroll_items(self, run_id):
        with self.session() as (_, cursor):
            cursor.execute("""SELECT * FROM payroll_items
                              WHERE run_id=%s ORDER BY employee_name, id""",
                           (int(run_id),))
            return cursor.fetchall()

    def payroll_item_for_employee(self, run_id, employee_id):
        with self.session() as (_, cursor):
            cursor.execute("""SELECT * FROM payroll_items
                              WHERE run_id=%s AND employee_id=%s""",
                           (int(run_id), int(employee_id)))
            return cursor.fetchone()

    def run_payroll(self, month, notes=""):
        """Create a consistent, immutable monthly snapshot in one transaction."""
        from .calculations import calculate_salary, parse_month
        period = parse_month(month) if isinstance(month, str) else month
        with self.session() as (_, cursor):
            cursor.execute("SELECT id FROM payroll_runs WHERE payroll_month=%s", (period,))
            if cursor.fetchone():
                raise ValueError("Payroll already exists for this month")
            cursor.execute("""SELECT e.*, d.name AS department_name
                              FROM employees e LEFT JOIN departments d ON d.id=e.department_id
                              WHERE e.active=1 AND e.joining_date <= LAST_DAY(%s)
                              ORDER BY e.id""", (period,))
            employees = cursor.fetchall()
            if not employees:
                raise ValueError("No eligible active employees for this month")
            cursor.execute("INSERT INTO payroll_runs(payroll_month,notes) VALUES (%s,%s)",
                           (period, notes[:250] or None))
            run_id = cursor.lastrowid
            for employee in employees:
                amounts = calculate_salary(
                    employee["basic_salary"], employee["hra_percent"],
                    employee["da_percent"], employee["tax_percent"])
                cursor.execute("""INSERT INTO payroll_items (
                    run_id, employee_id, employee_code, employee_name,
                    department_name, designation, basic_salary, hra_amount,
                    da_amount, gross_salary, tax_amount, other_deductions, net_salary
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (
                    run_id, employee["id"], employee["employee_code"],
                    employee["full_name"], employee["department_name"],
                    employee["designation"], amounts.basic, amounts.hra,
                    amounts.da, amounts.gross, amounts.tax,
                    amounts.other_deductions, amounts.net))
            return run_id

    def delete_payroll_run(self, run_id):
        with self.session() as (_, cursor):
            cursor.execute("DELETE FROM payroll_runs WHERE id=%s", (int(run_id),))
            if cursor.rowcount == 0:
                raise ValueError("Payroll run not found")
