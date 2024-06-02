from uuid import uuid4

from sqlmodel import Field

from schema import ProductBase


class Product(ProductBase, table=True):
    __tablename__ = "products"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
