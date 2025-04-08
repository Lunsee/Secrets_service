import pytz
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
#from app.db.database import Base
from app.db.base import Base

class Secrets(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    secret = Column(String, nullable=False)
    secret_key = Column(String, unique=True, nullable=False,index=True)
    passphrase = Column(String, nullable=True)
    ttl_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone("Europe/Moscow")))
    #ip_address = Column(String, nullable=True)
    is_revealed = Column(Boolean, default=False) # раскрыт секрет или нет
    revealed_at = Column(DateTime, nullable=True)
    #revealed_ip = Column(String, nullable=True)



    # datetime.now(pytz.UTC) +0 london