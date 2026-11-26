import os
from uuid import uuid4
from fastapi.testclient import TestClient
from ledger import create_app, meta
from seed import seed


def test_totals_reports_and_posting(tmp_path):
    # CI supplies a disposable Postgres service; developer runs default to temporary SQLite.
    url=os.getenv("TEST_DATABASE_URL", "sqlite:///"+str(tmp_path/"test.db"))
    app=create_app(url)
    with TestClient(app) as client:
        seed(app.state.engine)
        seed(app.state.engine)
        data=client.get("/api/dashboard").json()
        assert len(data)==12 and len(data["recent_entries"])==18
        assert data["totals"][0]=={"income":15318000,"expense":5548200,"balance":9769800}
        assert data["running_balance"][0]["balance"]==9769800
        assert sum(a["balance"] for a in data["account_balances"])==9769800
        assert data["monthly_change"][0]["change"] is None
        assert data["monthly_spending_rank"][0]["category"]=="Rent"
        payload={"posted":"2026-04-01","account_id":1,"category_id":2,"note":"Fruit","amount_minor":12500,
                 "request_key":str(uuid4())}
        first=client.post("/api/entries",json=payload)
        assert first.status_code==200
        assert client.post("/api/entries",json=payload).json()["id"]==first.json()["id"]
        assert client.post("/api/entries",json={**payload,"amount_minor":2}).status_code==409
        assert client.post("/api/entries",json={**payload,"amount_minor":-1}).status_code==422
        assert client.post("/api/entries",json={**payload,"account_id":999}).status_code==422
        new=client.get("/api/dashboard").json()
        assert new["totals"][0]["balance"]==9769800-12500
        assert new["recent_entries"][0]["note"]=="Fruit"
