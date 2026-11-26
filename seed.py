"""Add a repeatable fictional INR ledger for a three-month dashboard demo."""
import os
from uuid import NAMESPACE_URL, uuid5
from ledger import Entry, configure, initialize, post


def seed(engine):
    initialize(engine)
    with engine.begin() as conn:
        for month in (1, 2, 3):
            for day, account, category, note, amount in [
                (1,1,1,"Monthly salary",4500000),(3,1,3,"Flat rent",1400000),(8,2,2,"Market groceries",325000+month*1200),
                (15,1,5,"Weekend design work",600000+month*3000),(18,2,4,"Transit pass",80000),(24,1,6,"Cinema",42000)]:
                stamp = f"2026-{month:02d}-{day:02d}"
                post(conn, Entry(request_key=uuid5(NAMESPACE_URL,f"demo-ledger/{stamp}"), posted=stamp,
                                 account_id=account,category_id=category,note=note,amount_minor=amount))


if __name__ == "__main__":
    engine = configure(os.getenv("DATABASE_URL","sqlite:///ledger.db"))
    seed(engine)
    engine.dispose()
