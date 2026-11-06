"""Generate professional Excel workbooks and open them on Windows.

Excel exports contain personal employee data. Save them in a secure location.
"""
from datetime import datetime
from pathlib import Path
import os
import platform
import subprocess
import sys
import xlsxwriter
from .config import settings


class ExcelExporter:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir or settings.export_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _filename(self, prefix):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return self.output_dir / f"{prefix}_{timestamp}.xlsx"

    @staticmethod
    def _formats(book):
        return {
            "title": book.add_format({"bold": True, "font_size": 18,
                "font_color": "#FFFFFF", "bg_color": "#183153", "valign": "vcenter"}),
            "subtitle": book.add_format({"font_size": 10, "font_color": "#667085"}),
            "header": book.add_format({"bold": True, "font_color": "#FFFFFF",
                "bg_color": "#215A83", "border": 0, "text_wrap": True,
                "valign": "vcenter"}),
            "text": book.add_format({"font_color": "#25364A"}),
            "money": book.add_format({"num_format": '#,##0.00;[Red](#,##0.00)',
                "font_color": "#25364A"}),
            "percent": book.add_format({"num_format": '0.00"%"'}),
            "date": book.add_format({"num_format": "dd mmm yyyy"}),
            "total_label": book.add_format({"bold": True, "bg_color": "#DDECF5"}),
            "total_money": book.add_format({"bold": True, "bg_color": "#DDECF5",
                "num_format": '#,##0.00'}),
            "note": book.add_format({"italic": True, "font_color": "#9B4D13",
                "text_wrap": True}),
        }

    @staticmethod
    def _write_value(sheet, row, col, value, formats, kind="text"):
        if value is None:
            sheet.write_blank(row, col, None)
        elif kind == "money":
            sheet.write_number(row, col, float(value), formats["money"])
        elif kind == "percent":
            sheet.write_number(row, col, float(value), formats["percent"])
        elif kind == "date":
            sheet.write_datetime(row, col, value, formats["date"])
        elif isinstance(value, bool):
            sheet.write_string(row, col, "Active" if value else "Inactive")
        else:
            # Write as text: avoids interpreting user input as Excel formulas.
            sheet.write_string(row, col, str(value), formats["text"])

    @staticmethod
    def _setup_sheet(sheet, headers, formats, title, subtitle, widths):
        last_col = len(headers) - 1
        sheet.merge_range(0, 0, 1, last_col, title, formats["title"])
        sheet.merge_range(2, 0, 2, last_col, subtitle, formats["subtitle"])
        sheet.set_row(4, 31)
        for col, (header, width) in enumerate(zip(headers, widths)):
            sheet.write(4, col, header, formats["header"])
            sheet.set_column(col, col, width)
        sheet.freeze_panes(5, 0)
        sheet.hide_gridlines(2)
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.repeat_rows(4)

    def export_employees(self, employees):
        """Export all employee records to a formatted Excel worksheet."""
        path = self._filename("employees")
        headers = ["Employee Code", "Full Name", "Email", "Phone", "Department",
                   "Designation", "Joining Date", "Basic Salary", "HRA %",
                   "DA %", "Tax %", "Status"]
        keys = ["employee_code", "full_name", "email", "phone", "department_name",
                "designation", "joining_date", "basic_salary", "hra_percent",
                "da_percent", "tax_percent", "active"]
        widths = [18, 27, 30, 18, 20, 24, 18, 18, 12, 12, 12, 12]
        with xlsxwriter.Workbook(str(path)) as book:
            formats = self._formats(book)
            sheet = book.add_worksheet("Employees")
            self._setup_sheet(sheet, headers, formats, "EMPLOYEE DIRECTORY",
                              f"Generated {datetime.now():%d %b %Y %H:%M}", widths)
            for row, employee in enumerate(employees, start=5):
                for col, key in enumerate(keys):
                    kind = ("date" if key == "joining_date" else
                            "money" if key == "basic_salary" else
                            "percent" if key.endswith("_percent") else "text")
                    self._write_value(sheet, row, col, employee.get(key), formats, kind)
            if employees:
                sheet.autofilter(4, 0, 4 + len(employees), len(headers) - 1)
                sheet.conditional_format(5, 0, 4 + len(employees), len(headers)-1,
                    {"type": "formula", "criteria": '=MOD(ROW(),2)=0',
                     "format": book.add_format({"bg_color": "#F3F7FA"})})
            sheet.set_footer("Confidential employee information | Page &P of &N")
        return path

    def export_payroll(self, run, items):
        """Create detailed payroll, totals and an explanation worksheet."""
        if not run:
            raise ValueError("Payroll run does not exist")
        path = self._filename(f"payroll_{run['payroll_month']:%Y_%m}")
        headers = ["Employee Code", "Employee Name", "Department", "Designation",
                   "Basic", "HRA", "DA", "Gross", "Tax", "Other Deductions", "Net"]
        keys = ["employee_code", "employee_name", "department_name", "designation",
                "basic_salary", "hra_amount", "da_amount", "gross_salary",
                "tax_amount", "other_deductions", "net_salary"]
        widths = [18, 28, 20, 24, 17, 17, 17, 17, 17, 21, 19]
        with xlsxwriter.Workbook(str(path)) as book:
            formats = self._formats(book)
            sheet = book.add_worksheet("Payroll")
            self._setup_sheet(sheet, headers, formats, "MONTHLY PAYROLL REPORT",
                              f"Period: {run['payroll_month']:%B %Y}  |  "
                              f"Generated: {datetime.now():%d %b %Y %H:%M}", widths)
            for row, item in enumerate(items, start=5):
                for col, key in enumerate(keys):
                    kind = "money" if col >= 4 else "text"
                    self._write_value(sheet, row, col, item.get(key), formats, kind)
            total_row = 5 + len(items)
            sheet.write(total_row, 0, "TOTAL", formats["total_label"])
            for col in range(1, 4):
                sheet.write_blank(total_row, col, None, formats["total_label"])
            for col in range(4, len(headers)):
                col_letter = xlsxwriter.utility.xl_col_to_name(col)
                sheet.write_formula(total_row, col,
                    f"=SUM({col_letter}6:{col_letter}{total_row})",
                    formats["total_money"],
                    sum(float(item.get(keys[col]) or 0) for item in items))
            if items:
                sheet.autofilter(4, 0, total_row - 1, len(headers) - 1)
            sheet.set_footer("Confidential payroll data | Page &P of &N")
            notes = book.add_worksheet("About")
            notes.set_column("A:A", 26)
            notes.set_column("B:B", 78)
            notes.write("A1", "Payroll period")
            notes.write("B1", run["payroll_month"].strftime("%B %Y"))
            notes.write("A2", "Employees")
            notes.write_number("B2", len(items))
            notes.write("A4", "Calculation policy")
            notes.write("B4", "HRA and DA are percentages of basic salary")
            notes.write("B5", "Gross = Basic + HRA + DA")
            notes.write("B6", "Tax = configured percentage of gross")
            notes.write("B7", "Net = Gross - Tax - Other Deductions")
            notes.write("A9", "IMPORTANT")
            notes.write("B9", "Illustrative academic project only. Not a statutory Indian payroll/tax engine.",
                        formats["note"])
            notes.set_row(8, 34)
        return path

    def export_salary_slip(self, run, item):
        """Create a standalone payslip workbook for a single employee."""
        if not run or not item:
            raise ValueError("Payroll run or employee payroll item not found")
        path = self._filename(f"payslip_{item['employee_code']}_{run['payroll_month']:%Y_%m}")
        with xlsxwriter.Workbook(str(path)) as book:
            f = self._formats(book)
            sheet = book.add_worksheet("Salary Slip")
            sheet.set_column("A:A", 26)
            sheet.set_column("B:B", 28)
            sheet.set_column("C:C", 22)
            sheet.set_column("D:D", 22)
            sheet.merge_range("A1:D2", "EMPLOYEE SALARY SLIP", f["title"])
            sheet.write("A4", "Payroll month", f["header"])
            sheet.write("B4", run["payroll_month"].strftime("%B %Y"))
            sheet.write("A5", "Employee code", f["header"])
            sheet.write_string("B5", str(item["employee_code"]))
            sheet.write("A6", "Employee name", f["header"])
            sheet.write_string("B6", str(item["employee_name"]))
            sheet.write("A7", "Department", f["header"])
            sheet.write_string("B7", str(item.get("department_name") or "—"))
            sheet.write("A8", "Designation", f["header"])
            sheet.write_string("B8", str(item["designation"]))
            sheet.write("A10", "Earnings", f["header"])
            sheet.write("C10", "Deductions", f["header"])
            earnings = [("Basic", "basic_salary"), ("HRA", "hra_amount"),
                        ("DA", "da_amount"), ("Gross", "gross_salary")]
            deductions = [("Tax", "tax_amount"),
                          ("Other deductions", "other_deductions")]
            for idx, (label, key) in enumerate(earnings, start=10):
                sheet.write(idx, 0, label)
                sheet.write_number(idx, 1, float(item[key]), f["money"])
            for idx, (label, key) in enumerate(deductions, start=10):
                sheet.write(idx, 2, label)
                sheet.write_number(idx, 3, float(item[key]), f["money"])
            sheet.write("A17", "NET PAY", f["total_label"])
            sheet.write_number("B17", float(item["net_salary"]), f["total_money"])
            sheet.merge_range("A20:D21",
                "Demonstration payslip only; tax is an illustrative flat percentage, not statutory tax.",
                f["note"])
            sheet.set_landscape()
            sheet.fit_to_pages(1, 1)
        return path


def open_in_spreadsheet(path):
    """Open workbook using the OS file association.

    On Windows, .xlsx opens in Microsoft Excel if Excel is installed and
    associated with that file type. Other systems use their default app.
    """
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    if platform.system() == "Windows":
        os.startfile(str(path))
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])
    return path
