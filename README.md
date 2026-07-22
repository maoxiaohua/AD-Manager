# AD Hostname Manager

Windows AD Domain Hostname Registration & Management System — a web-based tool for IT administrators to sync and manage Active Directory computers (hostnames), users, and groups with their member relationships.

## Features

- **Dashboard**: Statistics overview with Computers/Users/Groups counts, active/disabled breakdown, recent sync activity, and sync status
- **Computer Inventory**: Search, filter by status, sort, paginated table with CSV/Excel import/export
- **User Directory**: User management with search and import/export support
- **AD Groups**: Sync AD security/distribution groups with full member list view (like AD Users and Computers console)
- **LDAP Sync**: Direct AD sync via LDAPS with NTLM auth — pull-only, never writes back to AD. Syncs computers, users, groups, and group memberships
- **Smart Setup**: Just enter your AD domain name (e.g. your-domain.com) and the system auto-discovers the domain controller and Base DN via DNS
- **File Import/Export**: CSV and Excel (.xlsx) import/export with column validation and styled output
- **Scheduled Sync**: Configurable cron-based automatic LDAP sync via APScheduler
- **Simple Auth**: Admin password with JWT (bcrypt hashed, 8-hour token expiry)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13 + FastAPI |
| Database | SQLite (via SQLAlchemy ORM) |
| LDAP Client | ldap3 with NTLM authentication |
| DNS Discovery | dnspython (SRV record lookup) |
| Frontend | React 18 + TypeScript + Vite |
| UI Framework | Ant Design 5 + ProLayout |
| Scheduler | APScheduler |

## Service Management (systemd)

```bash
# Restart both services
sudo systemctl restart ad-manager-backend ad-manager-frontend

# Check service status
sudo systemctl status ad-manager-backend ad-manager-frontend

# View logs
sudo journalctl -u ad-manager-backend -f
sudo journalctl -u ad-manager-frontend -f

# Restart individual services
sudo systemctl restart ad-manager-backend
sudo systemctl restart ad-manager-frontend
```

## Quick Start (Development)

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Default admin password: `admin123`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: **http://localhost:3000**

## LDAP Sync Setup

### Smart Setup

1. Go to **Settings → LDAP Config**
2. Enter your AD domain name: `your-domain.com` → click **Auto Discover**
3. Fill in Admin Username and Admin Password
4. Click **Save LDAP Config**
5. Go to **Sync & Import** → click **Trigger LDAP Sync**

## File Import Format

### Computers CSV
```csv
name,distinguished_name,ip_address,operating_system,os_version,description,status
PC01,CN=PC01,OU=Workstations,DC=example,DC=com,192.168.1.100,Windows 11 Pro,10.0.22621,,
```

### Users CSV
```csv
sam_account_name,distinguished_name,display_name,email,department
jdoe,CN=John Doe,CN=Users,DC=example,DC=com,John Doe,jdoe@example.com,Engineering
```

### Groups CSV
```csv
name,distinguished_name,display_name,group_type,group_scope,description,email
Domain Admins,CN=Domain Admins,CN=Users,DC=example,DC=com,Domain Admins,security,global,,
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/login | Login with admin password |
| GET | /api/auth/verify | Verify JWT token |
| GET | /api/dashboard/stats | Aggregate statistics |
| GET | /api/dashboard/recent-activities | Recent activity feed |
| GET/POST | /api/computers | List/Create computers |
| GET/PUT/DELETE | /api/computers/{id} | CRUD computer |
| GET/POST | /api/users | List/Create users |
| GET/PUT/DELETE | /api/users/{id} | CRUD user |
| GET/POST | /api/groups | List/Create groups |
| GET/PUT/DELETE | /api/groups/{id} | CRUD group |
| GET | /api/groups/{id}/detail | Group with member list |
| POST | /api/sync/ldap | Trigger LDAP sync |
| GET | /api/sync/logs | Sync history |
| GET | /api/sync/status | Sync status |
| POST | /api/import | Import CSV/Excel |
| GET | /api/export/{entity_type} | Export data |
| GET/PUT | /api/settings | Get/Update settings |
| POST | /api/settings/discover-ad | Auto-discover AD from domain |
