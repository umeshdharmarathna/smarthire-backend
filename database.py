import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Supabase PostgreSQL (Cloud) -> Local MySQL (XAMPP) -> SQLite fallback
DATABASE_URL = os.getenv("POSTGRES_URL_NON_POOLING") or os.getenv("DATABASE_URL") or "sqlite:///./database.db"

# SQLAlchemy needs "postgresql://" not "postgres://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine_args = {}
if "sqlite" in DATABASE_URL:
    engine_args["connect_args"] = {"check_same_thread": False}
elif "supabase" in DATABASE_URL:
    engine_args["connect_args"] = {"sslmode": "require"}
    engine_args["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
