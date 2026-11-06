"""Pure salary calculations and strict input validation.

Example payroll policy for a student demonstration. This is not an
implementation of Indian statutory payroll, income-tax slabs or PF/ESI.
"""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from .models import SalaryBreakdown

MONEY = Decimal("0.01")
CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{2,30}$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def to_decimal(value, label="Amount") -> Decimal:
    """Convert user input to a finite Decimal, rejecting invalid numbers."""
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{label} must be a valid number") from exc
    if not result.is_finite():
        raise ValueError(f"{label} must be finite")
    return result


def money(value) -> Decimal:
    return to_decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def percentage(value, label="Percentage") -> Decimal:
    result = to_decimal(value, label)
    if not Decimal("0") <= result <= Decimal("100"):
        raise ValueError(f"{label} must be between 0 and 100")
    return result


def nonnegative(value, label="Amount") -> Decimal:
    result = to_decimal(value, label)
    if result < 0:
        raise ValueError(f"{label} cannot be negative")
    return result


def validate_employee(data: dict) -> dict:
    """Return a cleaned dictionary suitable for parameterized SQL."""
    code = str(data.get("employee_code", "")).strip().upper()
    name = str(data.get("full_name", "")).strip()
    designation = str(data.get("designation", "")).strip()
    email = str(data.get("email") or "").strip() or None
    phone = str(data.get("phone") or "").strip() or None
    joining_date = data.get("joining_date")
    if not CODE_PATTERN.fullmatch(code):
        raise ValueError("Employee code must be 2-30 letters, digits, _ or -")
    if not 2 <= len(name) <= 150:
        raise ValueError("Employee name must be 2-150 characters")
    if not 2 <= len(designation) <= 100:
        raise ValueError("Designation must be 2-100 characters")
    if email and (len(email) > 190 or not EMAIL_PATTERN.fullmatch(email)):
        raise ValueError("Enter a valid email address")
    if phone and (len(phone) > 30 or not re.fullmatch(r"[+0-9 ()-]+", phone)):
        raise ValueError("Enter a valid phone number")
    if isinstance(joining_date, str):
        try:
            joining_date = date.fromisoformat(joining_date)
        except ValueError as exc:
            raise ValueError("Joining date must be YYYY-MM-DD") from exc
    if not isinstance(joining_date, date):
        raise ValueError("Joining date must be YYYY-MM-DD")
    basic = money(nonnegative(data.get("basic_salary"), "Basic salary"))
    hra = percentage(data.get("hra_percent", 20), "HRA percentage")
    da = percentage(data.get("da_percent", 10), "DA percentage")
    tax = percentage(data.get("tax_percent", 5), "Tax percentage")
    department_id = data.get("department_id")
    if department_id in ("", None):
        department_id = None
    else:
        try:
            department_id = int(department_id)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid department") from exc
        if department_id <= 0:
            raise ValueError("Invalid department")
    return {
        "employee_code": code,
        "full_name": name,
        "email": email,
        "phone": phone,
        "department_id": department_id,
        "designation": designation,
        "joining_date": joining_date,
        "basic_salary": basic,
        "hra_percent": hra,
        "da_percent": da,
        "tax_percent": tax,
        "active": bool(data.get("active", True)),
    }


def calculate_salary(basic, hra_percent=20, da_percent=10,
                     tax_percent=5, other_deductions=0) -> SalaryBreakdown:
    """Calculate gross and net salary with deterministic rounding.

    HRA and DA are percentages of basic pay; demonstration tax is a
    percentage of gross pay. Actual statutory deductions differ.
    """
    basic = money(nonnegative(basic, "Basic salary"))
    hra_rate = percentage(hra_percent, "HRA percentage")
    da_rate = percentage(da_percent, "DA percentage")
    tax_rate = percentage(tax_percent, "Tax percentage")
    other = money(nonnegative(other_deductions, "Other deductions"))
    hra = money(basic * hra_rate / 100)
    da = money(basic * da_rate / 100)
    gross = money(basic + hra + da)
    tax = money(gross * tax_rate / 100)
    net = money(gross - tax - other)
    if net < 0:
        raise ValueError("Deductions cannot exceed gross salary")
    return SalaryBreakdown(basic, hra, da, gross, tax, other, net)


def parse_month(value: str) -> date:
    """Parse YYYY-MM and return the first day of the month."""
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value.strip()):
        raise ValueError("Payroll month must be YYYY-MM")
    year, month = map(int, value.split("-"))
    return date(year, month, 1)
