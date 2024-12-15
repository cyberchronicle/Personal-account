import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=os.environ.get("DOCKER_ENV", ".env"),
                                      env_file_encoding="utf-8")
    app_name: str = "Личный кабинет"
    app_host: str = "http://localhost"
    app_port: int = 8000
    app_desc: str = "Мастер-система личной информации пользователя, закладок и тегов"
    app_version: str = "0.1.0"
    debug: bool = False
    logging_level: str = "info"

    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # minio s3 settings
    minio_url: str = "localhost:9000"
    minio_root_user: str
    minio_root_password: str
    s3_bucket_name: str = "static"

    @property
    def build_postgres_dsn(self) -> str:
        res = (
            "postgresql://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        return res


cfg = Config()