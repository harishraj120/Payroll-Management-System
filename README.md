# Payroll Management System

A desktop payroll management application built with **Python, Tkinter, MySQL, and Excel (.xlsx)**. Designed as a complete academic portfolio project for demonstrating CRUD operations, database connectivity, salary calculations, monthly payroll snapshots, and formatted Excel reporting.

## Features

- Administrator login with first-run account creation and salted PBKDF2 password hashing.
- Register employees with unique codes, names, contact details, joining dates, salary and department.
- Search, edit, activate, and deactivate employee records.
- Calculate monthly salary using configurable HRA, DA, and demonstration tax percentages.
- Generate one payroll snapshot per month and preserve historical salary figures.
- Store employee records and monthly payroll in MySQL.
- Export a professionally formatted employee directory to Excel.
- Export monthly payroll with totals, formatting and explanatory notes.
- Generate individual employee payslips as Excel workbooks.
- Open generated Excel workbooks using the operating system's default `.xlsx` application.
- Use parameterized SQL queries, input validation, database transactions and automated calculation tests.

## Requirements

- Windows 10/11 (recommended for Microsoft Excel integration), macOS, or Linux
- Python 3.10 or newer
- MySQL Server 8.0 or newer
- Microsoft Excel (to open exports in Excel on Windows)
- Tkinter (normally included with standard Python on Windows)

## Setup on Windows

1. Install Python from https://www.python.org/downloads/ and enable **Add Python to PATH**.
2. Install MySQL Community Server from https://dev.mysql.com/downloads/mysql/ and remember your MySQL password.
3. Extract this project ZIP into a folder.
4. Open PowerShell or Command Prompt inside the project folder.
5. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

6. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

7. Copy `.env.example` to `.env`:

   ```powershell
   copy .env.example .env
   ```

8. Edit `.env` with your **own MySQL credentials**. Never upload `.env` to GitHub.
9. Initialize the database:

   ```powershell
   python setup_database.py
   ```

10. Start the desktop application:

    ```powershell
    python main.py
    ```

11. On first launch, create an administrator username and password (minimum 10 characters). On later launches, sign in with those credentials.
12. Select **Add Employee**, enter details, and click **Save Employee**.
12. Open **Monthly Payroll**, choose a month in `YYYY-MM`, and generate payroll.
13. Open **Reports & Excel**, select a payroll run and click **Export Selected Payroll & Open Excel**.

If you prefer MySQL Workbench, run the entire `sql/schema.sql` script there instead of step 9.

## Folder structure

```text
Payroll-Management-System/
├── main.py
├── setup_database.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── LICENSE
├── payroll/
│   ├── auth.py
│   ├── __init__.py
│   ├── calculations.py
│   ├── config.py
│   ├── database.py
│   ├── excel_reports.py
│   ├── gui.py
│   ├── models.py
│   └── service.py
├── sql/
│   └── schema.sql
├── tests/
│   └── test_calculations.py
├── docs/
│   └── USER_GUIDE.md
└── exports/
    └── .gitkeep
```

## Example salary calculation

Assume an employee has basic salary 30,000, HRA 20%, DA 10%, tax 5%, and no other deductions:

| Component | Amount |
| --- | ---: |
| Basic | 30,000.00 |
| HRA (20% of basic) | 6,000.00 |
| DA (10% of basic) | 3,000.00 |
| Gross | 39,000.00 |
| Demonstration tax (5% of gross) | 1,950.00 |
| Net | 37,050.00 |

**Important:** This is an illustrative academic payroll formula. It is not a compliant implementation of Indian income tax, provident fund, ESI, professional tax, or other statutory requirements. Do not use it to process real payroll without a full regulatory and security review.

## Excel integration

Files are saved under `exports/`. The application opens the generated `.xlsx` file using the operating system's default application. On Windows, **Microsoft Excel opens automatically if Excel is installed and registered as the default `.xlsx` application**. If another spreadsheet program is set as default, that program will open instead.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

Tests validate salary calculations, rounding, input validation and month parsing. Database integration requires a running MySQL server and is not included in the unit tests.

## Database and privacy notes

- SQL data is stored locally in your configured MySQL server, not directly in the Excel file.
- Excel is an export of stored data. Editing the Excel file does not automatically change MySQL records.
- `.env` contains sensitive credentials and is excluded from Git. Administrator passwords are stored as salted PBKDF2 hashes in the `app_users` table.
- Do not upload actual employee information or salary spreadsheets to public GitHub repositories.
- Restrict MySQL user privileges and protect generated Excel reports in real deployments.
- Use the application only with demonstration data unless appropriate security and compliance controls have been added.

## GitHub

Create a public repository named `Payroll-Management-System`, upload these files (excluding `.env` and real payroll exports), and add screenshots of the application after running it. The project is released under the MIT License.
