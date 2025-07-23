from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_database_url

SQLALCHEMY_DATABASE_URL = get_database_url()

#engine = create_engine(SQLALCHEMY_DATABASE_URL)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=50,           # Número de conexiones activas
    max_overflow=30,        # Conexiones adicionales temporales
    pool_timeout=300,        # Espera máxima (segundos) antes de lanzar error
    pool_pre_ping=True      # Verifica conexiones inactivas automáticamente
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
