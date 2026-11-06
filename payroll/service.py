"""Business service that coordinates database and Excel operations."""
from .database import Database
from .excel_reports import ExcelExporter, open_in_spreadsheet
from .calculations import calculate_salary


class PayrollService:
    def __init__(self, database=None, exporter=None):
        self.db = database or Database()
        self.exporter = exporter or ExcelExporter()

    def initialize_database(self):
        self.db.initialize()

    def departments(self):
        return self.db.list_departments()

    def employees(self, search="", include_inactive=True):
        return self.db.list_employees(search, include_inactive)

    def employee(self, employee_id):
        return self.db.get_employee(employee_id)

    def create_employee(self, data):
        return self.db.create_employee(data)

    def update_employee(self, employee_id, data):
        return self.db.update_employee(employee_id, data)

    def change_status(self, employee_id, active):
        return self.db.set_employee_active(employee_id, active)

    def salary_preview(self, basic, hra, da, tax):
        return calculate_salary(basic, hra, da, tax)

    def generate_payroll(self, month):
        return self.db.run_payroll(month)

    def runs(self):
        return self.db.list_payroll_runs()

    def run_details(self, run_id):
        return self.db.get_payroll_run(run_id), self.db.payroll_items(run_id)

    def export_employees(self, open_file=False):
        path = self.exporter.export_employees(self.employees())
        if open_file:
            open_in_spreadsheet(path)
        return path

    def export_payroll(self, run_id, open_file=False):
        run, items = self.run_details(run_id)
        path = self.exporter.export_payroll(run, items)
        if open_file:
            open_in_spreadsheet(path)
        return path

    def export_payslip(self, run_id, employee_id, open_file=False):
        run = self.db.get_payroll_run(run_id)
        item = self.db.payroll_item_for_employee(run_id, employee_id)
        path = self.exporter.export_salary_slip(run, item)
        if open_file:
            open_in_spreadsheet(path)
        return path
