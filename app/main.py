import os
from app.db.database import engine, Base, connect_to_database, create_tables
from dotenv import load_dotenv
from fastapi import FastAPI
import logging
from app import routes
from app.db.database import delete_expired_secrets
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends
from app.db.database import get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)



app = FastAPI()


# create planner
scheduler = BackgroundScheduler() # planner time


def start_scheduler():
    try:
        # planner start for delete timeout secrets every 1 min
        scheduler.add_job(delete_expired_secrets, 'interval', minutes=1)
        scheduler.start()
        logger.info("Scheduler started successfully.")
    except Exception as e:
        logger.error(f"Error while starting scheduler: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("Startup initialization begining...")

    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")  #env url
    logger.info(f".env file path: {dotenv_path}")


    load_dotenv(dotenv_path) #Load .env file

    if os.path.exists(dotenv_path):
        logger.info(".env file successfully found.")
    else:
        logger.warning(".env file not found or failed to load.")

    connect_to_database()
    create_tables()

    start_scheduler()
    logger.info("Startup initialization completed.")

app.include_router(routes.router, tags=["routes"]) #endpoints