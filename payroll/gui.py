"""Tkinter desktop interface for employee and payroll management."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from decimal import Decimal
from .service import PayrollService
from .database import Database
from .auth import hash_password, verify_password


class EmployeeDialog(tk.Toplevel):
    """Validated employee editor; calls save callback only on submit."""
    FIELDS = [
        ("employee_code", "Employee Code *"),
        ("full_name", "Full Name *"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("designation", "Designation *"),
        ("joining_date", "Joining Date (YYYY-MM-DD) *"),
        ("basic_salary", "Basic Monthly Salary *"),
        ("hra_percent", "HRA Percentage *"),
        ("da_percent", "DA Percentage *"),
        ("tax_percent", "Tax Percentage *"),
    ]

    def __init__(self, parent, service, employee=None, on_saved=None):
        super().__init__(parent)
        self.service = service
        self.employee = employee
        self.on_saved = on_saved
        self.title("Edit Employee" if employee else "Register Employee")
        self.geometry("560x630")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg="#F3F6FA")
        self.vars = {}
        self.department_map = {}
        self._build()
        self._populate()
        self.focus_force()

    def _build(self):
        wrapper = ttk.Frame(self, padding=22)
        wrapper.pack(fill="both", expand=True)
        ttk.Label(wrapper, text="Employee Details", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        for index, (key, label) in enumerate(self.FIELDS, start=1):
            ttk.Label(wrapper, text=label).grid(row=index, column=0,
                sticky="w", padx=(0, 14), pady=6)
            var = tk.StringVar()
            entry = ttk.Entry(wrapper, textvariable=var, width=34)
            entry.grid(row=index, column=1, sticky="ew", pady=6)
            self.vars[key] = var
        department_row = len(self.FIELDS) + 1
        ttk.Label(wrapper, text="Department").grid(row=department_row, column=0,
            sticky="w", pady=6)
        self.department_var = tk.StringVar()
        self.department_combo = ttk.Combobox(wrapper, textvariable=self.department_var,
            state="readonly", width=31)
        self.department_combo.grid(row=department_row, column=1, sticky="ew", pady=6)
        try:
            departments = self.service.departments()
        except Exception:
            departments = []
        self.department_map = {d["name"]: d["id"] for d in departments}
        self.department_combo["values"] = ["(None)"] + list(self.department_map)
        self.department_var.set("(None)")
        self.active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(wrapper, text="Employee is active",
            variable=self.active_var).grid(row=department_row+1,
            column=1, sticky="w", pady=8)
        buttons = ttk.Frame(wrapper)
        buttons.grid(row=department_row+2, column=0, columnspan=2,
            sticky="e", pady=(18, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(
            side="left", padx=5)
        ttk.Button(buttons, text="Save Employee", style="Accent.TButton",
            command=self._save).pack(side="left", padx=5)
        wrapper.columnconfigure(1, weight=1)

    def _populate(self):
        defaults = {
            "joining_date": date.today().isoformat(),
            "basic_salary": "25000",
            "hra_percent": "20",
            "da_percent": "10",
            "tax_percent": "5",
        }
        if self.employee:
            defaults.update(self.employee)
        for key, var in self.vars.items():
            value = defaults.get(key)
            var.set(str(value) if value is not None else "")
        if self.employee:
            name = self.employee.get("department_name")
            self.department_var.set(name if name in self.department_map else "(None)")
            self.active_var.set(bool(self.employee["active"]))

    def _save(self):
        data = {key: var.get() for key, var in self.vars.items()}
        data["department_id"] = self.department_map.get(self.department_var.get())
        data["active"] = self.active_var.get()
        try:
            if self.employee:
                self.service.update_employee(self.employee["id"], data)
            else:
                self.service.create_employee(data)
        except Exception as exc:
            messagebox.showerror("Unable to save employee", str(exc), parent=self)
            return
        messagebox.showinfo("Saved", "Employee record saved successfully.", parent=self)
        if self.on_saved:
            self.on_saved()
        self.destroy()


class PayrollApp(tk.Tk):
    """Main desktop window with employees, payroll runs and Excel reports."""

    EMPLOYEE_COLUMNS = ["id", "employee_code", "full_name", "department_name",
                        "designation", "basic_salary", "active"]
    RUN_COLUMNS = ["id", "payroll_month", "employee_count", "gross_total", "net_total"]
    ITEM_COLUMNS = ["employee_id", "employee_code", "employee_name",
                    "basic_salary", "hra_amount", "da_amount", "gross_salary",
                    "tax_amount", "net_salary"]

    def __init__(self, service=None, current_user="admin"):
        super().__init__()
        self.service = service or PayrollService()
        self.current_user = current_user
        self.title("Payroll Management System | Python + MySQL + Excel")
        self.geometry("1220x770")
        self.minsize(1000, 650)
        self.configure(bg="#F3F6FA")
        self._style()
        self._build()
        self.after(100, self.refresh_all)

    def _style(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#F3F6FA")
        style.configure("TLabel", background="#F3F6FA", foreground="#27364B",
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"),
                        foreground="#183153")
        style.configure("Section.TLabel", font=("Segoe UI", 14, "bold"),
                        foreground="#183153")
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure("Accent.TButton", background="#215A83", foreground="white")
        style.map("Accent.TButton", background=[("active", "#174669")])
        style.configure("Treeview", rowheight=29, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=(18, 9))

    def _build(self):
        header = ttk.Frame(self, padding=(24, 18))
        header.pack(fill="x")
        ttk.Label(header, text="Payroll Management System",
                  style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="Logout", command=self.logout).pack(
            side="right", padx=5)
        ttk.Button(header, text="Database Setup", command=self.initialize_database).pack(
            side="right", padx=5)
        ttk.Button(header, text="Refresh", command=self.refresh_all).pack(
            side="right", padx=5)
        ttk.Label(header, text=f"Signed in: {self.current_user}").pack(
            side="right", padx=12)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, padding=(24, 0)).pack(fill="x")
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=22, pady=16)
        self.employees_tab = ttk.Frame(self.notebook, padding=14)
        self.payroll_tab = ttk.Frame(self.notebook, padding=14)
        self.reports_tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.employees_tab, text="Employees")
        self.notebook.add(self.payroll_tab, text="Monthly Payroll")
        self.notebook.add(self.reports_tab, text="Reports & Excel")
        self._build_employees()
        self._build_payroll()
        self._build_reports()
        ttk.Label(self, text="Academic demonstration • Salary/tax policy is illustrative",
                  padding=(24, 8)).pack(fill="x")

    def _table(self, parent, columns, labels=None):
        holder = ttk.Frame(parent)
        holder.pack(fill="both", expand=True, pady=(10, 0))
        tree = ttk.Treeview(holder, columns=columns, show="headings", selectmode="browse")
        labels = labels or {}
        for column in columns:
            tree.heading(column, text=labels.get(column, column.replace("_", " ").title()))
            width = 180 if "name" in column else 135
            if column == "id":
                width = 60
            tree.column(column, width=width, minwidth=75, stretch=True)
        yscroll = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(holder, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)
        return tree

    def _build_employees(self):
        bar = ttk.Frame(self.employees_tab)
        bar.pack(fill="x")
        ttk.Label(bar, text="Employee Directory", style="Section.TLabel").pack(
            side="left", padx=(0, 15))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(bar, textvariable=self.search_var, width=25)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<Return>", lambda _event: self.refresh_employees())
        ttk.Button(bar, text="Search", command=self.refresh_employees).pack(side="left")
        ttk.Button(bar, text="Add Employee", style="Accent.TButton",
            command=self.add_employee).pack(side="right", padx=5)
        ttk.Button(bar, text="Edit Selected", command=self.edit_employee).pack(
            side="right", padx=5)
        ttk.Button(bar, text="Activate / Deactivate", command=self.toggle_employee).pack(
            side="right", padx=5)
        self.employee_tree = self._table(self.employees_tab, self.EMPLOYEE_COLUMNS)
        self.employee_tree.bind("<Double-1>", lambda _event: self.edit_employee())

    def _build_payroll(self):
        bar = ttk.Frame(self.payroll_tab)
        bar.pack(fill="x")
        ttk.Label(bar, text="Monthly Payroll", style="Section.TLabel").pack(
            side="left", padx=(0, 20))
        ttk.Label(bar, text="Month (YYYY-MM)").pack(side="left")
        self.month_var = tk.StringVar(value=date.today().strftime("%Y-%m"))
        ttk.Entry(bar, textvariable=self.month_var, width=12).pack(side="left", padx=8)
        ttk.Button(bar, text="Generate Payroll", style="Accent.TButton",
            command=self.generate_payroll).pack(side="left", padx=5)
        ttk.Button(bar, text="View Selected", command=self.view_payroll).pack(
            side="left", padx=5)
        ttk.Label(self.payroll_tab, text="Existing Payroll Runs",
                  style="Section.TLabel").pack(anchor="w", pady=(18, 0))
        self.runs_tree = self._table(self.payroll_tab, self.RUN_COLUMNS)
        self.runs_tree.bind("<Double-1>", lambda _event: self.view_payroll())

    def _build_reports(self):
        ttk.Label(self.reports_tab, text="Excel Exports",
                  style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(self.reports_tab,
            text="Export employee records or monthly payroll. On Windows, exported .xlsx files "
                 "open in Microsoft Excel if it is installed and is your default spreadsheet app.",
            wraplength=850).pack(anchor="w", pady=(0, 18))
        actions = ttk.Frame(self.reports_tab)
        actions.pack(fill="x")
        ttk.Button(actions, text="Export Employees & Open Excel",
            style="Accent.TButton", command=self.export_employees).pack(side="left", padx=5)
        ttk.Button(actions, text="Export Selected Payroll & Open Excel",
            style="Accent.TButton", command=self.export_payroll).pack(side="left", padx=5)
        ttk.Button(actions, text="Export Selected Employee Payslip",
            command=self.export_payslip).pack(side="left", padx=5)
        ttk.Label(self.reports_tab, text="Select a payroll run below:",
                  style="Section.TLabel").pack(anchor="w", pady=(24, 4))
        self.report_runs_tree = self._table(self.reports_tab, self.RUN_COLUMNS)

    def _run_safe(self, action, success_message=None):
        try:
            result = action()
            if success_message:
                messagebox.showinfo("Success", success_message)
            return result
        except Exception as exc:
            messagebox.showerror("Operation failed", str(exc))
            self.status.set(f"Error: {exc}")
            return None

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.destroy()
            launch()

    def initialize_database(self):
        if not messagebox.askyesno("Initialize Database",
            "Create database tables if they do not exist? Existing data will be preserved."):
            return
        def action():
            self.service.initialize_database()
            self.refresh_all()
        self._run_safe(action, "Database initialized successfully.")

    def refresh_all(self):
        try:
            self.refresh_employees()
            self.refresh_payroll()
            self.status.set("Connected to MySQL • Data refreshed")
        except Exception as exc:
            self.status.set("Database unavailable • Check .env and initialize database")
            messagebox.showwarning("MySQL connection", str(exc))

    def _fill_tree(self, tree, records, columns):
        for child in tree.get_children():
            tree.delete(child)
        for record in records:
            values = []
            for key in columns:
                value = record.get(key)
                if isinstance(value, Decimal):
                    value = f"{value:,.2f}"
                elif isinstance(value, bool) or (key == "active" and value is not None):
                    value = "Active" if value else "Inactive"
                elif isinstance(value, date):
                    value = value.isoformat()
                values.append("" if value is None else value)
            tree.insert("", "end", values=values)

    def refresh_employees(self):
        records = self.service.employees(self.search_var.get())
        self._fill_tree(self.employee_tree, records, self.EMPLOYEE_COLUMNS)
        self.status.set(f"Showing {len(records)} employees")

    def refresh_payroll(self):
        records = self.service.runs()
        self._fill_tree(self.runs_tree, records, self.RUN_COLUMNS)
        self._fill_tree(self.report_runs_tree, records, self.RUN_COLUMNS)

    @staticmethod
    def _selected_id(tree):
        selection = tree.selection()
        if not selection:
            raise ValueError("Please select a record first")
        return int(tree.item(selection[0], "values")[0])

    def add_employee(self):
        EmployeeDialog(self, self.service, on_saved=self.refresh_employees)

    def edit_employee(self):
        def action():
            employee_id = self._selected_id(self.employee_tree)
            employee = self.service.employee(employee_id)
            if not employee:
                raise ValueError("Employee not found")
            EmployeeDialog(self, self.service, employee=employee,
                           on_saved=self.refresh_employees)
        self._run_safe(action)

    def toggle_employee(self):
        def action():
            employee_id = self._selected_id(self.employee_tree)
            employee = self.service.employee(employee_id)
            if not employee:
                raise ValueError("Employee not found")
            active = not bool(employee["active"])
            label = "activate" if active else "deactivate"
            if messagebox.askyesno("Confirm status", f"Do you want to {label} this employee?"):
                self.service.change_status(employee_id, active)
                self.refresh_employees()
        self._run_safe(action)

    def generate_payroll(self):
        def action():
            month = self.month_var.get().strip()
            if not messagebox.askyesno("Generate Payroll",
                f"Generate and store payroll for {month}? Existing runs cannot be overwritten."):
                return
            run_id = self.service.generate_payroll(month)
            self.refresh_payroll()
            messagebox.showinfo("Payroll generated", f"Created payroll run #{run_id}")
        self._run_safe(action)

    def view_payroll(self):
        def action():
            run_id = self._selected_id(self.runs_tree)
            run, items = self.service.run_details(run_id)
            if not run:
                raise ValueError("Payroll run not found")
            window = tk.Toplevel(self)
            window.title(f"Payroll Details - {run['payroll_month']:%B %Y}")
            window.geometry("1120x550")
            ttk.Label(window, text=f"Payroll Details • {run['payroll_month']:%B %Y}",
                      style="Section.TLabel", padding=15).pack(anchor="w")
            tree = self._table(window, self.ITEM_COLUMNS)
            self._fill_tree(tree, items, self.ITEM_COLUMNS)
            ttk.Label(window, text=f"Employees: {len(items)}",
                      padding=12).pack(anchor="w")
        self._run_safe(action)

    def export_employees(self):
        def action():
            path = self.service.export_employees(open_file=True)
            messagebox.showinfo("Export completed", f"Saved to:\n{path}")
        self._run_safe(action)

    def export_payroll(self):
        def action():
            run_id = self._selected_id(self.report_runs_tree)
            path = self.service.export_payroll(run_id, open_file=True)
            messagebox.showinfo("Export completed", f"Saved to:\n{path}")
        self._run_safe(action)

    def export_payslip(self):
        def action():
            run_id = self._selected_id(self.report_runs_tree)
            run, items = self.service.run_details(run_id)
            if not items:
                raise ValueError("No employees in this payroll run")
            dialog = tk.Toplevel(self)
            dialog.title("Choose Employee for Payslip")
            dialog.geometry("520x180")
            dialog.transient(self)
            dialog.grab_set()
            ttk.Label(dialog, text="Select employee", padding=12).pack(anchor="w")
            choices = {f"{i['employee_code']} - {i['employee_name']}": i["employee_id"]
                       for i in items}
            selected = tk.StringVar(value=next(iter(choices)))
            combo = ttk.Combobox(dialog, values=list(choices), textvariable=selected,
                                 state="readonly", width=55)
            combo.pack(padx=12, pady=6)
            def submit():
                try:
                    path = self.service.export_payslip(
                        run_id, choices[selected.get()], open_file=True)
                    dialog.destroy()
                    messagebox.showinfo("Export completed", f"Saved to:\n{path}")
                except Exception as exc:
                    messagebox.showerror("Export failed", str(exc), parent=dialog)
            ttk.Button(dialog, text="Export & Open", style="Accent.TButton",
                       command=submit).pack(pady=12)
        self._run_safe(action)


class AdminAccessWindow(tk.Tk):
    """First-run administrator setup and subsequent login screen."""

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.first_run = database.admin_count() == 0
        self.title("Payroll Management System - " +
                   ("Create Administrator" if self.first_run else "Administrator Login"))
        self.geometry("470x390")
        self.resizable(False, False)
        self.configure(bg="#F3F6FA")
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#F3F6FA")
        style.configure("TLabel", background="#F3F6FA", foreground="#27364B",
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"),
                        foreground="#183153")
        style.configure("Section.TLabel", font=("Segoe UI", 13, "bold"),
                        foreground="#183153")
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure("Accent.TButton", background="#215A83", foreground="white")
        self._build()

    def _build(self):
        panel = ttk.Frame(self, padding=28)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="Payroll Management System",
                  style="Title.TLabel", wraplength=400).pack(anchor="w", pady=(8, 5))
        heading = "Create your administrator account" if self.first_run else "Administrator sign in"
        ttk.Label(panel, text=heading, style="Section.TLabel").pack(anchor="w", pady=(8, 18))
        ttk.Label(panel, text="Username").pack(anchor="w")
        self.username_var = tk.StringVar(value="admin" if self.first_run else "")
        username = ttk.Entry(panel, textvariable=self.username_var, width=42)
        username.pack(fill="x", pady=(4, 12))
        ttk.Label(panel, text="Password").pack(anchor="w")
        self.password_var = tk.StringVar()
        password = ttk.Entry(panel, textvariable=self.password_var, show="•", width=42)
        password.pack(fill="x", pady=(4, 12))
        self.confirm_var = tk.StringVar()
        if self.first_run:
            ttk.Label(panel, text="Confirm password").pack(anchor="w")
            ttk.Entry(panel, textvariable=self.confirm_var, show="•", width=42).pack(
                fill="x", pady=(4, 12))
            ttk.Label(panel, text="Use at least 10 characters. Your password is stored as a salted hash.",
                      wraplength=400).pack(anchor="w", pady=(0, 8))
        self.error_var = tk.StringVar()
        ttk.Label(panel, textvariable=self.error_var, foreground="#B42318",
                  wraplength=400).pack(anchor="w", pady=(0, 8))
        button_text = "Create Admin Account" if self.first_run else "Sign In"
        ttk.Button(panel, text=button_text, style="Accent.TButton",
                   command=self.submit).pack(fill="x", pady=(4, 0))
        self.bind("<Return>", lambda _event: self.submit())
        username.focus_set()

    def submit(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        try:
            if not username:
                raise ValueError("Enter your username.")
            if self.first_run:
                if password != self.confirm_var.get():
                    raise ValueError("The passwords do not match.")
                encoded = hash_password(password)
                self.database.create_admin(username, encoded)
                messagebox.showinfo("Administrator created",
                                    "Your administrator account is ready. Please sign in.",
                                    parent=self)
                self.first_run = False
                self.password_var.set("")
                self.confirm_var.set("")
                self.title("Payroll Management System - Administrator Login")
                # Rebuild to remove the confirmation field and show the login form.
                for child in self.winfo_children():
                    child.destroy()
                self._build()
                return
            record = self.database.authenticate_admin(username)
            if not record or not verify_password(password, record["password_hash"]):
                raise ValueError("Incorrect username or password.")
        except Exception as exc:
            self.error_var.set(str(exc))
            return
        self.destroy()
        app = PayrollApp(current_user=username)
        app.mainloop()


def launch():
    database = Database()
    # Ensure the admin table exists even when the user is upgrading an existing database.
    database.initialize()
    access = AdminAccessWindow(database)
    access.mainloop()
