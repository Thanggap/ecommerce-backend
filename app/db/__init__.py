import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from colorama import Fore

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

Base = declarative_base()

# Create engine ONCE with connection pool
_engine = None

def get_db_engine():
    global _engine
    if _engine is None:
        try:
            # Connection pool settings for performance
            _engine = create_engine(
                DATABASE_URL,
                echo=False,  # Disable SQL logging for performance
                pool_size=10,  # Number of connections to keep in pool
                max_overflow=20,  # Extra connections allowed beyond pool_size
                pool_pre_ping=True,  # Check connection health before use
                pool_recycle=3600,  # Recycle connections after 1 hour
            )
            print(f"{Fore.GREEN}Database engine created with connection pool{Fore.WHITE}")
        except Exception as e:
            print(f"{Fore.RED}Error creating database engine: {e}{Fore.WHITE}")
            return None
    return _engine

# Create SessionLocal ONCE
_SessionLocal = None

def get_db_session():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_db_engine()
        _SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _SessionLocal()

def create_tables():
    engine = get_db_engine()
    Base.metadata.create_all(bind=engine)
