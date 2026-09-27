import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env ubicado en la carpeta backend
load_dotenv()

class Settings:
    PROJECT_NAME: str = "DeliverExpress API"
    
    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://usuario:password@localhost:5432/nombre_db")
    
    # Seguridad / JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS (permitir orígenes del frontend)
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

settings = Settings()