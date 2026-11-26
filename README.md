# Personal Finance Tracker and Analytical Ledger Platform

A single-user INR ledger with a React dashboard, a FastAPI REST service, and twelve SQL reports. Record income or expenses, see the balance change, and trace a monthly total back to its entries. Amounts are stored as integer paise.

## Run locally with PostgreSQL

```sh
docker compose up --build -d
docker compose exec web python seed.py
```

Open **http://localhost:8000** for the dashboard or **http://localhost:8000/docs** for the API. The optional seed adds 18 fictional entries across three months. Running it again leaves the totals unchanged. The demo starts with ₹1,53,180 income, ₹55,482 spending and a ₹97,698 net balance. Add an expense of ₹50.25 to see the balance fall to ₹97,647.75.

Compose binds the app to the loopback interface. It uses a persistent PostgreSQL volume. This local, single-user demo has no authentication. Its two accounts track income and expenses without opening balances or transfer functionality.

## Follow a number from the dashboard to SQL

The dashboard calls `GET /api/dashboard`. In [reports.py](reports.py), a shared CTE joins entries to account and category dimensions. Income contributes a positive amount and expenses contribute a negative amount. Each report then aggregates or ranks the same signed ledger lines. The API reads the reports from one consistent database snapshot.

| Question | Reports |
| --- | --- |
| How much came in, went out, and remains? | Ledger totals, account balances, income sources |
| When did cash flow change? | Monthly flow, daily flow, change since previous recorded month |
| Where did spending go? | Category spending, five largest expenses, monthly category ranking |
| Which entries explain the movement? | Recent entries, chronological running balance, category frequency |

`LAG` compares recorded months, `DENSE_RANK` ranks categories within each month, and a windowed `SUM` reconstructs the running balance. Entries posted on the same date are ordered by their database IDs.

## REST API

| Method and route | Purpose |
| --- | --- |
| `GET /api/options` | Available accounts and categories |
| `POST /api/entries` | Record an income or expense using a category and positive amount in paise |
| `GET /api/dashboard` | All twelve reports, including recent entries |

A caller generates a UUID for each new entry. Repeating a request with the same key and fields returns its existing entry. Reusing a key with changed fields returns HTTP 409. Database foreign keys and positive-amount constraints protect the ledger.

## Run without Docker

Use Python 3.11+ and Node 22. The API uses local SQLite unless `DATABASE_URL` points to PostgreSQL.

```sh
python -m pip install -r requirements.txt
npm --prefix frontend install
npm --prefix frontend run build
python seed.py
python -m uvicorn ledger:app --port 8000
```

## Verification

Run `python -m pytest -q` for the API and SQL integration test against a temporary SQLite database. GitHub Actions runs it against PostgreSQL 16, builds React, opens the dashboard in Chromium, posts an expense, and checks the updated balance and transaction row.

[MIT License](LICENSE)
