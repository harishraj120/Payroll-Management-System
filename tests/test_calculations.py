"""Run with python -m unittest discover -s tests -v."""
import unittest
from datetime import date
from decimal import Decimal
from payroll.calculations import (
    calculate_salary, parse_month, validate_employee, money, percentage,
)


class SalaryCalculationTests(unittest.TestCase):
    def test_basic_salary_calculation(self):
        result = calculate_salary(30000, 20, 10, 5)
        self.assertEqual(result.basic, Decimal("30000.00"))
        self.assertEqual(result.hra, Decimal("6000.00"))
        self.assertEqual(result.da, Decimal("3000.00"))
        self.assertEqual(result.gross, Decimal("39000.00"))
        self.assertEqual(result.tax, Decimal("1950.00"))
        self.assertEqual(result.net, Decimal("37050.00"))

    def test_zero_salary(self):
        result = calculate_salary(0, 0, 0, 0)
        self.assertEqual(result.net, Decimal("0.00"))

    def test_other_deductions(self):
        result = calculate_salary(10000, 0, 0, 0, 500)
        self.assertEqual(result.net, Decimal("9500.00"))

    def test_negative_salary_rejected(self):
        with self.assertRaises(ValueError):
            calculate_salary(-100)

    def test_negative_deductions_rejected(self):
        with self.assertRaises(ValueError):
            calculate_salary(1000, other_deductions=-1)

    def test_deductions_exceeding_gross_rejected(self):
        with self.assertRaises(ValueError):
            calculate_salary(100, 0, 0, 100, 1)

    def test_invalid_percentage(self):
        with self.assertRaises(ValueError):
            percentage(101)

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            money("NaN")

    def test_half_up_rounding(self):
        self.assertEqual(money("12.345"), Decimal("12.35"))

    def test_parse_month(self):
        self.assertEqual(parse_month("2026-11"), date(2026, 11, 1))

    def test_invalid_month(self):
        with self.assertRaises(ValueError):
            parse_month("2026-13")


class EmployeeValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "employee_code": "EMP001",
            "full_name": "Sample Employee",
            "designation": "Developer",
            "joining_date": "2026-01-01",
            "basic_salary": "35000",
            "hra_percent": "20",
            "da_percent": "10",
            "tax_percent": "5",
            "email": "sample@example.com",
            "phone": "+91 9000000000",
        }

    def test_valid_employee(self):
        clean = validate_employee(self.data)
        self.assertEqual(clean["employee_code"], "EMP001")
        self.assertEqual(clean["basic_salary"], Decimal("35000.00"))

    def test_invalid_email(self):
        self.data["email"] = "not-email"
        with self.assertRaises(ValueError):
            validate_employee(self.data)

    def test_invalid_employee_code(self):
        self.data["employee_code"] = "A"
        with self.assertRaises(ValueError):
            validate_employee(self.data)

    def test_invalid_date(self):
        self.data["joining_date"] = "2026-99-99"
        with self.assertRaises(ValueError):
            validate_employee(self.data)

    def test_missing_salary(self):
        self.data["basic_salary"] = ""
        with self.assertRaises(ValueError):
            validate_employee(self.data)

    def test_optional_email(self):
        self.data["email"] = ""
        self.assertIsNone(validate_employee(self.data)["email"])

    def test_invalid_department(self):
        self.data["department_id"] = "abc"
        with self.assertRaises(ValueError):
            validate_employee(self.data)


if __name__ == "__main__":
    unittest.main()
