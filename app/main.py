import re
from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session, init_db
from app.models import Currency, Expense, ExpenseCreate, ExpenseRead
from app.rates import get_usd_to_ngn

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

TWO_PLACES = Decimal("0.01")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="NairaTrack API",
    description="Track expenses in NGN and USD. Built on the OS Techs channel.",
    version="1.0.0",
    lifespan=lifespan,
)


def validate_month(month: str) -> str:
    if not MONTH_PATTERN.match(month):
        raise HTTPException(
            status_code=422, detail="month must look like YYYY-MM, e.g. 2026-10"
        )
    return month


@app.post("/expenses", response_model=ExpenseRead, status_code=201)
def create_expense(payload: ExpenseCreate, session: Session = Depends(get_session)):
    expense = Expense.model_validate(payload)
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


@app.get("/expenses", response_model=list[ExpenseRead])
def list_expenses(
    month: str | None = Query(default=None, description="Filter by month, YYYY-MM"),
    session: Session = Depends(get_session),
):
    query = select(Expense).order_by(Expense.date.desc(), Expense.id.desc())
    if month is not None:
        validate_month(month)
        query = query.where(Expense.date >= f"{month}-01", Expense.date <= f"{month}-31")
    return session.exec(query).all()


@app.get("/expenses/{expense_id}", response_model=ExpenseRead)
def get_expense(expense_id: int, session: Session = Depends(get_session)):
    expense = session.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, session: Session = Depends(get_session)):
    expense = session.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    session.delete(expense)
    session.commit()


@app.get("/summary")
def summary(
    month: str = Query(description="Month to summarise, YYYY-MM"),
    session: Session = Depends(get_session),
):
    validate_month(month)
    expenses = session.exec(
        select(Expense).where(
            Expense.date >= f"{month}-01", Expense.date <= f"{month}-31"
        )
    ).all()

    rate, rate_source = get_usd_to_ngn()

    total_ngn = Decimal("0")
    for e in expenses:
        if e.currency == Currency.NGN:
            total_ngn += e.amount
        else:
            total_ngn += e.amount * rate

    total_ngn = total_ngn.quantize(TWO_PLACES)
    total_usd = (total_ngn / rate).quantize(TWO_PLACES)

    by_category: dict[str, Decimal] = {}
    for e in expenses:
        ngn_value = e.amount if e.currency == Currency.NGN else e.amount * rate
        key = e.category.value
        by_category[key] = (by_category.get(key, Decimal("0")) + ngn_value).quantize(
            TWO_PLACES
        )

    return {
        "month": month,
        "count": len(expenses),
        "total_ngn": str(total_ngn),
        "total_usd": str(total_usd),
        "usd_to_ngn_rate": str(rate),
        "rate_source": rate_source,
        "by_category_ngn": {k: str(v) for k, v in sorted(by_category.items())},
    }
