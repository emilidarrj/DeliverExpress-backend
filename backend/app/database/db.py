from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Crea el motor de conexión forzando el esquema "deliverexpress"
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"options": "-c search_path=deliverexpress"}
)

# Configura la sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos de SQLAlchemy
Base = declarative_base()

# Dependencia para obtener la sesión en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()