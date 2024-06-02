from datetime import datetime
from uuid import uuid4

from pydantic import computed_field
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    email: str
    date: datetime = Field(default_factory=lambda: datetime.now())


class ProductBase(SQLModel):
    name: str
    price: float


class UserSchema(UserBase):
    password: str

    @computed_field
    @property
    def date_formated(self) -> str:
        return self.date.strftime('%d-%m-%Y')
