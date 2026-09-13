# TalentReadiness

TalentReadiness is a compact workforce-skills intelligence MVP. A manager records an absence, selects the impacted project, reviews ranked internal candidates, compares them, and explicitly assigns a temporary replacement.

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, Recharts, Lucide
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Pydantic and JWT authentication

## Quick start

Copy `.env.example` to `.env`, then run:

```bash
docker compose up --build
```

Open `http://localhost:5173`. The API docs are at `http://localhost:8000/docs`.

For non-Docker local development, create a Python environment in `backend`, install `requirements.txt`, run `alembic upgrade head`, then run `uvicorn app.main:app --reload`. In `frontend`, run `npm install` then `npm run dev`. By default, the backend uses local SQLite when `DATABASE_URL` is not set; set it to PostgreSQL for a production-like environment. Alembic honors `DATABASE_URL`, so the same migration command works for PostgreSQL.

## Demo

The database is seeded on first startup with 20 fictional employees, 32 skills, 6 active projects, availability records, and sample absence scenarios.

- Manager: `manager@talentreadiness.demo` / `demo123`
- Employee accounts also use `demo123`; for example `sarahwilson@talentreadiness.demo`.

Use the manager dashboard’s **Find replacement** action on John Smith’s Fraud Detection Platform absence. The finder returns ranked, explainable matches; select two or three candidates to compare and use **Assign replacement** to complete the workflow.

## User guide

### Manager workflow

1. Sign in with the manager demo account.
2. On **Dashboard**, choose **Record absence** and select an employee who is assigned to the affected project.
3. In **Today's absences**, choose **Find replacement**.
4. Select the absent employee, project, and required hours, then choose **Find Best Replacement**.
5. Review the ranked candidates, their skill matches, availability, workload, compatibility, and skill gaps.
6. Select up to three candidates to compare, then choose **Assign replacement** for the selected person.
7. Confirm the assignment. The system records it; it never assigns a person automatically.

### Employee availability

From **Employees**, a manager can choose an employee's status, enter working hours, and select **Save**.

- **Available** — available for the saved hours.
- **Remote** — working remotely and available for the saved hours.
- **Unavailable** — creates a dashboard absence when that employee has a project assignment.

Setting an employee to Available or Remote clears their full-day absence. Dashboard counts update for that same employee and local date.

### Interface modes

Use **Light interface** or **Dark interface** in the sidebar to switch themes. The selected mode is remembered in the browser and applies to the landing page, login pages, and workspace.

## Matching

The transparent score is 50% skill fit, 20% availability, 15% workload capacity, and 15% role/project compatibility. Missing mandatory skills get a strong penalty and candidates are omitted from final recommendations. Equal scores are ordered by availability, workload capacity, then project compatibility.

## Tests

```bash
cd backend
pytest -q
```

The scoring tests cover high-fit, missing mandatory skill, partial availability, role-based access, absence validation, and the manager assignment flow.

## Migrations

The repository includes an Alembic initial migration for PostgreSQL. From `backend`, set `DATABASE_URL` in your environment and run:

```bash
alembic upgrade head
```

The application seeds the demo dataset on first startup. Docker Compose starts PostgreSQL and the application services together.

## Coverage policy and Admin controls

TalentReadiness includes a compact **Admin** role for choosing how temporary coverage is approved. The seeded Admin account is `admin@talentreadiness.demo` with password `demo123`.

- **Consent Required** (the default): a manager sends a coverage request. No replacement assignment is created until the selected employee accepts it in their coverage requests view.
- **Direct Assignment**: a manager can confirm the selected replacement immediately. The employee can still review the project, date, extra hours, proposed incentive multiplier, and manager in their coverage assignments.

The Admin **Policy settings** page lets an Admin select either mode and set the default proposed incentive multiplier (1.5× by default). The multiplier is an internal proposal only: TalentReadiness does not perform payroll, payment, tax, email, or money-transfer actions.

Every sent request, acceptance, decline, direct assignment, and replacement change is recorded in the coverage audit log with the people, project, hours, policy mode, incentive proposal, actor, reason, and timestamp. Only Admins may update policy settings or read the audit log. Managers continue to manage coverage decisions; employees can only see and respond to their own coverage work.
