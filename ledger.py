"""Single-user cash ledger, amounts in INR minor units."""
import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import (BigInteger, CheckConstraint, Column, Date, ForeignKey, Integer, MetaData,
                        String, Table, create_engine, event, select, text)
from reports import REPORTS

meta = MetaData()
accounts = Table("accounts", meta, Column("id", Integer, primary_key=True), Column("name", String(60), nullable=False, unique=True))
categories = Table("categories", meta, Column("id", Integer, primary_key=True), Column("name", String(60), nullable=False, unique=True),
                   Column("kind", String(8), nullable=False), CheckConstraint("kind IN ('income','expense')"))
entries = Table("entries", meta, Column("id", Integer, primary_key=True), Column("request_key", String(36), nullable=False, unique=True),
                Column("posted", Date, nullable=False, index=True), Column("account_id", ForeignKey("accounts.id"), nullable=False),
                Column("category_id", ForeignKey("categories.id"), nullable=False), Column("note", String(120), nullable=False),
                Column("amount_minor", BigInteger, nullable=False), CheckConstraint("amount_minor > 0"))


class Entry(BaseModel):
    request_key: UUID
    posted: date
    account_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    note: str = Field(min_length=1, max_length=120)
    amount_minor: int = Field(strict=True, gt=0, le=10**12)


def configure(url):
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def enable_fks(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    return engine


def initialize(engine):
    meta.create_all(engine)
    with engine.begin() as conn:
        for i, name in [(1,"Current account"), (2,"Cash wallet")]:
            conn.execute(text("INSERT INTO accounts (id,name) VALUES (:id,:n) ON CONFLICT (id) DO NOTHING"), {"id":i,"n":name})
        for i, name, kind in [(1,"Salary","income"),(2,"Groceries","expense"),(3,"Rent","expense"),
                              (4,"Transport","expense"),(5,"Freelance","income"),(6,"Leisure","expense")]:
            conn.execute(text("INSERT INTO categories (id,name,kind) VALUES (:i,:n,:k) ON CONFLICT (id) DO NOTHING"),
                         {"i":i,"n":name,"k":kind})


def post(conn, entry):
    data = entry.model_dump()
    data["request_key"] = str(entry.request_key)
    if not all(conn.scalar(select(table.c.id).where(table.c.id == data[key])) is not None
               for table, key in [(accounts,"account_id"), (categories,"category_id")]):
        raise HTTPException(422, "Unknown account or category")
    stmt = text("INSERT INTO entries (request_key,posted,account_id,category_id,note,amount_minor) "
                "VALUES (:request_key,:posted,:account_id,:category_id,:note,:amount_minor) "
                "ON CONFLICT (request_key) DO NOTHING")
    conn.execute(stmt, data)
    saved = conn.execute(select(entries).where(entries.c.request_key == data["request_key"])).mappings().one()
    if any(saved[k] != v for k, v in data.items()):
        raise HTTPException(409, "This request key already belongs to another entry.")
    return dict(saved)


def create_app(url=None):
    engine = configure(url or os.getenv("DATABASE_URL", "sqlite:///ledger.db"))

    @asynccontextmanager
    async def lifespan(_):
        initialize(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Personal Finance Ledger", lifespan=lifespan)
    app.state.engine = engine

    @app.get("/api/options")
    def options():
        with engine.connect() as conn:
            return {t.name: [dict(r) for r in conn.execute(select(t).order_by(t.c.id)).mappings()]
                    for t in (accounts,categories)}

    @app.post("/api/entries")
    def add(entry: Entry):
        with engine.begin() as conn:
            return post(conn, entry)

    @app.get("/api/dashboard")
    def dashboard():
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                conn = conn.execution_options(isolation_level="REPEATABLE READ")
            else:
                conn.exec_driver_sql("BEGIN")
            return {name:[dict(row) for row in conn.execute(text(sql)).mappings()] for name, sql in REPORTS.items()}

    build = Path(__file__).parent/"frontend"/"dist"
    if build.is_dir():
        app.mount("/", StaticFiles(directory=build, html=True), name="dashboard")
    return app


app = create_app()
