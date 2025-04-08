import os
from fastapi import Request
from fastapi import Response, Query
import pytz
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Annotated
from app.db.database import get_db, delete_expired_secrets
from app.db.models import Secrets
import logging
from app.crypto import encrypt_secret,decrypt_secret
from datetime import datetime, timedelta, timezone
from app.key_generator import generate_unique_key
from typing import Optional


logger = logging.getLogger(__name__)
router = APIRouter()

time_to_save_sec_default = int(os.getenv("TIME_TO_SAVE_SECONDS_DEFAULT", 300))

class CreateSecret(BaseModel):
    secret_text: str
    passphrase: Optional[str] = Field(None, description="Optional passphrase for the secret")
    ttl_seconds: Optional[int] = Field(None, description="Optional TTL in seconds for the secret")


class DeleteSecretRequest(BaseModel):
    secret_key: str
    passphrase: Optional[str] = None





@router.post("/secret" , response_model=dict)
def create_secret(response:Response, request: Request,user_data: CreateSecret, db: Session = Depends(get_db)):
    logger.info("Create Secret endpoint - Attempt to add secret: %s", user_data.secret_text)

    #http lock cache
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    ip_address = request.client.host

    ttl_seconds = user_data.ttl_seconds if user_data.ttl_seconds else time_to_save_sec_default
    new_secret = Secrets(
        secret=encrypt_secret(user_data.secret_text),
        secret_key=generate_unique_key(),
        passphrase=user_data.passphrase,
        ttl_seconds=ttl_seconds,
        created_at=datetime.now(pytz.timezone("Europe/Moscow"))
        )
    db.add(new_secret)
    db.commit()

    logger.info(f"Secret created successfully with ID: {new_secret.id}, IP: {ip_address}, TTL: {ttl_seconds} seconds")
    return JSONResponse(content={"message": "Secret was added successfully", "unique_access_key": new_secret.secret_key}, status_code=201)



@router.get("/secret/{secret_key}")
def get_secret(response:Response,secret_key: str, request: Request, db: Session = Depends(get_db)):
    logger.info(f"Attempt to retrieve secret with secret_key: {secret_key}")

    # http lock cache
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    try:
        ip_address = request.client.host
        secret = db.query(Secrets).filter(Secrets.secret_key == secret_key).first()  # check key
        if secret:
            logger.info(f" secret_key is find on db: {secret_key}")
            if secret.is_revealed:
                logger.warning(f"Secret with key {secret_key} already revealed and cannot be retrieved again.")
                raise HTTPException(status_code=400, detail="This secret has already been revealed.")
            else:
                secret.is_revealed = True
                secret.revealed_at = datetime.now(pytz.timezone("Europe/Moscow")) # запись раскрытия секрета
                db.commit()
                logger.info(f"Secret with ID: {secret.id} was successfully retrieved. IP: {ip_address}")
                return JSONResponse(content={"secret":decrypt_secret(secret.secret)},status_code=200)
        else:
            logger.error(f"Secret with key {secret_key} not found.")
            raise HTTPException(status_code=404, detail="Secret not found.")

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"An error occurred while getting secret with used secret key: {secret_key}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")



@router.delete("/delete/{secret_key}")
def delete_secret(response:Response,secret_key: str, request: Request, db: Session = Depends(get_db),passphrase: str = Query(None),):
    logger.info(f"Attempt to delete secret with secret_key: {secret_key}")

    # http lock cache
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    try:
        ip_address = request.client.host
        secret = db.query(Secrets).filter(Secrets.secret_key == secret_key).first()  # check key
        if secret:
            logger.info(f" secret_key is find on db: {secret_key}")

            if secret.passphrase is not None:
                if passphrase is None:
                    logger.warning(f"Passphrase required but not provided for key: {secret_key}")
                    raise HTTPException(status_code=403, detail="Passphrase required.")
                if secret.passphrase != passphrase:
                    logger.warning(f"Incorrect passphrase for key: {secret_key}")
                    raise HTTPException(status_code=403, detail="Invalid passphrase.")

            db.delete(secret)
            db.commit()
            logger.info(f"Secret with ID: {secret.id} was successfully deleted by IP: {ip_address}")
            return JSONResponse(content={"status":"secret deleted"},status_code=200)
        else:
            logger.error(f"Secret with key {secret_key} not found.")
            raise HTTPException(status_code=404, detail="Secret not found.")
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"An error occurred while deleting secret {secret_key}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.")

