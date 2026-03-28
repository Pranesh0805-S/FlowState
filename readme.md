## Productivity Automation System (PyQt5 + MySQL)

### What this is
A desktop Productivity Automation System built with **Python + PyQt5** and a **MySQL** backend (no web frameworks).  
The client talks to backend logic via:

`response = server.main.handle_request(action, payload)`

Responses always follow:

```json
{ "status": "success/error", "data": { }, "message": "text" }
```

### Project layout
Matches the required structure under `ProductivityAutomationSystem/`.

### Setup
- **Python**: 3.10+ recommended
- **MySQL**: create a database (e.g. `productivity_automation`)

1) Install dependencies

```bash
pip install -r requirements.txt
```

2) Create tables
- Open `database/schema.sql` and run it in your MySQL client (Workbench / CLI).

3) Configure DB connection
Set environment variables (Windows PowerShell example):

```powershell
$env=PRODUCTIVITY_DB_HOST="localhost"
$env=PRODUCTIVITY_DB_PORT="3306"
$env=PRODUCTIVITY_DB_USER="root"
$env=PRODUCTIVITY_DB_PASSWORD="your_password"
$env=PRODUCTIVITY_DB_NAME="productivity_automation"
$env=PRODUCTIVITY_JWT_SECRET="change_me"
```

### Run
From inside `ProductivityAutomationSystem/`:

```bash
python client/main.py
```

### Notes
- The backend is **in-process** (imported by the client) and uses MySQL via `mysql-connector-python`.
- If the DB connection fails, the UI will show backend error messages so you can fix credentials/schema.

