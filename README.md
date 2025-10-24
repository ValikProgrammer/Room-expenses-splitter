
# Project: Roommate Expense Tracker

A lightweight Flask web app to track shared expenses for a room/flat.  
Core idea: create a room (group of members), add transactions (who paid, how cost is split), view history, compute per-person net balances and suggested settlement payments, and show simple charts.

Key behaviors:
- Record transactions with explicit per-person shares (avoids rounding mismatch).
- Compute net balance per member: positive = owed, negative = owes.
- Provide a settlement plan (greedy matcher) suggesting who pays whom.
- Minimal, responsive UI (Jinja2 + Bootstrap) with REST API for integration.

Purpose: quick MVP for coursework: Dockerized, tested, with Swagger docs and CI pipeline.


<!-- PAGES.md -->

## Pages (UI overview)

These are the main user-facing pages for the MVP.

### `/`
- Quick Add Transaction form.
- Choose room, date, description, payer, total, split type (equal/custom), and comment.

### `/rooms/create`
- Create a room and add members (names or link to users).

### `/transactions`
- Transactions table for selected room.
- Columns: Date, Description, Total, Payer, #Participants, Price per each, Comment, Actions (Edit, Remove).
- Search, sort, pagination, filters.

### `/transactions/<id>/edit`
- Edit transaction form (modal or page) showing shares.

### `/results`
- Per-member net balances.
- Suggested settlement transactions (who pays whom).
- Charts: donut/pie for total paid by member; bar for net owed.

### `/login`, `/register`, `/logout`
- Authentication pages.

### `/api/docs` (Swagger)
- Interactive API documentation.


<!-- ROUTES.md -->

## Routes & API Endpoints

### UI (server-rendered)
- `GET /` — Home / add-transaction form
- `GET /rooms/create` — Create room form
- `GET /transactions` — Transactions table (room context)
- `GET /transactions/<id>/edit` — Edit form
- `POST /transactions/<id>/remove` — Delete (or use API delete)
- `GET /results` — Balances + settlement + charts
- `GET /login`, `POST /login` — Login
- `GET /register`, `POST /register` — Register

### REST API (JSON)
- `GET  /api/rooms`  
  -> list rooms

- `POST /api/rooms`  
  Payload: `{ name, currency, members: [names or member_ids] }`

- `GET  /api/rooms/<room_id>/members`  
  -> members list

- `GET  /api/transactions?room_id=&page=&per_page=&sort=&q=&date_from=&date_to=&payer_id=&member_id=`  
  -> paginated transaction list

- `GET  /api/transactions/<id>`  
  -> transaction detail (includes `shares`)

- `POST /api/transactions`  
  Payload example:
  ```json
  {
    "room_id":1,
    "date":"2025-10-23",
    "description":"Groceries",
    "total_amount":43.44,
    "payer_member_id":2,
    "shares":[{"member_id":1,"owes_amount":14.48}, ...],
    "comment":"weekly shop"
  }


### Tech Stack 

- **Backend:** Flask (app factory + blueprints)  
- **ORM / DB:** SQLAlchemy + Alembic (Flask-Migrate)  
- **Database:** SQLite (development) / PostgreSQL (production)  
- **Auth:** Flask-Login (session-based)  
- **Frontend:** Jinja2 templates + Bootstrap; Chart.js for charts  
- **Containerization:** Docker + docker-compose  
- **Testing:** pytest (unit + integration)  
- **API docs:** Swagger (Flasgger or flask-restx)  
- **CI:** GitHub Actions (tests, linters, image build)  
- **CD:** Any Docker-capable host (Render / Railway / Fly / DigitalOcean / AWS etc.)




## Main TODO 

### Setup & infra
- [ ] Git repo + `.gitignore`, branches (`develop`, `main`)
- [ ] Dockerfile + docker-compose
- [ ] GitHub Actions workflow: run tests, linters, build image
- [ ] Swagger setup (`/api/docs`)

### Core models & DB
- [ ] Implement models: User, Room, RoomMember, Transaction, TransactionShare, Payment (optional)
- [ ] Alembic migrations
- [ ] Seed script (dev data)

### Auth & rooms
- [ ] Registration & login (Flask-Login)
- [ ] Room creation & member management
- [ ] Authorization checks (room-only access)

### Transactions
- [ ] Add transaction (explicit `shares`) — server + UI
- [ ] List transactions with search/sort/pagination
- [ ] Edit & delete transactions (API + UI)
- [ ] Validation: shares sum == total (with small rounding tolerance)

### Balances & settlement
- [ ] Implement per-member balances endpoint
- [ ] Implement settlement endpoint (greedy algorithm)
- [ ] Unit tests for both

### Frontend & UX
- [ ] `/` quick-add form
- [ ] `/transactions` table with actions
- [ ] `/results` page with charts (Chart.js)
- [ ] Responsive layout, form validation

### Testing & quality
- [ ] Unit tests for models and business logic
- [ ] Integration/API tests
- [ ] Linting (black, flake8) integrated into CI
- [ ] Coverage report

### Production readiness
- [ ] Environment variable config (SECRET_KEY, DATABASE_URL)
- [ ] HTTPS and secure headers
- [ ] Logging (stdout + rotating file)
- [ ] Healthcheck endpoint
- [ ] Backup strategy for DB

