# TalentReadiness

> **Find the right available person, with the right skills, before a critical team gap becomes a crisis.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20App-00b894?style=for-the-badge)](https://talentreadiness.vercel.app)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61dafb?style=for-the-badge)](#technology)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge)](#technology)

**TalentReadiness** is a workforce-readiness platform that helps managers react when a team member becomes unavailable. It compares skills, availability, workload, and project requirements to recommend the best replacement employee.

## Live project

**Website:** [talentreadiness.vercel.app](https://talentreadiness.vercel.app)

Demo manager account: `manager@talentreadiness.demo`  
Demo password: `demo123`

## The problem

In hospitals, businesses, and project teams, an urgent gap can occur when a specialist is unavailable. Managers may spend hours calling people, checking calendars, and guessing who has the right experience. That delay can be stressful and costly—especially when the work is time-sensitive.

## Our solution

TalentReadiness gives managers one place to:

- See employees, skills, projects, availability, and current workload.
- Record an absence or staffing gap.
- Find the best available replacement using transparent rule-based scoring.
- Send a coverage request for employee approval, or make a direct assignment when policy allows.
- Track readiness risks before they become an emergency.

## How it works

```
Manager records an absence
        ↓
TalentReadiness checks skills + availability + workload
        ↓
Ranks suitable employees and explains the match
        ↓
Manager requests or assigns coverage
        ↓
Team stays supported and work continues
```

## Key features

| Feature | What it does |
| --- | --- |
| Smart replacement matching | Ranks candidates using required skills, proficiency, availability, workload capacity, role similarity, and project experience. |
| Availability management | Employees and managers can update daily availability and available hours. |
| Project coverage | Managers record absences, find suitable coverage, and assign temporary replacements. |
| Consent-based workflow | Coverage can require employee acceptance before an assignment is confirmed. |
| Manager dashboard | Shows active projects, staff availability, absences, and staffing-risk alerts. |
| Employee workspace | Lets employees maintain their profile, skills, availability, and coverage requests. |
| Transparent decisions | Shows why a person was recommended instead of using a black-box decision. |

## Hospital example

A hospital needs a qualified specialist when a nurse or doctor becomes unexpectedly unavailable. Instead of waiting one or two hours for a possible replacement or sending a patient to another hospital, the manager can use TalentReadiness to identify available staff with similar skills and relevant experience. The system supports the manager’s decision—it does **not** replace medical judgment or emergency procedures.

## Technology

- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** SQLite
- **Deployment:** Vercel (frontend) and Render (API)

## Run locally

```bash
# Clone the repository
git clone https://github.com/sujalrao061/talentreadiness.git
cd talentreadiness/talentreadiness

# Start the app with Docker
docker compose up --build
```

Then open the frontend at `http://localhost:5173`.

## Project structure

```
talentreadiness/
├── frontend/        # React user interface
├── backend/         # FastAPI API and matching logic
├── docker-compose.yml
└── README.md        # Detailed technical documentation
```

For more technical details, see the [project documentation](./talentreadiness/README.md).

## Built for a hackathon

TalentReadiness was designed as a practical, human-centered response to staff shortages. Its goal is simple: help teams find capable people faster, while keeping managers in control of the final decision.

---

Built by [Sujal K Rao](https://github.com/sujalrao061) · [Open the live demo](https://talentreadiness.vercel.app)
