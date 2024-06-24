from enum import Enum
from typing import Optional

from pydantic import Field, StringConstraints, computed_field, field_validator
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated, ClassVar


class DatabaseTypes(str, Enum):
    MYSQL = 'mysql'
    POSTGRES = 'postgres'
    MARIADB = 'mariadb'


MotorString = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True,
                           pattern=r'^[postgres|mysql|mariadb]')]


class Settings(BaseSettings):
    # ENV VARIABLE FOR CONNECT TO DB
    DB_LOCALHOST: str = Field(default='localhost')
    DB_NAME: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_PORT: int = Field(default=5432)
    DB_URI: Optional[str] = None
    DB_SCHEME: str = Field(..., description='Database engine driver', examples=[
        'psycopg2'])
    DB_MOTOR: MotorString = Field(
        ..., description='Database engine', examples=['postgres', 'myqsl', 'mariadb'])

    _allowed_schemes: ClassVar[str] = ['psycopg2',
                                       'psycopg', 'pg8000', 'asyncpg', 'psycopg2cffi']

    _db_motors: ClassVar[str] = ['postgres', 'myqsl', 'mariadb']

    @field_validator('DB_SCHEME')
    @classmethod
    def verify_scheme(cls, value: str):
        if isinstance(value, str):
            if value not in cls._allowed_schemes:
                raise ValueError(
                    f'Database drive not found in: {str(cls._allowed_schemes)}')
            return value

    @field_validator('DB_MOTOR')
    @classmethod
    def verify_db_motor(cls, value: str):
        if isinstance(value, str):
            if value not in cls._db_motors:
                raise ValueError(
                    f'Database engine not found in: {str(cls._db_motors)} ')
            return value

    @computed_field
    @property
    def uri(self) -> str:
        _scheme = ""

        if self.DB_URI is not None and self.DB_URI != "":
            return self.DB_URI

        if self.DB_MOTOR == DatabaseTypes.MYSQL:
            _scheme = 'mysql+'
        if self.DB_MOTOR == DatabaseTypes.POSTGRES:
            _scheme = 'postgresql+'
        if self.DB_MOTOR == DatabaseTypes.MARIADB:
            _scheme = 'mariadb+'

        _scheme += self.DB_SCHEME

        return MultiHostUrl.build(scheme=_scheme, host=self.DB_LOCALHOST,
                                  username=self.DB_USERNAME,
                                  password=self.DB_PASSWORD, port=self.DB_PORT, path=self.DB_NAME).unicode_string()

    model_config = SettingsConfigDict(
        env_file='../.env', env_file_encoding='utf-8', extra='ignore')


config = Settings()
