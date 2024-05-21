from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    auth_key: str = Field(..., validation_alias='my_auth_key')

    # Añadimos soporte de Dotenv -> https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support
    model_config = SettingsConfigDict(env_file='../.env', env_file_encoding='utf-8', extra='ignore')


config = Settings()
