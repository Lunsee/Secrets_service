import logging
import os
import time
from sqlalchemy.exc import OperationalError
import pytz
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, func, inspect
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta, timezone
from app.db.models import Secrets
from fastapi import Depends
from app.db.base import Base

logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_NAME = os.getenv("DB_NAME", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# connect with reconnect
def connect_to_database():
    retries = 5
    while retries:
        try:
            with engine.connect() as connection:
                logger.info("Successfully connected to the database!")
                break
        except OperationalError as e:
            retries -= 1
            logger.warning(f"Database connection failed, retrying... {retries} retries left")
            time.sleep(2)
    else:
        logger.error("Failed to connect to the database after several attempts.")
        exit(1)

# check tables db
def create_tables():
    logger.info("Checking if tables exist and creating them if necessary...")
    try:
        inspector = inspect(engine)
        if not inspector.has_table(Secrets.__tablename__):
            Base.metadata.create_all(bind=engine)
            logger.info("Tables created successfully.")
        else:
            logger.info(f"Table '{Secrets.__tablename__}' already exists, skipping creation.")
    except Exception as e:
        logger.error(f"Error while creating tables: {e}")

def get_db():
    logger.info("Opening new database session.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.info("Database session closed.")


def delete_expired_secrets():
    db = SessionLocal()
    try:
        current_time = datetime.now(pytz.timezone("Europe/Moscow"))
        logger.info("Checking secrets for expiration at %s", current_time)


        secrets = db.query(Secrets).all()

        expired_secrets = []
        for secret in secrets:
            if secret.created_at.tzinfo is None:
                secret.created_at = pytz.timezone("Europe/Moscow").localize(secret.created_at)


            expiration_time = secret.created_at + timedelta(seconds=secret.ttl_seconds)


            if expiration_time <= current_time:
                expired_secrets.append(secret)


        for secret in expired_secrets:
            logger.info("secret id: %s - is timeout, he will be deleted", secret.id)
            db.delete(secret)
            logger.info("secret id: %s - was deleted", secret.id)
        db.commit()
    except Exception as e:
        logger.error(f"Error occurred while deleting expired secrets: {e}")

    finally:
        db.close()

