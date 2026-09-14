# AI Inventory Management System

A full-stack AI-powered inventory management system built with FastAPI, React, and Neon PostgreSQL.

## Features

- **Product Management** — Full CRUD with search, filtering, pagination
- **Stock Management** — Track stock changes with complete history
- **Sales Management** — Record sales with automatic stock deduction
- **Dashboard** — Real-time analytics with charts (Recharts)
- **AI Predictions** — Demand forecasting, low-stock alerts, reorder recommendations
- **Authentication** — JWT-based with access & refresh tokens
- **Authorization** — Role-based access control (Admin / Staff)
- **Responsive UI** — Modern admin dashboard with Tailwind CSS

## Tech Stack

| Layer       | Technology                                      |
|-------------|------------------------------------------------|
| Frontend    | React.js, Vite, Tailwind CSS, Recharts, Axios |
| Backend     | Python, FastAPI, SQLAlchemy, Alembic           |
| Database    | Neon PostgreSQL                                 |
| AI/ML       | Pandas, NumPy, Scikit-learn                    |
| Auth        | JWT, OAuth2 Password Flow, bcrypt              |

## Architecture

```
AI-Inventory-System/
├── backend/          # FastAPI REST API
│   ├── app/
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── routers/      # API route handlers
│   │   └── services/     # Business logic
│   ├── alembic/          # Database migrations
│   └── requirements.txt
├── frontend/         # React + Vite SPA
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client (Axios)
│   │   ├── context/      # React Context (Auth)
│   │   └── routes/       # Route protection
│   └── package.json
└── README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- A [Neon PostgreSQL](https://neon.tech) account and database

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd AI-Inventory-System
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your Neon PostgreSQL connection string and a secure secret key:

```
DATABASE_URL=postgresql://user:password@ep-xxx-xxx.region.aws.neon.tech/dbname?sslmode=require
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 3. Database Migrations

```bash
alembic upgrade head
```

### 4. Run the Backend

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 5. Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000/api
```

### 6. Run the Frontend

```bash
npm run dev
```

App available at: `http://localhost:5173`

## API Endpoints

| Method | Endpoint                      | Description          | Auth     |
|--------|-------------------------------|----------------------|----------|
| POST   | /api/auth/register            | Register a new user  | Public   |
| POST   | /api/auth/login               | Login                | Public   |
| POST   | /api/auth/refresh             | Refresh token        | Public   |
| GET    | /api/auth/me                  | Current user         | Required |
| GET    | /api/products                 | List products        | Required |
| POST   | /api/products                 | Create product       | Admin    |
| GET    | /api/products/{id}            | Get product          | Required |
| PUT    | /api/products/{id}            | Update product       | Admin    |
| DELETE | /api/products/{id}            | Delete product       | Admin    |
| POST   | /api/stock/adjust             | Adjust stock         | Required |
| GET    | /api/stock/history            | Stock history        | Required |
| GET    | /api/sales                    | List sales           | Required |
| POST   | /api/sales                    | Create sale          | Required |
| GET    | /api/sales/{id}               | Get sale             | Required |
| GET    | /api/dashboard                | Dashboard stats      | Required |
| GET    | /api/ai/demand-prediction     | Demand prediction    | Required |
| GET    | /api/ai/low-stock-prediction  | Low stock prediction | Required |
| GET    | /api/ai/reorder-recommendations| Reorder recs        | Required |

## Testing

```bash
cd backend
pytest -v
```

## Environment Variables

### Backend (.env)

| Variable                     | Description                       | Default |
|------------------------------|-----------------------------------|---------|
| DATABASE_URL                 | Neon PostgreSQL connection string | —       |
| SECRET_KEY                   | JWT signing secret                | —       |
| ACCESS_TOKEN_EXPIRE_MINUTES  | Access token lifetime             | 30      |
| REFRESH_TOKEN_EXPIRE_DAYS    | Refresh token lifetime            | 7       |
| CORS_ORIGINS                 | Allowed CORS origins              | —       |

### Frontend (.env)

| Variable     | Description        | Default                  |
|--------------|--------------------|--------------------------|
| VITE_API_URL | Backend API base URL | http://localhost:8000/api |

## License

MIT
