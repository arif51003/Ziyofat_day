from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SESSION_ID_EXPIRE_DAYS: int = 1


settings = Settings()
