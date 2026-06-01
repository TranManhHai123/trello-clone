# 🗂️ Trello Clone — Real-Time Task Management

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, JWT Auth
- **Frontend:** Next.js 13+, Zustand, Tailwind CSS, @hello-pangea/dnd
- **Architecture:** Layered Architecture (Presentation → API → Service → Repository → DB)

## Features

- ✅ Register / Login (JWT)
- ✅ Project Management (CRUD)
- ✅ Kanban Board — drag & drop tasks between 3 columns
- ✅ RBAC — Owner / Member role-based access control
- ✅ Assign tasks to project members
- ⏳ WebSocket Real-time (in progress)

## Getting Started

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Create `backend/.env`:
```
DATABASE_URL=postgresql://user:pass@localhost:5432/trello_db
SECRET_KEY=your-secret-key
```
