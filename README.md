# ResQAgent – Agentic AI Emergency Response & Coordination System

ResQAgent is an autonomous emergency response coordination platform powered by an Agentic AI cognitive loop:

$$\text{PERCEIVE} \longrightarrow \text{REASON} \longrightarrow \text{DECIDE} \longrightarrow \text{ACT} \longrightarrow \text{OBSERVE} \longrightarrow \text{ADAPT}$$

---

## 1. Authentication & Role-Based Access Control (RBAC)

ResQAgent enforces strict role-based access across four authenticated roles:

| Role | Permissions & Access Scope | Dashboard Route |
|---|---|---|
| **Citizen** | Self-registers, submits emergency SOS requests, views personal incident tracking & status updates. Restricted from viewing other citizens or responder fleets. | `/citizen` |
| **Responder** | Receives assigned emergency alerts, acknowledges calls (`Accept` / `Decline`), updates operational progress (`En Route` → `On Scene` → `Completed`). | `/responder` |
| **Dispatcher** | Full operational visibility across all active incidents, responder fleet monitoring, assignment overrides, SLA timeout simulation, and real-time AI cognitive traces. | `/dispatch` |
| **Administrator** | User and responder account provisioning, account activation/deactivation, system audit statistics, simulation reset, and dispatch operations. | `/admin` |

---

## 2. Password Security & JWT Tokens

- **Password Hashing**: Passwords hashed using `bcrypt` (12 salt rounds). Plain-text passwords are never stored, logged, or exposed in API responses.
- **Session Tokens**: Signed JSON Web Tokens (`HS256`, 24-hour expiration) passed via `Authorization: Bearer <token>` and mirrored in secure cookies.
- **Backend Enforced**: All sensitive endpoints independently verify authentication, active account status, and role permissions.

---

## 3. Initial Administrator Setup

To maintain data integrity and prevent fake production accounts, ResQAgent provides an initial administrator setup mechanism:

### Option A: Command-Line Interface (CLI)
```powershell
.\venv\Scripts\python -m backend.cli.init_admin --email admin@resqagent.org --name "System Administrator" --password "ResQAdmin2026!"
```

### Option B: Environment Variables (`.env`)
```env
INITIAL_ADMIN_EMAIL=admin@resqagent.org
INITIAL_ADMIN_PASSWORD=ResQAdmin2026!
INITIAL_ADMIN_NAME="System Administrator"
JWT_SECRET=resqagent-super-secret-jwt-key-32-chars-min-prod
```
When the application starts, it verifies that an administrator account exists. If not, it provisions the initial administrator using these configurations.

---

## 4. API Endpoints

### Authentication (`/api/auth`)
- `POST /api/auth/register`: Citizen self-registration.
- `POST /api/auth/login`: Authenticates user and issues JWT.
- `POST /api/auth/logout`: Invalidates authentication session.
- `GET /api/auth/me`: Retrieves currently authenticated user profile.
- `POST /api/auth/change-password`: Updates password with verification.
- `POST /api/auth/forgot-password`: Dispatches password recovery request.

### Administration (`/api/admin`)
- `GET /api/admin/users`: Lists all system accounts (Admin only).
- `POST /api/admin/users`: Provisions authorized Dispatchers, Responders, or Admins.
- `PATCH /api/admin/users/{id}/status`: Activates or deactivates an account.
- `GET /api/admin/system-stats`: Returns system audit counters.

### Emergency Operations (`/api/incidents`, `/api/assignments`, `/api/responders`)
- `POST /api/incidents/`: Submits emergency incident (Binds to authenticated user).
- `GET /api/incidents/`: Lists incidents (Filtered to user's own incidents for citizens; full list for dispatchers/admins).
- `POST /api/assignments/{id}/respond`: Responder accepts or declines assignment.
- `POST /api/assignments/{id}/progress`: Responder updates progress (`EN_ROUTE`, `COMPLETED`).
- `POST /api/reports/{id}/generate`: Synthesizes AI debrief postmortem.
- `POST /api/simulation/timeout/{id}`: Triggers SLA timeout breach and auto-escalation.

---

## 5. Running the Application

### Start Backend & Static Frontend Server
```powershell
.\venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Accessing the Web Application
Open your browser to:
👉 **`http://localhost:8000`**

- If unauthenticated, the application automatically displays the **Sign In** interface.
- Default Initial Administrator:
  - **Email**: `admin@resqagent.org`
  - **Password**: `ResQAdmin2026!`
- New citizens can register immediately via the **Create Account** tab.

---

## 6. Running Test Suites

```powershell
# 1. Complete Authentication & RBAC Security Suite (17 Tests)
.\venv\Scripts\python backend/test_auth_suite.py

# 2. End-to-End API Integration Suite
.\venv\Scripts\python backend/test_api_suite.py

# 3. Agentic AI Cognitive Loop & Escalation Verification
.\venv\Scripts\python backend/test_agent_flow.py
```
