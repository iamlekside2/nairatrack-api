from datetime import date as date_type
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class Currency(str, Enum):
    NGN = "NGN"
    USD = "USD"


class Category(str, Enum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    DATA_AIRTIME = "Data & airtime"
    RENT = "Rent"
    ENTERTAINMENT = "Entertainment"
    HEALTH = "Health"
    OTHER = "Other"


class ExpenseBase(SQLModel):
    title: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Currency
    category: Category
    date: date_type

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()


class Expense(ExpenseBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseRead(ExpenseBase):
    id: int
