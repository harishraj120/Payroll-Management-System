"""Application configuration loaded from environment variables."""
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("MYSQL_HOST", "localhost")
    port: int = int(os.getenv("MYSQL_PORT", "3306"))
    user: str = os.getenv("MYSQL_USER", "root")
    password: str = os.getenv("MYSQL_PASSWORD", "")
    database: str = os.getenv("MYSQL_DATABASE", "payroll_management")
    export_directory: str = os.getenv("EXPORT_DIRECTORY", "exports")

    @property
    def export_path(self) -> Path:
        value = Path(self.export_directory)
        return value if value.is_absolute() else PROJECT_ROOT / value


settings = Settings()
