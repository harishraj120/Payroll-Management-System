"""Typed domain objects used throughout the payroll system."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Employee:
    employee_code: str
    full_name: str
    designation: str
    joining_date: date
    basic_salary: Decimal
    hra_percent: Decimal = Decimal("20")
    da_percent: Decimal = Decimal("10")
    tax_percent: Decimal = Decimal("5")
    email: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    active: bool = True
    id: Optional[int] = None


@dataclass(frozen=True)
class SalaryBreakdown:
    basic: Decimal
    hra: Decimal
    da: Decimal
    gross: Decimal
    tax: Decimal
    other_deductions: Decimal
    net: Decimal


@dataclass(frozen=True)
class PayrollSummary:
    run_id: int
    month: date
    employee_count: int
    total_gross: Decimal
    total_tax: Decimal
    total_net: Decimal
