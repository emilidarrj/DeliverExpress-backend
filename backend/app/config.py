"""Lectura de configuracion desde .env. roadmap_backend.txt §1."""
import os
from dotenv import load_dotenv

load_dotenv()  # busca backend/.env


class Settings:
    def __init__(self) -> None:
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://de_app:CLAVE@localhost:5432/deliverexpress",
        )
        self.listen_url: str = os.getenv(
            "LISTEN_URL",
            "postgresql://de_app:CLAVE@localhost:5432/deliverexpress",
        )
        self.jwt_secret: str = os.getenv("JWT_SECRET", "cambiar_esto")
        self.jwt_expira_min: int = int(os.getenv("JWT_EXPIRA_MIN", "480"))
        # "a,b,c" -> ["a","b","c"]
        self.cors_origins: list[str] = [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        ]


settings = Settings()