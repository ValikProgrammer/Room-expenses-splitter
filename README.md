# Room Expense Splitter (single-room edition)

Simple Flask app for tracking shared expenses in a single room with a fixed list of members (no auth, one room only).

## Features

- Add expenses via simple form (`/`): date, description, payer, participants, comment; cost is split evenly.
- `/transactions`: sortable table of expenses, participant filter, quick access to balances.
- `/balances`: per-person breakdown showing who owes whom.
- `/members/add`: add/rename/delete members (deletion blocked if referenced by transactions).
- `/diagrams`: donut charts for number of payments per person and total amount paid.
- REST API: `GET /api/members`, `GET/POST /api/transactions`.
- Health endpoint `GET /health`.
- `client.py` uses `requests` to smoke-test main endpoints.

## Tech stack

- Python 3.11, Flask, Flask-SQLAlchemy, Jinja2, Bootstrap 5.
- SQLite stored in `instance/room_expenses.db` (auto-created).
- Docker for containerized runs.
- Requests for basic client checks (`client.py`).

## Testing
### Run unit and integration tests
```bash
pytest
```
### Test the running app
```bash
python client.py
```

## Docker

Build and run the application:

```bash
docker build -t room-expense-app .
docker run -p 5000:5000 \
  -v "$(pwd)/instance:/app/instance" \
  room-expense-app
```

The SQLite file located in `instance/room_expenses.db`.    
Override DB location via `DATABASE_URL` if needed.

## Routes overview

### UI

- `GET /` – add expense form (and handles submissions).
- `GET /transactions` – list of transactions with sorting/filtering.
- `GET|POST /transactions/<id>/edit` – edit existing transaction.
- `POST /transactions/<id>/delete` – delete transaction.
- `GET /balances` – per-person owed/owes breakdown.
- `GET|POST /members/add` – manage members (add + list).
- `POST /members/<id>/edit` – rename member.
- `POST /members/<id>/delete` – remove member (if unused).
- `GET /diagrams` – charts with payments count and volume.

### API

- `GET /api/members` – JSON list of members.
- `GET /api/transactions` – JSON list of transactions (supports `sort` and `member_id`).
- `POST /api/transactions` – create transaction from JSON payload.
- `GET /health` – basic health check.

